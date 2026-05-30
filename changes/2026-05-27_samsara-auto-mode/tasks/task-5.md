# Task 5: Document auto mode and run validation

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

This task documents the new mode for users and runs the required validation. It must keep the first-cut scope clear: session ask is supported; `samsara_config.yaml` is not.

## Files

- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `changes/2026-05-27_samsara-auto-mode/overview.md`
- Test: `tests/test_auto_mode`
- Test: `tests/test_converter/test_agent.py`
- Test: `tests/test_converter/test_agent_death.py`
- Test: `tests/integration/test_pipeline.py`
- Test: `tests/integration/test_format_validation.py`

## Death Test Requirements

- Test: documentation must not claim `samsara_config.yaml` support for the first cut.
- Test: documentation must not claim auto mode can fall back to human-in-the-loop after start.
- Test: final validation must include the primary evaluator and converter coverage.

## Implementation Steps

- [ ] Step 1: Write or extend documentation tests if existing README validation can cover the claims.
- [ ] Step 2: Run documentation-related tests with `source .venv/bin/activate` and `uv run pytest tests/test_release/test_readme_release_docs.py` if applicable.
- [ ] Step 3: Update `README.md` and `README.zh-TW.md` with concise auto-mode behavior.
- [ ] Step 4: Run the primary evaluator and targeted tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode tests/test_converter/test_agent.py tests/test_converter/test_agent_death.py tests/integration/test_pipeline.py tests/integration/test_format_validation.py`.
- [ ] Step 5: Run full pre-commit with `source .venv/bin/activate` and `uv run pre-commit run --all-files`.
- [ ] Step 6: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-5-scar.yaml`.
- [ ] Step 7: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: docs describe future config support as if implemented.
- Potential shortcut: validation skips integration tests because the feature is instruction-level.
- Assumption to verify: README test coverage is sufficient for user-facing behavior claims.

## Acceptance Criteria

- Covers: "Degradation - persistent config support is requested before session mode works"
- Covers: "Success - full auto workflow contract exists"
