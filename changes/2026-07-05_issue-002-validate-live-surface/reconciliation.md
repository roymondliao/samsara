# Reconciliation: issue-002-validate-live-surface（結構維度 + 0-dangling 終局抽查）

執行時間：2026-07-05。依 skills/validate-and-ship/SKILL.md 的 Step 1 0-dangling terminal audit 與 Step 5 Structural dimension 規則（本 feature 為 task-6 演練載體，非完整 ship —— 此記錄為驗屍環節的最小完整實體）。

## 0-dangling 終局抽查（referential-integrity，全量非抽樣）

| Entry | Evidence type | Ref | 解析結果 |
|---|---|---|---|
| SS-1 | git_history | issue.md | resolved（檔案存在，ISSUE-002 條目在內） |
| SD-1 | planned_task | task-1 | resolved（index.yaml 含 task-1） |

**結果：2/2 resolved，dangling = 0。** `structure_spec: present`（spec_path: default，非 absent/exempt）。

## Structural dimension（spec-vs-shipped compliance，與上方 referential-integrity 檢查相區分）

structure-spec.yaml 承諾 vs 實作最終狀態：

- SS-1（validator-live-surface-boundary）：**兌現** —— `samsara_cli/validators/target.py:117` 的 `_LIVE_SURFACE_EXCLUDED_TOP_LEVEL_DIRS` frozenset 與 spec 承諾的排除集完全一致；邊界由 12 個測試鎖定（含 docs-site/ 不誤傷、巢狀 changes 不誤排的精確性測試）。spec-mode reviewer 逐 entry 判定 Satisfied（verdict 原文摘錄見同目錄 `review-record.md`）。
- SD-1（單一常數規則）：**兌現** —— grep 證實全 codebase 唯一定義點；main.py 與 converter/engine.py 均經 TargetValidator.validate() 消費，無第二份清單；DTV-3-3 測試鎖定 CLI 與直接呼叫同行為。

structural_drift_final: []
（欄位顯式存在 = 對照已執行且無漂移；此欄位缺失才代表對照從未執行 —— 依 validate-and-ship Step 5 的 missing ≠ empty 語意。與 iteration 的 per-task structural_drift tally 為不同時點的不同量測，未合併。）
