# Problem Autopsy: workflow-subtraction-optimization

## original_statement

> 1. 關於 scar report 如何可以減少不必要產出或是有什麼可以優化的方向
> 2. 對於 changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md 的設計有什麼可以改進的？或是刪減的？
> 3. 整個 samsara 的 workflow 根據減法原則，有哪些部分是可以優化的？
>
> （後續指令）我們先對 1, 2, 3 部分開一個 branch 來優化處理

## reframed_statement

對 samsara 框架本身執行一次減法工程：把 scar report 的訊噪比拉回來（過濾規則 + schema 調整）、把 pre-thinking 重設計文件的開放項定案並刪掉自相矛盾的機制、把 workflow 中「消失了沒人會痛」的重複結構移除——同時保證所有既有守護行為（death tests、gate 語義、auto-mode 決策紀錄）不因減法而消失。

## translation_delta

```yaml
translation_delta:
  - original: "如何可以減少不必要產出或是有什麼可以優化的方向"
    reframed: "實作 codebase review 中提出的四項 scar 優化（systemic registry、verified:true 壓縮、narrative 約束、expiry 二選一）"
    delta: "user 問的是『方向』，agent 給了具體方案清單，user 以『對 1,2,3 開 branch 優化處理』接受——方案清單從建議升格為工作範圍。若 user 對個別方案有保留，需在 pre-thinking gate 攔截。"
  - original: "有哪些部分是可以優化的"
    reframed: "六個 must-have + 三個 nice-to-have，其中雙 reviewer 合併與 security-review 折入被降級為『先取證/待決策』"
    delta: "review 清單裡各項的證據強度不一。agent 自行做了分層（確定執行 vs 待評估），這個分層本身是一個未經 user 確認的判斷——已顯式標記在 kickoff 的 scope 中，供 gate 時挑戰。"
  - original: "根據減法原則"
    reframed: "north star 定為 instruction surface 下降 >=12% 且 death tests 全綠"
    delta: "user 沒有給量化目標；12% 是 agent 從 Auto Mode Gate 去重（~400 行）+ 其他項估算的下限。這個數字是推導不是需求，若不合理應在 pre-thinking 修正。"
  - original: "開一個 branch 來優化處理"
    reframed: "單一 branch feature/workflow-subtraction-optimization、單一 changes/ feature 目錄承載三個方向"
    delta: "三個方向彼此獨立可分批交付（W4 是純文件修訂、W1-W3 是 schema/skill 改動）。單一 feature 目錄意味著單一 Evaluation Contract 要涵蓋異質產出——這是 pre-thinking 需要對齊的設計決定。"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "scar 膨脹的根因被證實在 implementer 的行為層（prompt 誘導長篇輸出）而非 schema 層"
    rationale: "若 implementer agent 定義本身鼓勵冗長（如 Report Format 要求逐項覆述），改 schema 只是治標——膨脹會換個欄位再長回來。動工前需確認根因層級，必要時改 agent 定義而非 schema。"
  - condition: "Auto Mode Gate 去重後，任何一個 skill 的 auto-mode 行為無法只靠指針段落 + references/auto-mode.md 完整重建"
    rationale: "去重的前提是 reference 真的 canonical。若各 skill 的 gate 有不可歸一的階段特異行為（如 validate-and-ship 的雙重 trace check），強行去重會把特異行為靜默抹掉——該 skill 應保留完整段落，去重範圍縮小而不是硬上。"
  - condition: "雙 reviewer 的 changes/ 歷史顯示兩者曾各自攔截對方沒攔到的 Critical"
    rationale: "N1 的合併只有在『分開不曾產生額外攔截』時才成立。有反例就放棄合併，missing-reviewer 協議雖繁但有主。"
  - condition: "0-design-direction.md 的擁有者（user）打算在近期直接進入 pre-thinking 正式重寫"
    rationale: "W4 修訂的是設計文件；若重寫工程即將啟動，修訂應併入重寫的 research 而非獨立進行，避免同一設計在兩個工作流中演化。"
  - condition: "減法導致任一 death test 需要被刪除或弱化才能通過"
    rationale: "north star 的 invalidation condition：行數不是目的。守護行為的消失即為整個方向的失敗訊號，立即停止並回退。"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "本次實作（以及 CI）"
    cost: "skills 大改 → dist/codex/ 全量 regenerate、doc-contract 測試（tests/ 下 732 個中的 skill-presence 類）需同步修改。減法工程的第一批 diff 反而很大。"
  - who: "讀歷史 scar 的未來 session"
    cost: "新舊 scar 格式並存。iteration/validate-and-ship 的聚合邏輯必須同時解析兩代格式（延續 schema rule 8 的 backward-compat 精神），否則舊 feature 的 signal_lost 靜默歸零。"
  - who: "auto mode 使用者"
    cost: "Gate 去重後 gatekeeper 的 dispatch 語境變薄。若指針段落漏掉『本階段哪些決策點過 gate』，auto run 會靜默跳過本該記錄的決策——這是去重的第一個腐爛點。"
  - who: "習慣現有節奏的 human-in-the-loop 使用者"
    cost: "W5 讓 iteration 預設 skip——習慣被詢問的使用者會失去一個介入點。緩解：skip 時仍輸出一行『signal_lost=N、無 cross-task pattern，已 skip iteration』讓決策可見可推翻。"
```

## observable_done_state

改動合併後：任一新 feature 走完 implement，其 scar reports 平均行數 ≤70 且 `signal_lost` 所需的全部欄位仍在；9 個 SKILL.md 的 Auto Mode Gate 各縮為 ≤8 行指針且 auto-mode 測試全綠；`0-design-direction.md` 的四個開放項（交棒格式、輕想存廢、少數意見安全網、健康指標 owner）各有寫入文件的決定與理由。未解決狀態的可觀測特徵：scar 裡仍能 grep 到跨 feature 重複的「doc-presence ≠ runtime obedience」全文重述、任兩個 SKILL.md 的 Auto Mode Gate 段落 diff 相似度仍 >80%。
