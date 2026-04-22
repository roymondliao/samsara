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

# Shared state helpers (OS-temp daemon state management).
# OCP boundary: future bet — learnings_state owns daemon-state semantics;
# this module MUST NOT inline state-path logic.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Tunables ────────────────────────────────────────────────────────────────
# Each constant has exactly one caller below; deleting the caller MUST
# delete the constant (cohesion).

# Maximum characters to store per observation (prevent bloat).
MAX_CONTENT_LENGTH = 3000

# Auto-purge archived observation files older than this.
PURGE_AGE_DAYS = 30

# Rotate active observations file when it exceeds this.
ROTATE_SIZE_MB = 10

# Interval between purge sweeps.
PURGE_INTERVAL_SECONDS = 86400  # 24 hours

# Seconds/day conversion used by the purge sweep.
SECONDS_PER_DAY = 86400

# Git discovery timeout for project-dir fallback.
GIT_TIMEOUT_SECONDS = 3


# ── Secret scrubbing ────────────────────────────────────────────────────────
# Single source of truth for the secret pattern (DRY).
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
class HookInput:
    """Parsed UserPromptSubmit payload.

    Failure mode (SRP): represents "we have a usable prompt to observe".
    Returned as None by `parse_hook_input` when input is unusable — callers
    MUST treat None as "silently skip this invocation".
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str


def parse_hook_input(raw: str) -> Optional[HookInput]:
    """Parse the hook JSON payload from stdin contents.

    Returns None if the payload is empty, malformed, or missing content.
    All parse failures are silent by design — hook MUST NOT block the user.
    """
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    tool_input = data.get("tool_input", data.get("input", {}))
    if isinstance(tool_input, dict):
        content = tool_input.get("content", tool_input.get("message", ""))
    else:
        content = str(tool_input)

    if not content:
        return None

    return HookInput(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", ""),
        content=content,
        agent_id=data.get("agent_id", ""),
    )


# ── Project directory resolution ────────────────────────────────────────────


def resolve_project_dir(cwd: str) -> str:
    """Resolve project directory via env var, falling back to `git -C cwd`.

    Returns empty string when no project dir can be determined. Callers MUST
    treat "" as "skip observation".
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return project_dir

    if not (cwd and os.path.isdir(cwd)):
        return ""

    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired, FileNotFoundError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


# ── Observation writer ──────────────────────────────────────────────────────


def build_observation(hook_input: HookInput) -> dict:
    """Build the JSONL observation record from a parsed hook input."""
    content_clean = scrub_secrets(hook_input.content[:MAX_CONTENT_LENGTH])
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": hook_input.session_id,
        "type": "user_prompt",
        "content": content_clean,
        "cwd": hook_input.cwd,
    }


def append_observation(observations_file: str, observation: dict) -> bool:
    """Append one JSON line to the observations file. Returns False on IOError."""
    try:
        with open(observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError:
        return False


# ── Layer 1 → Layer 2 bridge ────────────────────────────────────────────────


def _lazy_start_daemon(project_dir: str) -> None:
    """Detached launch of the observer daemon.

    Called only when read_daemon_pid returned None. Failures are silent.
    """
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


def _signal_daemon(daemon_pid: int, counter_file: str) -> None:
    """Send SIGUSR1 and reset the counter. Failures are silent."""
    try:
        os.kill(daemon_pid, signal.SIGUSR1)
        learnings_state.reset_counter(counter_file)
    except ProcessLookupError, PermissionError, OSError:
        pass


def bridge_to_observer(project_dir: str) -> None:
    """
    Layer 1 → Layer 2 bridge:
    1. Increment observation counter
    2. Lazy-start observer daemon if not running
    3. Send SIGUSR1 every N observations (throttled)

    All failures are silent — hook MUST NEVER block the user's session.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        # No signal on the same invocation that starts the daemon.
        _lazy_start_daemon(project_dir)
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        _signal_daemon(daemon_pid, paths["counter_file"])


# ── Auto-purge sweep ────────────────────────────────────────────────────────


def _purge_due(purge_marker: str) -> bool:
    """True when no marker exists or the marker is older than the interval."""
    if not os.path.exists(purge_marker):
        return True
    age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
    return age > PURGE_INTERVAL_SECONDS


def _rotate_if_large(observations_file: str, archive_dir: str) -> None:
    """Move the active observations file to archive when it exceeds ROTATE_SIZE_MB."""
    if not os.path.exists(observations_file):
        return
    size_mb = os.path.getsize(observations_file) / (1024 * 1024)
    if size_mb <= ROTATE_SIZE_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(archive_dir, f"observations-{ts}.jsonl")
    os.rename(observations_file, archive_path)


def _prune_old_archives(archive_dir: str) -> None:
    """Delete archive files older than PURGE_AGE_DAYS."""
    now_ts = datetime.now().timestamp()
    for fname in os.listdir(archive_dir):
        fpath = os.path.join(archive_dir, fname)
        age_days = (now_ts - os.path.getmtime(fpath)) / SECONDS_PER_DAY
        if age_days > PURGE_AGE_DAYS:
            os.remove(fpath)


def run_purge_sweep(learnings_dir: str, observations_file: str) -> None:
    """Rotate oversized observation file and prune stale archives, at most daily.

    Failures are swallowed — the hook MUST NEVER block the user's session.
    """
    purge_marker = os.path.join(learnings_dir, ".last-purge")
    if not _purge_due(purge_marker):
        return

    try:
        archive_dir = os.path.join(learnings_dir, "observations.archive")
        os.makedirs(archive_dir, exist_ok=True)
        _rotate_if_large(observations_file, archive_dir)
        _prune_old_archives(archive_dir)
        with open(purge_marker, "w") as f:
            f.write("")
    except IOError, OSError:
        pass


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    hook_input = parse_hook_input(raw)
    if hook_input is None:
        return

    # Skip subagent sessions — they would double-count observations.
    if hook_input.agent_id:
        return

    project_dir = resolve_project_dir(hook_input.cwd)
    if not project_dir:
        return

    learnings_dir = os.path.join(project_dir, ".learnings")
    os.makedirs(learnings_dir, exist_ok=True)
    observations_file = os.path.join(learnings_dir, "observations.jsonl")

    observation = build_observation(hook_input)
    if not append_observation(observations_file, observation):
        return

    bridge_to_observer(project_dir)
    run_purge_sweep(learnings_dir, observations_file)


if __name__ == "__main__":
    main()
