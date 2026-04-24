# Code Review Reference — Imperative Code Behavioral Patterns

> 陽面的 code review 問「這段 code 有沒有 bug」。
> 陰面問的是「這段 code 在什麼條件下靜默腐爛，而作者永遠不知道」。

---

## Applicability

**Domain:** `code`

**Applies to:** Imperative code in any general-purpose programming language —
Python, TypeScript, JavaScript, Go, Rust, Java, Ruby, C, C++, C#, Kotlin, Swift,
and equivalents. These are files where the execution model is: function calls function,
errors propagate (or fail to), state mutates, and names make promises about behavior.

**Excluded principles:** None. All five review steps apply to imperative code.

**Does not apply to:** Infrastructure-as-code, container definitions, pipeline configurations,
or orchestration manifests. Those domains have their own reference files. If you are reviewing
one of those file types with this reference, the router selected incorrectly — return UNKNOWN.

---

## Purpose

This reference guides `samsara:code-reviewer` in applying domain-specific behavioral
patterns when reviewing imperative code. It provides the detection patterns for
Steps 1, 2, 3, and 5 of the review procedure. Step 4 (Scar Report Integrity)
is domain-agnostic and lives in the agent definition — not here.

The Three Mother Rules (also in the agent definition) supply the cross-domain judgment
standard. This reference translates those rules into concrete imperative-code patterns.

---

## Step 1: Deletion Analysis — What to Look For

**The core question:** Can this be deleted? If it disappeared and nothing felt pain, it shouldn't exist.

**Patterns to detect:**

### Dead Code

Code that is unreachable — after a `return`, inside a branch condition that can never be true,
in a function that is defined but never imported or called anywhere.

- Look for: functions defined in a module but not exported and not called within the file
- Look for: code following unconditional `return`, `raise`, `panic`, `exit`
- Look for: branches conditioned on constants that evaluate to `false`

**Dead code is Critical** — it misleads the next developer into believing it serves a purpose.

### Uncalled Functions

Functions that exist but have no callers — neither internal callers nor external callers
through the module's public interface.

- Ask of every function: who calls this? If the answer requires searching the entire codebase
  and finding no callers, flag it.
- Exception: test helpers, public API endpoints explicitly documented as such, and callbacks
  registered by convention (lifecycle hooks, framework decorators). These have implicit callers.
- When uncertain: flag as Important, note "unable to verify callers within this diff"

**Uncalled functions are Critical** when clearly internal. **Important** when callers may be external.

### Abstractions Serving No Current Purpose

An abstraction — a class, interface, base type, utility module, generic function — that
was written for anticipated future use but has exactly one use site with no variation.

- Look for: abstract base classes with one concrete subclass that overrides everything
- Look for: generic functions parameterized on types that only appear with one concrete type
- Look for: utility functions that wrap a single standard library call with no added behavior
- Ask: does this abstraction make the code simpler to understand, or does it require a detour?

**Abstractions with no current purpose are Important** — they may be premature optimization of structure.

---

## Step 2: Naming Honesty — What to Look For

**The core question:** Is this name lying? A name is lying if the name makes a promise
the implementation does not keep.

**Critical patterns (classify all findings as Critical):**

### Boolean Names That Include Non-Boolean Outcomes

`is_done`, `is_complete`, `is_ready` — these names promise a binary state.
If the implementation returns `True` for cases that are not actually done/complete/ready
(e.g., also returns `True` for "unknown" or "in-progress-but-gave-up"), the name lies.

- `is_done` that returns `True` when a task timed out: name implies completion, state is abandonment
- `is_complete` that returns `True` when result is partial: name implies whole, state is fragment
- `is_ready` that returns `True` when fallback data is in use: name implies operational, state is degraded

### Success/Failure Names That Include Ambiguous Outcomes

`is_success`, `succeeded`, `is_ok` — these names promise a binary result assessment.
If the implementation returns `True` for responses that contain error fields, partial results,
or uncertain states, the name lies.

- `is_success(response)` returning `True` when `response` is non-None but `response.error` is set
- `succeeded` returning `True` when an operation completed but produced no output
- `is_ok` returning `True` when a health check passes a threshold but the threshold is wrong

### Error Handler Names That Don't Handle

`handle_error`, `on_error`, `error_handler` — these names promise that the error is handled.
If the implementation swallows the error (catches and does nothing, or returns a default),
the name lies about what happens to the error.

- `handle_error` that logs and returns `None`: error is not handled, it is recorded and discarded
- `on_error` that sets a flag and continues: the error's effect on downstream logic is untracked
- Exception: `suppress_error` or `ignore_error` are honest names for intentional suppression

### Scope-Misleading Names

Names that imply a narrow scope but perform a wide action:
- `get_*` that also modifies state or has side effects
- `validate_*` that also transforms or persists data
- `check_*` that also triggers external calls

---

## Step 3: Silent Rot Paths — What to Look For

**The core question:** Does this code path fail without announcing it?
Silent rot is code that reaches a bad state but does not propagate the signal.

**Critical patterns (classify all findings as Critical):**

