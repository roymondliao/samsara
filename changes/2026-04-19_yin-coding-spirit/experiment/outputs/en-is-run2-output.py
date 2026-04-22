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

──────────────────────────────────────────────────────────────────────────
Shape notes (yin-side, per v-en-is spirit)

Each structure below is shaped around a single death-responsibility — the
one pain that would appear if it vanished. The seams between structures
are explicit rather than loose: callers hand dependencies in, so coupling
is visible instead of hidden behind a soundproof wall.

There are no one-impl interfaces or pattern-scaffolds here. Where the
original script bundled concerns together (parse + derive + write + bridge
+ purge), those concerns have been separated only to the degree that each
piece can answer "who feels the pain if I disappear?" with one name.

Every failure path is silent on purpose — the hook runs on the user's
prompt-submit path and must never block. That contract is the marked bet
of this module; every `except: pass` is a promise kept to that contract,
not sloppiness. The contract is named here so an inheritor doesn't mistake
silence for carelessness.
──────────────────────────────────────────────────────────────────────────
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
# Kept as a module import — learnings_state owns daemon-state death
# responsibility, and duplicating that here would be "two places telling
# the same lie" about where daemon state lives.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import learnings_state  # noqa: E402


# ── Tunables ──────────────────────────────────────────────────────────────
# Grouped so any inheritor sees the full set of magic numbers in one place.
# Splitting them across functions would hide the bet being made.

MAX_CONTENT_LENGTH = 3000  # per-observation char cap (prevent bloat)
PURGE_AGE_DAYS = 30  # archive retention
PURGE_INTERVAL_SECONDS = 86400  # run purge at most once per day
ROTATION_SIZE_MB = 10  # rotate observations.jsonl above this
GIT_TOPLEVEL_TIMEOUT = 3  # seconds; fallback project-root lookup

# Secret scrubbing pattern — one regex, one job.
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|credentials?|auth)"
    r"""(["'\s:=]+)"""
    r"([A-Za-z]+\s+)?"
    r"([A-Za-z0-9_\-/.+=]{8,})"
)


def scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED].

    Death-responsibility: if this disappears, the pain is "secrets leak
    into observations.jsonl." Nowhere else — so it lives alone.
    """
    return SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
        text,
    )


# ── Hook payload parsing ──────────────────────────────────────────────────


@dataclass(frozen=True)
class HookEvent:
    """The subset of the Claude Code hook payload this script cares about.

    Only fields we actually use live here. Ghost-promise avoidance: if a
    field isn't named by a real caller below, it doesn't belong in here.
    """

    session_id: str
    cwd: str
    content: str
    agent_id: str

    @property
    def is_subagent(self) -> bool:
        return bool(self.agent_id)


def parse_hook_event(raw: str) -> Optional[HookEvent]:
    """Parse raw stdin JSON into a HookEvent.

    Returns None on any parse failure or when the payload carries no
    user content. None is the single "nothing to do" signal — callers
    do not need to distinguish between "bad JSON" and "empty message."
    """
    if not raw or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError, ValueError:
        return None
    if not isinstance(data, dict):
        return None

    tool_input = data.get("tool_input", data.get("input", {}))
    if isinstance(tool_input, dict):
        content = tool_input.get("content", tool_input.get("message", "")) or ""
    else:
        content = str(tool_input)

    if not content:
        return None

    return HookEvent(
        session_id=str(data.get("session_id", "unknown")),
        cwd=str(data.get("cwd", "") or ""),
        content=str(content),
        agent_id=str(data.get("agent_id", "") or ""),
    )


# ── Project root resolution ───────────────────────────────────────────────


def resolve_project_dir(cwd: str) -> str:
    """Resolve the project root.

    Prefers CLAUDE_PROJECT_DIR; falls back to `git rev-parse --show-toplevel`
    against cwd. Returns "" if neither works — callers treat "" as
    "we do not have a project, drop the observation."

    This is a single death-responsibility: "where do .learnings live?"
    It is the only place that question is answered, so the lie cannot
    split across the codebase.
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
            timeout=GIT_TOPLEVEL_TIMEOUT,
        )
    except subprocess.TimeoutExpired, FileNotFoundError, OSError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


# ── Observation write path ────────────────────────────────────────────────


@dataclass(frozen=True)
class LearningsLayout:
    """Filesystem layout for .learnings under a given project root.

    All path decisions are frozen here so no other function is quietly
    recomputing them. If this type disappears, the pain is "paths drift
    and two places disagree about where observations live" — that is the
    exact lie this structure exists to prevent.
    """

    root: str
    observations_file: str
    archive_dir: str
    purge_marker: str

    @classmethod
    def for_project(cls, project_dir: str) -> "LearningsLayout":
        root = os.path.join(project_dir, ".learnings")
        return cls(
            root=root,
            observations_file=os.path.join(root, "observations.jsonl"),
            archive_dir=os.path.join(root, "observations.archive"),
            purge_marker=os.path.join(root, ".last-purge"),
        )

    def ensure_root(self) -> None:
        os.makedirs(self.root, exist_ok=True)


