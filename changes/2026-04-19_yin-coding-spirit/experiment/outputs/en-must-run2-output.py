#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

This is Layer 1 of the two-layer architecture:
- Layer 1 (this): passively capture data, no analysis
- Layer 2 (learnings-observer agent): background Haiku analyzes and writes learnings

Observations are append-only JSONL. Each line:
{
  "timestamp": "ISO8601",
  "session_id": "...",
  "type": "user_prompt",
  "content": "truncated user message",
  "cwd": "..."
}
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# Shared-state helpers live next to this script. The sys.path insertion is the
# designated source of truth for how the hook locates `learnings_state` — do
# not duplicate this shim elsewhere.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
import learnings_state  # noqa: E402  (import must follow sys.path mutation)


# ── Tunables ────────────────────────────────────────────────────────────────
# Closed boundaries: these constants mark future bets (OCP). If observation
# volume changes by an order of magnitude, revisit MAX_CONTENT_LENGTH and
# ARCHIVE_SIZE_MB together — they jointly bound disk usage.
MAX_CONTENT_LENGTH = 3000  # chars per observation (anti-bloat)
PURGE_AGE_DAYS = 30  # archives older than this are deleted
PURGE_INTERVAL_SEC = 86400  # purge at most once per day
ARCHIVE_SIZE_MB = 10  # rotate observations.jsonl above this size
GIT_TOPLEVEL_TIMEOUT_SEC = 3

# Secret scrubbing: single source of truth for the redaction pattern.
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


def scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED]."""
    return _SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
        text,
    )


# ── Project-directory resolution ────────────────────────────────────────────
def _git_toplevel(cwd: str) -> str:
    """Return `git rev-parse --show-toplevel` for cwd, or "" on any failure."""
    if not cwd or not os.path.isdir(cwd):
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=GIT_TOPLEVEL_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired, FileNotFoundError, OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def resolve_project_dir(cwd: str) -> str:
    """
    Resolve the project root. Prefers CLAUDE_PROJECT_DIR env var, falls back
    to the git top-level of cwd. Returns "" if neither is available.
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env_dir:
        return env_dir
    return _git_toplevel(cwd)


# ── Hook payload extraction ─────────────────────────────────────────────────
@dataclass(frozen=True)
class HookPayload:
    """Parsed subset of the Claude Code hook JSON we care about.

    Single failure mode (SRP): malformed or empty stdin → `parse` returns None.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)


def _extract_content(tool_input: object) -> str:
    """UserPromptSubmit delivers the message in tool_input.{content|message}."""
    if isinstance(tool_input, dict):
        return tool_input.get("content", tool_input.get("message", "")) or ""
    return str(tool_input) if tool_input is not None else ""


def parse_hook_payload(raw: str) -> Optional[HookPayload]:
    """Parse hook JSON from stdin text. Returns None if unusable."""
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError, ValueError:
        return None
    if not isinstance(data, dict):
        return None

    tool_input = data.get("tool_input", data.get("input", {}))
    content = _extract_content(tool_input)
    if not content:
        return None

    return HookPayload(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", "") or "",
        content=content,
        agent_id=data.get("agent_id", "") or "",
    )


# ── Observation I/O ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ObservationPaths:
    """Designated source of truth for per-project observation file layout."""

    learnings_dir: str
    observations_file: str
    archive_dir: str
    purge_marker: str

    @classmethod
    def for_project(cls, project_dir: str) -> "ObservationPaths":
        learnings_dir = os.path.join(project_dir, ".learnings")
        return cls(
            learnings_dir=learnings_dir,
            observations_file=os.path.join(learnings_dir, "observations.jsonl"),
            archive_dir=os.path.join(learnings_dir, "observations.archive"),
            purge_marker=os.path.join(learnings_dir, ".last-purge"),
        )


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_observation(payload: HookPayload) -> dict:
    """Construct the JSONL record, scrubbing secrets and enforcing length."""
    clean = scrub_secrets(payload.content[:MAX_CONTENT_LENGTH])
    return {
        "timestamp": _iso_utc_now(),
        "session_id": payload.session_id,
        "type": "user_prompt",
        "content": clean,
        "cwd": payload.cwd,
    }


def append_observation(observations_file: str, observation: dict) -> bool:
    """Append one JSONL record. Returns True on success, False on I/O error."""
    try:
        with open(observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError, OSError:
        return False


# ── Layer 1 → Layer 2 bridge ────────────────────────────────────────────────
def bridge_to_observer(project_dir: str) -> None:
    """
    Layer 1 → Layer 2 bridge:
    1. Increment observation counter
    2. Lazy-start observer daemon if not running
    3. Send SIGUSR1 every N observations (throttled)

    All failures are silent — hook must never block the user's session.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        _lazy_start_daemon(project_dir)
        # No signal on the same invocation that started the daemon.
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            # Daemon died or is inaccessible; leave counter alone so the next
            # invocation re-tries lazy-start.
            pass


