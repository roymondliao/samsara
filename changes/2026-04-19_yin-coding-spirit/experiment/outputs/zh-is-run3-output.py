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

# ── Refactor notes (陰面 / v-zh-is) ────────────────────────────────────────
# Each structure below exists for exactly one death (SRP). If you delete it,
# only one caller should hurt — that caller is marked in the docstring.
#
# Closure bets (OCP) are marked with "WAGER:" so an inheritor can find them.
#
# There are no interfaces with a single implementation here — we refuse the
# soundproof-wall abstraction (DIP). The seams are direct function calls,
# strongly-but-visibly coupled (Coupling), and dataclasses hold only the
# values that die together (Cohesion).
#
# Duplication: the two "age-in-seconds vs threshold" checks look similar but
# answer different questions (daily gate vs per-file archive age). They are
# NOT deduplicated, because merging them would be a lie — one lives in
# seconds against a 24h gate, the other in days against a retention policy.
# Forcing them into a shared helper would split the truth (DRY as anti-lie,
# not anti-repetition).

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
# Explicit, visible coupling: we depend on learnings_state by name, not via
# an injected interface. If learnings_state changes shape, this file must
# feel the pain — that is the point.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Tunables (WAGER markers) ────────────────────────────────────────────────
# WAGER: a user prompt rarely exceeds 3000 useful chars for learning signal.
# If prompts routinely carry long pasted logs we care about, raise this.
MAX_CONTENT_LENGTH = 3000

# WAGER: 30 days of archived observations is enough context for Layer 2.
# If Layer 2 ever needs longer memory, this purge is the thing to change.
PURGE_AGE_DAYS = 30

# WAGER: rotate observations.jsonl above 10 MiB. Chosen to keep grep/jq fast.
ROTATE_SIZE_MB = 10

# WAGER: run the purge pass at most once per 24h to avoid filesystem churn.
PURGE_INTERVAL_SECONDS = 24 * 60 * 60

# WAGER: git toplevel lookup should never block the hook; 3s is our ceiling.
GIT_TOPLEVEL_TIMEOUT_SECONDS = 3

# Secret scrubbing pattern. WAGER: these keyword families cover ~all secrets
# pasted into prompts in practice. Adding new families here is the open axis.
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


# ── Scrubbing ───────────────────────────────────────────────────────────────
def scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED].

    Dies alone: only the observation-content path calls this. If this
    function disappears, only observation content would leak secrets.
    """
    return SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
        text,
    )


# ── Hook payload extraction ─────────────────────────────────────────────────
@dataclass(frozen=True)
class HookPayload:
    """The slice of the Claude Code hook JSON this script actually reads.

    Co-death: these four fields are born together from one stdin read and
    die together when the payload is discarded. They do not belong in
    separate structures.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        """Subagent sessions are ignored — we only learn from top-level prompts."""
        return bool(self.agent_id)


def read_hook_payload(raw_stdin: str) -> Optional[HookPayload]:
    """Parse Claude Code hook JSON from a raw stdin string.

    Returns None when the payload is unusable (empty, malformed, or has no
    user content). The single caller — main() — uses None as "stop silently".
    """
    if not raw_stdin.strip():
        return None
    try:
        data = json.loads(raw_stdin)
    except json.JSONDecodeError:
        return None

    tool_input = data.get("tool_input", data.get("input", {}))
    if isinstance(tool_input, dict):
        content = tool_input.get("content", tool_input.get("message", "")) or ""
    else:
        content = str(tool_input)

    if not content:
        return None

    return HookPayload(
        session_id=data.get("session_id", "unknown"),
        cwd=data.get("cwd", ""),
        content=content,
        agent_id=data.get("agent_id", ""),
    )


# ── Project resolution ──────────────────────────────────────────────────────
def resolve_project_dir(cwd: str) -> str:
    """Resolve the project directory for this observation.

    Precedence: CLAUDE_PROJECT_DIR env var → git toplevel of cwd → "".
    Empty string means "give up quietly" — main() uses that as its signal.

    This is the only place we decide where observations go. If project
    resolution is ever wrong, there is exactly one place to fix.
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
            timeout=GIT_TOPLEVEL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired, FileNotFoundError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


# ── Observation writing ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class LearningsPaths:
    """All filesystem paths derived from a project directory.

    Co-death: computed together, used together, thrown away together. If we
    ever needed to point observations and archives at different roots, that
    would be a different structure — not a mutation of this one.
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


