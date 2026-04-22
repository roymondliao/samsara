# Code Quality Reference

## Purpose

This reference guides `samsara:code-quality-reviewer` in assessing code-level quality.
It is organized around 8 criteria, each anchored to a concrete judgment question and
paired with real code examples drawn from this codebase.

## Scope

**In scope:** readability, maintainability, extensibility, debuggability, reuse,
structural clarity, logic elegance, and absence of redundancy.

## Out of scope

The following concerns belong to `samsara:code-reviewer` (yin), not this reference:

- Silent rot (behavior drift unreported by tests)
- Dishonest naming (names that describe what code should do, not what it does)
- Security vulnerabilities
- Performance characteristics
- Unhandled exception paths that silently discard errors

When you observe an out-of-scope issue, note it as a pointer to yin review rather
than scoring it here.

## How to use these criteria

Read each criterion's judgment question. Look at the code under review. Compare it
to the Good and Bad examples. Produce one of: `Pass`, `Concern` (with explanation),
or `UNKNOWN` (when the code is too short, too context-dependent, or the criterion
does not apply). Do not produce `Pass` when you are actually unsure — `UNKNOWN` is
the honest answer.

---

## Criterion 1: Readability

**Judgment question:** The person taking over this code in 30 seconds — can they
read the intent of this block without tracing into other files?

**What makes code readable:** functions and variables named after what they represent
in the domain (not how they are implemented), short functions with a single visible
purpose, and absent comments that only re-state what the code already says.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-must-output.py`, lines 84–105

```python
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
```

The function name says what it does. The return type says when it gives up. Each
failure path has one `return None`. A reader who has never seen this codebase knows
what they get in 10 seconds.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 100–149

```python
def main() -> None:
    # Read hook JSON from stdin
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        return

    # Extract fields from Claude Code hook format
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", "")

    # UserPromptSubmit provides the user's message in tool_input
    tool_input = data.get("tool_input", data.get("input", {}))
    if isinstance(tool_input, dict):
        content = tool_input.get("content", tool_input.get("message", ""))
    else:
        content = str(tool_input)

    if not content:
        return

    # Skip subagent sessions
    agent_id = data.get("agent_id", "")
    if agent_id:
        return

    # Determine project directory
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        # Try to derive from cwd via git
        if cwd and os.path.isdir(cwd):
            try:
                import subprocess
                ...
```

`main()` begins parsing JSON, then extracts fields, then filters subagents, then
resolves project directory — four distinct jobs mixed together with only inline
comments to signal the transitions. A reader lands inside and cannot tell where one
responsibility ends and another begins.

---

**Verdict weight:** Critical. Unreadable code is the primary multiplier for all
other quality defects.

---

## Criterion 2: Maintainability

**Judgment question:** When a bug is found three months from now, can the
maintainer change exactly one place without accidentally changing something else?

**What makes code maintainable:** each logical rule exists in exactly one place,
configuration lives in named constants rather than inline literals, and error
handling is predictable (always returns a typed result, never swallows silently in
ways callers cannot detect).

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-must-output.py`, lines 31–38

```python
MAX_CONTENT_LENGTH = 3000          # per-observation character cap (anti-bloat)
PURGE_AGE_DAYS = 30                # archive retention window
ROTATE_SIZE_MB = 10                # rotate observations.jsonl above this size
PURGE_INTERVAL_SEC = 86400         # run purge at most once per day
GIT_TOPLEVEL_TIMEOUT_SEC = 3       # bound git rev-parse on fallback path
```

Each threshold is a named constant with a comment that explains the reasoning, not
just the value. When the retention policy changes, there is one place to edit, and
the comment tells the maintainer why that value was chosen.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 180–183

```python
    if os.path.exists(purge_marker):
        age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
        should_purge = age > 86400  # 24 hours
```

`86400` appears as a literal inside `main()`. The same concept (`PURGE_INTERVAL_SEC`)
is also implicitly used in the `_bridge_to_observer` call. If the interval changes,
a maintainer must know to search for the literal — and may miss it. The comment
`# 24 hours` only translates the number; it does not say why that threshold exists.

