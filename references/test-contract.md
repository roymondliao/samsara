# Test Contract Reference — Contract-Bound Unit Tests

> 陽面問「這個測試有沒有過」。
> 陰面問的是「這個測試在行為壞掉時會不會紅；它會不會在沒人受傷時誤報紅」。

---

## Applicability

**Domain:** `code` and any artifact with a stable, observable contract — public
API, CLI output, generated file shape, schema, documented protocol surface.

**Applies to:** Unit tests written under the Samsara implement workflow. Samsara
already requires death tests before unit tests; this reference defines what makes
the *unit* test healthy once the death test has pinned the failure mode.

**Companion, not replacement:** Death tests pin a known silent-failure mode. Unit
tests assert the positive contract. The rules here govern unit tests. The one
section that distinguishes the two — and protects death tests from being softened
— is deliberate and load-bearing; see "Unit tests are not death tests".

---

## Purpose

A unit test exists to make one promise: *if the behavior the contract names ever
changes, this test goes red; if nothing the user cares about changed, this test
stays green.* A test that breaks under a harmless rename is over-fit. A test that
stays green when the behavior actually broke is silent-green. Both are failures.
This reference gives the gate that rejects both, and the permitted-with-conditions
patterns (snapshots, spies, minimum-contract assertions) so the fix is never
"test less".

A unit test must assert at least one of: observable behavior, public API or
schema, user-visible output, documented artifact shape, a stable boundary
interaction, or a bug/death-case contract. If it asserts none of these, it
asserts an implementation detail.

---

## The Contract Gate

Before keeping any assertion, answer two questions about it. They are the whole
gate.

1. **The behavior-preserving refactor question.** If I refactor the
   implementation without changing any behavior the contract names — rename a
   private helper, reorder independent statements, swap a list comprehension for
   a loop — does this assertion still pass? It MUST. If a behavior-preserving
   refactor would turn it red, the assertion is pinned to *how* the code is
   written, not *what* it promises. That is the over-fit pole.

2. **The behavior-actually-broke question.** If the behavior the contract names
   actually broke — the function returns the wrong value, the file is written to
   the wrong place, the API drops a field — does this assertion go red? It MUST.
   If the behavior actually broke and this assertion still passed, it is the
   silent-green pole: a test that could never go red.

An assertion that survives a behavior-preserving refactor AND fails when behavior
actually broke is contract-bound. Keep it. Anything else is one of the two poles
below.

---

## Brittleness Filter (the over-fit pole)

A brittle test fails when nothing a user cares about changed. It is coupled to an
implementation detail: an exact private method name, a call count that the
contract never promised, an incidental ordering, an exact whitespace or log
string that no one reads as output, an internal data structure's exact shape.

Detection: ask the behavior-preserving refactor question. If you can name a
refactor that preserves behavior yet reddens the test, it is over-fit. The smell
is a test that fails the moment you touch the code even though the feature still
works.

Do NOT "fix" brittleness by deleting the assertion. Fix it by re-pointing the
assertion at the contract — assert the returned value, the written file's
documented shape, the user-visible output — and removing only the
implementation-detail coupling.

---

## Silent-Green Guard (the tautology pole)

A silent-green (tautological / vague) test stays green no matter what the code
does. It can never go red. Classic shapes:

- asserting only that a result is truthy / `is not None` / "not null" when the
  contract promises a specific value;
- asserting `len(result) >= 0`, which is always true;
- mocking the unit under test itself, so the assertion checks the mock;
- a try/except that swallows the failure and asserts nothing;
- a vague test whose only claim is "it ran without raising".

Detection: ask the behavior-actually-broke question, or mutate the implementation
on purpose (return a wrong value, drop a field) and confirm the test reddens. If
a plausible behavior break leaves the test green, it is silent-green.

Do NOT accept a silent-green test because "it's better than nothing". A test that
cannot fail is worse than nothing: it spends review attention and reports safety
it does not provide.

---

## The fix for both poles is the same shape

The fix for a brittle test is NOT "assert less", and the fix for a silent-green
test is NOT "assert more". Both are fixed by the same move: **assert the contract
precisely, and assert nothing else.** Over-fit means you asserted things outside
the contract; remove those. Silent-green means you asserted nothing inside the
contract; add the precise contract claim. "Assert less" alone slides a brittle
test toward silent-green; the target is the precise contract, not a quieter test.

---

