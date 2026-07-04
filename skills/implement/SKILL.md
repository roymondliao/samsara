---
name: implement
description: Use when a plan with tasks exists and you need to execute implementation — requires index.yaml and tasks/ directory
---

# Implement — Death Test First, Scar Report Always

Execute implementation tasks with death tests before unit tests, and scar reports on every completion.

> 陽面問「功能做完了嗎」，陰面問「做完的東西壞掉時你知道嗎」。

## Prerequisites

Read from the feature's `changes/` directory:
- `index.yaml` — task list with dependencies
- `overview.md` — shared architecture context
- `tasks/task-N.md` — individual task files

## Process

```dot
digraph implement {
    node [shape=box];
    compound=true;

    start [label="讀取 index.yaml\n分析 task 依賴\n+ TaskCreate per task" shape=doublecircle];
    mode [label="Execution strategy gate\nhuman: ask\nauto: gatekeeper" shape=diamond];

    subgraph cluster_implementer {
        label="samsara:implementer（subagent 或 inline）";
        style=dashed;
        step0 [label="STEP 0 前置四問"];
        death_test [label="Death Test 先行"];
        contract_gate [label="Test Contract Gate\n→ references/test-contract.md"];
        unit_test [label="Unit Test"];
        integration [label="Integration Test\n（如適用）"];
        scar [label="寫 scar-report\n→ changes/<feature>/scar-reports/task-N-scar.yaml"];
        report [label="回報 status + scar report\n（不 commit）"];
    }

    review [label="主 agent: Code Review\n（dispatch code-reviewer）"];
    fix [label="Implementer 修正" style=dashed];
    update [label="主 agent: 更新 index.yaml\n+ TaskUpdate completed"];
    more [label="還有 task？" shape=diamond];
    commit [label="主 agent: Commit\n（全部 task 完成後）"];
    criteria [label="Iteration-entry criteria\ncross-task pattern OR\nsignal_lost>=5 ?\n(parse failure -> unknown)" shape=diamond];
    gate [label="判準成立 / unknown\nhuman: ask\nauto: gatekeeper" shape=diamond];
    next [label="invoke samsara:validate-and-ship\nor samsara:iteration" shape=doublecircle];

    start -> mode;
    mode -> step0 [label="A/B: dispatch\n(paste full text)" lhead=cluster_implementer];
    mode -> step0 [label="C: 主 agent\n自己執行" lhead=cluster_implementer];

    step0 -> death_test;
    death_test -> contract_gate;
    contract_gate -> unit_test;
    unit_test -> integration;
    integration -> scar;
    scar -> report;

    report -> review;
    review -> update [label="PASS"];
    review -> fix [label="Critical issues"];
    fix -> review [label="re-review"];
    update -> more;
    more -> step0 [label="yes" lhead=cluster_implementer];
    more -> commit [label="no"];
    commit -> criteria;
    criteria -> gate [label="成立 / 解析失敗(unknown)"];
    criteria -> next [label="不成立 + 全部可解析\n預設 skip + 可推翻紀錄"];
    gate -> next [label="confirmed"];
}
```

## Progress Tracking

On entry, after reading `index.yaml`, create a TaskCreate item for each task to provide real-time UI progress.

```
Read index.yaml
  → For each task: TaskCreate({ title: "Task N: {title}", status: "open" })

After each task's review passes:
  → Update index.yaml (status, scar_count)
  → TaskUpdate({ status: "completed" }) for the corresponding task
```

index.yaml 是唯一真實狀態（source of truth）；TaskCreate/TaskUpdate 是盡力而為的 UI 投影，投影未更新不構成流程錯誤，但 index.yaml 未更新是。

## Execution Mode Selection

On entry, analyze `index.yaml` for task dependencies, create TaskCreate items
for each task, then use this execution strategy prompt:

> 「Plan 中有 N 個 tasks。
>
> 依賴分析：
> - task-1, task-2: 無依賴，可平行
> - task-3: 依賴 task-1 + task-2，必須 sequential
>
> 執行模式：
> (A) Subagent parallel — 無依賴的 tasks 平行分派，有依賴的 sequential
> (B) Subagent sequential — 每個 task 一個 fresh subagent，依序執行
> (C) Inline sequential — 主 agent 自己依序執行
>
> 選哪個？」

