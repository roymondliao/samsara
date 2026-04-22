# Yin-side Coding Spirit (v-en-is)

## Axiom
These principles describe what shape system structures ought to take.
The yin-side question is always the same one: under what conditions
will this shape lie to someone who inherits it — without them knowing?

## SRP — Death Responsibility
A structure is responsible for exactly one way of dying.
When it disappears, only one place feels the pain — that place
is the reason it exists. No pain anywhere means it shouldn't exist.
Pain in multiple places means it carries what isn't its own.

## OCP — The Marked Bet
A closed boundary is a bet on the future.
An unmarked closure-assumption is a fraud committed against
whoever inherits the code.

## LSP — Silent Breach
If substitution happens and the caller doesn't know its assumptions
were broken — that is the real violation. Every override is a silent
modification of the parent's contract.

## ISP — Ghost Promises
An interface method that cannot name its real caller is a ghost promise.
Ghost promises force implementers to be responsible for callers
that don't exist — in the end, nobody is truly responsible.

## DIP — The Soundproof Wall
Does this abstraction make error-tracing easier, or harder?
An abstraction that makes rot harder to see is not protecting
the design — it is protecting the rot.
An interface with exactly one implementation is a stage prop,
not an abstraction.

## Cohesion — The Right to Die Together
Delete the module. Does anything have to be rescued?
What must be rescued is evidence that cohesion failed.

## Coupling — Visibility Over Looseness
Explicit strong coupling is safe; implicit weak coupling is the trap.
Loose coupling is not the goal — making coupling visible is.

## DRY — Duplication Is a Lie Splitting
Duplicated code is not a line-count problem.
It is two places telling the same lie. Change one and forget the other,
and the lie splits — no one knows which version is true anymore.

## Pattern — A Named Bundle of Assumptions
Every pattern assumes your problem is the same as the one it was designed for.
Ask: where does this pattern's problem begin to diverge from mine?
That divergence point is where the pattern begins to lie.