def build_observation(event: HookEvent) -> dict[str, Any]:
    """Produce the JSON record to append. Pure function — no I/O.

    Pulled out of main() so its shape is inspectable and testable without
    touching the filesystem. One reason to change: the record schema.
    """
    content_clean = scrub_secrets(event.content[:MAX_CONTENT_LENGTH])
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": event.session_id,
        "type": "user_prompt",
        "content": content_clean,
        "cwd": event.cwd,
    }


def append_observation(layout: LearningsLayout, observation: dict[str, Any]) -> bool:
    """Append one JSONL record. Returns True on success.

    Silent on IOError by contract (see module docstring). Returning a bool
    rather than raising lets the caller decide whether to continue with
    the bridge + purge steps — the failure mode is visible at the call
    site, not hidden behind an exception no one will catch.
    """
    try:
        with open(layout.observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
        return True
    except IOError, OSError:
        return False


# ── Layer 1 → Layer 2 bridge ──────────────────────────────────────────────


def bridge_to_observer(project_dir: str) -> None:
    """Nudge the Layer-2 observer daemon.

    Steps:
      1. Touch sentinel so the daemon knows this project is live.
      2. Increment the observation counter.
      3. If no daemon is running, lazy-start it (detached) and return —
         no signal on the same invocation that started it.
      4. Otherwise, every SIGNAL_EVERY_N observations, send SIGUSR1 and
         reset the counter.

    Every failure is swallowed. The hook must never block the user's
    session — that is the marked bet this function is placed against.
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])

    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        _lazy_start_observer(project_dir)
        return

    if count >= learnings_state.SIGNAL_EVERY_N:
        try:
            os.kill(daemon_pid, signal.SIGUSR1)
            learnings_state.reset_counter(paths["counter_file"])
        except ProcessLookupError, PermissionError, OSError:
            pass


def _lazy_start_observer(project_dir: str) -> None:
    """Launch start-observer.sh detached, if present. Silent on failure."""
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


# ── Purge / rotation ──────────────────────────────────────────────────────


def _purge_marker_is_stale(marker_path: str) -> bool:
    """True if the purge marker is missing or older than the interval."""
    if not os.path.exists(marker_path):
        return True
    try:
        age = datetime.now().timestamp() - os.path.getmtime(marker_path)
    except OSError:
        return True
    return age > PURGE_INTERVAL_SECONDS


def _rotate_if_oversized(layout: LearningsLayout) -> None:
    """If observations.jsonl exceeds ROTATION_SIZE_MB, move it into archive."""
    if not os.path.exists(layout.observations_file):
        return
    try:
        size_mb = os.path.getsize(layout.observations_file) / (1024 * 1024)
    except OSError:
        return
    if size_mb <= ROTATION_SIZE_MB:
        return
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(layout.archive_dir, f"observations-{ts}.jsonl")
    try:
        os.rename(layout.observations_file, archive_path)
    except OSError:
        pass


def _prune_old_archives(archive_dir: str) -> None:
    """Delete archive files older than PURGE_AGE_DAYS."""
    try:
        entries = os.listdir(archive_dir)
    except OSError:
        return
    now = datetime.now().timestamp()
    for fname in entries:
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


def maybe_purge(layout: LearningsLayout) -> None:
    """Rotate + prune archives, at most once per PURGE_INTERVAL_SECONDS.

    Death-responsibility: disk hygiene for .learnings. If this function
    vanishes, the pain is "observations.jsonl grows without bound and old
    archives never expire." That pain lives nowhere else in this file.
    """
    if not _purge_marker_is_stale(layout.purge_marker):
        return

    try:
        os.makedirs(layout.archive_dir, exist_ok=True)
        _rotate_if_oversized(layout)
        _prune_old_archives(layout.archive_dir)
        with open(layout.purge_marker, "w") as f:
            f.write("")
    except IOError, OSError:
        # Silent by contract — see module docstring.
        pass


# ── Entry point ───────────────────────────────────────────────────────────


def main() -> None:
    """Orchestrate: parse → resolve project → write → bridge → purge.

    Each step short-circuits on "nothing to do." The flow is flat and
    linear on purpose — nesting would hide where early-exits live, and
    early-exits are this script's primary safety mechanism (the hook must
    never block the user's prompt path).
    """
    try:
        raw = sys.stdin.read()
    except IOError, OSError:
        return

    event = parse_hook_event(raw)
    if event is None or event.is_subagent:
        return

    project_dir = resolve_project_dir(event.cwd)
    if not project_dir:
        return

    layout = LearningsLayout.for_project(project_dir)
    layout.ensure_root()

    observation = build_observation(event)
    if not append_observation(layout, observation):
        return

    bridge_to_observer(project_dir)
    maybe_purge(layout)


if __name__ == "__main__":
    main()