---

**Verdict weight:** Critical. Maintainability defects compound over time; they cost
little to fix early and much to fix after the code is in production.

---

## Criterion 3: Extensibility

**Judgment question:** When the next similar requirement arrives, can it be added
by inserting new code rather than modifying existing code?

**What makes code extensible:** boundaries between collaborators are explicit,
each collaborator owns exactly one thing that can change, and the extension point
(the seam) is visible without tracing the full call graph.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/zh-is-output.py`, lines 169–208

```python
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
        ...
```

If the on-disk layout changes (e.g. one-file-per-day instead of one rolling file),
only `ObservationStore` needs to change. The caller (`main`) does not know or care
about paths. The seam is visible in the class boundary.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 150–211

```python
    learnings_dir = os.path.join(project_dir, ".learnings")
    os.makedirs(learnings_dir, exist_ok=True)

    observations_file = os.path.join(learnings_dir, "observations.jsonl")

    # ... 40 lines later ...

    if should_purge:
        try:
            archive_dir = os.path.join(learnings_dir, "observations.archive")
            os.makedirs(archive_dir, exist_ok=True)

            if os.path.exists(observations_file):
                size_mb = os.path.getsize(observations_file) / (1024 * 1024)
                if size_mb > 10:
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    archive_path = os.path.join(archive_dir, f"observations-{ts}.jsonl")
                    os.rename(observations_file, archive_path)
```

Path construction, file append, and rotation logic are all in `main()`. Adding a
second output sink (e.g. writing to a remote endpoint) requires finding three
separate places in `main()` and deciding which locals to duplicate. There is no
seam — only a long function that must be surgically modified.

---

**Verdict weight:** Important. Extensibility defects are invisible until the
requirement arrives; by then, modification cost is high.

---

## Criterion 4: Debuggability

**Judgment question:** When this code produces the wrong result, does the error
message or return value point toward the actual cause, or does it silently discard
the signal?

**What makes code debuggable:** errors are returned as typed values or raised with
context (not silently swallowed), functions have single exit contracts (`None` means
one specific thing, not "any of five things went wrong"), and the call site can
observe which collaborator failed.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/zh-is-output.py`, lines 185–207

```python
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
```

The return type (`bool`) has one documented meaning. The caller knows: `False` means
IO failure, not "something somewhere in the stack went wrong." A debugger can add
logging at the `except IOError` line and immediately see the failure.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 100–108

```python
def main() -> None:
    # Read hook JSON from stdin
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        return
```

`main()` returns `None` for at least five distinct reasons: empty stdin, JSON parse
error, missing content, missing project directory, and IO failure on write. All five
look identical to the caller. When the hook silently does nothing, there is no way
to distinguish "correct no-op" from "five different failure modes."

---

**Verdict weight:** Critical for production hooks and background daemons where
silent wrong-behavior can persist undetected for days.

---

## Criterion 5: Reuse

**Judgment question:** Is the same logic written more than once? If two blocks of
code describe the same operation, which one is authoritative when they diverge?

**What good reuse looks like:** shared logic is extracted to a named helper at the
first duplication, the helper has a single clear contract, and all callers use the
helper rather than copying the logic.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-must-output.py`, lines 51–56

```python
def scrub_secrets(text: str) -> str:
    """Replace common secret patterns with [REDACTED]."""
    return _SECRET_RE.sub(
        lambda m: m.group(1) + m.group(2) + (m.group(3) or "") + "[REDACTED]",
        text,
    )
```

One function. One regex. The regex is a module-level constant (`_SECRET_RE`). Every
caller that needs secret scrubbing uses this one function. If the pattern is wrong,
there is one place to fix it.

---

**Bad example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-is-output.py`, lines 75–97

```python
class SecretScrubber:
    """
    Replace common secret-like substrings with [REDACTED].

    Death-responsibility: this class exists solely so that a future change to
    the redaction rule has exactly one place to edit. ...
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
```

