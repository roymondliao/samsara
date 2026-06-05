# Task 2: Add mode routing and early-stage auto gates

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

This task adds session-level mode selection before research and updates the early workflow gates. Human-in-the-loop remains the default. Auto mode must not use `samsara_config.yaml` in the first implementation.

## Files

- Modify: `skills/samsara-bootstrap/SKILL.md`
- Modify: `skills/research/SKILL.md`
- Modify: `skills/pre-thinking/SKILL.md`
- Modify: `skills/planning/SKILL.md`
- Create: `tests/test_auto_mode/test_skill_auto_mode_protocol_death.py`
- Create: `tests/test_auto_mode/test_skill_auto_mode_protocol.py`

## Death Test Requirements

- Test: bootstrap must fail inspection if it does not ask for execution mode before invoking `research`.
- Test: research, pre-thinking, and planning must fail inspection if their transition gates do not mention `samsara-auto-gatekeeper`.
- Test: early-stage auto branches must fail inspection if they do not require append-only entries in `auto-decisions.md` for each workflow question or confirmation.
- Test: early-stage auto branches must fail inspection if they mention asking the user for confirmation after auto mode begins.

## Implementation Steps

- [ ] Step 1: Write death tests for missing session mode ask and missing auto branches in early workflow skills.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_skill_auto_mode_protocol_death.py` — verify they fail.
- [ ] Step 3: Write unit tests that inspect bootstrap/research/pre-thinking/planning for the expected auto protocol.
- [ ] Step 4: Run unit tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_skill_auto_mode_protocol.py` — verify they fail where expected.
- [ ] Step 5: Update the four skill files so each preserves the human path and adds the auto path.
- [ ] Step 6: Run the task test set — verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-2-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: mode selection is described but not made mandatory before research.
- Potential shortcut: auto branch says to "continue" but omits appending the original workflow prompt and gatekeeper answer to `auto-decisions.md`.
- Assumption to verify: existing skill transition wording can support mode branching without changing the converter.

## Acceptance Criteria

- Covers: "Silent failure - auto mode transitions without decision record"
- Covers: "Silent failure - auto mode asks human after start"
- Covers: "Degradation - persistent config support is requested before session mode works"
