# Pre-thinking: scar-report-subtraction

Execution mode: auto

## Step 1 — Locate the work

**Type:** refactor（scar report 寫入契約的重構）＋ data-structure change（scar YAML item 格式改版，新舊格式並存窗口）＋ feature（validate_format.py 新增長度預算檢查）。

**Depth: deep（兩軸皆非零，無法證入 fast-track）**

- uncertainty：槽位欄位設計未定（kickoff 的 what/bites_when/where/accepted_because 是待驗假設）、預算閾值未校準、backward-compat 規則搬到哪一端未定。
- blast radius：scar-schema.yaml 是 load-bearing seam —— 全文被逐字注入每次 implementer dispatch（`skills/implement/dispatch-template.md:38,84`）與 iteration fix dispatch（`skills/iteration/SKILL.md:224`）；被 `tests/test_skills/test_scar_schema_noise_rules.py`（680 行）等測試釘住；被 iteration Step 1 聚合消費（`skills/iteration/SKILL.md:74-103`）。改錯的損害會擴散到寫入面、讀取面、測試面三個方向。

**Codebase map:** `.samsara/codebase-map.yaml` last_updated 2026-07-05，churn 0（排除 changes/docs/bugfix 後無源碼變更）→ 新鮮，作為起始假設使用，關鍵事實已對 live artifacts 驗證。

## Step 2 — Assumptions + core identity

### Domain core identity

> **Scar report 是寫給未來讀者的最小損害地圖：一條疤 = 哪裡有疤、什麼條件下咬人、去哪裡看。它的 schema 是「寫入契約」，validator 是這份契約唯一有牙齒的執行者；任何不被機器消費、也不改變未來讀者行動的字，都不屬於這份文件。**

Operability test：這個 identity 能裁決具體結構選擇 ——
- 「review 裁決史要不要寫進 narrative？」→ 不改變未來讀者行動、無機器消費 → 不屬於，去 review-record.md。
- 「治冗長要加 Rule 18 還是加 validator 檢查？」→ 契約的執行者是 validator，不是註解 → 加檢查。
- 兩個相反選擇無法同時「服務」它 → 通過測試。

### Assumptions

**A1 — 長敘事無下游讀者（confident）**
- Assumption: iteration Step 1 只消費 `deferred_to_feature_iteration`、`status: resolved`／`resolved_items`、`systemic_ref`、parse 成敗；narrative 與長 description 無任何機械消費者。
- Boundary: 成立於機械消費面；人類讀者面由 kill condition 守著（owner 已表明不讀）。
- If it breaks: 減法方向整個錯 → kill condition #1。
- Basis: `skills/iteration/SKILL.md:74-103`（已讀）；使用者原話「沒有被看的必要性」。

**A2 — Schema 全文注入是寫入面的唯一通道（confident, 已驗證）**
- Assumption: 寫作者（implementer subagent）看到的 scar 格式 = scar-schema.yaml 全文貼進 dispatch prompt；inline 模式讀同一檔案。
- Boundary: 成立於 dispatch 與 inline 兩種執行模型；agents/implementer.md 可能另有摘要（待 Step 3 lens 確認）。
- If it breaks: 「schema 瘦身＝寫作者體驗改善＋token 節省」的推論失效。
- Basis: `skills/implement/dispatch-template.md:38`（"read templates/scar-schema.yaml … Paste its full content"）、`:84`；`skills/implement/scar-report.md:13-15`。

**A3 — validate_format.py 是 handoff 唯一機械 gate，且被強制執行（confident）**
- Assumption: implement 的 step 18 強制跑 validator 並貼輸出，缺輸出 = visible missing；因此在這裡加長度預算 = 預算真的有牙齒。
- Boundary: 只在 implement handoff 與 iteration fix 流程有效；不涵蓋 fast-track 寫的 scar（如有）。
- If it breaks: 預算淪為又一條 prose 規則 → 違反 kill condition #2。
- Basis: `skills/implement/SKILL.md:198-204,253`；`validate_format.py` 現有 6 類檢查、零長度檢查（已讀全文）。

**A4 — 測試對 schema 內容的釘死程度（NOT confident → Lens A）**
- Assumption: 測試釘的是規則的存在性與 validator 行為，不是 schema 全文 snapshot；重構後可透過改測試對齊，不會有隱藏的全文比對。
- If it breaks: 改動成本暴增，且 snapshot/integration 測試可能在 CI 端紅掉。
- Basis: 無 — `test_scar_schema_noise_rules.py` 680 行未讀 → 派 searcher。

