# Task 3: Add implementation, iteration, security, and validation auto gates

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

This task updates the later workflow stages. Auto mode must not ask for human decisions after it starts. Security/privacy unknowns must be recorded as high-uncertainty `reject` decisions instead of pretending a human accepted risk.

## Files

- Modify: `skills/implement/SKILL.md`
- Modify: `skills/iteration/SKILL.md`
- Modify: `skills/security-privacy-review/SKILL.md`
- Modify: `skills/validate-and-ship/SKILL.md`
- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol_death.py`
- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol.py`

## Death Test Requirements

- Test: implement, iteration, security/privacy review, and validate-and-ship must fail inspection if any auto branch can ask the user for gate confirmation.
- Test: security/privacy review must fail inspection if auto mode can accept unknown/no-capability review as human-accepted risk.
- Test: validate-and-ship must fail inspection if it can report auto completion without checking `auto-decisions.md`.
- Test: later-stage auto branches must fail inspection if they do not preserve the original workflow prompt in the append-only decision log.

## Implementation Steps

- [ ] Step 1: Extend death tests for later-stage gates and security/privacy unknown handling.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_skill_auto_mode_protocol_death.py` — verify they fail.
- [ ] Step 3: Extend unit tests for later workflow skills.
- [ ] Step 4: Run unit tests with `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode/test_skill_auto_mode_protocol.py` — verify they fail where expected.
- [ ] Step 5: Update the four skill files with auto branches and decision-file requirements.
- [ ] Step 6: Run the task test set — verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-3-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: security review language still implies human risk acceptance in auto mode.
- Potential shortcut: validate-and-ship checks final artifacts but not the append-only auto decision trace.
- Assumption to verify: "no human fallback" does not require changing implementer task execution semantics.

## Acceptance Criteria

- Covers: "Silent failure - auto mode asks human after start"
- Covers: "Unknown outcome - security or privacy review cannot determine pass"
- Covers: "Success - full auto workflow contract exists"
