# Task 1: Define new enum schema in planning templates

## Context

Read: `../overview.md` 與 `../2-plan.md`

本 task 是整個 feature 的 foundation——定義新 enum 的 single source of truth。後續所有 task (2~7) 依賴此 task 完成的 enum 定義。

新 enum: `type: silent_failure | boundary_fail | degradation | happy_path`

- `silent_failure`: system 啟動後死亡（看起來活著實際在說謊）
- `boundary_fail`: system 啟動前死亡（user 立即知道、user 該負責）
- `degradation`: fallback 啟動但未明確標記為降級
- `happy_path`: 成功 with 證據鏈

完全刪除 `type: death_path`，不保留任何 backward-compat alias（依 1.6-recalibration G1 決議）。

## Files

- Modify: `skills/planning/templates/acceptance.yaml` — 改寫 enum 範例為 silent_failure + boundary_fail 兩個 type 區塊
- Modify: `skills/planning/death-first-spec.md` — 重寫 Ordering Rule 與 enum 定義
- Modify: `skills/planning/templates/overview.md` — Death Cases Summary 措辭精確化（沒有強制 vocabulary 改動但需 review）
- Modify: `skills/planning/SKILL.md` — 更新任何提到 `death_path` 或描述 silent failure 為唯一死路的 prose
- Modify: `skills/planning/task-format.md` — 更新 Death Test Requirements 範例使用新 enum
- Test: `tests/cross_doc_grep.sh`（由 task-7 撰寫）— 本 task 不寫測試 script，但本 task 的死路測試項目會被納入 task-7

## Death Test Requirements

本 task 完成後必須通過以下死路測試（task-7 會把這些納入腳本）：

- Test: `grep -r "type: death_path" skills/planning/` 必須回傳 0 matches
- Test: `grep "silent_failure" skills/planning/templates/acceptance.yaml` 必須回傳 ≥1 match
- Test: `grep "boundary_fail" skills/planning/templates/acceptance.yaml` 必須回傳 ≥1 match
- Test: `grep "silent_failure" skills/planning/death-first-spec.md` 必須回傳 ≥1 match（含定義）
- Test: `grep "boundary_fail" skills/planning/death-first-spec.md` 必須回傳 ≥1 match（含定義）
- Test: `grep -i "death.path" skills/planning/SKILL.md` 必須回傳 0 matches（prose 也不能殘留）

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——在臨時文件放 `type: death_path` 字串，驗證 grep 規則能抓到
- [ ] Step 2: 改寫 `acceptance.yaml` template，按 2-plan.md Schema Delta Examples 的 After 結構
- [ ] Step 3: 改寫 `death-first-spec.md` — 重新定義 Ordering Rule、Format、Example 三節。確保兩個新 type 都有明確定義 + given/when/then 範例
- [ ] Step 4: 改 `overview.md` template 中「Top 3 most dangerous silent failure paths」措辭，改為「Top 3 most dangerous failures (silent_failure or boundary_fail)」
- [ ] Step 5: 全文 grep 修正 `SKILL.md` 與 `task-format.md` 中所有 `death_path` 字眼
- [ ] Step 6: 跑上述 6 條 grep 死路測試——確認全綠
- [ ] Step 7: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 8: 寫 scar report → `../scar-reports/task-1-scar.yaml`
- [ ] Step 9: 不要 commit（依 implement skill：所有 task 完成後一次 commit）

## Expected Scar Report Items

- Potential shortcut: 改 `overview.md` 措辭時可能只改 visible 段落，忽略 template comment 中的舊用語——必須完整全文檢視
- Potential shortcut: `death-first-spec.md` 既有 example 是 user-authentication，重寫時可能延用舊 case，導致範例的 type 是新的但語意框架仍是舊的
- Assumption to verify: 新 enum 是否需要在 schema 加 type field validation 規則？本 task 預設「不加 parser 規則，僅 prose 約束」——若日後發現需要 parser 層 enforce，視為 task 範圍設計失敗
- Assumption to verify: `silent_failure` 與舊 `death_path` 語意是否完全等價？預設「是」——若發現有舊 case 不歸 silent_failure 也不歸 boundary_fail，回 Planning

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - partial migration leaves cross-doc schema drift"（本 task 是潛在觸發點，但完成後須與 task-2 配合驗證）
- Covers: "Boundary fail - acceptance.yaml type 欄位使用未定義 enum 值"（本 task 定義合法 enum）
- Covers: "Happy path - acceptance.yaml self-bootstrap 驗證"（本 task 完成後新 enum 即可供本 feature 自身的 acceptance.yaml 使用）
