# Pre-thinking: structural-honesty-mechanisms

## Session: 2026-07-05T00:30:00+08:00

## Step A — Design and Gap Map

### Atomic Context Boundary（live codebase 事實基礎）

Codebase map 於本 session 完整重生（churn 227 > threshold 30 觸發 auto-regen；三 explorer 全跑完＋Phase 4 人工審查通過；`last_updated: 2026-07-05`）。與本 feature 直接相關的 live facts：

- **Skill 修改的落點**：planning（`skills/planning/SKILL.md` + `task-format.md` + `templates/`）、implement（`SKILL.md` + `dispatch-template.md`）、iteration（`SKILL.md`）、validate-and-ship（reconciliation 段）。9 skills 的 Auto Mode Gate 已去重指向 `references/auto-mode.md`（減法 branch 成果，新機制不得重新膨脹）。
- **Reviewer 雙軌**：`agents/code-quality-reviewer.md`（9 陰面原則）與 `agents/code-reviewer.md`（yin，含 Architectural Placement 維度，已有 placement Key Decisions 注入管道 —— M2/M3 的既有掛載點）。
- **機器可解析引用的前例**：`scar-schema.yaml` Rule 9 的 `systemic_ref: <id>` → `.samsara/systemic-scars.yaml` registry，含 dangling-ref = parse failure 的三分支語意 —— 證據引用格式（D2）的直接參考模式。
- **上游命名契約的前例**：task-format.md 的 Unit Test Contract（planning 在上游命名 contract source，implementer 只消費不推導）—— M2 task↔spec 片段映射（D4）的同型先例。
- **測試面**：857 tests；doc-contract 測試（`test_skills/`、`test_contract_bound_tests/`、`test_auto_mode/`）pin skill 文字。新 artifact schema + skill 修改必然觸發測試新增/更新。
- **已知系統性限制（yin 分析確認為全面性）**：workflow 編排層是 prose-executed，所有 gate 靠 LLM 遵循；測試只能證明文字存在，不能證明 runtime 遵守（systemic scar: doc-vs-runtime-obedience）。本 feature 的證據可解析性設計是首個把「機器可驗證」引入 workflow artifact 的嘗試 —— 這是機會也是它自身的 death case（kill condition 2：假證據不可偵測則不得以必填欄位存在）。
- **多平台供應鏈**：skill 修改需 `samsara-cli convert` regenerate `dist/`；`samsara-cli validate` 無 CI 消費者（ISSUE-002 開放中），轉換品質由 pytest fixtures 把關。

### Information Gaps

#### Gap I1: doc-contract 測試爆炸半徑
**Question:** planning/implement/iteration SKILL.md 的修改會使多少 doc-contract 測試需要同步更新？新 structure-spec artifact 需要哪些新測試？
**Hypothesis:** `test_skills/` 需新增 structure-spec 相關測試、`test_contract_bound_tests/` 的 concept-token 清單需擴充；現有測試破損量在個位數到低雙位數。實作前需 grep 實測，planning 的 task 拆分要含測試同步 task。

#### Gap I2: fixtures 與轉換覆蓋
**Question:** 新增 planning template（structure spec）後，`tests/fixtures/source/` 與 `expected/{codex,gemini-cli}/` 的 golden fixtures 是否需要同步擴充才能讓 converter 測試覆蓋新檔案？
**Hypothesis:** skills 的 templates/ 目錄由 SkillConverter 全量處理，新 template 自動被轉換；fixtures 需重生（`FIXTURE_VERSION` bump）。屬機械工作，但漏做會讓多平台輸出靜默缺檔。

### Design Decision Gaps

#### Gap D1: Structure spec artifact 的形式與位置
**Question:** 結構規格用什麼形式存在？(a) 獨立 `structure-spec.yaml`（machine-parsable，機器可驗證引用）(b) 獨立 `structure-spec.md`（人讀優先）(c) `2-plan.md` 內嵌章節（零新檔案）(d) `overview.md` Key Decisions 擴充（沿用既有注入管道）
**Hypothesis:** (a) 獨立 YAML —— 證據可解析性（北極星 corruption signature 的偵測前提）要求機器可驗證，scar-schema.yaml 是同型前例；overview.md 保留人讀的策展版。代價：新 schema、新 doc-contract 測試、儀式淨增量預算的主要消耗者。
**Planning impact:** 決定 artifact contract、下游三個消費點（dispatch/review/reconciliation）的讀取方式、doc-contract 測試範圍、File Map 推導來源。

