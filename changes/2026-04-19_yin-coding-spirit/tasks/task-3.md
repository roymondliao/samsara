# Task 3: Wire parallel dispatch into samsara:implement skill

## Context

Read: overview.md

既有 `samsara/skills/implement/SKILL.md` 在每個 implementer task 完成後會 dispatch 一個 reviewer (`samsara:code-reviewer`)。此 task 修改該 section，改為**並行** dispatch 兩個 reviewer（yin + quality），並要求 main agent 驗證兩份 result 都到達，任一 FAIL 即 block commit。

**Scope note (post-plan clarification)**：此修改必須同時覆蓋 implement 的**兩種執行模式**：
- **Mode B (subagent)**：implementer 由 subagent 執行，完成後 main agent 在 Line 115 區塊 dispatch reviewer
- **Mode A (inline)**：implementer 由 main agent inline 執行，review 階段在 Line 142 區塊 dispatch reviewer（即使 inline 模式，review 仍 dispatch subagent）

兩種模式最終都經過 code-reviewer dispatch，所以修改兩個區塊即可 cover 兩種模式。不要只改一個區塊——會造成其中一種 mode 被遺漏。

Dispatch template 也需同步更新 (`samsara/skills/implement/dispatch-template.md`) 加入 code-quality-reviewer 的 prompt template。

關鍵約束（來自 acceptance.yaml 的 "Parallel dispatch silent skip" death path）：
- Main agent **必須** 收到兩份 review output 才能判 PASS
- 收到一份 = FAIL with "missing reviewer" log
- 絕不可預設「沒回來的 reviewer 算 PASS」

## Files

- Modify: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/skills/implement/SKILL.md`
  - Line ~113-117 (現有 "Code review — dispatch samsara:code-reviewer" section)
  - Line ~142-143 (Main agent review + bookkeeping section)
  - Line ~164-167 (Never-do list: 加 "Skip code-quality-reviewer")
- Modify: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/skills/implement/dispatch-template.md`
  - Line ~72-80 (Code review dispatch template — 加 code-quality-reviewer 版本)

## Death Test Requirements

- **Dispatch statement test**: SKILL.md 必須明確說明兩個 reviewer 並行 dispatch，而非 sequential
- **Missing-reviewer handling test**: SKILL.md 必須有段落說明「若只收到一份 review output，視為 FAIL」
- **Template availability test**: dispatch-template.md 必須包含兩個 reviewer 的 template（一個既有、一個新）
- **No-silent-skip test**: SKILL.md "Never" section 必須包含 "Skip code-quality-reviewer dispatch"
- **Integration smoke test**: 讀 SKILL.md 後，一個無 context 的 agent 能正確推斷「兩個 reviewer 都要跑」

## Implementation Steps

- [ ] Step 1: 讀現有 `samsara/skills/implement/SKILL.md`，找出 review dispatch 位置
- [ ] Step 2: 讀現有 `samsara/skills/implement/dispatch-template.md`
- [ ] Step 3: 寫 validation shell `tests/samsara/code-quality-reviewer/implement-wiring.sh` 檢查關鍵 sentences
- [ ] Step 4: 執行 validation — verify fails (wiring 尚未更新)
- [ ] Step 5: 修改 SKILL.md：
  - Step 13 / Line 115 改為: "Parallel dispatch 兩個 reviewer: `samsara:code-reviewer` (yin) 和 `samsara:code-quality-reviewer` (quality)"
  - 加入 "Aggregation rule" 段: 兩份都 pass → 推進；任一 fail → fix；只收到一份 → block with error
  - "Never" list 加: "Skip code-quality-reviewer dispatch"
- [ ] Step 6: 修改 dispatch-template.md：
  - 在既有 reviewer template 後加 code-quality-reviewer 的 Agent tool call template
  - 明確標示 "Dispatch both in the same message to enable parallel execution"
- [ ] Step 7: 執行 validation — verify passes
- [ ] Step 8: 寫 scar report
- [ ] Step 9: Commit

## Expected Scar Report Items

- Potential shortcut: 只改 SKILL.md 沒同步改 dispatch-template.md，導致指令正確但 template 誤導
- Potential shortcut: 寫 "dispatch both" 但沒強調 parallel，agent 可能 sequential 跑導致 wall-clock 加倍
- Potential shortcut: 忽略 Aggregation rule 的 "missing reviewer" 分支（認為不會發生）
- Assumption to verify: main agent 能正確 parse 兩份 review output 並 aggregate（需 Task 5 實際驗證）
- Assumption to verify: Claude Code 的 Agent tool 多呼叫在同一 message 確實並行執行（樣本已在 2×2 實驗證實）

## Acceptance Criteria

Covers:
- "Parallel dispatch silent skip" — SKILL.md 的 Aggregation rule section 防止此
- "Success - parallel dispatch returns both results" — SKILL.md + template 的共同支撐
