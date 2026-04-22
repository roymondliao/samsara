# Task 2: Write samsara/agents/code-quality-reviewer.md — agent definition

## Context

Read: overview.md

此 agent 是整個 feature 的核心可執行物。它的 system prompt 決定 dispatch 時的實際行為。既有 `samsara/agents/code-reviewer.md` 是 yin reviewer（system-level），是這個新 agent 的 sibling 參考範本。

關鍵設計約束（來自 2-plan.md 和 overview.md）：
- Agent prompt **必須** 在開頭明確列出 out-of-scope 議題（silent rot, dishonest naming, security, performance），避免 Death Case 3 (Scope Violation)
- Agent **必須** 讀取 `samsara/references/code-quality.md` 作為 criteria 來源；讀不到時必須回 UNKNOWN 而非 fallback 到記憶
- Output 三態 (PASS / FAIL / UNKNOWN)，PASS 必須附具體 file:line 引用（避免 rubber-stamp）

## Files

- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/agents/code-quality-reviewer.md`

Reference (read, do not modify):
- `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/agents/code-reviewer.md`（sibling，參考結構）
- `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/references/code-quality.md`（Task 1 產出）

## Death Test Requirements

- **YAML frontmatter validity**: frontmatter 能被 parse，包含 `name`、`description`、`model`、`tools` fields
- **Scope boundary statement**: prompt 前 50 行內必須明確標示「不檢查 silent rot / dishonest naming / security / performance」並指向 samsara:code-reviewer
- **Reference dependency statement**: prompt 必須有 "reference file required" section，指定路徑 `samsara/references/code-quality.md`，並定義讀不到時的 UNKNOWN 行為
- **Output format enforcement**: prompt 必須定義 output schema：三態 (PASS/FAIL/UNKNOWN)、每個 state 的必要欄位
- **Anti-rubber-stamp clause**: prompt 必須明確要求 "PASS output 必須包含至少 1 個具體 file:line 觀察"
- **Dispatch fixture test**: dispatch agent on `fixtures/junior.py`（Task 5 準備）→ agent 必須回 FAIL 且 Critical issues ≥ 3

## Implementation Steps

- [ ] Step 1: 讀既有 `samsara/agents/code-reviewer.md`，了解 samsara agent 慣用結構
- [ ] Step 2: 讀 Task 1 產出的 `samsara/references/code-quality.md`
- [ ] Step 3: 寫 validation shell script `tests/samsara/code-quality-reviewer/agent-structure.sh` 檢查 frontmatter + 必要 sections
- [ ] Step 4: 執行 validation script — verify fails (agent file 尚未存在)
- [ ] Step 5: 寫 agent definition:
  - Frontmatter: name=code-quality-reviewer, model=sonnet, effort=high, tools=[Read, Glob, Grep, Bash]
  - Identity: who you are, your scope
  - **Scope Boundary section**: 列出 out-of-scope issues，指向 samsara:code-reviewer
  - **Reference File Protocol**: 如何讀 code-quality.md，讀不到時的 UNKNOWN 行為
  - **Review Procedure**: 對每個 diff file 跑 9-principle check（S/O/L/I/D + Cohesion/Coupling/DRY/Pattern），每個 principle 的違反在 output 標記對應的 outcome criteria (C1-C8)
  - **Output Format**: PASS/FAIL/UNKNOWN 的具體 schema，含 anti-rubber-stamp 要求
  - **Constraints**: "Do NOT duplicate yin reviewer's findings", "Do NOT perform security review" etc.
- [ ] Step 6: 執行 validation script — verify passes
- [ ] Step 7: 寫 scar report
- [ ] Step 8: Commit

## Expected Scar Report Items

- Potential shortcut: 直接 copy samsara:code-reviewer 結構但沒改 scope constraints，導致 agent 身份混淆
- Potential shortcut: 漏掉 UNKNOWN output state 的 explicit handling，讓 agent 在無法判斷時 fallback 到 PASS
- Potential shortcut: 抄既有 code-reviewer 的 "Do NOT give performative praise" constraint 而沒針對 code-quality 調整（可能該改為 "Do NOT rubber-stamp PASS without file:line reference"）
- Assumption to verify: sonnet 對這個 agent 的 task 足夠；可能需要 opus（但無證據前不升級以控制成本）
- Assumption to verify: agent 能正確讀 reference file（需 Task 5 validation 確認）

## Acceptance Criteria

Covers:
- "Silent false PASS on known-junior code" — agent 的 system prompt 必須讓 agent 在 junior fixture 下回 FAIL
- "Scope violation — duplicating yin reviewer" — agent prompt 的 Scope Boundary section 是主要防線
- "Unknown outcome — diff contains no reviewable code" — agent 的 output state machine 必須支援 UNKNOWN
- "Rubber-stamp PASS without evidence" — agent prompt 的 anti-rubber-stamp clause
- "Degradation - reference file temporarily unavailable" — Reference File Protocol section
