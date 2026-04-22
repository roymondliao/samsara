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

Structure (yin-coding-spirit v-en-is):
- Each class has a single reason to die:
  * SecretScrubber      — dies if the redaction pattern is wrong
  * HookPayload         — dies if the Claude Code hook JSON schema changes
  * ProjectResolver     — dies if project-root detection breaks
  * ObservationWriter   — dies if the JSONL on-disk contract changes
  * ObservationPurger   — dies if archive/retention policy changes
  * ObserverBridge      — dies if the Layer-1→Layer-2 handshake changes
  * HookApp             — dies if the overall hook wiring changes
- All boundaries are marked (see BETS comments) so the inheritor knows where
  a closure-assumption lives and what would be a silent contract breach.
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
from typing import Any, Optional

# Shared state helpers (OS-temp daemon state management).
# Imported via sys.path shim because this file lives in hooks/scripts/ and is
# invoked by a bash wrapper whose CWD is not guaranteed.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Configuration (named bets, not magic numbers) ────────────────────────────
# BET: a user prompt over 3000 chars is noise for the observer; truncating is
# cheaper than letting a pasted log blow out the JSONL file.
MAX_CONTENT_LENGTH = 3000

# BET: observations older than 30 days have no signal value for Layer 2.
PURGE_AGE_DAYS = 30

# BET: a single observations.jsonl over 10 MiB should rotate; larger files
# slow Layer 2 startup and are rarely re-read whole.
ROTATE_SIZE_MB = 10

# BET: running the purge sweep more than once per day is wasted I/O.
PURGE_INTERVAL_SECONDS = 86400

# BET: git toplevel detection must never hang the user's prompt; 3s is enough
# on any real filesystem, and we fall back to silent no-op on timeout.
GIT_TOPLEVEL_TIMEOUT_SECONDS = 3


# ── Secret scrubbing ─────────────────────────────────────────────────────────
class SecretScrubber:
    """
    Replace common secret-like substrings with [REDACTED].

    Death-responsibility: this class exists solely so that a future change to
    the redaction rule has exactly one place to edit. If the regex is wrong,
    the pain shows up here and nowhere else.
    """

    _PATTERN = re.compile(
        r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
        r"""(["'\s:=]+)"""
        r"([A-Za-z]+\s+)?"
        r"([A-Za-z0-9_\-/.+=]{8,})"
    )

    @classmethod
    def scrub(cls, text: str) -> str:
        return cls._PATTERN.sub(cls._replace, text)

    @staticmethod
    def _replace(m: re.Match[str]) -> str:
        return m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]"


