# Task 4: iteration structural_drift 聚合 + validate-and-ship reconciliation 結構維度與 0-dangling 終局抽查

## Context

Read: overview.md

本 task 建立「驗屍」環節。前置事實（task-3 已完成，此處直接給定）：
- spec-mode code-quality-reviewer 每 task 輸出 `drift_items`（三類：`undeclared_boundary`/`violated_boundary`/`abandoned_commitment`；顯式空陣列 = 查過無漂移；**欄位缺失 = 未檢查**）
- `changes/<feature>/structure-spec.yaml` 的 evidence ref 為 typed（`planned_task` → index.yaml task id；`git_history` → repo 路徑；`domain_boundary` → `machine_verifiable: false`）

本 task 的規則（pre-thinking D5 + KD-4 定案）：
1. **iteration Step 1 擴充**：聚合各 task reviewer 輸出的 drift_items → `structural_drift` 計數，**與 signal_lost 並列，不混計**（兩個訊號各自獨立報告）。drift_items 欄位缺失的 task → 列為 parse failure（比照 scar report 解析失敗語意：不准靜默 skip，unknown ≠ 不需要 iteration）。
2. **validate-and-ship reconciliation 擴充**（現行第 5 步「實際行為 vs spec 漂移」加上結構維度）：structure-spec.yaml 承諾的邊界 vs 實作最終狀態的 feature 級對照，輸出結構漂移清單（可為顯式空）。
3. **validate-and-ship 0-dangling 終局抽查**：解析 structure-spec.yaml 全部 evidence refs（三態：resolved / dangling=failure 列明細 / 解析基礎不可讀=unknown 過 gate）。任何 dangling = blocking finding（DC-1 終局防線）。exempt_poc 或 spec 不存在的 feature → 此步驟記錄 `structure_spec: absent/exempt` 後跳過，與漏做可區分。
4. 兩處都不新開章節：iteration 嵌入 Step 1 既有聚合流程；validate-and-ship 嵌入既有 reconciliation（第 5 步）與 failure budget review（第 1 步，0-dangling 併入其 systemic_ref 解析段落旁）。

減法紀律：兩檔合計淨增 ≤ 40 行。

## Files

- Modify: `skills/iteration/SKILL.md`（Step 1 加 structural_drift 聚合與 drift 欄位缺失 = parse failure）
- Modify: `skills/validate-and-ship/SKILL.md`（第 5 步 reconciliation 加結構維度；第 1 步旁加 0-dangling 終局抽查）
- Modify: `tests/test_skills/test_structure_spec_contract.py`（追加測試類，檔已存在）

## Death Test Requirements

追加到 `tests/test_skills/test_structure_spec_contract.py`：

- Test: iteration SKILL.md 必含「structural_drift 與 signal_lost 並列不混計」語句（混計會讓兩訊號互相污染）
- Test: iteration SKILL.md 必含「drift_items 欄位缺失 → parse failure」語句（DC-5 消費端語意）
- Test: validate-and-ship SKILL.md 必含 0-dangling 抽查的三態語句與「dangling = blocking」（DC-1 終局防線）
- Test: validate-and-ship SKILL.md 必含 `absent/exempt` 記錄語句（跳過與漏做可區分）

## Unit Test Contract

- Contract source: **documented artifact shape** —— 兩個 SKILL.md 的具名聚合/抽查規則語句（structural_drift 並列、parse failure 語意、三態抽查、absent/exempt 記錄）。測試斷言文件化語句存在，不斷言實作細節。

## Implementation Steps

- [ ] Step 1: Write death tests（上列 4 項）
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: structural_drift 目前只計數不設閾值（iteration 進入判準不因它改變）—— 第一版刻意不動 implement Transition 的進入判準（單一擁有者在 implement SKILL.md），記錄此邊界避免下游誤以為 drift 會觸發 iteration
- Assumption to verify: reviewer 輸出的持久化位置（drift_items 存在哪個 artifact 供 iteration 聚合）—— 若只在對話中，聚合無來源；需與 task-3 的輸出格式對齊，缺了記 assumption
- Potential shortcut: 0-dangling 抽查是「全量解析」還是「抽樣」—— 名為抽查實為全量（spec entries 數量小），寫死全量並記錄

## Acceptance Criteria

- Covers: "Silent failure - cargo-cult 證據通過審查"（終局防線）
- Covers: "Silent failure - drift 欄位缺失被讀作零漂移"（消費端語意）
