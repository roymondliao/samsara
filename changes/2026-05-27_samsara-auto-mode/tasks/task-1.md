# Task 1: Define auto gatekeeper and decision protocol

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

Samsara auto mode replaces human gate decisions with a reusable principle-level subagent. The first task creates the agent contract and the reusable append-only decision-file protocol used by every workflow question or confirmation.

## Files

- Create: `agents/auto-gatekeeper.md`
- Create: `references/auto-mode.md`
- Create: `tests/test_auto_mode/test_gatekeeper_contract_death.py`
- Create: `tests/test_auto_mode/test_gatekeeper_contract.py`
- Modify: `tests/test_converter/test_agent.py`
- Modify: `tests/test_converter/test_agent_death.py`

## Death Test Requirements

- Test: missing `references/auto-mode.md` or missing append-only decision fields must fail because the gatekeeper could produce unauditable approvals.
- Test: the decision protocol must require `workflow_prompt`, `gatekeeper_answer`, `prompt_type`, `decision`, `rationale`, `principles_used`, `evidence_checked`, `uncertainty`, and `consequences`.
- Test: `agents/auto-gatekeeper.md` must not instruct the agent to ask the user after auto mode begins.
- Test: converter naming coverage must include `auto-gatekeeper` so installed platforms expose `samsara-auto-gatekeeper`.

## Implementation Steps

- [ ] Step 1: Write death tests for missing append-only decision schema, human fallback language, and missing converter coverage.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_gatekeeper_contract_death.py tests/test_converter/test_agent_death.py` — verify they fail.
- [ ] Step 3: Write unit tests for gatekeeper contract presence and required sections.
- [ ] Step 4: Run unit tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_gatekeeper_contract.py tests/test_converter/test_agent.py` — verify they fail where expected.
- [ ] Step 5: Implement `agents/auto-gatekeeper.md`, `references/auto-mode.md`, and update converter agent lists.
- [ ] Step 6: Run the task test set — verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-1-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: gatekeeper prompt becomes generic reviewer language instead of principle-level decision authority.
- Potential shortcut: decision schema has fields but does not preserve the original workflow prompt or force question-specific gatekeeper answers.
- Assumption to verify: adding `auto-gatekeeper.md` to source agents is enough for platform conversion without fixture snapshot churn.

## Acceptance Criteria

- Covers: "Silent failure - decision file has shape but no judgment"
- Covers: "Success - full auto workflow contract exists"