- If `Execution mode: human-in-the-loop`, ask the user this question and follow
  the selected strategy.
- If `Execution mode: auto`, do not ask the user. Use the Auto Mode Gate below
  to dispatch `samsara:auto-gatekeeper`, append the strategy decision to
  `auto-decisions.md`, and follow the recorded execution strategy.

### Subagent Context

Use `subagent_type: "samsara:implementer"` — the agent definition (`agents/implementer.md`) provides samsara constraints (STEP 0, 禁止行為, 強制行為, death test ordering, scar report format). You do NOT need to inject these into the prompt.

The prompt provides per-task context. Follow the template in `./dispatch-template.md`:
- `task-N.md` — **paste full text**, never tell subagent to read the file
- `overview.md` — **curate relevant sections**, not the entire file
- Related death cases and prior scar reports (if task has dependencies)

### Subagent Review (modes A and B)

After each subagent completes (status DONE or DONE_WITH_CONCERNS):

1. **Parallel code review** — dispatch BOTH reviewers in the **same message** to enable parallel execution:
   - `samsara:code-reviewer` (yin) — spec compliance, deletion analysis, architectural placement (against the plan's placement/ownership Key Decisions — the yin dispatch includes them; see `./dispatch-template.md`), naming honesty, silent rot paths, correctness
   - `samsara:code-quality-reviewer` (quality) — structural truth-telling: S/O/L/I/D + Cohesion/Coupling/DRY/Pattern

   See `./dispatch-template.md` for both dispatch templates.

2. **Aggregation rule** — main agent MUST receive BOTH review outputs before proceeding:
   - Both pass → proceed to index.yaml update
   - Either reviewer reports Critical issues → implementer fixes → re-review (dispatch both again)
   - Either reviewer reports `UNKNOWN` → **blocking review failure**; fix the missing/unreadable reference or unsupported domain condition, then re-review (dispatch both again)
   - Only one review output received → **FAIL with "missing reviewer" error** — do NOT assume absent reviewer = PASS. Re-dispatch the missing reviewer before proceeding.

3. Review passes (both) → main agent updates `index.yaml` (status, scar_count, unresolved_assumptions).

Do not proceed to next task with open Critical issues. Do not commit until all tasks complete.

## Per-Task Execution Order

This order is mandatory. Death test before unit test. Scar report before self-iteration before report.

### Implementer（subagent 或 inline）

1. STEP 0 — answer the four prerequisite questions
2. Write death tests — test silent failure paths first
3. Run death tests — verify they fail (red)
4. **Test Contract Gate (before unit tests)** — for each unit-test assertion,
   run the contract gate from `references/test-contract.md`. Every unit test must
   assert a behavioral contract, not implementation details. This gate runs BEFORE
   unit tests are written — do not skip to writing unit tests. See
   `references/test-contract.md` for the contract sources and the both-poles rules
   (over-fit and silent-green); it is the single source of truth — do not restate
   the source list here.
5. Write unit tests — each bound to a named contract per the gate
6. Run unit tests — verify they fail (red)
7. Implement minimal code to pass all tests
8. Run all tests — verify they pass (green)
9. Write scar report → `changes/<feature>/scar-reports/task-N-scar.yaml` (read `templates/scar-schema.yaml` for the exact format; `<feature>` = the feature directory name from `changes/`)
10. Self-iteration (Level 1) — review scar items, fix task-scope actionable items
11. Update scar report — mark fixed items in place with `status: resolved` + a one-line `resolution` (`scar-schema.yaml` Rule 11; the older separate `resolved_items` list remains readable per Rule 14 but is retired for new writes), mark remaining items with `deferred_to_feature_iteration` flags where applicable
12. Run all tests — verify no regression from self-iteration fixes
13. Report back (do NOT commit)

### Main agent（review + bookkeeping）

14. **Parallel dispatch both reviewers in the same message** — `samsara:code-reviewer` (yin) and `samsara:code-quality-reviewer` (quality). See `./dispatch-template.md` for both dispatch templates.
    - Both outputs must arrive. A reviewer output that did not arrive is **not** the same as PASS or PASS_WITH_CONCERNS — it is an absent output. If only one review output is received → **FAIL with "missing reviewer" error**. Re-dispatch the missing reviewer (max 2 retries); if it still does not arrive, escalate and do not proceed.
15. If either reviewer reports `UNKNOWN` or Critical issues → implementer fixes the blocking reference/domain issue or review finding → re-review (both reviewers again)
16. Update `index.yaml` — set status, scar_count, unresolved_assumptions + TaskUpdate the corresponding task to `completed`
17. Proceed to next task

### After all tasks complete

18. Commit all changes

## Yin-Side Constraints

These are non-negotiable:

- **No optimistic completion:** A task without a scar report has status `completion_unverified`, not `done`
- **Death test ordering:** Death tests must be written and run before unit tests. This order cannot be swapped.
- **Test Contract Gate before unit tests:** Every unit-test assertion must pass the contract gate in `references/test-contract.md` BEFORE the unit test is written. A unit test asserts a behavioral contract, not implementation details. This gate runs before unit tests, never after — a gate run after the test is already on disk cannot stop a tautological test from landing.
- **Review before index update:** `index.yaml` is updated only after code-reviewer passes. No pre-review status changes.
- **UNKNOWN blocks review completion:** Reviewer `UNKNOWN` is not a partial pass. It means a required reference/domain condition could not be verified; do not proceed, update `index.yaml`, or mark review complete until the condition is fixed and both reviewers are re-run.
- **Commit after all tasks:** Do not commit per-task. Commit once after all tasks complete and all reviews pass.
- **Structural honesty applies at generation, not only at review:** The implementer's 結構誠實 constraints (`agents/implementer.md`) — justify every boundary/abstraction by what breaks if it is removed, and refuse speculative generalization built for a single consumer — apply whether the implementer runs as a subagent (modes A/B) **or inline (mode C)**. In inline mode the agent definition is not loaded, so the main agent owns these constraints directly; do not skip them just because no subagent was dispatched.
- **Read-before-write and dependency hygiene apply inline too:** The implementer's `agents/implementer.md` constraints — **read before you write** (read the files you touch + neighbors, copy existing patterns instead of inventing) and **no silent dependency addition** (ask whether the standard library or an existing dependency already covers it before adding one; record why one earns its place) — apply in subagent modes A/B **and inline mode C**. In inline mode the agent definition is not loaded, so the main agent owns these directly.

## Red Flags

**Never:**
- Make subagent read task or overview files (paste full text — see `./dispatch-template.md`)
- Use generic `general-purpose` subagent — always use `samsara:implementer`
- Skip yin-side review (dispatch `samsara:code-reviewer`)
- Skip `code-quality-reviewer` dispatch — both reviewers are required; skipping one means the review is incomplete
- Proceed to next task while code-reviewer or code-quality-reviewer has open Critical issues
- Proceed to next task when either reviewer returned `UNKNOWN` because a reference was missing/unreadable or the execution domain was unsupported
- Dispatch multiple implementer subagents in parallel (file conflicts)
- Ignore subagent NEEDS_CONTEXT or BLOCKED status — provide context or escalate
- Accept a task as DONE without a scar report
- Skip the Test Contract Gate before writing unit tests — a unit test with no named contract is brittle or tautological by default
- Accept an **over-fit / brittle** unit test that reddens on a behavior-preserving refactor (pins implementation details)
- Accept a **silent-green / tautological** unit test (a vague test that asserts almost nothing and can never go red — it stays green when the behavior actually breaks) — guarding only the over-fit pole re-creates the disease at the silent-green pole
- Let subagent commit — only the main agent commits, after all tasks complete
- Update index.yaml before both code-reviewer and code-quality-reviewer pass
- Assume an absent review output means PASS — missing reviewer output is always a FAIL
- Add a dependency without recording in the scar why the standard library or an existing dependency cannot do it — an unjustified dependency is deletable by default
- Write death tests before reading the files you are about to touch — a death test built on assumed (not read) conventions pins the wrong contract

## Support Files

- `./dispatch-template.md` — prompt template for implementer and reviewer dispatch
- `./scar-report.md` — scar report format reference
- `references/test-contract.md` — the canonical Test Contract Gate protocol (over-fit and silent-green poles, snapshot/spy/minimum-contract patterns); the Test Contract Gate points here rather than duplicating the catalog

## Transition

All tasks complete. Calculate the iteration-entry criteria:

1. Read every `changes/<feature>/scar-reports/task-N-scar.yaml`.
2. Compute `signal_lost` and identify parse failures using the SAME
   definition and parse-failure semantics as iteration SKILL.md's Step 1:
   Aggregate Remaining Scars (the signal_lost formula, and `systemic_ref`
   dangling = parse failure) — canonical there, not restated here.
3. Check for a **cross-task pattern**: the same item (by description or
   `systemic_ref` id) appears in ≥2 different task scar reports.
   已知限制：這是**字面比對**（description 全同或 id 相同）——兩個 task 用
   不同措辭描述同一 rot 時會漏判而落入預設 skip；可推翻紀錄的存在就是這個
   限制的補償措施。

Branch into exactly one of three states:

- **判準成立**（cross-task pattern found, OR `signal_lost >= 5` — this
  threshold is a rough estimate from historical iteration-log data, not a
  calibrated constant; adjust only by citing newer iteration-log evidence in
  the scar report） AND every scar report parsed → 依 execution mode 過
  gate（human: ask the user；auto: dispatch `samsara:auto-gatekeeper`，見下方
  Auto Mode Gate）建議進入 iteration，並列出找到的 cross-task patterns 與
  signal_lost 數值。
- **判準不成立，且全部 scar 可解析** → 預設 skip：不經過 gate
  （deterministic），但一律先印出這行可推翻紀錄，才能繼續：
  > 「signal_lost=N、無 cross-task pattern，已 skip iteration（回覆可推翻）」

  同一行紀錄必須同時寫入 feature 的 `index.yaml`（durable——auto mode 沒有人
  在讀對話輸出，只印不寫等於沒有紀錄）。然後直接進入
  `samsara:validate-and-ship`（其 Step 0 為 security/privacy gate；剩餘 items
  由 failure budget review 處理）。
- **任何 scar report 解析失敗** → 結果為 unknown，**不准 skip**（解析失敗代表
  signal_lost 可能被少算，unknown 不等於「不需要 iteration」）。列出每個 parse
  failure（file，以及懸空 `systemic_ref` 的 id），再依 execution mode 過
  gate（human: 連同 parse failures 詢問使用者；auto: dispatch
  `samsara:auto-gatekeeper`）決定 `samsara:iteration` 或
  `samsara:validate-and-ship` — 絕不落回上面的預設 skip 路徑。

- If `Execution mode: human-in-the-loop` and the gate above is invoked, the
  user's answer selects `samsara:iteration` or `samsara:validate-and-ship`.
- If `Execution mode: auto` and the gate above is invoked, do not ask the user. Use the Auto Mode Gate below to dispatch `samsara:auto-gatekeeper`,
  record the decision, and invoke the next skill named by the recorded
  decision.

## Auto Mode Gate

Canonical protocol: `references/auto-mode.md` Stage Gate Protocol —
dispatch, the append-only decision log, and what `proceed`/`revise`/
`reject`/`accept_gap` mean all live there; this section only names what
Implement adds.

- `workflow_prompt` sources: (1) the implementation completion gate — only
  invoked when the Transition iteration-entry criteria are met (canonical in
  Transition above) or scar parse failures make it unknown (deterministic
  default-skip never invokes this gate); (2) the implementation execution-mode selection — the original
  `(A) Subagent parallel / (B) Subagent sequential / (C) Inline sequential`
  prompt.
- Decision points this gate covers: the completion transition (when
  triggered) and the execution-mode selection.
- `proceed` invokes the next skill named by the gatekeeper answer
  (`samsara:iteration` or `samsara:validate-and-ship`) and/or applies the
  chosen execution strategy; `revise` revises implementation artifacts or
  scar reports then re-runs this gate; `accept_gap` continues to the
  recorded next skill with the accepted gap visible.