**A5 — CLI 轉換面不複製 schema 內容（NOT confident → Lens B）**
- Assumption: samsara_cli 轉 codex/gemini 時對 skills/implement/templates/ 的處理是複製或跳過，不是內嵌到別的 artifact；snapshot 測試不 pin schema 全文。
- If it breaks: 改 schema 需要同步 regenerate snapshot／conversion fixtures。
- Basis: 無 — 未查 converter config → 派 searcher。

**A6 — 舊 report 永不重新過 validator（confident, 有邊界）**
- Assumption: validate_format.py 以 feature-dir 為單位在 implement handoff 執行；已完結 feature 的舊 report 不會被新預算檢查追溯打紅。
- Boundary: 若 CI 或某測試對歷史 changes/ 全量跑 validator，則破。Lens A 順帶確認。
- If it breaks: 需要 grandfather 條款（依日期或 schema_version 欄位豁免舊檔）。
- Basis: `validate_format.py:241-268`（main 只吃單一 feature-dir 參數）；`skills/implement/SKILL.md:198`。

**A7 — 真疤能被定長槽位表達（NOT confident → Step 4 自行壓縮實測）**
- Assumption: 近期最長 report（task-4, 232 行）的「真疤內容」（扣掉 review 史、統計表、辯護文後）能收進每條 ≤6 行的槽位而不失誠實。
- If it breaks: 預算閾值錯或槽位語意設計錯 → 需要 escape hatch 或放寬。
- Basis: 待實測 — Step 4 將對 task-4 的三條 known_shortcuts 做壓縮示範作為證據。

**A8 — backward-compat 讀取規則已有先例住在 aggregator 端（confident）**
- Assumption: schema Rule 9 已宣告 resolution procedure 的 canonical home 在 iteration SKILL.md（"not restated here"）——把 Rules 7/8/11/14 的讀取相容半段搬過去是延續既有慣例，不是新機制。
- If it breaks: 兩處規則漂移 → must-have #4 的死亡條件。
- Basis: `scar-schema.yaml:99-102`；`skills/iteration/SKILL.md:77,80-83`（相容規則已在該處完整重述）。

（Step 3 lens 派遣：A4 → Lens A（測試釘死面）；A5＋A2 邊界 → Lens B（寫入面／轉換面＋schema 演化史）。A7 由主 agent 在 Step 4 以壓縮實測自行取證。）

## Step 3 — Multi-lens evidence

兩個 searcher（facts only）＋主 agent 自查。回報全文以事實併入下方；無矛盾事實。

**Lens A（測試釘死面）→ 驗證 A4、A6：**
- `tests/test_skills/test_scar_schema_noise_rules.py` 以 `_rules_section()` 取 schema 的 `# --- Rules ---` 區塊做**概念 token 子字串斷言**（自述 docstring :29-32「tolerant of rewording, intolerant of concept deletion」），不做全文 snapshot、不 yaml.safe_load schema 本身。
- 釘住的 verbatim 片語包括："missing deferred flag = false"、"plain string format backward compatibility"、"rules 7 and 8 continue to apply unchanged"（:248-288）——**compat 規則若搬出 schema，此 death test 與 :186-210 會紅，需同步重綁到新 canonical home**。
- `tests/test_skills/test_global_thinking_channel.py:204-233` 釘 schema 內 `structural_decisions:` 五個欄位名、"granularity floor"、"structural bet"、literal `structural_decisions: []`。
- `tests/test_skills/test_format_validators.py` 只測 validate_format.py 行為（synthetic fixtures），斷言用 `any(...)` 非窮舉 → **加長度檢查是 additive，唯一風險是新檢查誤傷 clean fixtures（SCAR_OK :91-105）**。
- `test_implementer_contract.py` 與 scar 三件套零關聯；integration/snapshot 測試不內嵌 real schema 內容。
- 無任何測試對歷史 changes/ 全量跑 validator → A6 成立。

**Lens B（寫入面／轉換面）→ 驗證 A2、A5：**
- `agents/implementer.md:182` 指向 dispatch 注入的 schema，不內嵌全文；但 :144,:184,:208,:255-256 **以規則編號引用**（Rule 11/13/15-17）。`skills/iteration/SKILL.md:77,80` 引 Rule 9/11/14。→ 規則編號是跨檔承重的，且無機制驗證編號引用 → 重編號＝silent rot。
- 轉換面：`samsara_cli/converter/skill.py:371,405-410` 對 YAML companion files 逐字複製（有註解明言 scar-schema.yaml）；`dist/codex`、`dist/gemini-cli` 下的 schema 與 source byte-identical → **改 schema 後需 regenerate dist**（機械步驟，交 planning）。
- 演化史（git log --follow）：af437a5（2026-04-16，創建即「unify into single source of truth」）→ 49f4964（加 compat Rule 8）→ eb4ae07（2026-07-04，noise rules 9-14）→ 7f14889（rules 15-17）→ 3a9c613。**規則只增不減的 accretion 模式有 git 證據。**

