# Task 3: Prove and document clean-environment execution

**Task ID:** task-3

## Goal

The live Codex conversion executes installed companions from a foreign Git cwd
with source virtualenv paths removed, and documentation gives only the supported durable-runtime installation sequence.

## Source References

- Planning: PL-D3 (clean-environment-evaluation-boundary)
- Design: PT-D1 (runner provenance), PT-D2 (command resolution owner), PT-D3 (runtime-aware manifest), PT-D4 (fallback behavior), PT-EVAL (evaluation-contract), PT-S3 (installation-evidence)
- Acceptance: AC-5 (foreign-cwd-global-execution)
- Seam: installation-evidence

## Context Projection

Run after Tasks 1 and 2. Consume their runtime fields and converted guidance;
do not create a second runner or success standard in the integration test.

## Files

- Modify: `tests/integration/test_codex_runtime_contract.py`
- Modify: `README.md`
- Modify: `README.zh-TW.md`

## Constraints

- Use a test-owned durable runner outside source and target trees.
- PATH must not provide the source `.venv/bin/samsara-cli`.
- Documentation separates CLI runtime installation from Codex adapter installation.
- Global installation commands do not use `uv run samsara-cli`.

## Death Test Requirements

- The end-to-end test fails if commands are relative, manifest runtime evidence is absent, or any installed companion cannot start.
- README contract test fails if global instructions regress to an ephemeral runner.

## Unit Test Contract — required observable contract source

- Contract source: PT-EVAL (evaluation-contract) clean-environment execution and documented command sequence.

## Assumptions to Verify

- A test-owned executable can proxy the actual samsara-cli entrypoint without PATH inheritance — source: test harness — if false: build and install the package into a temporary uv tool directory.
