# Plan: codex-global-companion-runtime

Planning judgment owner. Upstream design authority remains in `pre-thinking.md`.

## Source Contract

- Research: `1-kickoff.md`, `problem-autopsy.md`
- Design authority: `pre-thinking.md`
- Commitment: Proceed
- Accepted gaps: none
- Evaluation: PT-EVAL (evaluation-contract)

## Planning Decisions

### PL-D1: durable-runner-install-boundary

Source refs:
- PT-D1 (runner provenance)
- PT-D2 (command resolution owner)
- PT-D3 (runtime-aware manifest)
- PT-S1 (runtime-provenance)
- PT-S2 (command-materialization)
- PT-S3 (installation-evidence)
- `samsara_cli/installer/install.py`

- Decision: One task owns runner discovery, global provenance rejection, pre-install smoke checks, absolute command materialization, and schema-1-to-schema-2 manifest migration.
- Rationale: Splitting these steps would allow one writer to declare a runtime another writer never proved.
- Consequence: No success manifest can be written without one resolved runtime record and executable companion set.
- If wrong: Global install can again copy valid files whose commands cannot start after the installer exits.

### PL-D2: companion-portability-boundary

Source refs:
- PT-D4 (fallback behavior)
- PT-D5 (syntax compatibility)
- PT-S2 (command-materialization)
- `samsara_cli/config/platform/codex.yaml`
- `pyproject.toml`

- Decision: One task owns target-specific no-fallback guidance, companion syntax-floor configuration, grammar guards, and converter projections.
- Rationale: Runtime guidance and distributed source compatibility are two defenses for the same companion invocation boundary.
- Consequence: A missing runner produces CANNOT VALIDATE instead of an inferred interpreter command, and installed scripts remain parseable at the declared floor.
- If wrong: Weak models can bypass the runner or encounter a misleading syntax failure before the real missing-runtime signal.

### PL-D3: clean-environment-evaluation-boundary

Source refs:
- PT-EVAL (evaluation-contract)
- PT-D1 (runner provenance)
- PT-D2 (command resolution owner)
- PT-D3 (runtime-aware manifest)
- PT-D4 (fallback behavior)

- Decision: A final task integrates the live conversion, durable fake runner, foreign cwd, clean PATH, documentation, and install instructions after the two implementation tasks finish.
- Rationale: This is the only task that can prove the complete runtime edge rather than isolated file shapes.
- Consequence: README commands and the Primary evaluator describe the same supported installation path.
- If wrong: Unit tests can pass while the shipped global workflow remains unusable.

## File Allocation

- `samsara_cli/installer/install.py` — owner: task-1 — source refs: PL-D1 (durable-runner-install-boundary), PT-D1 (runner provenance)
- `samsara_cli/main.py` — owner: task-1 — source refs: PL-D1 (durable-runner-install-boundary), PT-D2 (command resolution owner)
- `tests/test_installer/test_owned_manifest.py` — owner: task-1 — source refs: PL-D1 (durable-runner-install-boundary)
- `tests/test_installer/test_install.py` — owner: task-1 — source refs: PL-D1 (durable-runner-install-boundary)
- `tests/test_cli/test_main.py` — owner: task-1 — source refs: PL-D1 (durable-runner-install-boundary)
- `samsara_cli/converter/engine.py` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary), PT-D4 (fallback behavior)
- `samsara_cli/config/platform/codex.yaml` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary), PT-D4 (fallback behavior)
- `pyproject.toml` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary), PT-D5 (syntax compatibility)
- `skills/codebase-map/scripts/validate_codebase_map.py` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary), PT-D5 (syntax compatibility)
- `tests/test_converter/test_engine.py` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary)
- `tests/test_skills/test_codebase_map_validator.py` — owner: task-2 — source refs: PL-D2 (companion-portability-boundary)
- `tests/integration/test_codex_runtime_contract.py` — owner: task-3 — source refs: PL-D3 (clean-environment-evaluation-boundary), PT-EVAL (evaluation-contract)
- `README.md` — owner: task-3 — source refs: PL-D3 (clean-environment-evaluation-boundary)
- `README.zh-TW.md` — owner: task-3 — source refs: PL-D3 (clean-environment-evaluation-boundary)

## Acceptance Mapping

- AC-1 (ephemeral-runner-rejected) → task-1 — planning ref: PL-D1 (durable-runner-install-boundary)
- AC-2 (runtime-manifest-migrates) → task-1 — planning ref: PL-D1 (durable-runner-install-boundary)
- AC-3 (missing-runner-no-fallback) → task-2 — planning ref: PL-D2 (companion-portability-boundary)
- AC-4 (companion-syntax-floor) → task-2 — planning ref: PL-D2 (companion-portability-boundary)
- AC-5 (foreign-cwd-global-execution) → task-3 — planning ref: PL-D3 (clean-environment-evaluation-boundary)

## Task Decomposition

- `task-1` — boundary: runtime provenance, absolute materialization, smoke checking, and manifest migration — refs: PL-D1 (durable-runner-install-boundary), PT-D1 (runner provenance)
- `task-2` — boundary: converted no-fallback guidance and distributed companion syntax floor — refs: PL-D2 (companion-portability-boundary), PT-D4 (fallback behavior)
- `task-3` — boundary: end-to-end clean-environment evaluation and supported installation docs — refs: PL-D3 (clean-environment-evaluation-boundary), PT-EVAL (evaluation-contract)

## Planning Assumptions

- `uv tool install` produces a stable executable outside the Samsara source tree — evidence: `uv tool dir --bin` — consequence if false: global install rejects it and reports the required durable path.
- Every distributed companion supports argparse `--help` without mutating workflow state — evidence: companion entrypoints — consequence if false: smoke checking uses syntax/dependency validation without invoking its main action.

## File Allocation Consistency

- PT-D1 (runner provenance) — matches — task-1 owns all provenance and preflight paths.
- PT-D2 (command resolution owner) — matches — converter emits scope-agnostic text; task-1 materializes it during install.
- PT-D3 (runtime-aware manifest) — matches — task-1 is the manifest's sole writer.
- PT-D4 (fallback behavior) — matches — task-2 owns the target instruction projection.
- PT-D5 (syntax compatibility) — matches — task-2 owns Ruff syntax floor and grammar tests.
