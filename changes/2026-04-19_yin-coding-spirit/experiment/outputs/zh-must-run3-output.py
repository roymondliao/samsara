#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

This is Layer 1 of the two-layer architecture:
- Layer 1 (this): passively capture data, no analysis
- Layer 2 (learnings-observer agent): background Haiku analyzes and writes learnings

Refactor notes (v-zh-must):
- SRP: every module-level class has exactly one reason to die.
    * `HookPayload` dies if Claude Code hook JSON shape changes.
    * `SecretScrubber` dies if the redaction policy changes.
    * `ObservationWriter` dies if the on-disk observation format changes.
    * `ArchiveRotator` dies if the purge/rotation policy changes.
    * `ObserverBridge` dies if the Layer1→Layer2 handoff protocol changes.
    * `ProjectResolver` dies if project-dir discovery rules change.
- OCP bets (explicit):
    * MAX_CONTENT_LENGTH, PURGE_AGE_DAYS, ROTATE_SIZE_MB, PURGE_INTERVAL_SEC —
      bet: tuning over time; kept as module constants so future tuning is
      localised. Failure boundary: values unsuitable for any deployment.
    * SECRET_RE — bet: secret patterns evolve; kept as a single compiled regex
      inside `SecretScrubber`. Failure boundary: novel secret formats.
- LSP: no inheritance is used; we do not override built-in semantics. All
  public methods are plain composition to avoid silent contract drift.
- ISP: every public method below has a named caller in `main()` (or in a peer
  collaborator). No ghost methods.
- DIP: we do not introduce interfaces with a single implementation. The
  classes below are concrete; injection is via constructor arguments only
  when a real seam (filesystem path) exists.
- Cohesion: when a class is deleted, all its members die together. No
  orphan helpers remain at module scope beyond the well-named dataclasses
  and constants.
- Coupling: every cross-class dependency is passed explicitly through the
  constructor or call site — no hidden globals except the OCP-marked tuning
  constants above and the `learnings_state` module (which is the source of
  truth for daemon-state paths).
- DRY: `datetime.now(...)` timestamp formatting and path building each have
  exactly one source of truth (`_utc_iso_now`, `learnings_state.state_paths`).
- Pattern: we intentionally do NOT apply a Strategy/Factory pattern here —
  divergence point: there is only one scrubber, one writer, one rotator
  today; introducing polymorphism would violate DIP (single-impl interface).
  Failure boundary: if a second scrubber/writer/rotator arrives, revisit.
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

# Shared state helpers (OS-temp daemon state management) — single source of
# truth for daemon PID/counter/sentinel paths. Do not duplicate path logic.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── OCP bet markers ─────────────────────────────────────────────────────────
# Bet: per-observation payload stays small enough that 3000 chars is "enough".
# Failure boundary: prompts larger than this silently lose tail context.
MAX_CONTENT_LENGTH = 3000

# Bet: archives older than 30 days have no forensic value.
# Failure boundary: long-running investigations need older context.
PURGE_AGE_DAYS = 30

# Bet: a 10 MB observations.jsonl is the right rotation threshold.
# Failure boundary: very chatty sessions rotate too often / too rarely.
ROTATE_SIZE_MB = 10

# Bet: purging once per 24h keeps disk use bounded without being expensive.
# Failure boundary: bursty deletes on machines that are rarely online.
PURGE_INTERVAL_SEC = 86400

# Bet: the set of tokens below covers the common "secret-looking" prefixes
# we see in user prompts. Novel formats (e.g. JWT without a keyword) will
# pass through unredacted — that is the known gap.
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


def _utc_iso_now() -> str:
    """Single source of truth for the observation timestamp format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Hook payload ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class HookPayload:
    """Parsed Claude Code UserPromptSubmit hook payload.

    Dies when the hook JSON shape changes.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @staticmethod
    def from_stdin(raw: str) -> Optional["HookPayload"]:
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

        return HookPayload(
            session_id=data.get("session_id", "unknown"),
            cwd=data.get("cwd", "") or "",
            content=content or "",
            agent_id=data.get("agent_id", "") or "",
        )

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)


# ── Secret scrubbing ────────────────────────────────────────────────────────


class SecretScrubber:
    """Replace common secret patterns with [REDACTED].

    Dies when the redaction policy changes.
    """

    def __init__(self, pattern: re.Pattern[str] = _SECRET_RE) -> None:
        self._pattern = pattern

    def scrub(self, text: str) -> str:
        return self._pattern.sub(
            lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
            text,
        )


# ── Project resolution ─────────────────────────────────────────────────────


