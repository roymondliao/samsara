#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

Layer 1 of the two-layer architecture: passively capture data, no analysis.
Layer 2 (learnings-observer agent) consumes observations and writes learnings.
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

# Shared state helpers (OS-temp daemon state management).
# SOURCE OF TRUTH for daemon state paths + signalling cadence lives in
# learnings_state; this module must not re-implement those concerns.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Tunables ────────────────────────────────────────────────────────────────
# BET: these limits are policy knobs. If bloat or retention needs change,
# only these constants should move — no call site should hard-code equivalents.

MAX_CONTENT_LENGTH = 3000  # characters stored per observation
PURGE_AGE_DAYS = 30  # archives older than this are removed
ROTATE_SIZE_MB = 10  # observations.jsonl rotates above this size
PURGE_INTERVAL_SEC = 86400  # purge runs at most once per day
GIT_TOPLEVEL_TIMEOUT_SEC = 3


# ── Secret scrubbing ────────────────────────────────────────────────────────
# BET: a single regex covers the secret shapes we care about. If a new shape
# (e.g. JWT, PEM) is needed, extend this regex — do not add a second scrubber.

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


# ── Hook input parsing ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class HookEvent:
    """Parsed UserPromptSubmit hook payload.

    Cohesion: these four fields always live and die together — they are the
    shape of one hook invocation. If any field becomes independently useful,
    relocate it out of this struct.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)


def _read_stdin_json() -> Optional[dict]:
    """Read JSON from stdin. Returns None on empty or malformed input."""
    try:
        raw = sys.stdin.read()
    except IOError:
        return None
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _extract_content(data: dict) -> str:
    """Pull the user's message out of the hook payload."""
    tool_input = data.get("tool_input", data.get("input", {}))
    if isinstance(tool_input, dict):
        return tool_input.get("content", tool_input.get("message", "")) or ""
    return str(tool_input)


def parse_hook_event(data: dict) -> HookEvent:
    return HookEvent(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", ""),
        content=_extract_content(data),
        agent_id=data.get("agent_id", ""),
    )


# ── Project directory resolution ────────────────────────────────────────────


def _git_toplevel(cwd: str) -> Optional[str]:
    """Return git repo root for cwd, or None if not in a repo / git missing."""
    if not cwd or not os.path.isdir(cwd):
        return None
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=GIT_TOPLEVEL_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired, FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def resolve_project_dir(cwd: str) -> Optional[str]:
    """
    Resolve the project directory.

    Priority:
      1. CLAUDE_PROJECT_DIR env var (explicit harness contract)
      2. git toplevel of cwd (fallback inference)
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env_dir:
        return env_dir
    return _git_toplevel(cwd)


# ── Observation writing ─────────────────────────────────────────────────────


def build_observation(event: HookEvent, now: datetime) -> dict:
    """Build the JSON-serialisable observation record."""
    content_clean = scrub_secrets(event.content[:MAX_CONTENT_LENGTH])
    return {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": event.session_id,
        "type": "user_prompt",
        "content": content_clean,
        "cwd": event.cwd,
    }


def append_observation(observations_file: str, observation: dict) -> bool:
    """Append an observation as a JSONL line. Returns True on success."""
    try:
        with open(observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError:
        return False


# ── Layer 1 → Layer 2 bridge ────────────────────────────────────────────────


def _spawn_observer_daemon(project_dir: str) -> None:
    """Detached launch of the observer daemon. Silent on all failures."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    start_script = os.path.join(script_dir, "start-observer.sh")
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


def bridge_to_observer(project_dir: str) -> None:
    """
    Layer 1 → Layer 2 bridge:
      1. Touch sentinel + increment observation counter.
      2. Lazy-start observer daemon if it is not running.
      3. Throttled SIGUSR1 every SIGNAL_EVERY_N observations.

    All failures are silent — this hook must never block the user's session.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        # BET: no signal on the same invocation that launched the daemon.
        # The daemon will read the counter on its own startup.
        _spawn_observer_daemon(project_dir)
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass


# ── Purge / rotation ────────────────────────────────────────────────────────


def _should_purge(purge_marker: str, now_ts: float) -> bool:
    if not os.path.exists(purge_marker):
        return True
    age = now_ts - os.path.getmtime(purge_marker)
    return age > PURGE_INTERVAL_SEC


def _rotate_if_large(observations_file: str, archive_dir: str, now: datetime) -> None:
    if not os.path.exists(observations_file):
        return
    size_mb = os.path.getsize(observations_file) / (1024 * 1024)
    if size_mb <= ROTATE_SIZE_MB:
        return
    ts = now.strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(archive_dir, f"observations-{ts}.jsonl")
    os.rename(observations_file, archive_path)


def _prune_old_archives(archive_dir: str, now_ts: float) -> None:
    for fname in os.listdir(archive_dir):
        fpath = os.path.join(archive_dir, fname)
        age_days = (now_ts - os.path.getmtime(fpath)) / 86400
        if age_days > PURGE_AGE_DAYS:
            os.remove(fpath)


def _touch(path: str) -> None:
    with open(path, "w") as f:
        f.write("")


def run_purge_if_due(learnings_dir: str, observations_file: str, now: datetime) -> None:
    """Rotate + prune archives, at most once per PURGE_INTERVAL_SEC."""
    purge_marker = os.path.join(learnings_dir, ".last-purge")
    now_ts = now.timestamp()
    if not _should_purge(purge_marker, now_ts):
        return

    try:
        archive_dir = os.path.join(learnings_dir, "observations.archive")
        os.makedirs(archive_dir, exist_ok=True)
        _rotate_if_large(observations_file, archive_dir, now)
        _prune_old_archives(archive_dir, now_ts)
        _touch(purge_marker)
    except IOError, OSError:
        pass


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    data = _read_stdin_json()
    if data is None:
        return

    event = parse_hook_event(data)
    if not event.content:
        return
    if event.is_subagent:
        return

    project_dir = resolve_project_dir(event.cwd)
    if not project_dir:
        return

    learnings_dir = os.path.join(project_dir, ".learnings")
    os.makedirs(learnings_dir, exist_ok=True)
    observations_file = os.path.join(learnings_dir, "observations.jsonl")

    now = datetime.now(timezone.utc)
    observation = build_observation(event, now)
    if not append_observation(observations_file, observation):
        return

    bridge_to_observer(project_dir)
    run_purge_if_due(learnings_dir, observations_file, now)


if __name__ == "__main__":
    main()
