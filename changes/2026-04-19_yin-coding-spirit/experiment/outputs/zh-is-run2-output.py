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

─────────────────────────────────────────────────────────────────────────────
Design notes (yin / shadow-side SRP):

Each structure below exists for exactly one death. If deleted, exactly one
thing should break — that's the reason it exists. If nothing breaks, it
shouldn't be here; if many things break, it has taken on responsibility
that isn't its own.

- `scrub_secrets`            — dies when secret regex needs to change.
- `HookPayload.parse`        — dies when Claude Code's hook JSON shape changes.
- `resolve_project_dir`      — dies when the "where am I?" contract changes.
- `ObservationWriter`        — dies when the on-disk observation schema changes.
- `ObservationArchiver`      — dies when the rotation/purge policy changes.
- `ObserverBridge`           — dies when the Layer-1→Layer-2 handoff changes.

These are deliberately kept as **visible** (explicit) couplings in `main()`
rather than hidden behind a god-object orchestrator. Per the yin principle
on coupling: visible strong coupling is safer than hidden weak coupling.
─────────────────────────────────────────────────────────────────────────────
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
# Kept as a direct import of the sibling module — the coupling is real and
# hiding it behind a protocol would be an OCP "bet-marker" for a second
# implementation that doesn't exist. A single-impl interface is a disguise.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ─── Tunables ───────────────────────────────────────────────────────────────
# These three constants each answer a distinct "how much?" question.
# They are not grouped into a Config class because grouping would falsely
# imply they change together; they don't.

MAX_CONTENT_LENGTH = 3000  # per-observation truncation
PURGE_AGE_DAYS = 30  # archive retention
ROTATE_SIZE_MB = 10  # rotate observations.jsonl above this size
PURGE_INTERVAL_SECONDS = 86400  # once per day
GIT_TOPLEVEL_TIMEOUT_SEC = 3


# ─── Secret scrubbing ───────────────────────────────────────────────────────
# Dies when the secret-detection policy changes. Nothing else should.

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


# ─── Hook payload parsing ───────────────────────────────────────────────────
# One structure, one death: if Claude Code changes the hook JSON shape,
# only `HookPayload.parse` needs to move.


@dataclass(frozen=True)
class HookPayload:
    session_id: str
    cwd: str
    content: str
    agent_id: str

    @classmethod
    def parse(cls, raw: str) -> Optional["HookPayload"]:
        """
        Parse Claude Code hook JSON from stdin.

        Returns None when:
          - input is empty / not valid JSON
          - there is no user content to record
          - this is a subagent invocation (agent_id set)

        Returning None is the single "nothing to do" signal; callers must
        not try to distinguish the reasons. Keeping the reasons private
        here avoids an ISP phantom-promise (no caller actually needs them).
        """
        if not raw.strip():
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError, ValueError:
            return None

        agent_id = data.get("agent_id", "") or ""
        if agent_id:
            return None  # skip subagent sessions

        tool_input = data.get("tool_input", data.get("input", {}))
        if isinstance(tool_input, dict):
            content = tool_input.get("content", tool_input.get("message", "")) or ""
        else:
            content = str(tool_input)

        if not content:
            return None

        return cls(
            session_id=data.get("session_id", "unknown") or "unknown",
            cwd=data.get("cwd", "") or "",
            content=content,
            agent_id=agent_id,
        )


# ─── Project-directory resolution ───────────────────────────────────────────
# The "where do I write?" question. Isolated because it's the most likely
# thing to silently change behaviour (LSP violation risk) if inlined.


def resolve_project_dir(cwd: str) -> str:
    """
    Resolve the project root for persistence.

    Priority:
      1. $CLAUDE_PROJECT_DIR (authoritative — harness sets it)
      2. `git -C <cwd> rev-parse --show-toplevel`
      3. "" (caller must treat empty as "refuse to write")
    """
    explicit = os.environ.get("CLAUDE_PROJECT_DIR", "") or ""
    if explicit:
        return explicit

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


# ─── On-disk observation writing ────────────────────────────────────────────


@dataclass(frozen=True)
class Observation:
    """The schema. Duplicated nowhere — that would split a lie into two."""

    timestamp: str
    session_id: str
    type: str
    content: str
    cwd: str

    def as_jsonl(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False) + "\n"


class ObservationWriter:
    """
    Owns the single responsibility of *appending* one observation to disk.

    Delete this class and: appends stop working. Nothing else should care.
    Rotation/purge explicitly lives elsewhere (ObservationArchiver) —
    mixing them would violate cohesion by making the writer die for two
    reasons (append failure *or* policy change).
    """

    def __init__(self, learnings_dir: str) -> None:
        self._learnings_dir = learnings_dir
        self._path = os.path.join(learnings_dir, "observations.jsonl")

    @property
    def path(self) -> str:
        return self._path

    def ensure_dir(self) -> None:
        os.makedirs(self._learnings_dir, exist_ok=True)

    def append(self, obs: Observation) -> bool:
        """Return True on success, False on IOError (silently swallowed)."""
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(obs.as_jsonl())
            return True
        except IOError, OSError:
            return False