**Unverified gaps:** 無 lens 失敗；A7（槽位表達力）由 Step 4 壓縮實測取證。

## Step 4 — Converge to design decisions

### D1 — Item 結構：定長槽位取代自由文本 blob（新寫入）【self-derived】
- 決定：`known_shortcuts` 與 `silent_failure_conditions` 的新寫入格式改為固定短欄位：`what`（疤是什麼，一行白話）／`bites_when`（什麼條件下咬人，一行）／`where`（file:line 或段落指針）／`accepted_because`（可選，一行）。`assumptions_made` 保持現有三欄（assumption/verified/note——note 已被 Rule 10 約束為 pointer）只加預算。`structural_decisions` **不動**（已是定長欄位、運作正常、被測試重釘、被 quality reviewer 消費）。
- 推導鏈：core identity（哪裡有疤／何時咬人／去哪看）→ 三個必答槽位一一對應；axiom（存在即責任）→ 每個欄位都有明確消費者（未來讀者的行動）；既有慣例證據：`structural_decisions` 本身就是「定長欄位在本 schema 內成功運作」的先例（Lens B: quality reviewer 逐欄消費它）。
- Why not the others：沿用自由文本＋加 prose 規則 = 已失敗七次的 accretion 路線（git 證據）；全 markdown 化 = 丟掉 iteration 的 YAML 機械聚合。
- 最先腐爛處：若 `what` 欄被塞入多句長文（槽位被當 blob 用）→ D2 的欄位字元預算就是為此而設。
- Reversal cost: 低 — 聚合端以欄位形狀推斷世代（D6），退回舊格式不需遷移。

### D2 — 預算住在 validate_format.py，超標 = finding【evidence-decided】
- 決定：新增 `length-budget` 檢查類：欄位字元上限、單 item 行數上限、narrative 行數上限、整份 report 行數上限。超標 = FINDING（同現有 finding 語彙），handoff 不得通過。**確切數值由 planning 以歷史 report 的「真疤內容壓縮後分佈」校準**；pre-thinking 給定形狀與候選值（欄位 ≤200 chars、item ≤6 行、narrative ≤10 行、報告 ≤60 行）。
- 證據：A3（validator 是唯一有牙齒的 gate，SKILL.md:198-204 強制執行）＋Lens A（additive 檢查被測試結構容忍）＋git 證據（prose 規則路線已證失敗）。
- 硬 finding 而非 warning：warning 無執行力 = 回到 prose 規則 → 違反 kill condition #2。
- 最先腐爛處：閾值若過緊，誠實內容被砍 → kill condition #3 的重校準路徑；planning 必須在 acceptance 裡放「壓縮不失誠實」的對照驗證。

### D3 — 寫入契約與讀取契約分家【self-derived，沿既有慣例】
- 決定：scar-schema.yaml 瘦身為**純寫入契約**（一頁：欄位模板＋預算＋write filter＋「去別處」對照表）；backward-compat 讀取規則（現 Rules 7/8/11 相容半段/14）的 canonical home 移到 `skills/iteration/SKILL.md` Step 1；`test_scar_schema_noise_rules.py` 中綁在 schema 位置的 compat 斷言同步重綁到 iteration（Lens A 已證 :213-245,:604-621 本就讀 iteration，先例存在）。
- 推導鏈：core identity（schema 是寫入契約）→ 寫作者永遠只寫當前格式，永遠不需要 compat 規則；讀者（aggregator）才讀三代格式 → 規則跟著讀者住。既有慣例：Rule 9 已把 resolution procedure 的 canonical home 設在 iteration SKILL.md（schema 明言 "not restated here"）。
- Why not the others：留在 schema（現狀）= 每次 dispatch 注入 205 行立法史給一個永遠用不到它的寫作者；兩處都寫 = must-have #4 死亡條件（漂移）。
- 最先腐爛處：iteration 端 compat 文字與 aggregator 實作脫節 → 由重綁後的 death tests 守。

