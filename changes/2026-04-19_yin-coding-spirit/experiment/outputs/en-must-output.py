#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

Layer 1 of the two-layer architecture:
- Layer 1 (this): passively capture data, no analysis.
- Layer 2 (learnings-observer agent): background Haiku analyzes and writes learnings.
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

# Shared daemon-state helpers live beside this script.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ─── Configuration (closed boundaries, future bets marked) ──────────────────
# OCP: if limits change, edit here — these are the only knobs.
MAX_CONTENT_LENGTH = 3000  # per-observation character cap (anti-bloat)
PURGE_AGE_DAYS = 30  # archive retention window
ROTATE_SIZE_MB = 10  # rotate observations.jsonl above this size
PURGE_INTERVAL_SEC = 86400  # run purge at most once per day
GIT_TOPLEVEL_TIMEOUT_SEC = 3  # bound git rev-parse on fallback path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── Secret scrubbing (single source of truth) ──────────────────────────────
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


# ─── Hook input parsing ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class HookInput:
    """Parsed Claude Code hook payload — only the fields we actually use."""

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)

    @property
    def is_empty(self) -> bool:
        return not self.content


def _extract_content(tool_input: object) -> str:
    """Pull user message from the hook's tool_input field."""
    if isinstance(tool_input, dict):
        return tool_input.get("content", tool_input.get("message", "")) or ""
    return str(tool_input) if tool_input else ""


def parse_hook_stdin() -> Optional[HookInput]:
    """Read and parse hook JSON from stdin. Returns None on any malformed input."""
    try:
        raw = sys.stdin.read()
    except IOError:
        return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    tool_input = data.get("tool_input", data.get("input", {}))
    return HookInput(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", ""),
        content=_extract_content(tool_input),
        agent_id=data.get("agent_id", ""),
    )


# ─── Project directory resolution ───────────────────────────────────────────
def _git_toplevel(cwd: str) -> str:
    """Return git toplevel of `cwd`, or empty string on any failure."""
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
    return result.stdout.strip() if result.returncode == 0 else ""


def resolve_project_dir(cwd: str) -> str:
    """Resolve project dir: CLAUDE_PROJECT_DIR env first, else git toplevel of cwd."""
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return env_dir or _git_toplevel(cwd)


# ─── Observation writing ────────────────────────────────────────────────────
@dataclass(frozen=True)
class LearningsPaths:
    """Filesystem layout under `<project>/.learnings/`."""

    root: str
    observations_file: str
    archive_dir: str
    purge_marker: str

    @classmethod
    def for_project(cls, project_dir: str) -> "LearningsPaths":
        root = os.path.join(project_dir, ".learnings")
        return cls(
            root=root,
            observations_file=os.path.join(root, "observations.jsonl"),
            archive_dir=os.path.join(root, "observations.archive"),
            purge_marker=os.path.join(root, ".last-purge"),
        )


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_observation(hook: HookInput) -> dict:
    """Build the JSONL record from a hook input (content already length-capped)."""
    return {
        "timestamp": _utc_timestamp(),
        "session_id": hook.session_id,
        "type": "user_prompt",
        "content": scrub_secrets(hook.content[:MAX_CONTENT_LENGTH]),
        "cwd": hook.cwd,
    }


def append_observation(path: str, observation: dict) -> bool:
    """Append observation as one JSONL line. Returns False on IO failure."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError:
        return False


# ─── Layer 1 → Layer 2 bridge ───────────────────────────────────────────────
def _spawn_observer_daemon(project_dir: str) -> None:
    """Detached launch of start-observer.sh; silent on failure."""
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


def bridge_to_observer(project_dir: str) -> None:
    """
    1. Increment observation counter.
    2. Lazy-start observer daemon if not running.
    3. Send SIGUSR1 every SIGNAL_EVERY_N observations (throttled).

    All failures are silent — hook MUST NOT block the user's session.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        _spawn_observer_daemon(project_dir)
        return  # No signal on the same invocation that started the daemon.

    if count >= learnings_state.SIGNAL_EVERY_N:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass


# ─── Auto-purge / rotation ──────────────────────────────────────────────────
def _should_run_purge(marker_path: str) -> bool:
    """True if marker is missing or older than PURGE_INTERVAL_SEC."""
    if not os.path.exists(marker_path):
        return True
    age = datetime.now().timestamp() - os.path.getmtime(marker_path)
    return age > PURGE_INTERVAL_SEC


def _rotate_if_oversized(observations_file: str, archive_dir: str) -> None:
    if not os.path.exists(observations_file):
        return
    size_mb = os.path.getsize(observations_file) / (1024 * 1024)
    if size_mb <= ROTATE_SIZE_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.rename(observations_file, os.path.join(archive_dir, f"observations-{ts}.jsonl"))


def _prune_old_archives(archive_dir: str) -> None:
    now = datetime.now().timestamp()
    for fname in os.listdir(archive_dir):
        fpath = os.path.join(archive_dir, fname)
        age_days = (now - os.path.getmtime(fpath)) / 86400
        if age_days > PURGE_AGE_DAYS:
            os.remove(fpath)


def _touch(path: str) -> None:
    with open(path, "w") as f:
        f.write("")


def maybe_auto_purge(paths: LearningsPaths) -> None:
    """Rotate oversize log + prune expired archives, at most once per day. Silent on failure."""
    if not _should_run_purge(paths.purge_marker):
        return
    try:
        os.makedirs(paths.archive_dir, exist_ok=True)
        _rotate_if_oversized(paths.observations_file, paths.archive_dir)
        _prune_old_archives(paths.archive_dir)
        _touch(paths.purge_marker)
    except IOError, OSError:
        pass


# ─── Entry point ────────────────────────────────────────────────────────────
def main() -> None:
    hook = parse_hook_stdin()
    if hook is None or hook.is_empty or hook.is_subagent:
        return

    project_dir = resolve_project_dir(hook.cwd)
    if not project_dir:
        return

    paths = LearningsPaths.for_project(project_dir)
    os.makedirs(paths.root, exist_ok=True)

    if not append_observation(paths.observations_file, build_observation(hook)):
        return

    bridge_to_observer(project_dir)
    maybe_auto_purge(paths)


if __name__ == "__main__":
    main()
