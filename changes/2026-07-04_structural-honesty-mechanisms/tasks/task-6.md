# Task 6: Primary evaluator 執行 — mini-feature 證據鏈四環節演練 + evaluation-result.md

## Context

Read: overview.md

本 task 是 pre-thinking Evaluation Contract 的 Primary evaluator 本體，不是額外發明的成功標準。機制（task 1-5）已全部落地，現在用一個**小型真實 feature** 走完 spec path，檢查證據鏈四環節是否全部可觀測。

**Mini-feature 選擇準則**：真實（不是 mock 目錄）、小（1-2 tasks）、觸及至少一個結構決策（否則 structure_refs 全空，環節 2/3 驗不到）。候選：本 repo issue.md / roadmap.md 中一個小項，或一個真實小改進 —— 由執行者依當下 repo 狀態挑選並記錄選擇理由。禁止：為演練而發明無存在理由的假需求（違反公理——演練 feature 本身也要能回答「消失了什麼會痛」）。

**證據鏈四環節（Evaluation Contract 原文）**：
1. **生成**：`changes/<mini-feature>/structure-spec.yaml` 存在且全部 evidence refs 0 dangling（typed ref 逐條機器解析：`planned_task` → index.yaml、`git_history` → repo 路徑）
2. **注入**：task-N.md 含 `structure_refs` 欄位；dispatch 記錄含對應 spec 片段
3. **消費**：reviewer verdict 引用 spec entry id 並含顯式 `drift_items`（可為空陣列但欄位必在）
4. **驗屍**：reconciliation 輸出含結構維度對照

**Pass**：四環節全部可觀測且 0 dangling。**Fail**：任一環節缺失、任一 dangling、或 verdict 未引用任何 spec id。
**Feedback loop（fail 時）**：缺失環節 → 對應 skill 段落回修（生成→planning SKILL；注入→implement dispatch-template；消費→code-quality-reviewer agent；驗屍→validate-and-ship reconciliation），修正後**重跑同一 mini-feature** 檢查。

## Files

- Create: `changes/<mini-feature>/`（完整 workflow artifacts —— 走真實 samsara workflow 產生，不是手寫模擬）
- Create: `changes/2026-07-04_structural-honesty-mechanisms/evaluation-result.md`（四環節檢查結果：每環節的證據位置、pass/fail、dangling 明細或 0、發現的機制缺陷與回修記錄）

## Death Test Requirements

本 task 的「death test」即檢查本身的反向驗證（先證明檢查會抓到壞的）：

- Test: 在檢查器邏輯確定前，人為構造一個 dangling ref（指向不存在的 task id），確認四環節檢查會回報 failure 而非 pass —— 檢查器抓不到人為壞例 = 檢查器是瞎的，先修檢查邏輯
- Test: 人為移除一個 task 的 structure_refs 欄位，確認環節 2 檢查回報缺失

（兩個壞例驗證後還原，再跑正式演練。）

## Unit Test Contract

- Contract source: **documented artifact shape** —— Evaluation Contract 寫定的四環節可觀測條件（pre-thinking.md 原文）。evaluation-result.md 逐環節斷言 artifact 實際內容，不斷言演練過程的主觀品質。

## Implementation Steps

- [ ] Step 1: 反向驗證（兩個人為壞例，確認檢查會紅）
- [ ] Step 2: 還原壞例
- [ ] Step 3: 選擇並記錄 mini-feature（含存在理由）
- [ ] Step 4: 以 spec path 走完 mini-feature workflow（research 可精簡但 planning 起必須真實走）
- [ ] Step 5: 執行四環節檢查
- [ ] Step 6: Fail → 依 feedback loop 回修對應 skill → 重跑（記錄每輪）
- [ ] Step 7: Write evaluation-result.md + scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: mini-feature 選得太小以致 structure_refs 全空 —— 環節 2/3 空轉通過（形式 pass 實質未驗）；選擇準則已防，若仍發生如實記錄並換 feature 重跑
- Assumption to verify: 「dispatch 記錄」的可稽核位置（延續 task-2 的 scar item）—— 演練是第一次實測此環節可觀測性的機會
- Potential shortcut: 演練由同一個 agent 身兼執行者與檢查者 —— 自我評分偏誤；檢查步驟盡可能逐條引用 artifact 原文而非總結

## Acceptance Criteria

- Covers: "Success - mini-feature 證據鏈四環節（Primary evaluator）"
