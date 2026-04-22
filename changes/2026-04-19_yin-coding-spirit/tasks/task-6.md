# Task 6: Extend fast-track Step 4 checklist for quality symmetry

## Context

Read: overview.md

`samsara:fast-track` 是低風險小改動（< 100 行）的簡化 workflow，Step 4 做 "Quick Review + Ship"。問題：目前的 inline checklist 只有 `能刪？命名說謊？`——這兩個是 **yin 問題**，**完全沒有 code-quality 問題**。

此 task 不 dispatch code-quality-reviewer subagent（會破壞 fast-track 的 "fast" 本質），而是**對稱化 Step 4 的 inline checklist**：main agent 自審時同時問 yin 面和 quality 面的問題。Quality 問題 pick 自 **8 outcome criteria (C1-C8)**，不是從 9 principles 抽象層——outcome 層問題更適合 inline quick check（例如「結構明確？」比「有沒有違反 Cohesion 的共同死亡的權利？」更能在 fast-track 節奏下被真的檢查）。挑 3-4 條，不是全部 8 條。

同時更新 `fast-track.yaml` output schema，加入 `quality_checklist:` 欄位，記錄 main agent 實際檢查了哪些 quality criteria。這讓 fast-track 的 quality 覆蓋可被後續 audit。

關鍵設計約束：
- **不 dispatch subagent**——保持 fast-track 的 inline 本質
- **不塞全部 8 條**——fast-track 的 "fast" 取決於 review 時間；8 條全檢查 = 走回 full path
- **Quality 問題要有選擇性**——對小改動最相關的 criteria 優先（reuse、結構、優雅、冗餘；extensibility 和 maintainability 對 < 100 行改動相關性較低）

## Files

- Modify: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/skills/fast-track/SKILL.md`
  - Line ~71-76 (Step 4: Quick Review + Scar Tag + Ship section) — 擴充 checklist
  - Line ~77-82 (Yin-Side Constraints section) — 加一條 quality coverage constraint
  - Line ~85-99 (Output section, fast-track.yaml template) — 加 `quality_checklist:` 欄位

Reference (read, do not modify):
- `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/references/code-quality.md`（Task 1 產出 — quality questions 的來源）

## Death Test Requirements

- **Symmetry test**: Step 4 的 checklist 必須同時包含 yin 問題（至少 2 條: "能刪？" "命名誠實？"）和 quality 問題（至少 3 條，from 8 outcome criteria C1-C8）
- **Selection rationale test**: checklist 必須明述為什麼選這 3-4 條 quality 問題（對小改動的相關性），避免未來維護者隨意增減
- **Template field test**: `fast-track.yaml` output schema 必須包含 `quality_checklist:` list，實際 fast-track 使用時必須填入檢查的 criteria
- **Reference link test**: SKILL.md 必須在 quality 問題處明述「完整 criteria 見 samsara/references/code-quality.md」，不自建 criteria list
- **Fast-check test**: checklist 的 quality 部分**不得超過 4 條**——超過就等於走 full review，違反 fast-track 設計
- **No subagent dispatch test**: Step 4 中不得出現 `Agent tool` 或 `dispatch code-quality-reviewer` 等 subagent 觸發字眼（fast-track 是 main agent inline review）

## Implementation Steps

- [ ] Step 1: 讀現有 `samsara/skills/fast-track/SKILL.md`，確認 Step 4 + Yin-Side Constraints + Output section 的精確位置
- [ ] Step 2: 讀 Task 1 產出的 `samsara/references/code-quality.md`，挑選 3-4 條對「小改動」最相關的 criteria
- [ ] Step 3: 寫 validation shell `tests/samsara/code-quality-reviewer/fast-track-checklist.sh` 檢查 Step 4 含 quality questions + fast-track.yaml schema 含 quality_checklist
- [ ] Step 4: 執行 validation — verify fails
- [ ] Step 5: 修改 Step 4 section：
  - 保留 "能刪？命名說謊？" 兩條 yin 問題
  - 加入 3-4 條 quality 問題（建議 from: reuse、結構明確、優雅邏輯、無冗餘）
  - 明述「完整 8 條見 samsara/references/code-quality.md；此處選此 3-4 條因為小改動的典型品質風險」
- [ ] Step 6: 修改 Yin-Side Constraints section，加入：「Quality symmetry — fast-track 的 review 必須同時檢查 yin 和 quality 兩面，不可只問其中一面」
- [ ] Step 7: 修改 Output section 的 fast-track.yaml template，加入：
  ```yaml
  quality_checklist:
    - criterion: "<criterion name from 8>"
      checked: true | false
      note: "<what was observed>"
  ```
- [ ] Step 8: 執行 validation — verify passes
- [ ] Step 9: 寫 scar report — 特別 note 挑選哪 3-4 條 criteria 的 rationale
- [ ] Step 10: Commit

## Expected Scar Report Items

- Potential shortcut: 直接抄 code-quality.md 全部 8 條進 fast-track，破壞 "fast" 本質
- Potential shortcut: 把 "能刪？" 這種 yin 問題解讀為 quality 問題來湊數，而不是真的加 quality 問題
- Potential shortcut: `quality_checklist:` 欄位變成填字遊戲——main agent 不真檢查就填 true（corruption signature 和正式 reviewer 相同）
- Assumption to verify: 挑選的 3-4 條 criteria 對「真實的小改動類型」（bug fix、config、dep update、small refactor）都相關——不同改動類型可能需要不同子集
- Assumption to verify: `quality_checklist:` 會被使用者/audit 真的讀到——若沒人讀，此欄位只是形式

## Acceptance Criteria

Covers:
- "Silent failure - fast-track review checks yin but not quality" (death path 7, to be added to acceptance.yaml)

Does NOT cover（這是 feature 的 known limitation）:
- fast-track 的 inline review 本質上**無法**像 subagent reviewer 那樣嚴格，它依靠 main agent 的自律
- 若 corruption signature 出現（fast-track commits 被人工標為 junior-level），需要重新評估是否要升級為 subagent dispatch（這是 Task 6 之外的後續決策）
