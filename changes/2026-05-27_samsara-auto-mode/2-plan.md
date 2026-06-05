# Plan: samsara-auto-mode

## Pre-thinking Commitments Consumed

**Decision:** Proceed

**Accepted gaps:** none

**System design constraints:**
- First implementation prefers session ask before `research`; `samsara_config.yaml` support is intentionally out of scope for the first cut.
- The gatekeeper is a reusable principle-level subagent contract, not duplicated gate logic inside each workflow skill.
- Auto mode does not degrade back to human-in-the-loop once started in the initial design.
- A dedicated append-only `auto-decisions.md` file records the gatekeeper's decisions for each workflow question or confirmation.
- The gatekeeper must combine project prior knowledge, principle-level reasoning, problem insight, and system architecture judgment.

**Primary evaluator:** Full autonomous Samsara workflow completion in auto mode.

**Pass signal:** The workflow reaches the normal completion point without human intervention, every required stage artifact exists, and the auto decision file records the principle-level subagent's decision for each former human question or confirmation.

**Fail signal:** The workflow asks for human input after auto mode begins, skips a required Samsara stage, fails to produce required artifacts, or lacks a decision record for any former human question or confirmation.

**Feedback loop:** First inspect the stage where the workflow stopped, skipped, or produced an incomplete decision record; then revise the auto-mode gatekeeper contract or the stage integration that caused the break.

## Technical Specification

### Goal

Add an explicit Samsara `auto` execution path that preserves the existing workflow while replacing each human gate with a reusable principle-level gatekeeper subagent. The first implementation is instruction/protocol level: it changes Samsara's source skills and agent definitions so installed agents can run either human-in-the-loop or auto mode consistently.

### Execution Mode Selection

Input source:
- `human-in-the-loop`: default mode. Existing behavior remains: each phase asks the user to confirm before moving to the next phase.
- `auto`: selected by a session ask before `research` begins. Once selected, no later stage asks the user for gate confirmation.

Out of scope for first implementation:
- `samsara_config.yaml` or other persistent config support.
- Switching from `auto` back to human-in-the-loop after auto mode begins.

Output states:
- `success`: mode is known before `research` begins and every stage can read the active mode from the conversation/change context.
- `failure`: mode is explicitly invalid or contradictory.
- `unknown`: mode cannot be determined. Unknown must not silently default to `auto`; default is human-in-the-loop unless the user explicitly selected auto before research.

### Reusable Gatekeeper Subagent

Create `agents/auto-gatekeeper.md`. Conversion will expose this as `samsara-auto-gatekeeper` on target platforms.

Responsibilities:
- Act as the human gate replacement in `auto` mode.
- Review the current stage artifact and the next transition question.
- Answer from project prior knowledge, Samsara principles, problem insight, and system architecture judgment.
- Record a decision in the dedicated auto decision file.
- Decide among `proceed`, `revise`, `reject`, or `accept_gap`.

Non-responsibilities:
- It does not implement tasks.
- It does not skip stages.
- It does not ask the user for help once auto mode has started.
- It does not accept security/privacy risk without evidence. For security/privacy unknowns, it records a high-uncertainty `reject` decision rather than asking the user to accept risk.

Output states:
- `success`: gate decision is recorded with enough evidence to continue.
- `failure`: gatekeeper records `revise` or `reject` and the workflow follows that recorded decision.
- `unknown`: gatekeeper cannot determine whether the gate can pass from available principles/evidence. Unknown must be recorded as uncertainty in `auto-decisions.md` and must not be treated as silent success or converted into a human question.

### Auto Decision File

Create `references/auto-mode.md` as the reusable protocol and schema. Each auto run writes append-only entries to `changes/<feature>/auto-decisions.md`.

Minimum decision record fields:
- `decision_id`
- `stage`
- `prompt_type`: `question | confirmation`
- `workflow_prompt`
- `gatekeeper_answer`
- `decision`: `proceed | revise | reject | accept_gap`
- `rationale`
- `principles_used`
- `architecture_considerations`
- `evidence_checked`
- `uncertainty`
- `consequences`
- `timestamp`

Append-only rules:
- Existing decision entries must not be edited.
- A correction or changed judgment must be appended as a new decision entry that references the superseded decision id.
- The log must preserve the original workflow prompt so an audit can see exactly what human question or confirmation the gatekeeper answered.

Output states:
- `success`: all former human questions or confirmations have one append-only decision entry.
- `failure`: a required gate has no entry, malformed entry, or a decision that contradicts the next action.
- `unknown`: the decision file exists but cannot be matched to workflow gates. Unknown fails the primary evaluator.

