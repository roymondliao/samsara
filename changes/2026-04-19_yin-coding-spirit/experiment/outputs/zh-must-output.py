#!/usr/bin/env python3
"""
observe-learnings.py — Capture user prompt + context to observations.jsonl.

Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
Reads hook JSON from stdin, extracts the user's message, and appends a
structured observation to .learnings/observations.jsonl.

Layer 1 of the two-layer architecture:
- Layer 1 (this): passively capture data, no analysis
- Layer 2 (learnings-observer agent): background Haiku reads observations

Observation schema (JSONL, append-only):
{
  "timestamp":  "ISO8601",
  "session_id": "...",
  "type":       "user_prompt",
  "content":    "truncated user message",
  "cwd":        "..."
}

────────────────────────────────────────────────────────────────────────────
Structure policy (yin-must):

  - Each class / function below owns ONE way to die. If it is removed, exactly
    one behavior disappears. No function here mixes "extract" with "write"
    with "signal". See SRP sections per class.

  - Tunable policy constants (OCP bets) are grouped in Policy. Any future
    change to capture volume, rotation, or purge horizon lives there. The bet
    is: "these numbers will drift; the shape of the pipeline will not."

  - There are no single-implementation interfaces. `learnings_state` is a
    direct module dependency — deliberately not hidden behind an abstract
    port, because there is only one state backend and an indirection here
    would make failures harder to trace, not easier (DIP).

  - All failure swallowing is at hook boundaries only, and each swallow is
    labeled with the rationale ("hook must never block the user's session").
    Internal helpers let errors propagate so the boundary stays the single
    chokepoint (Coupling: implicit exception policy is displaced into the
    explicit boundary).
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
# Kept as direct dependency — see "no single-impl interfaces" in module docstring.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ─── Policy (OCP bets) ──────────────────────────────────────────────────────
# Each value is a closed assumption. If any of these need to change, they
# change HERE and only here. The bet being made is labeled alongside.


class Policy:
    # Bet: a single user prompt beyond this size is almost certainly a paste
    # bomb or file dump, not a question the observer should study.
    MAX_CONTENT_LENGTH = 3000

    # Bet: archived observation files older than this horizon have no residual
    # value for the Layer-2 observer.
    PURGE_AGE_DAYS = 30

    # Bet: 10 MB per JSONL is the point where rotation buys more than it costs.
    ROTATE_SIZE_MB = 10

    # Bet: purge/rotate maintenance at most once per day is sufficient; running
    # it on every prompt would waste syscalls with no observable benefit.
    PURGE_INTERVAL_SECONDS = 86_400

    # Bet: 3s is enough to resolve `git rev-parse` locally; longer and we'd
    # rather silently skip than stall the user's prompt.
    GIT_TOPLEVEL_TIMEOUT_SECONDS = 3


# ─── Secret scrubbing ───────────────────────────────────────────────────────
# SRP: one responsibility — redact secret-shaped substrings from text.

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
# SRP: turn raw stdin bytes into a typed HookEvent, or signal "nothing to do".
# Death mode: if this disappears, nothing can interpret the hook's JSON.


@dataclass(frozen=True)
class HookEvent:
    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        # Caller: main() — used to skip subagent sessions.
        return bool(self.agent_id)


def parse_hook_event(raw: str) -> Optional[HookEvent]:
    """
    Parse the Claude Code hook JSON. Returns None when the event is empty,
    malformed, or carries no user content — all cases where the observer has
    nothing to record.
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

    return HookEvent(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", ""),
        content=content,
        agent_id=data.get("agent_id", ""),
    )


# ─── Project directory resolution ───────────────────────────────────────────
# SRP: answer one question — "which project should this observation belong to?"
# Coupling: the env var CLAUDE_PROJECT_DIR is the primary, explicit contract;
# the git fallback is the secondary, explicitly-marked escape hatch.


def resolve_project_dir(cwd: str) -> Optional[str]:
    """
    Return the project root, or None if it cannot be determined.

    Primary source: CLAUDE_PROJECT_DIR env var (explicit contract from harness).
    Fallback:       `git rev-parse --show-toplevel` on cwd.
    """
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env_dir:
        return env_dir

    if not (cwd and os.path.isdir(cwd)):
        return None

    try:
        result = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=Policy.GIT_TOPLEVEL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired, FileNotFoundError:
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


# ─── Observation writing ────────────────────────────────────────────────────
# SRP: append one observation record to disk. Nothing else.
# Cohesion: paths and writes live together — deleting ObservationStore deletes
# the entire on-disk layout for Layer 1.