# ─── Rotation / purge policy ────────────────────────────────────────────────


class ObservationArchiver:
    """
    Owns file rotation + archive cleanup. Deliberately separate from
    `ObservationWriter`: different death condition (policy change, not
    append failure).

    Policy:
      - Runs at most once per PURGE_INTERVAL_SECONDS (marker file).
      - If observations.jsonl > ROTATE_SIZE_MB, rotate it into archive.
      - Delete any archive file older than PURGE_AGE_DAYS.

    Failures are silent by design — a purge error must never block the
    user's prompt submission.
    """

    def __init__(self, learnings_dir: str, observations_path: str) -> None:
        self._learnings_dir = learnings_dir
        self._observations_path = observations_path
        self._archive_dir = os.path.join(learnings_dir, "observations.archive")
        self._marker = os.path.join(learnings_dir, ".last-purge")

    def _due(self) -> bool:
        if not os.path.exists(self._marker):
            return True
        age = datetime.now().timestamp() - os.path.getmtime(self._marker)
        return age > PURGE_INTERVAL_SECONDS

    def _rotate_if_large(self) -> None:
        if not os.path.exists(self._observations_path):
            return
        size_mb = os.path.getsize(self._observations_path) / (1024 * 1024)
        if size_mb <= ROTATE_SIZE_MB:
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = os.path.join(self._archive_dir, f"observations-{ts}.jsonl")
        os.rename(self._observations_path, archive_path)

    def _drop_old_archives(self) -> None:
        now = datetime.now().timestamp()
        for fname in os.listdir(self._archive_dir):
            fpath = os.path.join(self._archive_dir, fname)
            try:
                age_days = (now - os.path.getmtime(fpath)) / 86400
            except OSError:
                continue
            if age_days > PURGE_AGE_DAYS:
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def _touch_marker(self) -> None:
        with open(self._marker, "w") as f:
            f.write("")

    def maybe_run(self) -> None:
        if not self._due():
            return
        try:
            os.makedirs(self._archive_dir, exist_ok=True)
            self._rotate_if_large()
            self._drop_old_archives()
            self._touch_marker()
        except IOError, OSError:
            # Silent: purge must never break the hook.
            pass


# ─── Layer-1 → Layer-2 bridge ───────────────────────────────────────────────


class ObserverBridge:
    """
    Nudges Layer 2 (observer daemon) that new observations exist.

    Responsibilities (one death: the handoff protocol):
      - Touch sentinel so daemon can detect activity.
      - Increment observation counter.
      - Lazy-start the daemon if it isn't running.
      - Every SIGNAL_EVERY_N observations, SIGUSR1 the daemon and reset.

    All failures are silent — the hook must never block the user's session.
    """

    def __init__(self, project_dir: str) -> None:
        self._project_dir = project_dir
        self._paths = learnings_state.state_paths(project_dir)

    def _lazy_start_daemon(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "start-observer.sh")
        if not os.path.exists(start_script):
            return
        try:
            # Detached launch — do not wait, do not hold std{in,out,err}.
            subprocess.Popen(
                ["bash", start_script, self._project_dir],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError, subprocess.SubprocessError:
            pass

    def _signal_daemon(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGUSR1)
            learnings_state.reset_counter(self._paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass

    def notify(self) -> None:
        learnings_state.touch_sentinel(self._paths["sentinel_file"])
        count = learnings_state.increment_counter(self._paths["counter_file"])
        daemon_pid = learnings_state.read_daemon_pid(self._paths["pid_file"])

        if daemon_pid is None:
            self._lazy_start_daemon()
            # Do not signal on the same invocation that started the daemon.
            return

        if count >= learnings_state.SIGNAL_EVERY_N:
            self._signal_daemon(daemon_pid)


# ─── Entry point ────────────────────────────────────────────────────────────


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_observation(payload: HookPayload) -> Observation:
    cleaned = scrub_secrets(payload.content[:MAX_CONTENT_LENGTH])
    return Observation(
        timestamp=_now_iso_utc(),
        session_id=payload.session_id,
        type="user_prompt",
        content=cleaned,
        cwd=payload.cwd,
    )


def main() -> None:
    """
    Orchestrate one hook invocation. Each early-return is a real
    "nothing to record" case — none of them are silent semantic changes
    (LSP), they are all "no observation exists to write".
    """
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    payload = HookPayload.parse(raw)
    if payload is None:
        return

    project_dir = resolve_project_dir(payload.cwd)
    if not project_dir:
        return

    learnings_dir = os.path.join(project_dir, ".learnings")
    writer = ObservationWriter(learnings_dir)
    writer.ensure_dir()

    observation = _build_observation(payload)
    if not writer.append(observation):
        return

    # Layer 1 → Layer 2 handoff. Explicit, visible coupling on purpose.
    ObserverBridge(project_dir).notify()

    # Rotation / purge policy. Separate object, separate death.
    ObservationArchiver(learnings_dir, writer.path).maybe_run()


if __name__ == "__main__":
    main()