### Swallowed Exceptions

An exception is caught in a block that neither re-raises it nor logs it.
The caller receives a default value (None, False, 0, empty list) with no indication
that the operation failed.

Pattern to look for:
- Bare `except:` or `except Exception:` blocks with no log statement and no re-raise
- `.catch(() => null)` in JavaScript/TypeScript catch chains
- `recover()` in Go blocks that return zero values without accompanying error returns

**The key test:** Can the caller distinguish "operation succeeded with empty result"
from "operation failed silently"? If no, this is a swallowed exception.

### Fallbacks Without Degraded State Marking

When a primary source fails, the code falls back to a secondary source — but the caller
is not informed that degraded data is in use.

The problem: downstream logic assumes it has authoritative data. If the secondary source
is stale or the default is a placeholder, the caller silently makes decisions on wrong data.

**Detection:** Any fallback chain where the return type does not distinguish
"authoritative result" from "fallback result."

Example shape: `primary.get(key)` fails silently, returns `secondary.get(key, DEFAULT)`.
The caller sees a value and proceeds as if it is authoritative.

### Default Values Turning Unknown Into Known

A missing field, absent key, or failed lookup is silently replaced with a default value.
The caller receives a "known" value when the true state is "unknown."

- `dict.get(key, 0)` — if 0 is a valid non-zero count, caller cannot detect the key was missing
- `os.getenv("API_URL", "http://localhost")` — caller may not know it's using a local fallback
- ORM `.first()` returning `None` when `.get()` would raise — but `None` is also a valid result

**Key question:** Can the caller detect that the default was used instead of a real value?
If the default is indistinguishable from a valid value for that field, this is silent rot.

### Retry Logic Without Idempotency

Retry loops that re-invoke an operation that has side effects, without verifying
that re-invocation is safe.

- Retrying a payment charge without checking if the first attempt succeeded
- Retrying a database insert without checking if a duplicate now exists
- Retrying an API call that creates resources without deduplication

Pattern: `for attempt in range(N): call()` where `call()` creates or modifies external state.
The test: if the operation succeeds on attempt 1 but the response is lost, does retry 2 duplicate?

### Timeouts With Silent Continuation

An operation that times out, but code execution continues as if the result were available.

Pattern: timeout function returns `None` or a sentinel on expiry, but the caller does not
check the sentinel before using the result. `None` or the sentinel then propagates silently
into downstream processing.

Look for:
- `asyncio.wait_for` without a timeout handling branch
- `Promise.race` where the timeout branch returns a sentinel that downstream ignores
- Timeout wrappers that return zero-values indistinguishable from successful empty responses

---

## Step 5: Correctness — What to Look For

**The core question:** Does this code do what it claims to do, under all inputs?
Apply correctness review ONLY after completing steps 1-4.

**Patterns to detect:**

### Logic Errors

Code that produces incorrect results due to wrong conditions, wrong operators, or
wrong sequencing of operations.

- Conditions using assignment instead of comparison where the language permits
- Boolean logic errors: `and` instead of `or`, negated conditions, short-circuit errors
- Off-by-one in loop bounds: `range(n)` vs `range(n+1)`, `<` vs `<=` at boundaries
- Index arithmetic that doesn't account for zero-based vs one-based indexing

### Race Conditions

State shared between concurrent execution paths without synchronization.

- Global mutable state written by multiple goroutines/threads without locks
- Check-then-act patterns without atomic guarantee: existence check followed by create in concurrent context
- File or database operations where two processes can interleave between check and write
- Lazy initialization without `sync.Once` or equivalent atomic initialization guard

### Security Vulnerabilities

Code patterns that expose the system to attack.

- String interpolation or concatenation in SQL queries without parameterization (SQL injection)
- User-controlled input passed to `eval()`, `exec()`, or template engines without sanitization
- Secrets or credentials in source code, log statements, or error messages
- Missing authentication or authorization checks on sensitive operations
- Insecure deserialization of user-provided data

### Off-by-One Errors

Boundary conditions at array/list edges, string slices, pagination, and loop termination.

- List slicing that misses the last element: `items[:n]` when `items[n]` should be included
- Pagination that returns one page too few or one item too many
- String parsing that drops the first or last character

---

## Pattern Application Notes

These patterns are not a checklist to mechanically scan. Apply them with judgment:

**Severity escalation:** A single swallowed exception in an authentication path is more
severe than one in a logging path. Apply the Three Mother Rules to assess severity:
- Mother Rule 1 (articulate death): Does this code know how it fails?
- Mother Rule 2 (label assumptions): Does this name label what it assumes about inputs?
- Mother Rule 3 (errors easier to see): Does this abstraction hide or reveal failure?

**Context matters:** A swallowed exception in a cache-read function with documented semantics
("returns None on miss") is different from one in a write path that the caller assumes
always succeeds. Name the difference in your finding.

**Don't flag what you can't verify:** If you cannot see the full call tree, note the
limitation rather than producing a false PASS or false FAIL. Use "Unable to verify
[pattern] within this diff — callers not visible" and classify as Important.