## Snapshot and Golden Tests — normalize, then snapshot

Snapshots and golden files are NOT banned. They are the honest tool for a wide
contract: full CLI output, a generated config file, a rendered template. They
become brittle only when they capture volatile fields the contract never
promised.

Rule: **normalize volatile fields before snapshotting.** Replace absolute paths,
port numbers, version strings, dates/timestamps, and random ids with stable
placeholders, then snapshot the normalized form. The snapshot then asserts the
contract (the stable structure and content) and survives a behavior-preserving
run on another machine, another day, another port.

Worked example (normalize-then-snapshot):

```python
import re

def normalize(output: str) -> str:
    # Replace volatile fields the contract does not promise, THEN snapshot.
    output = re.sub(r"/Users/[^/\s]+/", "/Users/<user>/", output)      # path
    output = re.sub(r":\d{4,5}\b", ":<port>", output)                  # port
    output = re.sub(r"\b\d+\.\d+\.\d+\b", "<version>", output)         # version
    output = re.sub(r"\d{4}-\d{2}-\d{2}T[\d:.+Z-]+", "<date>", output)  # date
    output = re.sub(r"\b[0-9a-f]{8,}\b", "<random-id>", output)        # random-id
    return output

def test_cli_report_matches_golden(cli, snapshot):
    result = cli.run(["report"])
    # Snapshot the NORMALIZED contract surface, not the raw volatile output.
    assert normalize(result.stdout) == snapshot
```

If you cannot normalize a field, it is either part of the contract (assert it
explicitly) or noise that does not belong in the snapshot at all.

---

## Boundary Spy Exception — when the interaction IS the feature

Mocks and spies are not banned either. The anti-mock instinct targets mocking the
unit under test. But sometimes the *interaction at a boundary* is itself the
observable feature: "on a 429 the client retries with backoff", "the migration
runs inside a single transaction", "the cache is read before the network is
touched". There, the call to the boundary is the contract, and a spy is the only
honest way to observe it.

Use a boundary-spy only where the interaction itself is the observable feature,
and assert the contract of the interaction (that it happened, with the arguments
the contract names), not an incidental call count the contract never promised.

Worked example (boundary-spy):

```python
def test_retries_once_on_rate_limit(spy_transport):
    # The retry-on-429 interaction IS the feature, so spying the boundary is
    # the contract — not an implementation detail.
    spy_transport.queue([Response(429), Response(200)])
    client = Client(transport=spy_transport)

    client.get("/things")

    # Assert the interaction contract: a retry happened. Do not pin an exact
    # total-call count the contract never promised.
    assert spy_transport.calls >= 2
    assert spy_transport.last_request.path == "/things"
```

---

## Minimum-Contract Workflow Assertions — many legal paths

A multi-step workflow (an agent run, a wizard, a navigation flow) usually has
several legal paths to the same correct outcome. Pinning one exact path is
over-fit: a behavior-preserving change to the path reddens the test. Instead
assert the **minimum contract** the outcome requires — "at least one click
happened", ">= 2 snapshots were produced", "the final state contains the created
record" — which passes for every legal path and fails only when the outcome is
actually wrong. Never assert a single hard-coded path through a multi-path
workflow.

Worked example (minimum-contract, multi-path):

```python
def test_checkout_flow_completes(agent_run):
    steps = agent_run("buy the blue widget")

    # Minimum contract: the outcome's required facts hold on ANY legal path.
    # No single hard-coded step sequence — multiple valid paths are allowed.
    assert any(s.kind == "click" for s in steps)        # at least one click
    assert sum(s.kind == "snapshot" for s in steps) >= 2
    assert agent_run.final_state.order is not None       # the real outcome
```

---

## Unit tests are not death tests

The anti-over-fit rule above applies to **unit tests, not death tests.** A death
test exists to pin one specific silent-failure mode; that failure mode IS its
contract. A death test MAY (and should) assert the exact failure mode — the exact
error, the exact dropped field, the exact wrong path — because pinning the exact
silent-failure mode is precisely the value it provides. Death tests are an
explicit exception to the "don't pin exact strings" guidance.

Do NOT soften a death test in the name of anti-brittleness. If you find yourself
loosening a death test's exact assertion to make it "less brittle", you are
weakening the one test that was doing its job. Apply the brittleness filter to
unit tests; leave the death test pinning its failure mode.

---

## DAMP over DRY in tests