### Workflow Integration

Modify these workflow sources:
- `skills/samsara-bootstrap/SKILL.md`
- `skills/research/SKILL.md`
- `skills/pre-thinking/SKILL.md`
- `skills/planning/SKILL.md`
- `skills/implement/SKILL.md`
- `skills/iteration/SKILL.md`
- `skills/security-privacy-review/SKILL.md`
- `skills/validate-and-ship/SKILL.md`

Each stage keeps the human gate path. Each stage adds an auto path:
1. Detect active execution mode.
2. If human-in-the-loop, use existing gate behavior.
3. If auto, dispatch `samsara-auto-gatekeeper`.
4. Gatekeeper appends to `changes/<feature>/auto-decisions.md`.
5. The main agent follows the recorded decision.
6. The stage must not silently continue if the decision file cannot be written or read.

### Primary Evaluator Harness

The first evaluator is a fixture-driven inspection test rather than a live autonomous run. It must verify that the source skills and gatekeeper contract contain enough protocol to run from `research` through validation without human answers after auto mode starts.

The evaluator checks:
- session ask before research exists in bootstrap instructions;
- every workflow transition has an auto-mode branch;
- every auto branch dispatches `samsara-auto-gatekeeper`;
- every auto branch requires appending to `changes/<feature>/auto-decisions.md`;
- no auto branch says to ask the user for gate confirmation after auto mode begins;
- installed/conversion tests include the new agent name.

This is not a substitute for a later live end-to-end run. It is the first version of the agent-evaluable contract.

## Death Cases

### Death Case 1: Auto Mode Looks Complete Without Gate Decisions

Trigger condition: a stage transitions to the next Samsara phase in auto mode without a decision entry.

The lie: the workflow appears autonomous and complete.

The truth: the human gate was skipped, not replaced.

Detection: tests inspect every workflow skill for an auto branch that dispatches `samsara-auto-gatekeeper` and requires writing `auto-decisions.md`.

### Death Case 2: Decision File Exists But Contains Generic Approval

Trigger condition: `auto-decisions.md` contains templated approvals without answering the stage question.

The lie: audit fields are present, so the decision looks traceable.

The truth: the file records shape, not judgment.

Detection: the gatekeeper contract requires question-specific `workflow_prompt`, `gatekeeper_answer`, `rationale`, `principles_used`, `evidence_checked`, and `uncertainty`; tests reject records/protocol examples that omit these fields.

### Death Case 3: Auto Mode Secretly Falls Back To Human

Trigger condition: a later stage asks the user to confirm, accept risk, or choose next action after auto mode has started.

The lie: the run is reported as auto.

The truth: the primary evaluator is invalid because human intervention occurred.

Detection: tests scan auto-mode sections for prohibited human confirmation language and require a recorded auto decision instead of user fallback.

### Death Case 4: Security Unknown Is Treated As Accepted Risk

Trigger condition: security/privacy review is unavailable, unknown, or failing in auto mode.

The lie: the workflow continues as if risk was accepted.

The truth: only a human can knowingly accept unverified risk in the current philosophy; first-cut auto mode must abort unknown security risk.

Detection: security/privacy review skill must state that auto mode can proceed only on review pass or explicit evidence; unknown/fail/no-capability records a high-uncertainty `reject` decision.

### Death Case 5: Config Support Bloats The First Cut

Trigger condition: implementation adds `samsara_config.yaml` parsing before the session ask path works.

The lie: the feature is more complete.

The truth: config support adds schema and persistence surface before the core auto workflow is proven.

Detection: acceptance criteria and tasks keep config support out of scope; tests should not require or introduce persistent config.

### Death Case 6: Feature Ships Without Version Bump

Trigger condition: auto mode implementation is complete but release metadata remains at `0.10.0` or drifts across metadata files.

The lie: the feature appears ready to ship.

The truth: consumers and installers cannot distinguish the auto-mode release from the previous release, or version metadata is internally inconsistent.

Detection: release metadata must set marketplace source-of-truth version to `0.11.0`, synchronize secondary metadata through release tooling, and pass `samsara-cli release check-version`.

## Task Decomposition

1. Define the auto gatekeeper and decision protocol.
2. Add session-level execution-mode routing and research/pre-thinking/planning auto gates.
3. Add implementation/iteration/security/validation auto gates.
4. Add the primary evaluator tests and converter coverage for the new agent.
5. Update user-facing docs and run validation.
6. Bump release metadata from `0.10.0` to `0.11.0` and verify synchronized versions.