def _utc_timestamp() -> str:
    # Single source of truth for the observation timestamp format.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ObservationStore:
    """On-disk layout for a project's Layer-1 observations."""

    project_dir: str

    @property
    def learnings_dir(self) -> str:
        return os.path.join(self.project_dir, ".learnings")

    @property
    def observations_file(self) -> str:
        return os.path.join(self.learnings_dir, "observations.jsonl")

    @property
    def archive_dir(self) -> str:
        return os.path.join(self.learnings_dir, "observations.archive")

    @property
    def purge_marker(self) -> str:
        return os.path.join(self.learnings_dir, ".last-purge")

    def ensure_dirs(self) -> None:
        os.makedirs(self.learnings_dir, exist_ok=True)

    def append(self, event: HookEvent) -> None:
        """
        Write a single observation line. Caller is expected to have called
        ensure_dirs(). IOError is NOT swallowed here — propagated to the hook
        boundary (main) which is the single point that decides to silently
        drop on failure.
        """
        observation = {
            "timestamp": _utc_timestamp(),
            "session_id": event.session_id,
            "type": "user_prompt",
            "content": scrub_secrets(event.content[: Policy.MAX_CONTENT_LENGTH]),
            "cwd": event.cwd,
        }
        with open(self.observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")


# ─── Layer 1 → Layer 2 bridge ───────────────────────────────────────────────
# SRP: deliver the "new observation available" edge to the observer daemon.
# Death mode: if this class goes away, Layer 2 no longer learns about new
# observations until its next periodic wake — no other behavior breaks.


class ObserverBridge:
    """
    Bridge Layer 1 (this hook) to Layer 2 (observer daemon).

    Responsibilities, in order:
      1. Increment the observation counter.
      2. Lazy-start the daemon if it is not running.
      3. Throttled SIGUSR1 when the counter crosses SIGNAL_EVERY_N.

    All failures are silent: this runs inside a UserPromptSubmit hook and must
    never block the user's session. That is the one explicit exception policy;
    internal helpers propagate, this class swallows.
    """

    def __init__(self, project_dir: str) -> None:
        self._project_dir = project_dir
        self._paths = learnings_state.state_paths(project_dir)

    def notify(self) -> None:
        learnings_state.touch_sentinel(self._paths["sentinel_file"])
        count = learnings_state.increment_counter(self._paths["counter_file"])
        daemon_pid = learnings_state.read_daemon_pid(self._paths["pid_file"])

        if daemon_pid is None:
            # Do not signal on the same invocation that starts the daemon —
            # the daemon's own startup path handles the initial read.
            self._lazy_start_daemon()
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
            subprocess.Popen(
                ["bash", start_script, self._project_dir],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError, subprocess.SubprocessError:
            # Boundary swallow: hook must never block.
            pass

    def _signal_daemon(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGUSR1)
            learnings_state.reset_counter(self._paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            # Boundary swallow: hook must never block.
            pass


# ─── Auto-purge / rotation ──────────────────────────────────────────────────
# SRP: keep the observation directory from growing without bound.
# Cohesion: rotate-when-too-large, delete-when-too-old, and mark-as-ran all
# die together — they are a single maintenance pass.


class ObservationPurger:
    """Runs rotation + archive cleanup at most once per Policy.PURGE_INTERVAL_SECONDS."""

    def __init__(self, store: ObservationStore) -> None:
        self._store = store

    def run_if_due(self) -> None:
        if not self._is_due():
            return
        try:
            self._rotate_if_oversized()
            self._delete_old_archives()
            self._touch_marker()
        except IOError, OSError:
            # Boundary swallow: maintenance failures must not break capture.
            pass

    # ── internals ──
    def _is_due(self) -> bool:
        marker = self._store.purge_marker
        if not os.path.exists(marker):
            return True
        age = _now_epoch() - os.path.getmtime(marker)
        return age > Policy.PURGE_INTERVAL_SECONDS

    def _rotate_if_oversized(self) -> None:
        os.makedirs(self._store.archive_dir, exist_ok=True)
        obs_file = self._store.observations_file
        if not os.path.exists(obs_file):
            return
        size_mb = os.path.getsize(obs_file) / (1024 * 1024)
        if size_mb <= Policy.ROTATE_SIZE_MB:
            return
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = os.path.join(self._store.archive_dir, f"observations-{ts}.jsonl")
        os.rename(obs_file, archive_path)

    def _delete_old_archives(self) -> None:
        archive_dir = self._store.archive_dir
        if not os.path.isdir(archive_dir):
            return
        horizon = Policy.PURGE_AGE_DAYS * Policy.PURGE_INTERVAL_SECONDS
        now = _now_epoch()
        for fname in os.listdir(archive_dir):
            fpath = os.path.join(archive_dir, fname)
            if (now - os.path.getmtime(fpath)) > horizon:
                os.remove(fpath)

    def _touch_marker(self) -> None:
        with open(self._store.purge_marker, "w") as f:
            f.write("")


def _now_epoch() -> float:
    # Single source of truth — all "current wall-clock as seconds" reads go here.
    return datetime.now().timestamp()


# ─── Entry point ────────────────────────────────────────────────────────────
# SRP: orchestrate the hook pipeline. No business logic lives here — only the
# order of the three phases (capture → bridge → maintain) and the boundary
# failure policy.


def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    event = parse_hook_event(raw)
    if event is None or event.is_subagent:
        return

    project_dir = resolve_project_dir(event.cwd)
    if not project_dir:
        return

    store = ObservationStore(project_dir)
    store.ensure_dirs()

    try:
        store.append(event)
    except IOError:
        # Boundary swallow: if we can't write, we also can't usefully bridge.
        return

    # Layer 1 → Layer 2 edge notification.
    ObserverBridge(project_dir).notify()

    # Opportunistic maintenance (rate-limited to once/day internally).
    ObservationPurger(store).run_if_due()


if __name__ == "__main__":
    main()