### D4 — 廢除規則編號，改具名錨點【self-derived】
- 決定：新 schema 不再用 Rule 1–17 編號清單；保留的規則以具名錨點行內化（如 `# write-filter:`、`# granularity-floor:`），跨檔引用（implementer.md、iteration SKILL.md、validate_format.py、scar-report.md 共 8+ 處）同批改為具名引用。
- 證據鏈：Lens B 證實編號被跨檔承重且無機制驗證引用 → 任何增刪規則都會靜默斷鏈（本 feature 自己就要刪規則，若保留編號制，改完當下就製造 dangling references）。
- 最先腐爛處：具名錨點被改名而引用未同步 —— 與編號制相同的風險但頻率更低（名字比序號穩定）；殘餘風險記入 residual list。

### D5 — narrative 保留但設預算【self-derived】
- 決定：narrative 保留為 escape hatch（真疤複雜到槽位裝不下時用），行數預算 ≤10 行，review-diary 反模式禁令保留（併入「去別處」表）。
- 推導鏈：kill condition #3（預算不得傷誠實）→ 刪除 escape hatch 的誠實風險 > 設預算的噪音風險；失敗要響亮（超標 = finding）而非沉默（偷塞進槽位）。
- Why not delete：複雜疤被硬塞槽位 = 逼出不誠實的省略，且無響亮失敗。

### D6 — 世代識別用欄位形狀推斷，不加 schema_version【self-derived】
- 決定：aggregator 以欄位形狀分辨三代（plain string → 最舊；`description` → 第二代；`what`/`bites_when` → 新代），與既有 Rule 8 的 plain-string 推斷慣例一致。舊 report 不遷移、不豁免標記（A6：validator 不會追溯跑舊 feature）。
- Reversal cost: 低；若日後出第四代再引入 version 欄位不遲——現在加 = 為想像中的未來建擴充點，違反 structural honesty。

### D7 — Real Seams（named decision category）
- **seam: scar-write-contract** — scar-schema.yaml 作為單一寫入契約、全文注入每次 dispatch。Tier: **already-happened**（git: af437a5 "unify into single source of truth"；dispatch-template.md:38,84）。本 feature 坐在其上（瘦身其內容，不動其單一源地位）。
- **seam: write-read-boundary** — 寫入端（schema→implementer）與讀取端（iteration aggregator）的邊界。Tier: **already-happened**（Rule 9 canonical-home 先例，git: eb4ae07）＋ domain-essential（寫者只見當前格式、讀者見全歷史——生命週期本質不同）。本 feature 銳化此縫（D3 把 compat 規則搬過界）。
- **seam: format-vs-judgment** — validate_format.py 只管機械可判定形狀，judgment 歸 reviewer。Tier: **already-happened**（validate_format.py:2-8 docstring 明文；review 流程既有分工）。D2 的預算檢查必須留在 format 側（行數 = 機械；「夠不夠白話」= judgment，永不進 validator）。

### A7 壓縮實測（槽位表達力證據）
task-4 最長條目（60 行，`task-4-scar.yaml:48-83`）之真疤內容以 D1 槽位重寫：
```yaml
- what: "validate-and-ship Step 0 本文與 Auto Gate overrides 三處重述『unknown != pass』"
  bites_when: "任一處措辭被單獨修改時，另外兩處靜默失同步"
  where: "skills/validate-and-ship/SKILL.md:85,108,209-211"
  accepted_because: "test_security_gate_fold.py 釘住 Auto Gate 段內的措辭 — 有測試守的刻意冗餘"
```
4 行，誠實無損；原 60 行中其餘為 review 裁決史（→ review-record.md）、行數統計表（→ commit message）、辯護文（無讀者）。A7 成立（單例證據，閾值最終校準交 planning）。

### 型別 checklist 缺漏檢查
- data-structure change → 相容性/共存窗口/回滾點：D6 已覆蓋；回滾 = 新寫入退回舊格式即可（聚合端仍讀）。
- refactor → 行為不破證明：Lens A 已列出會紅的測試與重綁路徑，交 planning 任務化。
- feature → where/reuse/style：D2 沿用既有 finding 語彙與 exit-code 慣例。
- 無帶著缺口的維度；全部落入三盒。

## Step 5 — Ask what must be asked

### Group 1: Evaluation Contract（auto → gatekeeper, decision-002）

**Q:** 這個 feature 的 Primary evaluator（唯一 canonical 回饋源）是哪一個？（A: tests-only／B: golden re-expression／C: A 為 Primary、B 為 supporting）

