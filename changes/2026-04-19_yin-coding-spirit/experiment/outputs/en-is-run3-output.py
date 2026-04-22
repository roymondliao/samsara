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

# Shared state helpers (OS-temp daemon state management)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Module-level policy constants ───────────────────────────────────────────
# These are the single source of truth; duplicating them elsewhere would split
# the lie (DRY). They are values, not knobs — callers have no reason to override.

MAX_CONTENT_LENGTH = 3000  # Characters stored per observation
PURGE_AGE_DAYS = 30  # Archive retention
PURGE_INTERVAL_SECONDS = 86400  # Once per day
ROTATE_THRESHOLD_MB = 10  # Rotate active log when it exceeds this
GIT_TIMEOUT_SECONDS = 3

_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


def scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED].

    Exposed at module scope because the regex itself is the single fact this
    module owns — tests and future callers depend on it.
    """
    return _SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]", text
    )


# ── Value types ─────────────────────────────────────────────────────────────
# These dataclasses exist to make the shape of the data visible at call sites
# rather than buried in dict-key lookups. Their right-to-die-together is the
# hook-handling path below; delete this file and they should go with it.


@dataclass(frozen=True)
class HookInput:
    """The slice of a Claude Code hook payload this script cares about.

    If the payload is unparseable or missing required fields, `parse` returns
    None — the caller's only responsibility is to exit silently.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @classmethod
    def parse(cls, raw: str) -> Optional["HookInput"]:
        if not raw.strip():
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError, ValueError:
            return None

        tool_input = data.get("tool_input", data.get("input", {}))
        if isinstance(tool_input, dict):
            content = tool_input.get("content", tool_input.get("message", ""))
        else:
            content = str(tool_input)

        if not content:
            return None

        return cls(
            session_id=data.get("session_id", "unknown"),
            cwd=data.get("cwd", ""),
            content=content,
            agent_id=data.get("agent_id", ""),
        )


@dataclass(frozen=True)
class LearningsPaths:
    """Filesystem layout for a project's .learnings directory.

    Centralized so that any change to the layout happens in exactly one
    place — two callers composing paths independently would be duplication.
    """

    learnings_dir: str
    observations_file: str
    archive_dir: str
    purge_marker: str

    @classmethod
    def for_project(cls, project_dir: str) -> "LearningsPaths":
        learnings_dir = os.path.join(project_dir, ".learnings")
        return cls(
            learnings_dir=learnings_dir,
            observations_file=os.path.join(learnings_dir, "observations.jsonl"),
            archive_dir=os.path.join(learnings_dir, "observations.archive"),
            purge_marker=os.path.join(learnings_dir, ".last-purge"),
        )


# ── Project directory resolution ────────────────────────────────────────────


def resolve_project_dir(cwd: str) -> str:
    """Return the project root, or '' if it cannot be determined.

    Prefers CLAUDE_PROJECT_DIR; falls back to `git rev-parse --show-toplevel`
    from `cwd`. Returning '' (rather than raising) keeps the hook's contract
    simple: missing project → silent no-op.
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env_dir:
        return env_dir

    if not cwd or not os.path.isdir(cwd):
        return ""

    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired, FileNotFoundError, OSError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


# ── Observation persistence ─────────────────────────────────────────────────


def _build_observation(hook: HookInput) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": hook.session_id,
        "type": "user_prompt",
        "content": scrub_secrets(hook.content[:MAX_CONTENT_LENGTH]),
        "cwd": hook.cwd,
    }


def _append_observation(paths: LearningsPaths, observation: dict) -> bool:
    """Append one JSONL record. Returns True on success, False on I/O error."""
    os.makedirs(paths.learnings_dir, exist_ok=True)
    try:
        with open(paths.observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError, OSError:
        return False


# ── Layer 1 → Layer 2 bridge ────────────────────────────────────────────────
# The sole reason this module signals a daemon: to wake the observer agent.
# If the daemon concept disappears tomorrow, this function is the only thing
# that needs to die — that is its single responsibility.


def _spawn_observer_daemon(project_dir: str) -> None:
    """Detached launch of the observer start script. Silent on failure."""
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


def _bridge_to_observer(project_dir: str) -> None:
    """Increment counter, lazy-start daemon, SIGUSR1 on threshold.

    All failures are silent — the hook must never block the user's session.
    """
    state = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(state["sentinel_file"])

    count = learnings_state.increment_counter(state["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(state["pid_file"])

    if daemon_pid is None:
        # No signal on the same invocation that started the daemon.
        _spawn_observer_daemon(project_dir)
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(state["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass


# ── Archival / purge ────────────────────────────────────────────────────────
# These helpers share the same death: if observations go away, archival goes
# with them. They live next to each other for that reason.


def _should_purge(purge_marker: str) -> bool:
    if not os.path.exists(purge_marker):
        return True
    try:
        age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
    except OSError:
        return True
    return age > PURGE_INTERVAL_SECONDS


def _rotate_if_oversized(paths: LearningsPaths) -> None:
    if not os.path.exists(paths.observations_file):
        return
    try:
        size_mb = os.path.getsize(paths.observations_file) / (1024 * 1024)
    except OSError:
        return
    if size_mb <= ROTATE_THRESHOLD_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(paths.archive_dir, f"observations-{ts}.jsonl")
    try:
        os.rename(paths.observations_file, archive_path)
    except OSError:
        pass


def _evict_old_archives(archive_dir: str) -> None:
    try:
        names = os.listdir(archive_dir)
    except OSError:
        return
    now = datetime.now().timestamp()
    for fname in names:
        fpath = os.path.join(archive_dir, fname)
        try:
            age_days = (now - os.path.getmtime(fpath)) / 86400
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
    except IOError, OSError:
        pass


def _maybe_purge(paths: LearningsPaths) -> None:
    """Rotate oversized log and evict old archives, at most once per day."""
    if not _should_purge(paths.purge_marker):
        return
    try:
        os.makedirs(paths.archive_dir, exist_ok=True)
        _rotate_if_oversized(paths)
        _evict_old_archives(paths.archive_dir)
        _touch_purge_marker(paths.purge_marker)
    except IOError, OSError:
        # Any purge-phase failure is non-fatal; observations are already saved.
        pass


# ── Entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    hook = HookInput.parse(raw)
    if hook is None:
        return

    # Skip subagent sessions — they are not user prompts.
    if hook.agent_id:
        return

    project_dir = resolve_project_dir(hook.cwd)
    if not project_dir:
        return

    paths = LearningsPaths.for_project(project_dir)

    if not _append_observation(paths, _build_observation(hook)):
        return

    _bridge_to_observer(project_dir)
    _maybe_purge(paths)


if __name__ == "__main__":
    main()