class ProjectResolver:
    """Resolve the project root directory.

    Dies when the rules for locating a project root change.
    """

    @staticmethod
    def resolve(cwd: str) -> str:
        env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        if env_dir:
            return env_dir
        if cwd and os.path.isdir(cwd):
            try:
                result = subprocess.run(
                    ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except subprocess.TimeoutExpired, FileNotFoundError, OSError:
                pass
        return ""


# ── Observation writing ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Observation:
    timestamp: str
    session_id: str
    type: str
    content: str
    cwd: str

    def to_json_line(self) -> str:
        return (
            json.dumps(
                {
                    "timestamp": self.timestamp,
                    "session_id": self.session_id,
                    "type": self.type,
                    "content": self.content,
                    "cwd": self.cwd,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


class ObservationWriter:
    """Append observations to `.learnings/observations.jsonl`.

    Dies when the observation on-disk format or target file moves.
    """

    def __init__(self, learnings_dir: str) -> None:
        self._learnings_dir = learnings_dir
        os.makedirs(self._learnings_dir, exist_ok=True)

    @property
    def observations_file(self) -> str:
        return os.path.join(self._learnings_dir, "observations.jsonl")

    def append(self, observation: Observation) -> bool:
        try:
            with open(self.observations_file, "a", encoding="utf-8") as f:
                f.write(observation.to_json_line())
            return True
        except IOError, OSError:
            return False


# ── Archive rotation / purging ─────────────────────────────────────────────


class ArchiveRotator:
    """Rotate oversize observation logs and purge stale archives.

    Dies when the rotation/purge policy changes.
    """

    def __init__(
        self,
        learnings_dir: str,
        observations_file: str,
        *,
        rotate_size_mb: float = ROTATE_SIZE_MB,
        purge_age_days: int = PURGE_AGE_DAYS,
        purge_interval_sec: int = PURGE_INTERVAL_SEC,
    ) -> None:
        self._learnings_dir = learnings_dir
        self._observations_file = observations_file
        self._rotate_size_mb = rotate_size_mb
        self._purge_age_days = purge_age_days
        self._purge_interval_sec = purge_interval_sec
        self._marker = os.path.join(learnings_dir, ".last-purge")
        self._archive_dir = os.path.join(learnings_dir, "observations.archive")

    def _should_purge(self) -> bool:
        if not os.path.exists(self._marker):
            return True
        age = datetime.now().timestamp() - os.path.getmtime(self._marker)
        return age > self._purge_interval_sec

    def _rotate_if_oversize(self) -> None:
        if not os.path.exists(self._observations_file):
            return
        size_mb = os.path.getsize(self._observations_file) / (1024 * 1024)
        if size_mb <= self._rotate_size_mb:
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = os.path.join(self._archive_dir, f"observations-{ts}.jsonl")
        os.rename(self._observations_file, archive_path)

    def _purge_stale_archives(self) -> None:
        cutoff = self._purge_age_days
        now_ts = datetime.now().timestamp()
        for fname in os.listdir(self._archive_dir):
            fpath = os.path.join(self._archive_dir, fname)
            age_days = (now_ts - os.path.getmtime(fpath)) / 86400
            if age_days > cutoff:
                os.remove(fpath)

    def _touch_marker(self) -> None:
        with open(self._marker, "w") as f:
            f.write("")

    def maybe_run(self) -> None:
        if not self._should_purge():
            return
        try:
            os.makedirs(self._archive_dir, exist_ok=True)
            self._rotate_if_oversize()
            self._purge_stale_archives()
            self._touch_marker()
        except IOError, OSError:
            # All failures are silent — hook must never block the session.
            pass


# ── Layer 1 → Layer 2 bridge ───────────────────────────────────────────────


class ObserverBridge:
    """Lazy-start the observer daemon and SIGUSR1-throttle it.

    Dies when the handoff protocol between hook and daemon changes.
    """

    def __init__(self, project_dir: str) -> None:
        self._project_dir = project_dir
        self._paths = learnings_state.state_paths(project_dir)
        self._script_dir = os.path.dirname(os.path.abspath(__file__))

    def _try_start_daemon(self) -> None:
        start_script = os.path.join(self._script_dir, "start-observer.sh")
        if not os.path.exists(start_script):
            return
        try:
            # Detached launch — do not wait, do not hold stdin/stdout/stderr.
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

    def handoff(self) -> None:
        learnings_state.touch_sentinel(self._paths["sentinel_file"])
        count = learnings_state.increment_counter(self._paths["counter_file"])
        daemon_pid = learnings_state.read_daemon_pid(self._paths["pid_file"])

        if daemon_pid is None:
            # Lazy-start only; do not signal the same invocation that
            # spawned the daemon.
            self._try_start_daemon()
            return

        if count >= learnings_state.SIGNAL_EVERY_N:
            self._signal_daemon(daemon_pid)


# ── Entry point ────────────────────────────────────────────────────────────


def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError, OSError:
        return

    payload = HookPayload.from_stdin(raw)
    if payload is None or not payload.content or payload.is_subagent:
        return

    project_dir = ProjectResolver.resolve(payload.cwd)
    if not project_dir:
        return

    learnings_dir = os.path.join(project_dir, ".learnings")
    writer = ObservationWriter(learnings_dir)

    scrubber = SecretScrubber()
    content_clean = scrubber.scrub(payload.content[:MAX_CONTENT_LENGTH])

    observation = Observation(
        timestamp=_utc_iso_now(),
        session_id=payload.session_id,
        type="user_prompt",
        content=content_clean,
        cwd=payload.cwd,
    )

    if not writer.append(observation):
        return

    # Layer 1 → Layer 2 handoff.
    ObserverBridge(project_dir).handoff()

    # Rotate + purge (throttled internally to once per PURGE_INTERVAL_SEC).
    ArchiveRotator(learnings_dir, writer.observations_file).maybe_run()


if __name__ == "__main__":
    main()