# ── Hook payload parsing ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class HookPayload:
    """
    Normalized view of a Claude Code UserPromptSubmit hook payload.

    Death-responsibility: this class owns the on-the-wire JSON contract of
    Claude Code's hook. If Anthropic renames `tool_input` to something else,
    this is the one place that has to change.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @classmethod
    def parse(cls, raw: str) -> Optional["HookPayload"]:
        """Return a payload, or None if stdin was empty / malformed / no content."""
        if not raw.strip():
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None

        content = cls._extract_content(data)
        if not content:
            return None

        return cls(
            session_id=str(data.get("session_id", "unknown")),
            cwd=str(data.get("cwd", "")),
            content=content,
            agent_id=str(data.get("agent_id", "")),
        )

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        # BET: UserPromptSubmit provides the prompt under `tool_input` or
        # `input`, as either a dict with `content`/`message` or a raw string.
        # This matches the observed Claude Code shapes in 2026-04; if a future
        # Claude Code version adds a new shape, extend this method only.
        tool_input = data.get("tool_input", data.get("input", {}))
        if isinstance(tool_input, dict):
            return str(tool_input.get("content", tool_input.get("message", "")) or "")
        return str(tool_input or "")

    def is_subagent(self) -> bool:
        """A non-empty agent_id means this prompt came from a subagent session."""
        return bool(self.agent_id)


# ── Project directory resolution ─────────────────────────────────────────────
class ProjectResolver:
    """
    Resolve the project root directory for a given hook invocation.

    Death-responsibility: if the user renames $CLAUDE_PROJECT_DIR or git
    changes its `rev-parse` contract, the failure lives here only.
    """

    @staticmethod
    def resolve(cwd: str) -> Optional[str]:
        env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        if env_dir:
            return env_dir
        return ProjectResolver._git_toplevel(cwd)

    @staticmethod
    def _git_toplevel(cwd: str) -> Optional[str]:
        if not cwd or not os.path.isdir(cwd):
            return None
        try:
            result = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=GIT_TOPLEVEL_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired, FileNotFoundError:
            return None
        if result.returncode != 0:
            return None
        toplevel = result.stdout.strip()
        return toplevel or None


# ── Observation writing ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class Observation:
    """One JSONL line. One row. One atomic unit of user-prompt evidence."""

    timestamp: str
    session_id: str
    type: str
    content: str
    cwd: str

    @classmethod
    def from_payload(cls, payload: HookPayload) -> "Observation":
        clean = SecretScrubber.scrub(payload.content[:MAX_CONTENT_LENGTH])
        return cls(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            session_id=payload.session_id,
            type="user_prompt",
            content=clean,
            cwd=payload.cwd,
        )

    def to_json_line(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False) + "\n"


class ObservationWriter:
    """
    Append-only writer for observations.jsonl.

    Death-responsibility: this class owns the on-disk layout of `.learnings/`.
    If the file layout changes (e.g. one-file-per-day), edit here only.
    """

    OBSERVATIONS_FILENAME = "observations.jsonl"
    LEARNINGS_DIR_NAME = ".learnings"

    def __init__(self, project_dir: str) -> None:
        self.project_dir = project_dir
        self.learnings_dir = os.path.join(project_dir, self.LEARNINGS_DIR_NAME)
        self.observations_file = os.path.join(
            self.learnings_dir, self.OBSERVATIONS_FILENAME
        )

    def ensure_dir(self) -> None:
        os.makedirs(self.learnings_dir, exist_ok=True)

    def append(self, observation: Observation) -> bool:
        """Return True on success, False on any IOError. Hook must not crash."""
        try:
            with open(self.observations_file, "a", encoding="utf-8") as f:
                f.write(observation.to_json_line())
            return True
        except IOError:
            return False


# ── Auto-purge / rotation ────────────────────────────────────────────────────
class ObservationPurger:
    """
    Rotate a too-large observations file and delete archives older than
    PURGE_AGE_DAYS. Runs at most once per PURGE_INTERVAL_SECONDS.

    Death-responsibility: if retention or rotation policy changes, this is
    the one place to edit.
    """

    PURGE_MARKER_NAME = ".last-purge"
    ARCHIVE_DIR_NAME = "observations.archive"

    def __init__(self, writer: ObservationWriter) -> None:
        self.writer = writer
        self.purge_marker = os.path.join(writer.learnings_dir, self.PURGE_MARKER_NAME)
        self.archive_dir = os.path.join(writer.learnings_dir, self.ARCHIVE_DIR_NAME)

    def run_if_due(self) -> None:
        if not self._is_due():
            return
        try:
            os.makedirs(self.archive_dir, exist_ok=True)
            self._rotate_if_large()
            self._delete_old_archives()
            self._touch_marker()
        except IOError, OSError:
            # BET: purging is best-effort. A failed sweep must never surface
            # to the user; Layer 2 will retry tomorrow.
            pass

    def _is_due(self) -> bool:
        if not os.path.exists(self.purge_marker):
            return True
        age = datetime.now().timestamp() - os.path.getmtime(self.purge_marker)
        return age > PURGE_INTERVAL_SECONDS

    def _rotate_if_large(self) -> None:
        path = self.writer.observations_file
        if not os.path.exists(path):
            return
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb <= ROTATE_SIZE_MB:
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = os.path.join(self.archive_dir, f"observations-{ts}.jsonl")
        os.rename(path, archive_path)

    def _delete_old_archives(self) -> None:
        now = datetime.now().timestamp()
        for fname in os.listdir(self.archive_dir):
            fpath = os.path.join(self.archive_dir, fname)
            age_days = (now - os.path.getmtime(fpath)) / 86400
            if age_days > PURGE_AGE_DAYS:
                os.remove(fpath)

    def _touch_marker(self) -> None:
        with open(self.purge_marker, "w") as f:
            f.write("")


# ── Layer 1 → Layer 2 bridge ─────────────────────────────────────────────────
class ObserverBridge:
    """
    Wake up the learnings-observer daemon.

    Death-responsibility: owns the Layer-1→Layer-2 handshake:
      1. Touch sentinel so daemon knows it is still wanted.
      2. Increment observation counter.
      3. Lazy-start the daemon if it is not running.
      4. Throttled SIGUSR1 once every SIGNAL_EVERY_N observations.

    All failures are swallowed. The hook must never block the user's prompt.
    """

    START_SCRIPT_NAME = "start-observer.sh"

    def __init__(self, project_dir: str) -> None:
        self.project_dir = project_dir
        self.paths = learnings_state.state_paths(project_dir)

    def notify(self) -> None:
        learnings_state.touch_sentinel(self.paths["sentinel_file"])
        count = learnings_state.increment_counter(self.paths["counter_file"])
        daemon_pid = learnings_state.read_daemon_pid(self.paths["pid_file"])

        if daemon_pid is None:
            # No signal on the same invocation that started the daemon.
            self._lazy_start_daemon()
            return

        if count >= learnings_state.SIGNAL_EVERY_N:
            self._signal_daemon(daemon_pid)

    def _lazy_start_daemon(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, self.START_SCRIPT_NAME)
        if not os.path.exists(start_script):
            return
        try:
            # Detached launch — do not wait, do not hold stdin/stdout/stderr.
            subprocess.Popen(
                ["bash", start_script, self.project_dir],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError, subprocess.SubprocessError:
            pass

    def _signal_daemon(self, daemon_pid: int) -> None:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(self.paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass


# ── Top-level hook wiring ────────────────────────────────────────────────────
class HookApp:
    """
    The hook's orchestration. Reads stdin, writes one observation, pokes the
    observer daemon, and runs the purge sweep at most once per day.

    Death-responsibility: owns the sequence of steps. If the hook's overall
    lifecycle changes (e.g. add a second output sink), edit here.
    """

    def run(self) -> None:
        payload = self._read_payload()
        if payload is None or payload.is_subagent():
            return

        project_dir = ProjectResolver.resolve(payload.cwd)
        if not project_dir:
            return

        writer = ObservationWriter(project_dir)
        writer.ensure_dir()

        observation = Observation.from_payload(payload)
        if not writer.append(observation):
            return

        ObserverBridge(project_dir).notify()
        ObservationPurger(writer).run_if_due()

    @staticmethod
    def _read_payload() -> Optional[HookPayload]:
        try:
            raw = sys.stdin.read()
        except IOError:
            return None
        return HookPayload.parse(raw)


def main() -> None:
    HookApp().run()


if __name__ == "__main__":
    main()