def build_observation(payload: HookPayload) -> dict:
    """Build the dict that becomes one JSONL line.

    Dies alone: the one and only producer of the observation record shape.
    If the schema changes, this function is where it happens.
    """
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": payload.session_id,
        "type": "user_prompt",
        "content": scrub_secrets(payload.content[:MAX_CONTENT_LENGTH]),
        "cwd": payload.cwd,
    }


def append_observation(observations_file: str, observation: dict) -> bool:
    """Append one JSON line to observations.jsonl.

    Returns True on success, False on IOError. The caller decides whether a
    failed write should short-circuit the rest of the hook.
    """
    try:
        with open(observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError:
        return False


# ── Layer 1 → Layer 2 bridge ────────────────────────────────────────────────
def _start_observer_daemon(project_dir: str) -> None:
    """Detached launch of the observer daemon. Silent on failure by design.

    Dies alone: exists solely to encapsulate the Popen flags that keep the
    hook from holding on to stdin/stdout/stderr.
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


def _signal_observer(daemon_pid: int, counter_file: str) -> None:
    """Wake the observer and reset the throttle counter. Silent on failure."""
    try:
        os.kill(daemon_pid, signal.SIGUSR1)
        learnings_state.reset_counter(counter_file)
    except ProcessLookupError, PermissionError, OSError:
        pass


def bridge_to_observer(project_dir: str) -> None:
    """Layer 1 → Layer 2 bridge.

    1. Increment observation counter.
    2. Lazy-start observer daemon if not running.
    3. Send SIGUSR1 every SIGNAL_EVERY_N observations (throttled).

    All failures are silent — hook must never block the user's session.
    This is the only place that signals the observer; its death is the
    death of the bridge.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        _start_observer_daemon(project_dir)
        # No signal on the same invocation that just started the daemon.
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        _signal_observer(daemon_pid, paths["counter_file"])


# ── Purge / rotation ────────────────────────────────────────────────────────
def _should_purge_now(purge_marker: str) -> bool:
    """Daily-gate check against the purge marker.

    Note: this reads mtime in seconds vs PURGE_INTERVAL_SECONDS. It looks
    like the archive-age check below, but it is NOT the same question — one
    is a run-frequency gate, the other is a retention decision. We keep
    them separate so neither lies on behalf of the other.
    """
    if not os.path.exists(purge_marker):
        return True
    age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
    return age > PURGE_INTERVAL_SECONDS


def _rotate_if_large(observations_file: str, archive_dir: str) -> None:
    """Rotate observations.jsonl into the archive if it crosses ROTATE_SIZE_MB."""
    if not os.path.exists(observations_file):
        return
    size_mb = os.path.getsize(observations_file) / (1024 * 1024)
    if size_mb <= ROTATE_SIZE_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(archive_dir, f"observations-{ts}.jsonl")
    os.rename(observations_file, archive_path)


def _prune_old_archives(archive_dir: str) -> None:
    """Remove archive files older than PURGE_AGE_DAYS."""
    now = datetime.now().timestamp()
    for fname in os.listdir(archive_dir):
        fpath = os.path.join(archive_dir, fname)
        age_days = (now - os.path.getmtime(fpath)) / 86400
        if age_days > PURGE_AGE_DAYS:
            os.remove(fpath)


def maybe_purge(paths: LearningsPaths) -> None:
    """Rotate + prune archives, at most once per PURGE_INTERVAL_SECONDS.

    Dies alone: the only housekeeping entry point. If purge behavior needs
    to change, this function is the single door.
    """
    if not _should_purge_now(paths.purge_marker):
        return

    try:
        os.makedirs(paths.archive_dir, exist_ok=True)
        _rotate_if_large(paths.observations_file, paths.archive_dir)
        _prune_old_archives(paths.archive_dir)
        # Touch the marker last — if we crashed above, we'll retry next hook.
        with open(paths.purge_marker, "w") as f:
            f.write("")
    except IOError, OSError:
        pass


# ── Entry point ─────────────────────────────────────────────────────────────
def main() -> None:
    try:
        raw = sys.stdin.read()
    except IOError:
        return

    payload = read_hook_payload(raw)
    if payload is None or payload.is_subagent:
        return

    project_dir = resolve_project_dir(payload.cwd)
    if not project_dir:
        return

    paths = LearningsPaths.for_project(project_dir)
    os.makedirs(paths.learnings_dir, exist_ok=True)

    observation = build_observation(payload)
    if not append_observation(paths.observations_file, observation):
        return

    bridge_to_observer(project_dir)
    maybe_purge(paths)


if __name__ == "__main__":
    main()
