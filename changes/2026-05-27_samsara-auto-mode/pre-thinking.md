# Pre-thinking: samsara-auto-mode

## Session: 2026-05-27T23:37:37+08:00

## Step A — Design and Gap Map

### Information Gaps

#### Gap I1: Existing gate inventory
**Question:** Which existing Samsara transitions currently require human confirmation, and which artifacts or messages define those gates?
**Hypothesis:** The primary gates are the transitions between research, pre-thinking, planning, implementation, iteration, security/privacy review, and validate-and-ship, but the exact gate inventory should be discovered from current skill files and change artifacts during planning.

#### Gap I2: Project-principles source
**Question:** Which existing artifact should the auto-mode gatekeeper treat as the canonical source of project principles when reasoning from first principles?
**Hypothesis:** The canonical source should be the current Samsara axiom and skill instructions already present in the repository and agent skill files; auto mode should not invent a separate principle system until a reusable artifact is deliberately introduced.

### Design Decision Gaps

#### Gap D1: Execution-mode ownership
**Question:** Where should `human-in-the-loop` versus `auto` be selected and persisted?
**Hypothesis:** Support both project config default and session-level override, with the session-level selection taking precedence for a single run.
**Planning impact:** This changes CLI/config schema tasks, runtime policy lookup, test fixtures, and how agents report the active mode before gates begin.

#### Gap D2: Gatekeeper integration boundary
**Question:** Should the principle-level gatekeeper be modeled as a new reusable skill/subagent contract, or embedded as gate-specific logic inside each workflow skill?
**Hypothesis:** Model it as a reusable gatekeeper contract used by existing workflow skills, because auto mode is cross-cutting and must preserve the same workflow stages.
**Planning impact:** This determines whether planning creates one central contract and adapters, or many local changes across research, pre-thinking, planning, iteration, and validation.

#### Gap D3: Auto gate decision contract
**Question:** What exact fields must every auto gate decision record so later humans and agents can audit the run?
**Hypothesis:** Each decision should record gate id, stage, decision, rationale, project principles used, evidence checked, uncertainty, rejected alternatives, fallback reason if any, and next-step consequence.
**Planning impact:** This defines artifact schemas, test assertions, validation behavior, and the minimum quality bar for pre-production-level auto runs.

#### Gap D4: Fallback threshold
**Question:** When should auto mode stop and degrade to human-in-the-loop instead of continuing with a gatekeeper decision?
**Hypothesis:** Fallback should be required when the gatekeeper cannot tie a decision to explicit project principles, cannot identify verifiable evidence, detects conflicting requirements, or sees irreversible/high-risk impact.
**Planning impact:** This affects failure modes, UX, test cases, and whether auto mode is allowed to complete fully autonomous runs under uncertainty.

#### Gap D5: Evaluation authority
**Question:** What should be the single primary evaluator for deciding that auto mode is implemented correctly?
**Hypothesis:** The primary evaluator should be an end-to-end dry-run or fixture-driven workflow simulation that exercises auto mode across multiple gates and inspects the produced decision trace.
**Planning impact:** This determines whether implementation optimizes around CLI tests, artifact inspection, a synthetic workflow harness, or a rubric-based review of generated change files.

---

## Step B — Gap Answers

### Group 1: mode-and-gatekeeper

**Q:** `auto mode` 的模式選擇應該在哪裡生效？
**A:** Mode selection can be handled in two ways: read from `samsara_config.yaml`, or ask the user before invoking `research`. The current preference is to avoid config-file handling for the first version because it may be over-engineering; session ask before `research` is the lighter initial path.

**Q:** principle-level gatekeeper 應該是一個可重用的 subagent/skill contract，還是分散寫進每個 workflow skill 的 gate logic？
**A:** The principle-level gatekeeper should be a reusable subagent, not distributed gate-specific logic. It should function like "agent as human, human as agent": a reusable decision actor that stands in for the human gatekeeper across workflow stages.

**Q:** gatekeeper 做 first-principles reasoning 時，應該以哪個既有 artifact 當作 project principles 的 canonical source？
**A:** The gatekeeper needs project prior knowledge, principle-level reasoning ability, problem insight, and system architecture judgment. This implies the source cannot be only a single prompt; planning must define how a reusable gatekeeper is grounded in project knowledge and conventions while retaining high-level architectural judgment.

