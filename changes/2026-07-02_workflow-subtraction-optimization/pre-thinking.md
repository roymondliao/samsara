# Pre-thinking: workflow-subtraction-optimization

## Session: 2026-07-02T00:00:00+08:00

Execution mode: human-in-the-loop

## Step A — Design and Gap Map

### Atomic Context Boundary（live artifacts 驗證結果）

- **Codebase map**：`.samsara/codebase-map.yaml` 為 STALE（last_updated 2026-04-23，churn = 217 個變更檔，遠超閾值 30），且仍使用已棄用欄位 `staleness_threshold_days`。依 live pre-thinking skill 規則應 auto-initiate 重建；但本 feature 的全部 boundary facts 已於本 session 直接從 live artifacts 逐檔驗證（全部 skills/agents/references、73 份 scar、10 份 iteration log）。是否重建為流程權重決策 → Gap D0。
- **Module ownership**：skills/（11 skill）、agents/（7 agent 定義）、references/（6 canonical checklist）、hooks/（session-start + check-codebase-map）、samsara_cli/（converter + release）、dist/codex/（生成物，隨 skills 變更需 regenerate）。
- **Runtime entrypoints**：skill 由 Skill tool 載入（**注意：載入的是 plugin cache 0.11.2，不是 repo 工作副本**——本 feature 改的是 repo，生效需經 release/install 週期）；hooks 由 hooks.json 註冊。
- **既有 evaluator/tests**：`uv run pytest`（732 passed 基線）；doc-contract 測試直接斷言 SKILL.md 內容（W1/W3 的改動會使部分測試需同步更新——這是預期成本，不是回歸）。
- **expiry 消費者鏈**（W2 事實驗證）：`skills/iteration/SKILL.md`（accept 必附 expiry）+ `skills/validate-and-ship/ship-manifest.md` rule 2（accepted_risks 必附 expiry、須再評估）。**全 repo 無任何檢查器**（hooks、CLI、tests 皆無）。⇒ W2 選「刪欄位」時 ship-manifest rule 2 必須一併處理，否則留下指向不存在欄位的規則。
- **雙 reviewer 歷史證據**（N1 事實驗證）：證據雙向。(a) 2026-06-28 task-3 narrative：同一輪中 quality 抓到 churn definition 漂移、yin 抓到測試 context-blindness——兩個 lens 產出不同類別發現。(b) 2026-04-19 scars：兩者 scope 刻意重疊（I-principle koan vs dishonest-naming），且記錄了「quality 讓給 yin 時被轉交 issue 靜默掉落」的風險。review 輸出本身不落盤，無法統計獨有攔截率。⇒ 合併與否是取捨題，不是證據已決定題。

### Information Gaps

#### Gap I1: scar 膨脹的根因層級
**Question:** scar 平均 113 行的膨脹，多少來自 schema 設計（欄位結構鼓勵重抄）、多少來自 implementer agent 的 Report Format（要求逐項覆述）？
**Hypothesis:** 兩者皆有：schema 的 `resolved_items` 強制重抄原文是結構性原因；implementer.md Report Format 要求「Scar report (YAML) + Self-iteration summary + Self-review findings」三處重疊是行為性原因。W1 需同時動 schema 與 implementer.md 的報告格式，只動 schema 會讓膨脹換欄位再生。（kill condition 已在 autopsy 登記；此假設在 planning 時以 task 拆分驗證。）

### Design Decision Gaps

#### Gap D0: stale codebase map 的處置
**Question:** map churn 217 超標，依規則應重建；但本 feature 的 planning facts 已全部直接驗證。重建 or 標記 stale 續行？
**Hypothesis:** 標記 stale + 記錄 information gap 續行（本 feature 不消費 map；重建是 3-explorer 大流程，對本次 planning 無增量資訊）。但這偏離字面規則，需 user 拍板——這也是「auto-initiate 是否淪為 warn-only」的第一個 live 觀測點。
**Planning impact:** 選重建則本 feature 前多一個 codebase-map 工作流（含 Phase 4 human review）；選續行則 pre-thinking 記錄豁免理由，並可把「map 重建」留給 W1-W3 改完 skills 之後（屆時 churn 更高、重建一次涵蓋全部變更）。

#### Gap D1: N2 — security-privacy-review 是否折入 validate-and-ship
**Question:** 獨立 skill（293 行、固定位於 validate-and-ship 前）折入成 validate-and-ship 的第 0 步 STOP gate，或保留獨立？
**Hypothesis:** 折入。獨立存在的唯一論據是心理權重，而 STOP 步驟的不可跳過性相同、少一次 skill 轉場與一個 gate。但這個 gate 是 user 刻意建立的（2026-04-21 feature），廢立是 user 的決策權。
**Planning impact:** 折入 → W3 的 Auto Mode Gate 去重少一個 skill、bootstrap 路由圖與 README 工作流圖需同步改、該 skill 的 doc-contract 測試遷移。

