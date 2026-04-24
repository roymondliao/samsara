# Code Quality Reference — Yin-side Principles

> 陽面的 code quality 回答「這段 code 寫得好不好」。
> 陰面問的是「這個結構在什麼條件下會對繼承它的人說謊」。

---

## Purpose

The 9 principles in the agent definition (`samsara:code-quality-reviewer`) supply the
review spirit — the structural judgment standards that define WHAT to look for and WHY.
This reference provides the domain-specific foundation — what those principles look
like when violated in imperative/OOP code.

This reference is organized around **9 yin-side principles** — 5 SOLID reframings,
2 structural principles (Cohesion, Coupling), 1 reuse principle (DRY), and 1 pattern
principle — each expressed in spirit form (what the principle protects against), not
in rule form (what the code must do).

Each principle appears with:
- **Axiom** — the one-line spirit statement
- **Why it matters** — the spirit-level reasoning
- **Violation shapes (koans)** — imagistic descriptions of how the violation appears
  in imperative code. These are illustrative, not exhaustive — a violation that matches
  the principle's spirit but no specific koan is still a violation.
- **Judgment questions** — generative questions a reviewer asks the code
- **Outcome cross-reference** — which of the 8 outcome criteria surface when this
  principle is broken

This reference is **language-agnostic by design**. It describes structural truth,
not syntactic form. If you see a language-specific adapter appended to this
reference in the future, that adapter translates these principles to a language;
the principles themselves remain unchanged.

---

## Scope

**In scope:** The 9 principles below. All of them describe **code structure** — how
responsibilities are divided, how boundaries are drawn, how dependencies are
declared, how abstractions behave at their seams.

**Out of scope:**

- Silent rot (behavior drifting unreported)
- Dishonest naming (names that describe intent rather than actual behavior)
- Security vulnerabilities
- Performance characteristics
- Correctness of specific algorithms

These belong to `samsara:code-reviewer` (yin), not to this reference. If you
observe an out-of-scope issue, note it as a pointer to yin review rather than
scoring it here.

---

## Applicability

**Domain:** `code`

**Excluded principles:** none — all 9 principles apply to code-domain files.

The structured representation below is equivalent to the prose above and is
provided for machine-readable extraction. Both say the same thing: no principles
are excluded.

```yaml
domain: code
excluded_principles: []
```

When the reviewer reaches Step 3 and checks this section, it finds an empty
`excluded_principles` list. This means every principle in the Step 3 table is
applicable and must be reviewed. No principle receives an automatic UNKNOWN
verdict from this file.

---

## How to use this reference

When reviewing code:

1. For each principle, read the **judgment question**. Apply it to the code under
   review.
2. Compare what you see to the **violation shapes (koans)**. If the code matches a
   koan, the principle is violated.
3. Produce one of: `Pass`, `Concern` (with specific reference to which principle
   and where), or `UNKNOWN` (when the principle does not apply to this code — too
   short, wrong domain, context missing).
4. `UNKNOWN` is the honest answer **when the principle cannot be applied to
   this code** — the code is too short to exhibit the pattern, the domain does
   not fit, or the code is a different artifact (config, data, docs). It is
   NOT the answer for "I looked at the code but could not decide"; in that
   case, produce `Concern` with the note "insufficient context to verify X",
   so the ambiguity is visible to downstream reviewers. **Do not produce `Pass`
   by default** when the principle might apply but you cannot judge — `Pass`
   must be an affirmative judgment, not an absence of concern.

Every `Pass` must include at least one specific observation that demonstrates
active review. `Pass` without a concrete reference is indistinguishable from
rubber-stamping.

---

## S — Death Responsibility (死法責任)

### Axiom

A structure is responsible for exactly one way of dying.

### Why it matters

A structure exists not because of what it can do, but because of what would hurt
if it disappeared. If a structure vanishes and nothing feels pain, the structure
had no reason to exist. If a structure vanishes and several unrelated places feel
pain, the structure was carrying responsibilities that do not belong together —
it is several structures sharing a single name.

Responsibility is not the union of functions. Responsibility is **the single
failure you are willing to fully answer for**.

### Violation shapes (koans)

- **Ghost structure**: It exists, but when it disappears nothing feels pain. It
  decorates, but it guards nothing.
- **Three-faced structure**: When it disappears, three unrelated downstream things
  stop working. It is three structures crammed into one name.
- **Wordless structure**: Ask a maintainer, "If this disappears, who calls first
  to complain?" They cannot answer, or they name three different teams.

