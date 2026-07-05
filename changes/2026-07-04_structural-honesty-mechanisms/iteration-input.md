# Iteration Input: structural-honesty-mechanisms（feature 級回顧 —— iteration 階段的候選清單）

本檔為 task 1-6 review 歷程累積的 cross-task 觀察的 durable 落地處（自 evaluation-result.md 遷出 —— 該檔的契約職責是四環節檢查報告）。**每項標記 grounding 狀態**：`durable` = 有 repo 內 artifact 佐證；`session-memory` = 僅存在於本 session 對話/transcript，接手者應視為待驗證線索而非既定事實。

## 候選 1：Domain router gap（cross-task pattern）

- 主張：code-reviewer 的 domain router 對 skill/agent markdown 無路由，依 dispatch 錨點措辭與先例運作；本 feature 期間三次現身。
- Grounding：
  - 現身 3（task-4 yin 首派硬 UNKNOWN 後重派）：**durable** —— `index.yaml` task-4 review 欄明文記錄。
  - 現身 1（task-3 yin 的 domain-routing caveat）與現身 2（task-3 quality 的 router 觀察）：**session-memory** —— reviewer 原文在 session transcript，未摘錄至 repo。
- 建議 triage：fix（可能形式：`references/` 增 skill-definition domain 或 router 顯式列出 markdown 類的處置）。

## 候選 2：自我回報數字失準模式（implementer 與 coordinator 皆發生）

- 主張：implementer 側 task-1（11 vs 9）、task-2（28 vs 27）、task-3 前三度發生（dispatch 內建 `--collect-only` 要求後止血）；**coordinator 側** task-6 dispatch 寫入未實測的「spec 30 行」（實際 25），被 verdict 繼承後由 round-2 yin review 抓出。
- Grounding：implementer 側三例 **session-memory**；coordinator 側一例 **durable** —— `changes/2026-07-05_issue-002-validate-live-surface/review-record.md` 轉錄註記。
- 建議 triage：fix（把「報數前實測」寫進 `agents/implementer.md` 定義；coordinator 側同理 —— dispatch 模板的量化欄位標注「實測值」要求）。

## 候選 3：KD-5 儀式淨增量超標

- 主張：217/200 行，超標 17。
- Grounding：**durable** —— `scar-reports/task-5-scar.yaml` 首項（含逐檔明細，量測可重現，yin 已獨立重現）。
- 建議 triage：iteration 裁決 —— 修剪 vs 以證據調整預算（acceptance 的該 scenario 目前為 fail）。

## 候選 4：dispatch-record durability 缺口

- 主張：注入片段只活在 transcript；scar echo 證明「聲稱收到」不證明內容正確。
- Grounding：**durable** —— `scar-reports/task-2-scar.yaml` 與 `scar-reports/task-6-scar.yaml` 同源條目；task-6 的 ring-3 個案已以 `changes/2026-07-05_issue-002-validate-live-surface/review-record.md`（verdict 原文摘錄）緩解，但通用機制未定。
- 建議 triage：fix 或 accept + re_review_signal（可能形式：dispatch-template 加「verdict 摘錄入 feature dir」的 durability 慣例）。