#### Gap D2: N1 — 雙 reviewer 合併或保留
**Question:** yin + quality 兩個 reviewer agent 合併為一個帶雙 checklist 的 reviewer（dispatch 減半、missing-reviewer 協議消失），或維持分開（兩個獨立 lens 各自成篇）？
**Hypothesis:** 無傾向——Atomic Context 的證據雙向（見上）。合併保住兩個 lens 的檢查項但失去「兩個獨立 context 各自掃一遍」的冗餘；保留則 missing-reviewer 協議的複雜度有主。
**Planning impact:** 合併 → agents/ 兩檔合一、implement/iteration 的 dispatch 流程與 aggregation rule 重寫、相關 wiring 測試全改——是 W 系列之外最大的 diff；保留 → N1 從 scope 移除。

#### Gap D3: W2 — expiry 的二選一方向
**Question:** (a) 加過期掃描器（掛 validate-and-ship failure budget review：掃全 repo iteration-log/ship-manifest 的 expiry，過期未再評估 → 警告），或 (b) 刪 expiry 欄位 + ship-manifest rule 2 同步改寫（accept 改為永久豁免、但必須寫明「誰負責在何種訊號出現時重審」）？
**Hypothesis:** (a) 加掃描器。理由：accept-with-expiry 的語義（風險接受非永久）符合公理，缺的只是警報；刪欄位則失去唯一的時間維度追蹤。成本：掃描邏輯 + 一條 death test。
**Planning impact:** (a) → validate-and-ship SKILL.md 加一步 + 掃描實作位置的選擇；(b) → iteration/ship-manifest 兩處 schema 與規則改寫 + 舊資料的解讀約定。

#### Gap D4: W1 — systemic-scar registry 的位置與 owner
**Question:** repo 層級的系統性傷疤登記檔放哪、誰寫入？
**Hypothesis:** `.samsara/systemic-scars.yaml`（`.samsara/` 已是 repo 層級狀態的家，如 codebase-map.yaml）。寫入時機：Level 2 iteration 或 validate-and-ship 發現某 scar item 屬跨 feature 結構性事實時登記；scar report 此後以 `systemic_ref: <id>` 引用。首版由本 feature 預填已知的 2–3 條（doc-vs-runtime-obedience、doc-instruction-no-code-enforcement）。
**Planning impact:** 影響 scar-schema.yaml 新欄位、iteration 聚合邏輯（systemic_ref 不計入 signal_lost 或另計）、以及 converter 對新檔的處理。

#### Gap D5: W5 — iteration 預設 skip 的判準
**Question:** 「資料驅動進入 iteration」的具體條件？
**Hypothesis:** 同時滿足才建議進入：(1) 存在 cross-task pattern（同一 item 出現於 ≥2 個 task scar），或 (2) `signal_lost ≥ 5`。否則預設 skip 並輸出一行可見紀錄「signal_lost=N、無 cross-task pattern，已 skip iteration（可推翻）」。閾值 5 是從歷史 iteration log 的中位數粗估，planning 時校準。
**Planning impact:** implement 的 Transition 段改寫（從詢問改為條件判斷 + 可推翻通知）；iteration SKILL.md 的 entry 條件段新增。

---

## Step B — Answers

### Group 1: 流程與範圍決策 (round 1)

**Q(D0): stale codebase map 處置？**
**A:** 標記 stale 續行。豁免理由：本 feature 的全部 planning facts 已於本 session 直接從 live artifacts 驗證，map 非本次消費對象；重建留到 W1–W3 改完 skills 後一次做（屆時一次涵蓋全部變更）。Information gap 已登記：map 過時且用舊欄位 `staleness_threshold_days`，任何後續 feature 若要消費 map 需先重建。

**Q(D1): security-privacy-review 折入 validate-and-ship？**
**A:** 折入。成為 validate-and-ship 的第 0 步 STOP gate，不可跳過性不變；bootstrap 路由圖、README 工作流圖、相關 doc-contract 測試同步遷移。N2 升格為正式 scope。

**Q(D2): 雙 reviewer 處置？**
**A:** 保留兩個 reviewer。N1 整項移出 scope——獨立 context 的冗餘檢查是刻意設計，missing-reviewer 協議的複雜度是其合理代價。本 feature 不動 reviewer 結構，也不加觀測點。

### Group 2: 機制設計決策 (round 1)

