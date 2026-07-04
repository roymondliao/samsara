# Plan: workflow-subtraction-optimization

## Pre-thinking Commitments Consumed

- **Decision:** Proceed
- **Accepted gaps:** none
- **System design constraints（Step B 決定）:**
  1. codebase map 標記 stale 續行；重建留到本 feature skills 改完後
  2. security-privacy-review 折入 validate-and-ship 成第 0 步 STOP gate
  3. 雙 reviewer 保留，不合併、不加觀測點（移出 scope）
  4. expiry 欄位刪除；ship-manifest rule 2 改為訊號驅動重審（誰在什麼訊號出現時重審）
  5. systemic-scar registry 放 `.samsara/systemic-scars.yaml`，scar 以 `systemic_ref` 引用
  6. iteration 進入判準：cross-task pattern 或 signal_lost ≥ 5，否則預設 skip ＋ 可推翻紀錄
  7. 0-design-direction.md 修訂含六項（含刪第一步成熟度分類）
  8. implement 的 UI 清單措辭：index.yaml 唯一 truth，TaskCreate 盡力投影
- **Primary evaluator:** 三段式檢核程序（測試全綠且 death tests 無刪除弱化／指令面積淨減且無搬家假減法／逐項可觀測完成條件）
- **Pass signal:** 三段全部成立
- **Fail signal:** 任一段不成立
- **Feedback loop:** 定位失敗段對應的 must-have，修正或回退該項後重跑；不得為過檢核而刪弱測試

### Contract Amendment（已定案 2026-07-03）

Planning 實測推翻原推導數字：精確基線 **6,356 行**（kickoff 的 5,643 漏算 skills 支援檔）；Auto Mode Gate 七段合計僅 **203 行**（原估 ~400 偏高）；誠實可達淨減量 ≈ 325 行 ≈ 5%，原「≥12%」不可達。**User 決定：「先減少為主」**——第二段改為「淨量必須為負，~300 行為參考值非硬性驗收」；搬家假減法檢查保留為硬性；驗收重量由第一段（測試）與第三段（逐項條件）承擔。pre-thinking Evaluation Contract 已同步修訂。

## I/O — 三態輸出

| 介面 | success | failure | unknown（≠ 任何一態） |
|---|---|---|---|
| 三段式檢核 | 三段成立 | 任一段明確不成立 | 基線量測不可得／git diff 無法判定測試弱化 → `blocked_by_evaluator`，不得當 pass |
| iteration 進入判斷（新） | 判準成立→建議進入 | 判準不成立→skip＋可推翻紀錄 | scar 解析失敗致 signal_lost 不可算 → **不准 skip**，列出 parse failures 過 gate |
| scar 聚合讀 `systemic_ref` | ref 命中 registry | ref 懸空 → 列為 parse failure | registry 檔缺失 → 全部 systemic_ref 標 unknown，不准靜默略過 |
| security gate（折入後） | review pass | fail（列 issues 進 fix loop） | timeout/partial/工具錯 → unknown ≠ pass，過 execution-mode gate |

## Death Cases

| # | 觸發 | 表象（謊言） | 實際 | 偵測 |
|---|---|---|---|---|
| DC1 | 內容從 skill 搬到 reference/新檔 | 行數目標達成 | 淨 loaded-context 未降 | 檢核第二段比較「單 session 載入總行數」淨值 |
| DC2 | Gate 去重時抹掉階段特異行為（validate-and-ship 雙重 trace check、security auto-reject） | 各 skill 都有指針、看似一致 | 特異語義消失 | death tests 釘住特異條款必須 inline 存在 |
| DC3 | 舊格式 scar（plain string／有 expiry_date）進聚合 | 聚合正常結束 | 舊 items 靜默歸零 | fixture 舊格式 death test：舊 items 必須被計入或列為 parse failure |
| DC4 | scar 寫了懸空的 `systemic_ref` | scar 看似已去重 | 引用指向不存在的登記 | 懸空 ref = parse failure 的條款 + death test |
| DC5 | security gate 折入後被當一般步驟跳過，或 unknown 當 pass | 流程走完、manifest 產出 | 未經 security 檢查即 ship | STOP 順序斷言（gate 在 failure budget 之前）＋ unknown≠pass 條款測試 |
| DC6 | scar 解析失敗使 signal_lost 少算 → 誤觸預設 skip | 「無需 iteration」 | system-level rot 漏到 ship | unknown 不准 skip 的條款 + death test |
| DC7 | fast-track 空違規清單 | 「檢查過且乾淨」 | 根本沒檢查 | 空清單必須伴隨 reviewed 聲明行；缺聲明 = 未檢查 |
| DC8 | 0-design-direction 修訂與其第 7/8 節既有決定衝突 | 文件更新完成 | 同文件內自相矛盾 | task 內建交叉核對步驟 + acceptance 條款 |

## Task Decomposition（8 tasks，sequential）

| # | 任務 | 主要檔案 | depends |
|---|---|---|---|
| 1 | Scar 產出瘦身：schema 規則＋systemic registry＋implementer 報告格式 | scar-schema.yaml、`.samsara/systemic-scars.yaml`（新）、scar-report.md、agents/implementer.md、dispatch-template.md、iteration SKILL 聚合段 | — |
| 2 | expiry 移除 → 訊號驅動重審 | iteration SKILL accept 段、ship-manifest.md rule 2、ship-manifest 模板 | — |
| 3 | security-privacy-review 折入 validate-and-ship | validate-and-ship SKILL（新 Step 0）、刪 skills/security-privacy-review/、bootstrap 路由、README×2、implement/iteration 轉場、test helpers stage 表 | — |
| 4 | Auto Mode Gate 去重（6 skills → 指針＋canonical） | references/auto-mode.md、6 個 SKILL.md、tests/test_auto_mode/* | task-3 |
| 5 | iteration 資料驅動進入＋implement 轉場＋UI 清單措辭 | implement SKILL、iteration SKILL | task-3 |
| 6 | fast-track checklist 只記違規 | fast-track SKILL＋模板 | — |
| 7 | 0-design-direction.md 六項修訂 | changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md | — |
| 8 | 最終對帳：dist regen＋全測試＋三段檢核執行記錄 | dist/codex/、evaluation-result.md | 1–7 |

順序註記：3 在 4/5 之前（折入後才去重、轉場才改指向）；其餘依序執行避免同檔衝突（iteration SKILL 被 1/2/5 觸及、validate-and-ship 被 2/3/4 觸及）。

## File Map Consistency Check（對 Key Decisions）

- 「registry 是 repo 層級狀態」→ `.samsara/systemic-scars.yaml` ✅ matches（`.samsara/` 為既有 repo 層級狀態家）
- 「security gate 併入 validation 階段」→ 內容進 `skills/validate-and-ship/SKILL.md`、刪除 `skills/security-privacy-review/` ✅ matches
- 「canonical auto-mode 行為只存在一處」→ 協議進 `references/auto-mode.md`，skills 只留指針 ✅ matches
- 「設計文件修訂屬該 feature 目錄」→ 改 `changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md`，不動 `skills/pre-thinking/` ✅ matches（正式重寫 out of scope）
- 其餘 Key Decisions（訊號驅動重審、資料驅動進入）不約束路徑 → out of scope
- 結論：無 contradicts，通過。
