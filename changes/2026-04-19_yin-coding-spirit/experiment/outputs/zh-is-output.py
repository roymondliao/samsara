#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

Layer 1 of the two-layer architecture:
- Layer 1 (this): passively capture data, no analysis
- Layer 2 (learnings-observer agent): background Haiku analyzes and writes learnings

──────────────────────────────────────────────────────────────────────
Design notes (陰面 / yin-coding-spirit):

This module has one death-reason (SRP): if it disappears, the
UserPromptSubmit hook stops writing observations. That is the only
place that should hurt.

Internally it has four *distinct* death-reasons, each isolated into a
small collaborator so that a break in one does not silently mutate the
others:

  HookInput            — parse stdin, extract the user prompt
  ProjectRoot          — resolve the project directory (env → git → cwd)
  ObservationStore     — append + rotate + archive observations.jsonl
  ObserverBridge       — lazy-start the daemon and throttle SIGUSR1

Failures in the bridge or the auto-purge must never break observation
writing, and failures in observation writing must never block the
user's session. Those silent boundaries are made *visible* here: each
collaborator owns its own `except` and explicitly returns control.
──────────────────────────────────────────────────────────────────────
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

# Shared daemon-state helpers live next to this file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402  (path-dependent import)


# ── Tunables ───────────────────────────────────────────────────────────
# These are explicit capacity bets (OCP). Each constant is one assumption
# about "how big / how old / how often"; if a caller changes the world,
# these are the knobs that must move.

MAX_CONTENT_LENGTH = 3000  # per-observation char cap, anti-bloat
PURGE_AGE_DAYS = 30  # archive retention before deletion
PURGE_INTERVAL_SECONDS = 86400  # run auto-purge at most once per day
ROTATE_THRESHOLD_MB = 10  # rotate observations.jsonl above this
GIT_RESOLVE_TIMEOUT_SEC = 3  # cap for `git rev-parse` fallback

# Secret scrubbing: matches label → separator → optional keyword → payload.
# The four groups are kept distinct so the replacement preserves the
# caller's original formatting instead of collapsing whitespace.
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


def _scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED], preserving the label."""
    return _SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
        text,
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── HookInput ──────────────────────────────────────────────────────────
# Death-reason: if stdin format changes, only this dies.


@dataclass(frozen=True)
class HookInput:
    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)

    @classmethod
    def from_stdin(cls) -> Optional["HookInput"]:
        """
        Parse Claude Code hook JSON from stdin.

        Returns None when the input is empty, malformed, or carries no
        user content. Callers treat None as "nothing to observe" — this
        is load-bearing: the hook must never raise into the user's
        session.
        """
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

        tool_input = data.get("tool_input", data.get("input", {}))
        if isinstance(tool_input, dict):
            content = tool_input.get("content", tool_input.get("message", ""))
        else:
            content = str(tool_input)
        if not content:
            return None

        return cls(
            session_id=data.get("session_id", "unknown"),
            cwd=data.get("cwd", "") or "",
            content=content,
            agent_id=data.get("agent_id", "") or "",
        )


# ── ProjectRoot ────────────────────────────────────────────────────────
# Death-reason: if project-root resolution rules change, only this dies.


def _resolve_project_dir(cwd: str) -> str:
    """
    Resolve the project directory. Returns "" when no root can be found.

    Priority:
      1. CLAUDE_PROJECT_DIR environment variable (hook contract)
      2. `git rev-parse --show-toplevel` rooted at cwd
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
            timeout=GIT_RESOLVE_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired, FileNotFoundError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


# ── ObservationStore ──────────────────────────────────────────────────
# Death-reason: if the on-disk observation format or rotation policy
# changes, only this dies. The daemon bridge does not know or care how
# files are laid out here.