### Judgment questions

- If this structure is deleted tomorrow, which one place feels the loss?
- Can the author of this structure state, in one sentence, the single failure
  they are responsible for?
- If the answer names multiple unrelated concerns, should this be one structure
  or several?

### Outcome cross-reference

When violated, surfaces as:
- (C1 Readability) A module carrying multiple unrelated responsibilities
  cannot be understood in 30 seconds
- (C2 Maintainability) Changes require reasoning about multiple unrelated
  concerns simultaneously
- (C6 Clear Structure) Boundaries cannot justify "why here, not there"

---

## O — The Marked Bet (賭注標記)

### Axiom

A closed boundary is a bet on the future. The bet must be marked where it is
made.

### Why it matters

Every closure is a prediction about what will and will not change. Where the
prediction holds, the closure is protection: it prevents downstream chaos from
bleeding into a stable region. Where the prediction fails, the closure is a
sarcophagus: it entombs the old assumption and makes it expensive to extract.

A closure without its bet written down is not design — it is a trap for
inheritors. They will encounter the boundary, assume it is reasoned, and plan
around it. When the unstated assumption finally breaks, they will have no way to
tell whether this boundary was intentional or accidental.

### Violation shapes (koans)

- **Nameless bet**: A closed boundary exists, but no one can say what it is
  betting on.
- **Sarcophagus**: The boundary was drawn under an assumption that no longer
  holds, and the boundary is still guarding the ghost of the old assumption.
- **Tacit boundary**: The boundary's assumption lives only in the original
  author's head; every inheritor learns it by stepping on it.

### Judgment questions

- What does this boundary assume will not change?
- Is that assumption written somewhere an inheritor will find it?
- If the assumption breaks, what is the smallest change that revises the
  boundary — a rewrite, a new seam, or a deletion?

### Outcome cross-reference

When violated, surfaces as:
- (C2 Maintainability) Changes require archaeology to recover the original
  assumption
- (C3 Extensibility) Extensions that conflict with the unstated assumption fail
  silently or require invasive rewrites

---

## L — Silent Breach (靜默違約)

### Axiom

The real violation is when a substitute changes the meaning and the caller
doesn't know.

### Why it matters

The conventional reading of Liskov is "subtype can replace supertype." That is
the surface. The yin reading is: substitution is only true substitution when the
caller's assumptions survive intact. If the caller must learn about the subtype
to use it correctly, substitution leaked. If the caller does not need to learn,
substitution is true.

Between these two states lies the dangerous third: substitution happens, the
caller does not need to learn, **and their assumptions are silently broken
anyway**. This is not substitution failure detected at compile time. It is
contract breach at runtime, under conditions no test covered, discovered by
whoever is on call when the first wrong result reaches production.

### Violation shapes (koans)

- **Silent contract modification**: An override changes the return semantics; the
  caller does not know and begins accumulating wrong results.
- **False substitution**: A subtype throws, at a boundary condition, an exception
  the supertype never throws; callers without that catch crash.
- **Implicit dependency**: The caller depends on an implementation detail of the
  supertype; an override moves or redefines that detail; the caller breaks, and
  no contract declares whose fault it is.

### Judgment questions

- If this subtype replaces the supertype, do existing callers need to be told?
- If yes, where is that requirement declared — in a type, a docstring, or only
  in the subtype author's head?
- What does this override silently change that a type-checker cannot catch?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Wrong results appear far from the override site, with no
  declaration of origin
- (C2 Maintainability) Refactoring the supertype requires auditing every
  subtype's silent assumptions

---

## I — Ghost Promises (幽靈承諾)

### Axiom

A method you cannot name a real caller for is a ghost promise.

### Why it matters

An interface is not a list of capabilities. An interface is a public declaration
of which behaviors you accept accountability for. Every method on an interface
is a commitment to maintain that method's contract indefinitely, because
inheritors will trust it.

Methods invented for a "future caller" — a caller that might exist someday —
create a contradiction: the implementer is bound to maintain a guarantee for
someone who has never shown up, may never show up, and whose actual needs you
cannot verify. The interface inflates with phantom commitments. Each phantom
method increases the surface area of the contract without increasing the
protection offered.

### Violation shapes (koans)

- **Phantom caller**: The interface has a method; asked "who calls this?" the
  answer is "someone might need it later."
- **Inflated interface**: Twenty methods on one interface; implementers must
  maintain contracts for all twenty; only three have verifiable callers.