This class packages the scrubbing logic behind **three names** callers can reach
for: `SecretScrubber.scrub` (public), `SecretScrubber._replace` (underscore but
still accessible), and the class itself (inheritable). A future caller that wants
similar scrubbing can call the method, inherit from the class, or — perceiving
class-as-namespace friction — just write their own scrubber. Three plausible reuse
paths, three plausible divergences.

The `scrub_secrets` free-function version (shown above as Good) offers exactly one
reuse path: `from x import scrub_secrets`. There is no inheritance surface, no
hidden `_replace` that someone can patch without the author knowing, and no
temptation to "just write my own because depending on a class feels heavy."

This is why class-wrapping-a-function is a **reuse** regression even when it looks
like "reuse achieved": it multiplies the shapes of reuse instead of forcing one.

Note: the distinction between Criterion 5 and Criterion 7 (Elegant Logic) is that
Criterion 5 asks "can future callers reuse this cleanly through one path?" while
Criterion 7 asks "is this the shortest path from intent to implementation?"
Class-wrapping often fails both, but the reuse lens is about *divergence over time*
across callers, while the elegance lens is about *extra structure now*. Cross-ref
Criterion 7's `ProjectResolver` example for the elegance framing of the same
anti-pattern.

Criterion 5 differs from Criterion 8 (No Redundancy) in that 5 is about *missing*
extraction (logic duplicated across sites), while 8 is about *extra* code that
says the same thing the surrounding code already says.

---

**Verdict weight:** Important. Duplicated logic creates divergence over time; the
wrong copy gets fixed and the right copy stays broken.

---

## Criterion 6: Clear Structure

**Judgment question:** For each module, function, and class boundary, can you give
a one-sentence answer to "why is this here and not in the neighbor"?

**What clear structure looks like:** each boundary corresponds to a distinct reason
to change; if two things live together, they share one death-reason; if they live
apart, each has its own death-reason that the other does not share.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/zh-is-output.py`, lines 1–34

```python
"""
...
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
...
"""
```

Each collaborator boundary is stated in the module docstring. A reader can verify
that `ObservationStore` does not call `learnings_state` (that is `ObserverBridge`'s
job) and that `HookInput` does not resolve paths (that is `ProjectRoot`'s job).
The structure is documented at the top and verifiable line by line.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 58–98

```python
def _bridge_to_observer(project_dir: str) -> None:
    """
    Layer 1 → Layer 2 bridge:
    1. Increment observation counter
    2. Lazy-start observer daemon if not running
    3. Send SIGUSR1 every N observations (throttled)
    ...
    """
    paths = learnings_state.state_paths(project_dir)
    learnings_state.touch_sentinel(paths["sentinel_file"])
    count = learnings_state.increment_counter(paths["counter_file"])
    daemon_pid = learnings_state.read_daemon_pid(paths["pid_file"])

    if daemon_pid is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "start-observer.sh")
        if os.path.exists(start_script):
            try:
                subprocess.Popen(...)
            except (OSError, subprocess.SubprocessError):
                pass
        return
```

`_bridge_to_observer` does three things: state-file management (sentinel, counter),
daemon lifecycle (lazy start), and signaling (SIGUSR1 throttle). These have
different reasons to change: state format could change without changing the daemon
start logic, and the signal throttle is independent of both. Calling this one
function means one change to the signaling logic requires reading and understanding
all three responsibilities.

---

**Verdict weight:** Important. Structural violations lower the accuracy of all other
criteria because reviewers cannot tell which parts of the code are load-bearing.

---

## Criterion 7: Elegant Logic (no extras)

**Judgment question:** Is there any abstract layer, temporary variable, or parameter
that could be removed without changing the observable behavior?

**What elegance looks like:** the shortest path between intent and implementation,
where every intermediate value earns its name by being used more than once or by
naming something the reader needs to understand.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-must-output.py`, lines 125–128

```python
def resolve_project_dir(cwd: str) -> str:
    """Resolve project dir: CLAUDE_PROJECT_DIR env first, else git toplevel of cwd."""
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return env_dir or _git_toplevel(cwd)
```

Two lines of logic. `env_dir` earns its name: it would be unclear to write
`os.environ.get(...) or _git_toplevel(cwd)` in one line without it. Nothing is
extra; nothing is missing.