#### Gap D2: 變動理由證據的引用格式
**Question:** 結構投資引用證據的格式怎麼定義才能機器可解析？證據三等級（已發生/已計畫/domain 本質分界）各自的解析目標是什麼？
**Hypothesis:** typed reference —— `evidence: {type: git_history|planned_task|domain_boundary, ref: <path|task-id|scope-item-anchor>, note: <一行>}`。前兩型可機器解析（path 存在性、task id 存在於 index.yaml、kickoff 條目 anchor 存在）；`domain_boundary` 型無法機器驗證 ref，只能要求 rationale 非空＋human/reviewer 判斷 —— 這是判準的已知軟肋，需在 acceptance 明示（不假裝三型都同等可驗證）。Dangling ref 比照 systemic_ref 的 parse failure 語意。
**Planning impact:** 決定 validate-and-ship 抽查的實作方式、reviewer 證據審查的判定規則、以及 cargo-cult 證據偵測的可行性上限。

#### Gap D3: Spec path 進入判準的執行位置（M4）
**Question:** 「走不走 structure spec path」在哪個階段、由誰判定？POC 豁免（死期寫入 kickoff）在哪裡檢查？
**Hypothesis:** planning 入口新增 guard：讀 kickoff —— 有 `poc_death_date` 且未過期 → 豁免（記錄於 2-plan.md）；否則 spec path 為預設。fast-track 完全不觸及（其入口 gate 已存在）。research 的 kickoff template 增加可選 `poc_death_date` 欄位。
**Planning impact:** 決定 research template 是否改動、planning guard 的新分支、豁免記錄的 artifact 位置。

#### Gap D4: task ↔ spec 片段映射由誰產生（M2 定向注入的機制）
**Question:** 「這個 task 觸及哪些 spec 條目」的映射，是 planning 在 task 檔案裡上游標注（靜態），還是 implement 主 agent 派發時動態判斷？
**Hypothesis:** planning 上游標注（task-N.md 增加 `structure_refs: [<spec-entry-id>]` 欄位）—— 與 Unit Test Contract 的「上游命名」哲學同型；implement 主 agent 只按 id 取片段貼入 dispatch，不做判斷。純行為 task 允許 `structure_refs: []`（空 = 不注入，不是漏標 —— 需與漏標可區分：欄位必須存在）。
**Planning impact:** 決定 task-format.md 的 schema 變更、dispatch-template.md 的注入段落、以及「定向注入率」sub-metric 的計算來源。

#### Gap D5: Structural rot signal 的計算與擁有者（M5）
**Question:** 結構漂移怎麼定義、誰產生訊號、iteration 怎麼消費？
**Hypothesis:** 漂移 = 三類：(1) 實作出現 spec 未承諾的新 module/邊界（未申報）(2) spec 承諾的邊界被違反（跨界依賴）(3) spec 條目被實作放棄（承諾未兌現）。訊號來源：spec-mode 的 code-quality-reviewer 在每 task review 時回報 per-task drift items（新增輸出欄位）；iteration Step 1 聚合為 `structural_drift` 計數（與 signal_lost 並列，不混入）；validate-and-ship reconciliation 做 feature 級最終對照。恆為零觸發 M5 death condition 的重新評估。
**Planning impact:** 決定 reviewer agent 定義的輸出 schema 變更、iteration SKILL.md 的聚合邏輯、reconciliation 的新維度。

---

## Step B — Answers

### Group 1: spec artifact 契約（D1–D3）

**Q (D1):** Structure spec artifact 用什麼形式存在？
**A:** 獨立 YAML —— `changes/<feature>/structure-spec.yaml`，machine-parsable。overview.md 保留人讀策展版。scar-schema.yaml 為 schema 前例。

