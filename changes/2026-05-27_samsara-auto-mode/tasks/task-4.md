# Task 4: Add primary evaluator and converter coverage

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

The primary evaluator is full autonomous workflow completion in auto mode. In the first implementation this is represented by fixture-driven source inspection: the evaluator verifies that every workflow stage has the auto gatekeeper path and append-only decision-file requirement needed to complete without human intervention.

## Files

- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol.py`
- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol_death.py`
- Modify: `tests/integration/test_pipeline.py`
- Modify: `tests/integration/test_format_validation.py`
- Modify: `tests/integration/test_smoke_codex.py`
- Modify: `tests/integration/test_smoke_gemini_cli.py`

## Death Test Requirements

- Test: evaluator must fail if one required workflow skill is omitted from the auto-mode inspection list.
- Test: evaluator must fail if a required workflow skill omits append-only `auto-decisions.md` logging for its former human questions or confirmations.
- Test: evaluator must fail if the new `samsara-auto-gatekeeper` agent is not present in converted Codex output.
- Test: evaluator must fail if Gemini output does not include the auto gatekeeper markdown agent.

## Implementation Steps

- [ ] Step 1: Write death tests that prove the evaluator catches missing stage coverage and missing converted gatekeeper agent.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_skill_auto_mode_protocol_death.py tests/integration/test_pipeline.py` — verify targeted failures.
- [ ] Step 3: Add positive evaluator assertions for all required workflow stages and converted agent outputs.
- [ ] Step 4: Run targeted integration tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode tests/integration/test_pipeline.py tests/integration/test_format_validation.py`.
- [ ] Step 5: Run platform smoke tests if runtime cost is acceptable: `source .venv/bin/activate` and `uv run pytest tests/integration/test_smoke_codex.py tests/integration/test_smoke_gemini_cli.py`.
- [ ] Step 6: Fix evaluator gaps until the primary evaluator passes.
- [ ] Step 7: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-4-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: evaluator only checks keyword presence, not stage-specific auto branch semantics.
- Potential shortcut: Codex conversion is checked but Gemini conversion is missed.
- Assumption to verify: fixture-driven inspection is acceptable as the first primary evaluator before live auto execution exists.

## Acceptance Criteria

- Covers: "Silent failure - auto mode transitions without decision record"
- Covers: "Success - full auto workflow contract exists"