---

**Bad example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-is-output.py`, lines 153–186

```python
class ProjectResolver:
    """
    Resolve the project root directory for a given hook invocation.
    ...
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
                ...
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        if result.returncode != 0:
            return None
        toplevel = result.stdout.strip()
        return toplevel or None
```

`ProjectResolver` is a class with no instance state and two static methods. The
class adds one name (`ProjectResolver`) and one indirection without adding any
reuse, testability, or boundary that a module-level function with a private helper
does not already provide. The final line `return toplevel or None` introduces an
intermediate variable (`toplevel`) that is only used once — it could be
`return result.stdout.strip() or None`.

---

**Verdict weight:** Suggestion (usually). Extra abstraction layers are low-severity
until they compound into the pattern seen in the full `en-is-output.py` (8 classes
for a 215-line script), at which point the overhead is Critical.

---

## Criterion 8: No Redundancy

**Judgment question:** Do two sections of code describe the same fact? If the same
fact is stated twice and one copy is updated, will the other copy silently diverge?

**What no-redundancy looks like:** each fact — each configuration value, each
decision rule, each data shape — appears exactly once. A change to that fact
requires editing exactly one line or one function.

---

**Good example**
source: `changes/2026-04-19_yin-coding-spirit/experiment/outputs/zh-is-output.py`, lines 53–62

```python
MAX_CONTENT_LENGTH = 3000          # per-observation char cap, anti-bloat
PURGE_AGE_DAYS = 30                # archive retention before deletion
PURGE_INTERVAL_SECONDS = 86400     # run auto-purge at most once per day
ROTATE_THRESHOLD_MB = 10           # rotate observations.jsonl above this
GIT_RESOLVE_TIMEOUT_SEC = 3        # cap for `git rev-parse` fallback
```

Five facts, five names, five places to edit. No fact appears twice.
`ObservationStore._should_purge` uses `PURGE_INTERVAL_SECONDS` directly — it does
not restate `86400`.

---

**Bad example**
source: `hooks/scripts/observe-learnings.py`, lines 178–193

```python
    purge_marker = os.path.join(learnings_dir, ".last-purge")
    should_purge = True
    if os.path.exists(purge_marker):
        age = datetime.now().timestamp() - os.path.getmtime(purge_marker)
        should_purge = age > 86400  # 24 hours

    if should_purge:
        try:
            archive_dir = os.path.join(learnings_dir, "observations.archive")
            os.makedirs(archive_dir, exist_ok=True)

            if os.path.exists(observations_file):
                size_mb = os.path.getsize(observations_file) / (1024 * 1024)
                if size_mb > 10:
```

Two facts appear as literals: `86400` (purge interval) and `10` (rotation threshold
in MB). Both also exist implicitly in the understanding that `PURGE_AGE_DAYS = 30`
is a third threshold (defined at the top), while `86400` and `10` are not named
constants at all. If the rotation threshold changes to 20 MB, there is one copy to
update — but a maintainer must first find it by searching for `10` (which also
appears in other contexts). The path `".last-purge"` and `"observations.archive"`
are also literal strings not extracted to a data structure, meaning a layout change
requires grepping for string literals rather than editing one place.

---

**Verdict weight:** Important. Redundancy creates divergence traps that are
invisible until they activate in production.

---

## Closing: How to turn 8 criteria into a review output

1. Read the code under review against each criterion's judgment question.
2. For each criterion, produce one of:
   - `Pass` — the code clearly satisfies the criterion
   - `Concern: [specific observation]` — the code has a deficiency with a concrete location
   - `UNKNOWN` — the code is too short or too context-dependent for this criterion to apply
3. Note the verdict weight (Critical / Important / Suggestion) when reporting concerns.
4. If you see something that belongs to yin review (silent rot, dishonest naming,
   security, performance), mark it `[yin]` and do not score it under these 8 criteria.
5. Do not produce `Pass` as a default. If you cannot evaluate a criterion, say `UNKNOWN`.
   `UNKNOWN` is not a failure of the review — it is honest signal about the limits
   of what these 8 criteria can detect on the code provided.
