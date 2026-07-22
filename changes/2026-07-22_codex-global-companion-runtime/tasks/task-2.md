# Task 2: Make companion guidance and syntax portable

**Task ID:** task-2

## Goal

Converted Codex instructions prohibit inferred interpreter fallback and every
distributed Python companion parses at the declared Python 3.11 syntax floor.

## Source References

- Planning: PL-D2 (companion-portability-boundary)
- Design: PT-D4 (fallback behavior), PT-D5 (syntax compatibility), PT-S2 (command-materialization)
- Acceptance: AC-3 (missing-runner-no-fallback), AC-4 (companion-syntax-floor)
- Seam: command-materialization

## Context Projection

Read the complete Overview and preserve source skill authority: the extra rule
is a Codex target runtime projection, not a new workflow-stage procedure.

## Files

- Modify: `samsara_cli/converter/engine.py`
- Modify: `samsara_cli/config/platform/codex.yaml`
- Modify: `pyproject.toml`
- Modify: `skills/codebase-map/scripts/validate_codebase_map.py`
- Modify: `tests/test_converter/test_engine.py`
- Modify: `tests/test_skills/test_codebase_map_validator.py`

## Constraints

- The converter keeps a scope-agnostic runner token for Installer to resolve.
- Missing runner is CANNOT VALIDATE; never authorize Python, python3, uv, or another inferred runtime.
- Python 3.11 is a syntax floor only; dependency execution remains runner-owned.
- Tests assert behavior and parseability, not prose layout.

## Death Test Requirements

- Converted output containing a run-companion command also contains the no-fallback contract.
- Every distributed companion fails the test if Python 3.14-only syntax returns.

## Unit Test Contract — required observable contract source

- Contract source: Converted Codex instruction semantics and Python grammar parsing of distributed companion sources.

## Assumptions to Verify

- Ruff per-file target versions apply to formatter output — source: Ruff configuration behavior — if false: use exception tuple constants that remain cross-version.