**Q(D3): expiry 的二選一方向？**
**A:** 刪除 expiry 欄位。連同 ship-manifest.md rule 2 一併改寫：accept 項目不再附到期日，改為必須寫明「誰在什麼訊號出現時重審」（訊號驅動重審取代時間驅動重審）。理由：到期日在本 repo 從未被任何機制消費，時間驅動的重審承諾已被證明是空承諾；訊號驅動至少把重審條件綁在可觀測的事件上。舊資料的 expiry_date 欄位保留原樣（backward-compat），聚合時忽略。

**Q(D4): systemic-scar registry 位置與寫入機制？**
**A:** 照假設——`.samsara/systemic-scars.yaml`，iteration/validate-and-ship 時登記，scar report 以 `systemic_ref: <id>` 引用不重抄。首版由本 feature 預填已知條目。

**Q(D5): iteration 預設 skip 判準？**
**A:** 照假設——存在 cross-task pattern 或 signal_lost ≥ 5 才建議進入，否則預設 skip 並輸出一行可推翻紀錄。閾值於 planning 時校準。

### Group 3: 補遺確認 (round 1)

**Q: 0-design-direction.md 修訂清單是否加入「刪第一步的 repo 情境分類（成熟度），併進第四步依據規則」？**
**A:** 加入（user：「可以刪，因為第四步就會是一個決定關鍵點」）。W4 增為六項：交棒定案、刪輕想層、刪少數意見安全網、健康指標 owner/trigger、K3b 沿用、刪成熟度分類併入第四步。

**Q: implement skill「UI 清單與 index.yaml 絕不准只更新一個」措辭是否修正？**
**A:** 修正，順手做（不開獨立 task）。改為：index.yaml 是唯一真實狀態，UI 清單（TaskCreate/TaskUpdate）是盡力而為的投影，未更新投影不構成流程錯誤。user 原話確認：「index.yaml 是唯一的真實狀態，UI 清單只是給你看的投影，這敘述沒錯。」

## Evaluation Contract

**Primary evaluator:** 三段式檢核程序（單一 checklist，三段全過才算 pass）
**Agent can perform it by:**
1. `source .venv/bin/activate && uv run pytest` — 全綠，且以 `git diff` 檢查既有 death tests 無刪除或斷言弱化（僅允許因 doc 措辭同步而更新的斷言字串，且更新後仍會在行為破壞時轉紅）
2. 指令面積量測（`find skills -name "*.md" -not -path "*/templates/*" | xargs wc -l` ＋ `wc -l agents/*.md references/*.md`）與基線 **6,356 行**比較 — **淨量必須為負（必須真的減少），以淨減 ~300 行為參考值、非硬性驗收**；搬家假減法檢查為硬性：references/ 與新增檔案的增量不得抵銷 skills 減量（「單一 session 會載入的總行數」淨減）
   > Amendment 2026-07-03：原「基線 5,643、下降 ≥12%」經 planning 實測修正——精確基線 6,356（原數漏算 skills 支援檔）、Gate 重複實measure 203 行（原估 ~400），12% 不可達。user 決定「先減少為主」：不設硬性百分比，減少本身＋搬家檢查＋第三段逐項條件承擔驗收重量。
3. 逐項可觀測完成條件（在 acceptance.yaml 中逐條列出）：每個 skill 的 Auto Mode Gate 段 ≤ 8 行；`.samsara/systemic-scars.yaml` 存在且 scar schema 支援 `systemic_ref`；scar schema 的 verified:true 壓縮與 resolved_items 不重抄規則落地；expiry 欄位移除且 ship-manifest rule 2 改為訊號驅動重審；0-design-direction.md 六項修訂各有對應決定文字；iteration 進入條件為資料驅動；fast-track checklist 改為只記違規；security-privacy-review 折入 validate-and-ship 且 bootstrap 路由圖/README 同步
**Pass signal:** 三段全部成立
**Fail signal:** 任一段不成立（含：行數達標但搬家假減法檢查不過）
**Feedback loop:** 先定位失敗段落對應的 must-have 項目，修正該項或回退該項的變更後重跑檢核；不得為通過檢核而刪除/弱化測試
**Out of scope validation:** 未來 session 對修訂後文件的 runtime 服從度（agent 是否真的照新規則行動）——只能在後續 feature 的 dogfood 中觀測；scar 平均行數 ≤ 70 的實測同屬 dogfood 範圍

## Step C — Commitment

**Date:** 2026-07-03T00:00:00+08:00
**Decision:** Proceed
**Accepted gaps:** none
**Notes:** N1（雙 reviewer 合併）經決策移出 scope；codebase map 標記 stale 續行的豁免已記錄於 Step B Group 1；I1（scar 膨脹根因層級）為 planning 時以 task 拆分驗證的假設，非未解缺口。
