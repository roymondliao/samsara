# Task 8: 最終對帳 — dist regenerate + 全測試 + 三段式檢核執行與記錄

## Context

Read: overview.md

前七個 task 完成後的收攏：重新生成 dist/codex/（skills 大改後的生成物同步）、跑全測試、執行 Primary evaluator（三段式檢核）並留下證據鏈。行數目標依 Contract Amendment 的 user 決定（預設 A：淨減 ≥300 行；基線 6,356 行，量測命令見下）。

## Files

- Regenerate: `dist/codex/`（`source .venv/bin/activate && uv run samsara-cli convert --platform codex`；folded security skill 的舊目錄 `dist/codex/.agents/skills/samsara-security-privacy-review/` 必須消失）
- Create: `changes/2026-07-02_workflow-subtraction-optimization/evaluation-result.md` — 三段檢核的證據鏈：
  - 第一段：pytest 輸出摘要（passed 數）＋ `git diff --stat main...HEAD -- tests/` 與逐檔說明（每個被修改的既有測試：斷言目標同步 vs 弱化的判定）
  - 第二段：行數對照表——基線命令 `find skills -name "*.md" -not -path "*/templates/*" | xargs wc -l; wc -l agents/*.md references/*.md`（基線合計 6,356）vs 改後同命令 ＋ 新增檔（`.samsara/systemic-scars.yaml`、新測試檔不計入指令面積但列出）；淨減值與目標比對；搬家檢查：references/ 增量 vs skills 減量明細
  - 第三段：逐項可觀測條件核對表（acceptance.yaml happy path 的清單，逐條附證據指標）
- Verify: `uv run samsara-cli validate --platform codex` 通過

## Death Test Requirements

- 本 task 不寫新死測；它**執行**死測。三態誠實輸出：任一段量測無法執行（如基線命令因檔案結構變動失真）→ 該段記 `unknown`（blocked_by_evaluator），不得記 pass。
- 檢核發現 fail 時依 Evaluation Contract feedback loop：定位對應 task 的變更，修正或回退後重跑；不得為過檢核刪弱測試。

## Unit Test Contract

- Contract source: 文件化 artifact shape——evaluation-result.md 必須含三段各自的：執行命令原文、輸出證據、pass/fail/unknown 判定。缺任一段或任一段無命令原文 ＝ 本 task 未完成
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: regenerate dist/codex ＋ validate
- [ ] Step 2: 全測試（`uv run pytest`）
- [ ] Step 3: 執行三段檢核，逐段記錄命令與輸出
- [ ] Step 4: 寫 evaluation-result.md（三態判定）
- [ ] Step 5: Write scar report
- [ ] Step 6: Report back (do not commit)

## Expected Scar Report Items

- Assumption to verify: dist/codex 的 CI snapshot 測試（2026-05-26_ci_snapshot_version_drift 引入）在 regenerate 後綠——若紅，判斷是 snapshot 該更新還是 converter 行為回歸
- Potential shortcut: 行數淨減若落在目標邊緣（±10%），記錄各 task 的貢獻明細供 user 在 validate-and-ship 判斷，不自行放寬
- Assumption to verify: 基線 6,356 在 task 執行期間未被本 feature 以外的 commit 改變（若有，重測基線並記錄）

## Acceptance Criteria

- Covers: "Success - 三段檢核全過"
- Covers: "Silent failure - 搬家假減法"