**Q (D2):** 變動理由證據的引用格式？
**A:** Typed ref + 診斷式驗證 —— `evidence: {type: git_history|planned_task|domain_boundary, ref, note}`。前兩型機器解析（path 存在、task id 在 index.yaml）；`domain_boundary` 型顯式標記 `machine_verifiable: false`、只要求 rationale 非空。不假裝三型同等可驗證。Dangling ref 比照 systemic_ref 的 parse failure 語意。

**Q (D3):** Spec path 進入判準在哪裡執行？
**A:** Planning 入口 guard —— 讀 kickoff：有未過期 `poc_death_date` → 豁免（記錄於 2-plan.md）；否則 spec path 為預設。research kickoff template 增加可選 `poc_death_date` 欄位。fast-track 完全不觸及。

### Group 2: 注入與訊號機制（D4–D5）

**Q (D4):** task ↔ spec 片段映射由誰產生？
**A:** Planning 上游標注 —— task-N.md 新增必填 `structure_refs: [<spec-entry-id>]` 欄位；implement 主 agent 只按 id 取片段貼入 dispatch。純行為 task 寫空陣列（欄位必須存在，空 ≠ 漏標）。與 Unit Test Contract 上游命名哲學同型。

**Q (D5):** Structural rot signal 誰產生、怎麼聚合？
**A:** Reviewer 產生 + iteration 聚合 —— spec-mode 的 code-quality-reviewer 每 task 回報 drift items（三類：未申報新邊界／邊界被違反／承諾未兌現）；iteration 聚合為 `structural_drift` 計數（與 signal_lost 並列不混計）；validate-and-ship reconciliation 做 feature 級最終對照。零新 agent。

---

## Evaluation Contract

**Primary evaluator:** 合成 mini-feature 證據鏈檢查 —— 實作完成後，用一個小型真實 feature 走完 spec path，agent 檢查證據鏈四環節全部可觀測
**Agent can perform it by:** artifact inspection —— (1) 生成：`structure-spec.yaml` 存在且全部 evidence refs 0 dangling（typed ref 機器解析）；(2) 注入：task-N.md 含 `structure_refs` 欄位，dispatch 記錄含對應 spec 片段；(3) 消費：reviewer verdict 引用 spec entry id 並回報 drift items（可為空但欄位存在）；(4) 驗屍：reconciliation 輸出含結構維度
**Pass signal:** 四環節全部可觀測且 evidence refs 0 dangling
**Fail signal:** 任一環節缺失、任一 evidence ref dangling、或 reviewer verdict 未引用任何 spec id
**Feedback loop:** 從缺失環節對應的 skill 段落回修（生成→planning SKILL、注入→implement dispatch-template、消費→code-quality-reviewer agent 定義、驗屍→validate-and-ship reconciliation 段），修正後重跑同一 mini-feature 檢查
**Out of scope validation:** 「結構品質是否實質提升」（北極星 invalidation condition 的長期判斷，需跨 feature 觀察）；`domain_boundary` 型證據的實質合理性（機器只能驗 rationale 非空，合理性靠 reviewer/human 判斷）

---

## Step C — Commitment

**Date:** 2026-07-05T01:05:00+08:00
**Decision:** Proceed
**Accepted gaps:** none（I1 doc-contract 測試爆炸半徑、I2 fixtures 同步為 planning 內實測驗證項，非用戶裁決假設 —— planning 的 task 拆分必須包含對應驗證步驟）
**System design constraints consumed by planning:**
- D1: 獨立 `structure-spec.yaml`（machine-parsable；overview.md 保留人讀策展版）
- D2: typed evidence ref（`git_history`/`planned_task` 機器解析；`domain_boundary` 顯式 `machine_verifiable: false`；dangling = parse failure）
- D3: planning 入口 guard（kickoff `poc_death_date` 未過期 → 豁免；fast-track 不觸及）
- D4: task-N.md 必填 `structure_refs` 欄位，planning 上游標注（空陣列 ≠ 漏標）
- D5: spec-mode code-quality-reviewer 回報 drift items；iteration 聚合 `structural_drift`（與 signal_lost 並列）；reconciliation 做 feature 級對照；零新 agent