### Group 2: decision-and-evaluation

**Q:** 每個 auto gate decision 最少需要留下哪些欄位，才算可審計？
**A:** Auto mode likely needs a dedicated file that records the principle-level subagent's decisions for each workflow step. The record should focus on the subagent's answer to each step's questions and why that answer is acceptable for continuing the workflow.

**Q:** gatekeeper 在什麼條件下必須停止 auto mode，改回 human-in-the-loop？
**A:** Once auto mode starts, it should not switch back to human-in-the-loop in the initial design. Fallback to human is explicitly out of scope for now, even though earlier research treated fallback as a safety boundary. Planning must account for this by making the autonomous decision record and workflow completion criteria stricter.

**Q:** 你希望這個 feature 的唯一 Primary evaluator 是什麼？
**A:** The primary evaluator is whether Samsara can complete the full workflow in auto mode without any human intervention.

### Design Note: auto-decisions.md contract

`auto-decisions.md` should be an append-only event log for auto-mode gate decisions, not a post-hoc summary. Each workflow step that would normally ask the user a question or request confirmation must append a decision entry containing the original workflow prompt, the principle-level gatekeeper's answer, the workflow-actionable decision, rationale, principles used, evidence checked, uncertainty, and consequence for the next step.

If a later decision corrects or supersedes an earlier one, the earlier entry should not be edited. The correction should be appended as a new decision entry that references the superseded decision id. This keeps the record auditable and preserves the reasoning sequence of the auto run.

Suggested entry shape:

```md
## Decision 001 — <stage>.<gate-id>
- timestamp: <timestamp>
- stage: <research | pre-thinking | planning | implementation | iteration | validation>
- prompt_type: <question | confirmation>
- workflow_prompt: "<original question or confirmation text>"
- gatekeeper_answer: "<principle-level subagent answer>"
- decision: <proceed | revise | reject | accept_gap>
- rationale: "<why this answer is acceptable>"
- principles_used:
  - "<project prior / principle / convention>"
- architecture_considerations:
  - "<system boundary, coupling, reversibility, or operational concern>"
- evidence_checked:
  - "<artifact, observation, or verification>"
- uncertainty:
  level: <low | medium | high>
  notes: "<remaining uncertainty>"
- consequences:
  - "<what this decision causes the workflow to do next>"
```

## Evaluation Contract

**Primary evaluator:** Full autonomous Samsara workflow completion in auto mode.
**Agent can perform it by:** Run or simulate an auto-mode Samsara workflow from `research` through validation with no human answers after auto mode begins, then inspect the produced artifacts and auto decision file.
**Pass signal:** The workflow reaches the normal completion point without human intervention, every required stage artifact exists, and the auto decision file records the principle-level subagent's decision for each former human question or confirmation.
**Fail signal:** The workflow asks for human input after auto mode begins, skips a required Samsara stage, fails to produce required artifacts, or lacks a decision record for any former human question or confirmation.
**Feedback loop:** First inspect the stage where the workflow stopped, skipped, or produced an incomplete decision record; then revise the auto-mode gatekeeper contract or the stage integration that caused the break.
**Out of scope validation:** Proving that every autonomous decision matches what the user would have chosen in every real project; first-version evaluation focuses on uninterrupted workflow completion plus auditable gate decisions.

## Step C — Commitment

**Date:** 2026-05-27T23:53:28+08:00
**Decision:** Proceed
**Accepted gaps:** none
**Planning constraints:**
- First implementation should prefer session ask before `research`; `samsara_config.yaml` support is likely over-engineering for the first cut.
- The gatekeeper is a reusable principle-level subagent contract, not gate logic duplicated inside each workflow skill.
- Auto mode does not degrade back to human-in-the-loop once started in the initial design.
- A dedicated append-only `auto-decisions.md` file must record the gatekeeper's decisions for each workflow question or confirmation.
- The primary evaluator is full autonomous Samsara workflow completion in auto mode without human intervention.
