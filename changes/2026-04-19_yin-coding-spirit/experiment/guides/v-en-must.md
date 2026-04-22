# Yin-side Coding Guide (v-en-must)

## Axiom
These principles define the required shape of system structures.
Structures MUST NOT lie to future inheritors.

## SRP
A structure MUST have exactly one failure mode.
When removed, exactly one location MUST experience loss.
If no loss occurs, the structure MUST be deleted.
If multiple losses occur, the structure MUST be split.

## OCP
Every closed boundary MUST explicitly mark its future bets.
Unmarked closure assumptions MUST NOT exist.

## LSP
Any override that changes parent semantics MUST be explicitly marked.
Overrides MUST NOT silently modify inherited contracts.

## ISP
Every interface method MUST have a named real caller.
Methods without identifiable callers MUST be removed.

## DIP
Abstractions MUST make error-tracing easier.
Interfaces with exactly one implementation MUST be eliminated.

## Cohesion
When a module is deleted, all members MUST die with it.
Any rescuable member MUST be relocated immediately.

## Coupling
All dependencies MUST be explicit.
Implicit coupling MUST be made visible or removed.

## DRY
Duplicated code MUST be unified or explicitly marked as intentional divergence.
Each duplication MUST have a designated source of truth.

## Pattern
Before applying a pattern, the divergence point from its original problem
MUST be identified and documented as a failure boundary.