**A:** Chosen: **C**
- Why not A alone: A 對 kill_condition #3（預算不傷誠實）結構性失明 — synthetic fixtures 非真實歷史疤內容，A-only 可全綠而本 feature 要防的失敗（誠實被壓縮掉）未被檢查；且 D2 已承諾 acceptance 需要壓縮誠實對照，A-only 自相矛盾。
- Why not B alone: B 含 judgment 成分、單例證據（A7），且 flow §6(2) 要求 Primary 被 planning/iteration/validate-and-ship 逐任務重用 — 一次性 artifact＋人工判斷無法當可重複的 per-task gate。
- What this assumes: 擴充後的 pytest 套件足以作為每個分解任務的 done 訊號；golden-artifact 檢核在 planning acceptance 做一次即滿足 kill_condition #3，不需成為常設 evaluator。
- What rots first: kickoff North Star sub_metric 已命名的脫鉤情境 — 測試全綠但人類在 validate-and-ship 仍讀不懂 report；由 decoupling_detection 條款（主觀抽查）承接。
- Uncertainty: medium；非 unconfirmed guess（推導僅依 Evaluation Contract 自身成文約束＋本 feature 已寫定的 kill condition 與 North Star）。

## Step 6 — Honest handoff

### L1 handoff（core identity + real seams → planning Key Decisions single source）

- **Core identity**（Step 2）：Scar report 是寫給未來讀者的最小損害地圖：一條疤 = 哪裡有疤、什麼條件下咬人、去哪裡看。Schema 是寫入契約，validator 是契約唯一有牙齒的執行者；不被機器消費也不改變未來讀者行動的字，不屬於這份文件。
- **Real seams**（Step 4 D7）：
  - `scar-write-contract` — tier: already-happened（git: af437a5；dispatch-template.md:38,84）
  - `write-read-boundary` — tier: already-happened（Rule 9 先例，git: eb4ae07）＋ domain-essential（寫者只見當前格式、讀者見全歷史）
  - `format-vs-judgment` — tier: already-happened（validate_format.py:2-8 docstring）
- Planning 引用上述決定（含 D1–D6），不重推導、不新增 placement 決定；planned-change tier 由 planning 分解任務時補標。
- 不預建接縫的未來抽象：先具體（本次只做新寫入格式＋預算檢查），第二個真實力量出現才抽象。

## Evaluation Contract

**Primary evaluator:** 擴充後的完整測試套件 —— `uv run pytest tests/` 全綠，必含：新 length-budget 行為測試（over-budget fixture 產生 finding、clean fixture 不誤傷）、重綁至新 canonical home 的 compat death tests、新槽位欄位的 validator 解析測試。（decision-002，明示選擇 tests 為唯一標準）
**Agent can perform it by:** `uv run pytest tests/`（repo root），輔以 `uv run python skills/implement/scripts/validate_format.py <feature-dir>` 對 fixture 目錄的直接執行。
**Pass signal:** 全套件 0 failed；新增測試存在且非 tautological（能對 over-budget/舊格式 fixture 轉紅）。
**Fail signal:** 任何 failed/error；或新檢查誤傷既有 clean fixtures（SCAR_OK）。
**Feedback loop:** 先讀 finding 訊息定位是「檢查錯」還是「fixture/文件未同步」；規則重綁類失敗優先改測試綁定目標（write-read-boundary 的正確側），行為類失敗改 validator。
**Out of scope validation:** 「夠不夠白話／具體」的語意品質（format-vs-judgment seam 的 judgment 側，歸 reviewer 與人類抽查）；North Star 的長期 corruption signature（內容位移到 commit message 等——validate-and-ship 抽查承接）。

**Supporting evidence（非回饋源）:** golden re-expression —— task-4-scar.yaml（232 行）以新格式重寫＋誠實無損對照清單，planning 必須將其任務化為 acceptance artifact（decision-002 的附帶義務）。

### Residual list（交給 planning 或更晚）

1. 預算確切數值需 planning 以歷史 report 壓縮分佈校準（D2；候選值：欄位 ≤200 chars、item ≤6 行、narrative ≤10 行、report ≤60 行）。
2. `dist/` 下 codex/gemini 的 schema 副本需在改動後 regenerate（Lens B；機械步驟，入 task）。
3. 具名錨點取代規則編號後，跨檔引用（agents/implementer.md、skills/iteration/SKILL.md、scar-report.md、validate_format.py docstring、dispatch-template.md）需同批更新 —— 錨點改名的殘餘 silent-rot 風險低於編號制但非零。
4. fast-track 路徑若產 scar report，不經 validate_format.py gate（A3 boundary）—— 本次不解，記錄為已知邊界。
5. 舊 reports 維持原樣（kickoff 明示不遷移）；aggregator 三代格式推斷（D6）的測試覆蓋交 planning。

### Commitment

**Date:** 2026-07-07T10:08:14Z
**Decision:** Proceed
**Accepted gaps:** none
**Unresolved gaps:** none