class ObservationStore:
    def __init__(self, project_dir: str):
        self._root = os.path.join(project_dir, ".learnings")
        self._observations_file = os.path.join(self._root, "observations.jsonl")
        self._archive_dir = os.path.join(self._root, "observations.archive")
        self._purge_marker = os.path.join(self._root, ".last-purge")

    @property
    def observations_path(self) -> str:
        return self._observations_file

    def ensure_root(self) -> None:
        os.makedirs(self._root, exist_ok=True)

    def append(self, hook: HookInput) -> bool:
        """
        Append a single observation. Returns True on success, False on IO
        failure. The caller uses the return value to decide whether the
        downstream bridge / purge work should run — no point nudging the
        observer daemon if the write itself failed.
        """
        observation = {
            "timestamp": _utc_now_iso(),
            "session_id": hook.session_id,
            "type": "user_prompt",
            "content": _scrub_secrets(hook.content[:MAX_CONTENT_LENGTH]),
            "cwd": hook.cwd,
        }
        try:
            with open(self._observations_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(observation, ensure_ascii=False) + "\n")
            return True
        except IOError:
            return False

    def maybe_purge(self) -> None:
        """
        Run auto-purge at most once per PURGE_INTERVAL_SECONDS. Rotates
        the active log if oversized, then deletes archives older than
        PURGE_AGE_DAYS. All IO failures are swallowed — purge is
        best-effort housekeeping, never critical-path.
        """
        if not self._should_purge():
            return
        try:
            os.makedirs(self._archive_dir, exist_ok=True)
            self._rotate_if_oversized()
            self._delete_old_archives()
            self._touch_purge_marker()
        except IOError, OSError:
            # Silent by design: see module docstring.
            return

    # ── internals ──
    def _should_purge(self) -> bool:
        if not os.path.exists(self._purge_marker):
            return True
        age = datetime.now().timestamp() - os.path.getmtime(self._purge_marker)
        return age > PURGE_INTERVAL_SECONDS

    def _rotate_if_oversized(self) -> None:
        if not os.path.exists(self._observations_file):
            return
        size_mb = os.path.getsize(self._observations_file) / (1024 * 1024)
        if size_mb <= ROTATE_THRESHOLD_MB:
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = os.path.join(self._archive_dir, f"observations-{ts}.jsonl")
        os.rename(self._observations_file, archive_path)

    def _delete_old_archives(self) -> None:
        now = datetime.now().timestamp()
        for fname in os.listdir(self._archive_dir):
            fpath = os.path.join(self._archive_dir, fname)
            age_days = (now - os.path.getmtime(fpath)) / 86400
            if age_days > PURGE_AGE_DAYS:
                os.remove(fpath)

    def _touch_purge_marker(self) -> None:
        with open(self._purge_marker, "w") as f:
            f.write("")


# ── ObserverBridge ────────────────────────────────────────────────────
# Death-reason: if the Layer 1 → Layer 2 handoff protocol changes
# (counter, sentinel, pidfile, signal number), only this dies. The
# coupling to `learnings_state` is *explicit and visible* — that module
# owns the state files, this one owns the orchestration.


class ObserverBridge:
    def __init__(self, project_dir: str):
        self._project_dir = project_dir
        self._paths = learnings_state.state_paths(project_dir)

    def notify(self) -> None:
        """
        Mark the project as active, increment the observation counter,
        lazy-start the observer daemon if needed, and send a throttled
        SIGUSR1. Every failure is silent: the hook must not block the
        user's session.
        """
        learnings_state.touch_sentinel(self._paths["sentinel_file"])
        count = learnings_state.increment_counter(self._paths["counter_file"])
        daemon_pid = learnings_state.read_daemon_pid(self._paths["pid_file"])

        if daemon_pid is None:
            self._lazy_start_daemon()
            # No signal on the same invocation that started the daemon —
            # the daemon handles the initial sweep itself.
            return

        if count >= learnings_state.SIGNAL_EVERY_N:
            self._signal_daemon(daemon_pid)

    # ── internals ──
    def _lazy_start_daemon(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "start-observer.sh")
        if not os.path.exists(start_script):
            return
        try:
            # Detached launch: do not wait, do not hold stdio. The
            # daemon is expected to reparent to init.
            subprocess.Popen(
                ["bash", start_script, self._project_dir],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError, subprocess.SubprocessError:
            return

    def _signal_daemon(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGUSR1)
            learnings_state.reset_counter(self._paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            # Stale pid or permission drift — the next call will either
            # re-signal or re-start via the lazy-start path.
            return


# ── Entry point ───────────────────────────────────────────────────────


def main() -> None:
    hook = HookInput.from_stdin()
    if hook is None or hook.is_subagent:
        return

    project_dir = _resolve_project_dir(hook.cwd)
    if not project_dir:
        return

    store = ObservationStore(project_dir)
    store.ensure_root()
    if not store.append(hook):
        return

    ObserverBridge(project_dir).notify()
    store.maybe_purge()


if __name__ == "__main__":
    main()