Prefer DAMP (Descriptive And Meaningful Phrases) over DRY in test bodies. A test
should read top to bottom and tell you the contract it asserts without chasing
shared fixtures and helper indirection. Some duplication across tests is healthy
when it keeps each test's contract legible at the point of assertion. Extract a
helper only when it names a *concept* (like `normalize` above), not merely to
remove repeated lines, because over-DRYed tests hide which contract each case
actually checks.

---

## Writing assertions that can fail in the right direction

The Contract Gate above asks whether an assertion goes red when behavior actually
broke. That question has a sharper form that the build of this very feature proved
necessary six times over: **an assertion is only as strong as its weakest clause,
and it must be able to fail in the direction the contract cares about.** An
assertion that merely proves a topic is *mentioned* — rather than *asserted in the
right direction* — is silent-green wearing a disguise: it reads like a real check
and passes review, but the behavior it claims to guard can rot underneath it
without ever turning the test red.

These five sub-rules are concrete instances of the silent-green pole. They are
written generally — they apply to any contract-bound assertion — but the worked
examples come from concept-token evaluators (a tuple of alternative tokens joined
by `any()`), because that is where each one bit hardest.

1. **Weakest-token-in-an-OR floor.** When an assertion is a disjunction — a tuple
   of alternative tokens joined by `any()`, or several `or`-ed conditions — the
   *loosest* member sets the floor. A single bare "assert less" / "fix the test" /
   "contract gate" token alongside strict directional siblings silently nullifies
   those strict siblings: the disjunction passes whenever the weakest clause does,
   so the strict ones never get a chance to fail. The assertion is only as strong
   as its weakest token. Cure: delete the loose member, or tighten every member to
   carry the same strictness, so no weakest clause sets a low floor.

2. **Presence-not-polarity.** A token can match a concept's keyword while saying
   nothing about its DIRECTION. A document that ENDORSES the wrong practice then
   passes identically to one that REJECTS it — the assertion proves the keyword is
   present, not that the contract's polarity holds.
   A presence-not-polarity token must reject the wrong direction, not just spot the keyword.
   Cure: a hostile **wrong-direction
   decoy** — a fixture that uses the REAL phrase in the WRONG direction (e.g.
   "always fix the test to make it pass", endorsing the bug) — and assert the
   concept is reported MISSING. If the decoy is reported covered, the token matches
   the keyword and not its direction; bind the keyword to its polarity.

3. **Green-by-construction.** A token keyed on a common word ("date", "test",
   "contract", "path") matches almost any prose and can never go red.
   A green-by-construction token can never go red, so it must be tightened.
   It reports its
   concept covered even on text that says nothing about the protocol. Cure: a
   hostile **unrelated-prose decoy** that sprinkles in exactly those common words
   and asserts ZERO concepts covered (every concept reported missing). Any concept
   covered on the decoy keys on a word, not the rule, and must be tightened.

4. **Order-by-label.** An ORDERING claim ("X must come before Y") asserted with a
   label-presence token is not an order check at all: it passes as long as both
   labels appear, in any order. Reorder the steps and the test stays green. Cure:
   read the position STRUCTURALLY and compare indices — `index_of(X) < index_of(Y)`
   — and add a reversed-order fixture that goes red. A structural position
   comparison is the only assertion that actually fails when the order breaks.

5. **Boundary bleed.** A proximity regex that binds two words "near each other"
   needs a stop class, and a loose one leaks. `[^.]` stops only at a literal period,
   so a far-away word leaks across newlines, list markers, and block boundaries —
   binding clauses that were never meant to relate, and the assertion silently
   matches prose it should reject. Cure: bound the gap to a tight clause — stop at
   `.?!>` and the newline — so the two words must belong to the same clause/line.

Each cure is a deepening of the behavior-actually-broke question: do not ask only
"does this assertion mention the contract", ask "can this assertion go red in the
exact direction the contract cares about, and have I built the hostile fixture that
proves it does". These rules apply to the tokens that check this very document —
see the self-exemplar note.

## Self-exemplar note

Any evaluator that checks an instruction surface for these concepts must itself
obey this protocol: assert the intent-bearing concept that survives an honest
rewrite, never an exact heading string or whole sentence. An evaluator that
reddens when a heading is renamed while the concept is preserved is itself
over-fit and refutes the protocol it is checking. The canonical concept tokens
live in one shared source so the checks across tasks cannot drift.