def _lazy_start_daemon(project_dir: str) -> None:
    """Spawn the observer daemon detached. Silent on failure."""
    start_script = os.path.join(_SCRIPT_DIR, "start-observer.sh")
    if not os.path.exists(start_script):
        return
    try:
        subprocess.Popen(
            ["bash", start_script, project_dir],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError, subprocess.SubprocessError:
        pass


# ── Auto-purge / rotation ───────────────────────────────────────────────────
def _should_purge(purge_marker: str) -> bool:
    if not os.path.exists(purge_marker):
        return True
    try:
        age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
    except OSError:
        return True
    return age > PURGE_INTERVAL_SEC


def _rotate_if_large(observations_file: str, archive_dir: str) -> None:
    if not os.path.exists(observations_file):
        return
    try:
        size_mb = os.path.getsize(observations_file) / (1024 * 1024)
    except OSError:
        return
    if size_mb <= ARCHIVE_SIZE_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(archive_dir, f"observations-{ts}.jsonl")
    os.rename(observations_file, archive_path)


def _prune_old_archives(archive_dir: str) -> None:
    now_ts = datetime.now().timestamp()
    for fname in os.listdir(archive_dir):
        fpath = os.path.join(archive_dir, fname)
        try:
            age_days = (now_ts - os.path.getmtime(fpath)) / 86400
        except OSError:
            continue
        if age_days > PURGE_AGE_DAYS:
            try:
                os.remove(fpath)
            except OSError:
                pass


def _touch_purge_marker(purge_marker: str) -> None:
    try:
        with open(purge_marker, "w") as f:
            f.write("")
    except OSError:
        pass


def maybe_purge(paths: ObservationPaths) -> None:
    """At most once per day, rotate oversized logs and prune old archives."""
    if not _should_purge(paths.purge_marker):
        return
    try:
        os.makedirs(paths.archive_dir, exist_ok=True)
        _rotate_if_large(paths.observations_file, paths.archive_dir)
        _prune_old_archives(paths.archive_dir)
        _touch_purge_marker(paths.purge_marker)
    except IOError, OSError:
        # Purge is best-effort; never surface to the user session.
        pass


# ── Entry point ─────────────────────────────────────────────────────────────
def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    payload = parse_hook_payload(raw)
    if payload is None or payload.is_subagent:
        return

    project_dir = resolve_project_dir(payload.cwd)
    if not project_dir:
        return

    paths = ObservationPaths.for_project(project_dir)
    try:
        os.makedirs(paths.learnings_dir, exist_ok=True)
    except OSError:
        return

    observation = build_observation(payload)
    if not append_observation(paths.observations_file, observation):
        return

    # Layer 1 → 2 bridge: lazy-start daemon + SIGUSR1 throttle.
    bridge_to_observer(project_dir)

    # Auto-purge: rotate oversized logs, drop stale archives (daily).
    maybe_purge(paths)


if __name__ == "__main__":
    main()