- **Name-level promise**: The interface declares `sort()`; the implementation
  performs `shuffle()`; the caller trusted the name.

### Judgment questions

- For each method on this interface, can you name at least one real caller that
  depends on it today?
- For each method without a real caller, what protection does keeping it on the
  interface provide?
- Would removing the phantom methods break any test, or only hypothetical future
  callers?

### Outcome cross-reference

When violated, surfaces as:
- (C3 Extensibility) Implementers must satisfy contracts that serve no current
  purpose
- (C1 Readability) Interface size exceeds the useful surface; readers must
  distinguish real contracts from phantom ones
- (C7 Elegant Logic) Extra structure exists without extra protection

---

## D — The Soundproof Wall (隔音牆)

### Axiom

An abstraction that makes errors harder to see is protecting the rot, not the
design.

### Note on reframing

The canonical Dependency Inversion Principle (SOLID's D) is about dependency
direction: high-level modules should not depend on low-level modules; both
should depend on abstractions. The yin version below **deliberately reframes**
D from dependency-direction to abstraction-visibility. The original DIP concern
is valid but has been absorbed into the structural reviewer's general toolkit
(a direct dependency on a concrete database driver, for example, surfaces
under Coupling as an implicit dependency on something that should have been
explicit). What yin-D focuses on instead is a subtler failure the canonical
framing does not address: the abstraction as a signal dampener.

### Why it matters

Abstractions buy decoupling at the cost of visibility. The decoupling is the
visible benefit; the visibility loss is the invisible cost. When the lower layer
silently changes behavior, the abstraction will speak for it — translating, or
swallowing, or rephrasing — and the upper layers will hear only the
abstraction's voice. The rot continues, soundproofed.

A well-placed abstraction makes the underlying system's failures **easier** to
trace, not harder. If the only effect of an abstraction is to hide what the
lower layer is saying, the abstraction is not serving the design. It is serving
whoever wants the lower layer's problems to stay invisible.

A related pattern: interfaces with exactly one implementation. These are stage
props. They offer the appearance of decoupling without any of the substance. The
single implementation is always known to callers; the interface exists only to
give the design a "clean" silhouette.

### Violation shapes (koans)

- **Soundproof wall**: The lower layer emits a warning; the abstraction swallows
  it; the caller hears only "success."
- **Single-implementation interface**: An interface with exactly one
  implementing class; the interface serves no decoupling need.
  (This pattern also appears under the I lens as a phantom promise — a method
  surface with no caller who has real implementation choice. Both framings are
  valid; use the D lens when the concern is abstraction-as-soundproofing, use
  the I lens when the concern is methods without real callers.)
- **Translation lie**: The lower layer throws exception A; the abstraction
  translates it to exception B; the caller never learns what actually broke.

### Judgment questions

- Does this abstraction make failures in the lower layer easier to trace, or
  harder?
- If this interface has one implementation, what decoupling does the interface
  provide that a direct module dependency would not?
- Where does this abstraction translate or swallow signals from the layer
  beneath it? Are those translations reversible?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Failures originate in a layer the caller cannot see
- (C6 Clear Structure) Boundaries exist without the responsibility separation
  that would justify them

---

## Cohesion — The Right to Die Together (共同死亡的權利)

### Axiom

Cohesion is not about relatedness. It is about the right to die together.

### Why it matters

A module is truly cohesive when every element inside it shares a single
death-reason: if the module disappears, every element should disappear with it,
no orphans. An element that would have to be rescued to live elsewhere does not
belong in this module — it is a tenant, not a citizen. It just has not found its
own home yet.

The mainstream reading of cohesion asks "are these things related?" The yin
reading asks "do these things share a fate?" Relatedness is a weak criterion —
any two things can be called related if you squint. Shared fate is binary: when
the structure dies, do they die with it, or do they need to be saved?

### Violation shapes (koans)

- **Orphan module**: Delete the module. One function must be rescued to
  elsewhere. That function never belonged here.
- **Heterogeneous grouping**: One module contains database access, UI rendering,
  and business rules; three unrelated downstream systems depend on its survival.
- **False relatedness**: Elements in the module appear related by naming, but
  they share no death-reason; the truth is they were gathered by alphabetic
  ordering.

### Judgment questions

- If this module disappears, does every element disappear with it? Or does
  something need to be saved?
- What element would you rescue? Where does it actually belong?
- Do the elements here share one death-reason, or are several different
  failures tangled together?

### Outcome cross-reference

When violated, surfaces as:
- (C6 Clear Structure) Module boundaries do not correspond to responsibility
  boundaries
- (C3 Extensibility) Extensions that touch one concern cascade into modifying
  unrelated concerns in the same module

---

## Coupling — Visibility Over Looseness (可見性優先於鬆散)

### Axiom

The danger of coupling is not the dependency. The danger is not knowing you
depend.

### Why it matters

Explicit strong coupling is safe. It announces itself: A imports B, calls B's
method, fails loudly when B is broken. Responsibility is clear; the relationship
is declared.

Implicit coupling is the trap. Two modules look independent — no imports, no
direct calls, no shared types. But one silently reads global state the other
silently writes, or one depends on an ordering guarantee the other silently
provides. When the hidden party changes its behavior, the dependent party
produces wrong results without any declared relationship to investigate.

Loose coupling is not the goal. **Visible** coupling is. A visible strong
coupling can be reasoned about, tested, refactored. An invisible loose coupling
can corrupt silently for years.

### Violation shapes (koans)

- **Invisible dependency**: A and B look independent. A's internal assumption
  depends on B's internal state. No import, no call, no log.
- **Tacit shared state**: Two modules read and write the same global mutable
  state, but no one declared who may write and who may only read.
- **Name-level lock-in**: A depends on B only because of B's naming convention;
  renaming B breaks A, but no import shows the coupling.

### Judgment questions

- Can you draw every dependency this structure has on another structure?
- Are there dependencies that are not import-visible — shared state, ordering,
  naming conventions, filesystem layout?
- If the other party changes silently, does this structure notice, or keep
  producing wrong results?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Failures cannot be traced back to their true source; the
  dependency path is invisible
- (C2 Maintainability) Refactoring either side risks silent breakage on the
  other

---

## DRY — Duplication Is a Lie Splitting (重複是謊言的分裂)

### Axiom

Duplicated code is not a line-count problem. It is two places telling the same
lie.

### Why it matters

The conventional reading of DRY is "don't repeat yourself — it wastes lines."
That is the surface. The yin reading is: each copy of a duplicated logic is
making an independent truth claim. When the truth changes and one copy is
updated, the lie **splits**: the two copies now claim different truths, and no
reader can tell which is authoritative.

Duplication is not a formatting flaw. It is **source-of-truth theft**. Every
copy dilutes the authority of every other copy. When the divergence is
discovered months later — usually because of a bug where one site was patched
and the other was not — there is no way to recover the original shared intent.
The history of the duplication is lost.

### Violation shapes (koans)

- **Split lie**: The same validation logic written in three places; one is
  fixed, two keep telling the old truth.
- **False uniqueness**: A helper function exists, but three callers have inlined
  copies of its logic; the helper is a phantom source of truth.
- **Parallel evolution**: Two functions that look unrelated perform the same
  operation in variant forms; when the requirement changes, both must change in
  lockstep, or they silently diverge.

### Judgment questions

- Are there two places in this change that make the same truth claim about the
  same fact?
- If one of them is updated and the other is not, which version will the next
  reader treat as authoritative?
- Where is the single source of truth for this fact? If you cannot name one,
  the fact is split.

### Outcome cross-reference

When violated, surfaces as:
- (C5 Reuse) Shared logic lacks a single authoritative location; callers
  cannot know which copy is the source of truth
- (C8 No Redundancy) Multiple sites encode the same fact; divergence is a
  matter of when, not if
- (C2 Maintainability) Every change that touches the underlying fact requires
  finding and updating every copy

---

## Pattern — A Named Bundle of Assumptions (被命名的假設集合)

### Axiom

Every pattern assumes your problem is the same as the one it was designed for.

### Why it matters

A design pattern is not a solution template. A design pattern is a **set of
assumptions about the problem**, bundled under a name. Factory assumes you need
to vary construction logic across types. Observer assumes you need many
listeners reacting to one source of events. Singleton assumes you need exactly
one instance across the program's lifetime.

Using a pattern without acknowledging which of its assumptions apply to your
situation — and which do not — inherits all of the pattern's machinery without
inheriting the justification. The machinery is then a liability: it constrains
future changes to match the pattern's shape, even when the pattern's original
reason is absent.

The question is never "is this pattern suitable?" The question is: **where does
this pattern's original problem differ from mine?** That difference is where
the pattern will begin to lie.

### Violation shapes (koans)

- **Naked pattern**: Factory / Observer / Singleton is used, with no note on
  which problem it is solving here, or where it diverges from its original
  purpose.
- **Stale assumption**: The pattern's original problem no longer exists in
  this codebase, but the pattern's complexity remains — the machinery now
  constrains changes the pattern was never meant to constrain.
- **Naming cargo cult**: The name of the pattern is adopted; the pattern's
  constraints are not. The overhead is paid; the protection is not received.

### Judgment questions

- What pattern is being used here, and what original problem was it designed
  for?
- Where does the original problem differ from the current problem?
- If the pattern's assumptions do not match here, what is being kept — the
  machinery, the name, or the actual protection?

### Outcome cross-reference

When violated, surfaces as:
- (C1 Readability) Pattern's machinery creates complexity readers cannot map
  back to a problem
- (C3 Extensibility) Pattern's constraints block extensions that the original
  problem would have permitted
- (C7 Elegant Logic) Structure exists without the justification that would
  make it elegant

---

## Turning principles into review output

For each diff under review:

1. For each of the 9 principles, ask the judgment question. Compare to the
   violation shapes.
2. For each principle, produce one of:
   - **`Pass`** — the principle is affirmatively satisfied; note one specific
     observation as evidence.
   - **`Concern`** — the principle is violated; cite which koan matches, and
     which file/line reveals it.
   - **`UNKNOWN`** — the principle does not apply to this code (too short,
     wrong domain, context missing). Explicitly state why.
3. Aggregate into an overall verdict:
   - All principles `Pass` or `UNKNOWN` with reasoning → **PASS**
   - Any `Concern` at severity `Critical` → **FAIL**
   - Any `Concern` at severity `Important` → **PASS_WITH_CONCERNS**
   - Severity is judged by:
     - **Critical**: Violation would cause silent wrong results or prevent a
       future maintainer from understanding the code at all.
     - **Important**: Violation increases maintenance cost but does not cause
       silent failure.
     - **Suggestion**: Stylistic refinement that does not block review.

A review output without any specific observations — even on `Pass` — is
indistinguishable from rubber-stamping. Every verdict must be grounded in the
code.

---

## Cross-reference: 9 principles → 8 outcome criteria

The 8 outcome criteria describe **what good code looks like from the outside**.
The 9 principles describe **what makes code that way from the inside**. A
violation of any principle surfaces as one or more of these outcomes becoming
worse.

| Principle | Primary outcomes affected |
|-----------|--------------------------|
| S — Death Responsibility | C1 Readability, C2 Maintainability, C6 Clear Structure |
| O — The Marked Bet | C2 Maintainability, C3 Extensibility |
| L — Silent Breach | C4 Debuggability, C2 Maintainability |
| I — Ghost Promises | C3 Extensibility, C1 Readability, C7 Elegant Logic |
| D — The Soundproof Wall | C4 Debuggability, C6 Clear Structure |
| Cohesion | C6 Clear Structure, C3 Extensibility |
| Coupling | C4 Debuggability, C2 Maintainability |
| DRY | C5 Reuse, C8 No Redundancy, C2 Maintainability |
| Pattern | C1 Readability, C3 Extensibility, C7 Elegant Logic |

The 8 outcomes (for reference):

- **C1 Readability** — A reader understands the intent within 30 seconds
- **C2 Maintainability** — A change three months from now does not require
  stepping on landmines
- **C3 Extensibility** — A similar future requirement can be inserted without
  modifying existing code
- **C4 Debuggability** — Error signals point toward their actual source
- **C5 Reuse** — Shared logic has exactly one authoritative location
- **C6 Clear Structure** — Every boundary can justify "why here, not there"
- **C7 Elegant Logic** — No extra abstraction, no temporary variables, no
  unused parameters
- **C8 No Redundancy** — Two places never state the same fact

A `Concern` can cite both a principle (the yin inside) and an outcome (the
visible consequence). Doing so makes the concern actionable to both the agent
and the human who reads the review.

---

## Closing

This reference is philosophy, not style. A code review that scores highly on
the 9 principles may still be bad code — the principles cover structural
truth-telling, not correctness, not performance, not security. They are
**necessary, not sufficient**, for good code.

An agent using this reference for review should treat each principle as a lens,
not a checklist. Lenses reveal; checklists obscure by selection bias. The
difference is the difference between noticing that a structure cannot state its
death-reason (lens) and verifying that a `@dataclass` decorator is present
(checklist). The first is review; the second is lint.

If this reference ever starts to feel like a checklist, it has drifted. Return
it to its axioms.
