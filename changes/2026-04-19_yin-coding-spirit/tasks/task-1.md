# Task 1: Write samsara/references/code-quality.md — 8 criteria + good/bad examples

## Context

Read: overview.md

此 reference 是 samsara:code-quality-reviewer agent 的 knowledge source——agent dispatch 時會讀此檔來決定 review criteria。若 reference 寫得含糊，agent 判斷就失準；若寫得過度 prescriptive，會誘發 compliance theater。

Examples 必須來自真實 code：good examples 使用 `experiment/outputs/en-must-output.py`（clean Pythonic）和 `experiment/outputs/zh-is-output.py`（collaborator 分離）；bad examples 使用 `hooks/scripts/observe-learnings.py`（known junior）和 `experiment/outputs/en-is-output.py`（over-OOP）。

## Files

- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/references/code-quality.md`

## Death Test Requirements

- **Fixture consistency test**: 檔案必須 parse 為 valid Markdown，所有 code blocks 能被語法高亮為 python
- **8-criteria coverage test**: 8 個 section headers 分別對應 8 條 criteria，無遺漏無重複
- **Example sourcing test**: 每個 criterion 至少 1 good + 1 bad example，每個 example 附具體來源路徑
- **No rule-list test**: 檔案不得出現 "MUST"/"MUST NOT"/"禁止" 等 rule-style 措辭（實驗證明 rule-style 在英文誘發 compliance theater；此 reference 應為 example-driven）
- **Scope boundary test**: 檔案前言必須明確標示 "out of scope" 議題（silent rot, dishonest naming, security, performance）並指向對應 reviewer

## Implementation Steps

- [ ] Step 1: Write death test fixtures — create `tests/samsara/code-quality-reviewer/reference-structure.sh` that validates markdown structure
- [ ] Step 2: Run structure test — verify it fails (file doesn't exist yet)
- [ ] Step 3: Write reference content following these sections:
  - Frontmatter: purpose, scope, out-of-scope
  - For each of 8 criteria: 陰面判斷問題 + Good Example（附 path:line ref） + Bad Example（附 path:line ref） + 決策規則 (Critical / Important / Suggestion)
  - Closing: 使用指南 (如何從 8 條轉成 review output)
- [ ] Step 4: Run structure test — verify it passes
- [ ] Step 5: Write scar report: assumptions made about examples, any criterion hard to example-ize
- [ ] Step 6: Commit

## Expected Scar Report Items

- Potential shortcut: 某些 criterion（例如 "易拓展"）在短 code 裡難找明顯 example——可能誘惑去造假 example 或抄教科書
- Potential shortcut: 為求省事，bad examples 全部取自 hooks/scripts/observe-learnings.py——應分散來源以涵蓋多種失敗模式
- Assumption to verify: 「bad example 被 reader 認為 bad」——若 reader 的直覺與 example 分類不一致，criterion 需重新設計
- Assumption to verify: 「8 條之間無重疊」——實際寫 examples 時可能發現某 example 同時觸犯多條；這時要決定如何分類

## Acceptance Criteria

Covers (from acceptance.yaml):
- (部分) "Silent false PASS on known-junior code" — 此 task 提供 reviewer 用來判斷的 criteria 來源
- "Degradation - reference file temporarily unavailable" — reference 必須存在於此路徑且 parseable
