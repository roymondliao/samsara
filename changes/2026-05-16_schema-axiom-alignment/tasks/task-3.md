# Task 3: Sync vocabulary in remaining skills

## Context

Read: `../overview.md` 與 `../2-plan.md`

依 task-1 已完成的 enum 定義，把新詞彙同步進剩下的 4 個 skill：
- `validate-and-ship` (3 files)
- `codebase-map` (2 files)
- `debugging` (1 file)
- `iteration` (1 file)

主要改動：`silent_failure_surface` 計算邏輯精確化（明寫此欄位只計 silent_failure，不含 boundary_fail）；或新增 `boundary_fail_surface` 作為 parallel 維度（由本 task 決定）。

## Files

- Modify: `skills/validate-and-ship/ship-manifest.md` — `silent_failure_surface` 註解精確化；補充 boundary_fail 評估方向
- Modify: `skills/validate-and-ship/templates/ship-manifest.yaml` — schema 同步
- Modify: `skills/validate-and-ship/SKILL.md` — prose 中 silent failure / death_path 字眼更新
- Modify: `skills/codebase-map/SKILL.md` — `silent_failure_surface` 計算邏輯文案精確化
- Modify: `skills/codebase-map/templates/codebase-map.yaml` — schema 同步
- Modify: `skills/debugging/templates/fix-summary.yaml` — `silent_failure_conditions` 註解更新
- Modify: `skills/iteration/SKILL.md` — vocabulary 同步
- Test: 死路測試在 task-7 整合，本 task 內 grep 自我驗證

## Death Test Requirements

- Test: `grep -rn "death_path" skills/{validate-and-ship,codebase-map,debugging,iteration}/` 必須回傳 0 matches
- Test: `grep "silent_failure" skills/validate-and-ship/ship-manifest.md` 必須回傳 ≥1 match（保留意指明確 silent failure 的場合）
- Test: `grep -i "boundary.fail\|boundary_fail" skills/validate-and-ship/ship-manifest.md` 必須回傳 ≥1 match（新軸提及）
- Test: `grep -i "boundary.fail\|boundary_fail" skills/codebase-map/SKILL.md` 必須回傳 ≥1 match

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——故意在 staging file 寫「all death paths must be covered」這類 prose，驗證 grep 規則能否抓到無 type 前綴的死路用語
- [ ] Step 2: 改 `validate-and-ship/ship-manifest.md` 中 `silent_failure_surface` 註解：明寫「此計算只計 silent_failure（system 啟動後死亡）。boundary_fail 不計入此 surface，因為它是 user-facing 立即可見的 failure，不屬於 silent rot」
- [ ] Step 3: 在 `ship-manifest.md` 與 `ship-manifest.yaml` 加可選 `boundary_fail_surface` 欄位（low/medium/high；用於評估 system boundary 設計健康度）
- [ ] Step 4: 改 `validate-and-ship/SKILL.md` 中 prose 提及 death_path / silent failure 為唯一死路類別之處
- [ ] Step 5: 改 `codebase-map/SKILL.md` `silent_failure_surface` 計算邏輯文案——精確化計入範圍
- [ ] Step 6: 同步 `codebase-map/templates/codebase-map.yaml`
- [ ] Step 7: 改 `debugging/templates/fix-summary.yaml` — `silent_failure_conditions` 註解加說明「若 fix 屬於 boundary_fail 類別，請改記於 boundary_fail_conditions（同樣 list 結構）」
- [ ] Step 8: 改 `iteration/SKILL.md` aggregation 邏輯文案（涉及 count silent_failure_conditions 處需擴充至 boundary_fail_conditions）
- [ ] Step 9: 跑上述 4 條 grep 死路測試——確認全綠
- [ ] Step 10: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 11: 寫 scar report → `../scar-reports/task-3-scar.yaml`

## Expected Scar Report Items

- Potential shortcut: 7 個檔案改動範圍可能落差很大——某些檔案只需小幅措辭更新，某些（如 SKILL.md）需重寫整段。可能略過某些「看似不需改」的小幅措辭點
- Potential shortcut: iteration/SKILL.md 中的 aggregation 公式可能用 silent_failure_conditions 為單一變量名——改用新雙欄位後公式可能變複雜，誘惑寫「總和兩欄位」而非「分別 surface 計算」
- Assumption to verify: 是否所有 skill 都應該採「並列雙欄位」而非「unified typed list」？本 task 預設「保留並列」（與 task-2 一致）。若 task-3 執行中發現某 skill 自然傾向 typed list（例如 iteration aggregation），標記為 cross-task 不一致候選
- Assumption to verify: `boundary_fail_surface` 作為新欄位是否需要 corruption signature？參考 1-kickoff.md 「boundary-fail 比例 > 30% 警告」——可能在 ship-manifest.md 明寫此 threshold

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - partial migration leaves cross-doc schema drift"（本 task 與 task-2 共同覆蓋）
- Covers: "Degradation - 部分 skill prose 殘留舊 vocabulary 但 type 欄位已更新"
- Covers: "Boundary fail - task 執行時發現需改 samsara_cli 程式碼"（本 task 風險最高——若 ship-manifest schema 改動觸發 parser，必須立即停下）
