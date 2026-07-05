# Plan: structural-honesty-mechanisms

## Pre-thinking Commitments Consumed

- **Decision:** Proceed
- **Accepted gaps:** none（I1 測試爆炸半徑已於 planning 實測：`test_skills/` 一行為一測試檔模式、`test_contract_bound_tests/` pin 用語、fixtures 需 regen `FIXTURE_VERSION` bump；I2 由 task-5 供應鏈同步 task 吸收）
- **System design constraints:**
  - D1: 獨立 `structure-spec.yaml`（machine-parsable；overview.md 保留人讀策展版）
  - D2: typed evidence ref（`git_history`/`planned_task` 機器解析；`domain_boundary` 顯式 `machine_verifiable: false`；dangling = parse failure）
  - D3: planning 入口 guard（kickoff `poc_death_date` 未過期 → 豁免；fast-track 不觸及）
  - D4: task-N.md 必填 `structure_refs` 欄位，planning 上游標注（空陣列 ≠ 漏標）
  - D5: spec-mode code-quality-reviewer 回報 drift items；iteration 聚合 `structural_drift`（與 signal_lost 並列）；reconciliation 做 feature 級對照；零新 agent
- **Primary evaluator:** 合成 mini-feature 證據鏈檢查（四環節：生成／注入／消費／驗屍）
- **Pass signal:** 四環節全部可觀測且 evidence refs 0 dangling
- **Fail signal:** 任一環節缺失、任一 evidence ref dangling、或 reviewer verdict 未引用任何 spec id
- **Feedback loop:** 從缺失環節對應的 skill 段落回修，重跑同一 mini-feature 檢查

## Technical Specification

### structure-spec.yaml Schema（新 artifact，template 置於 `skills/planning/templates/structure-spec.yaml`）

```yaml
feature: <feature-name>
spec_path: default          # default | exempt_poc（豁免時本檔僅含此欄位與豁免記錄）
# exempt_poc 時：poc_death_date: "YYYY-MM-DD" + exemption_note，不寫 modules/patterns

modules:
  - id: SS-<n>               # 唯一 id，下游以 id 引用（task structure_refs / reviewer verdict / drift items）
    name: <module-name>
    responsibility: "<一句話>"
    boundary_rationale: "<這個邊界消失了，哪個已存在或已計畫的變動會變貴>"
    evidence:
      type: git_history | planned_task | domain_boundary
      ref: "<path | task-id | scope-anchor>"   # git_history: repo 內路徑；planned_task: index.yaml 的 task id；domain_boundary: 可省略
      machine_verifiable: true                  # domain_boundary 型必為 false
      note: "<一行>"

patterns:
  - id: SP-<n>
    pattern: "<pattern 名>"
    serves_change_reason: "<這個 pattern 服務的變動理由>"
    evidence: { ...同上 }

dependency_rules:
  - id: SD-<n>
    rule: "<依賴方向約束，一句話>"
    evidence: { ...同上 }
```

**證據解析規則（三態，比照 systemic_ref 三分支語意）：**

| 輸入 | 結果 |
|---|---|
| `git_history` ref 存在於 repo / `planned_task` ref 存在於 index.yaml | `resolved` |
| ref 不存在（dangling） | `failure` —— parse failure，明列檔案與 id，絕不靜默跳過 |
| 解析目標本身不可讀（index.yaml 缺失/損壞） | `unknown` —— 標記後過 gate，計入待驗清單，絕不靜默歸入 resolved 或 dropped |

`domain_boundary` 型不進解析：`machine_verifiable: false` 顯式標記，rationale 非空為唯一機器檢查，實質合理性由 reviewer/human 判斷（Evaluation Contract 的 out-of-scope 條款）。

### 五個機制落點的 I/O 三態

1. **Planning spec-path guard**（D3）：`spec_path`（預設）/ `exempt_poc`（`poc_death_date` 存在且 > today）/ `unknown`（date 格式不可解析）→ unknown 不准靜默選邊，過 execution-mode gate 問。過期的 `poc_death_date` = 豁免失效 → spec path（硬性，DC-6）。
2. **Implement 注入**（D4）：task 的 `structure_refs` 欄位 —— 有值（注入對應片段）/ 空陣列（純行為 task，不注入）/ **欄位缺失 = schema violation**（不是空，dispatch 前 FAIL，DC-3）。
3. **Reviewer 模式選擇**（M3）：spec 存在且可讀（spec mode）/ spec 不存在（principles mode）/ spec 存在但不可讀（**UNKNOWN，blocking**，沿用既有 UNKNOWN 語意，DC-4）。verdict 必須聲明所用模式。
4. **Drift 回報**（D5）：drift items 非空 / 顯式空（`drift_items: []` = 檢查過且無漂移）/ 欄位缺失 = 未檢查（不是零漂移，DC-5）。
5. **Validate 抽查**：全部 refs resolved / 任一 dangling（fail，列明細）/ 解析基礎不可用（unknown → gate）。

### Death Cases

| id | 觸發條件 | 謊言（表象） | 真相 | 偵測 |
|---|---|---|---|---|
| DC-1 | agent 為每個結構投資自動生成煞有介事的假引用 | spec 全數附證據，看起來完整 | 引用解析不到 artifact（cargo-cult 證據） | typed ref 機器解析：reviewer per-task + validate-and-ship 終局 0-dangling 檢查；kill condition 2 的直接防線 |
| DC-2 | 主 agent 圖省事把整份 spec 貼進每個 dispatch | 「已注入」形式上成立 | 定向失效，token 稅全額課徵 | 單 task 注入量 > spec 50% 為失效訊號（M2 death condition 的量測基礎），mini-feature 演練時檢查 |
| DC-3 | planning 產出的 task 檔漏掉 `structure_refs` 欄位 | 該 task 被當純行為 task 正常派發 | 漏標與「確認無結構觸及」不可區分 | 欄位必填：dispatch 前檢查，缺失 = FAIL not empty |
| DC-4 | spec 檔存在但 YAML 損壞/不可讀 | reviewer 退回 principles mode 給 PASS | 結構承諾存在但沒人對照 | spec 存在但不可讀 = UNKNOWN（blocking），不准靜默降級 |
| DC-5 | reviewer 從不回報 drift（prompt 沒逼它區分「查過無漂移」vs「沒查」） | 零 drift = 結構健康 | 零可能是瞎 | `drift_items` 欄位必須存在且顯式空；feature 級連續恆零觸發 M5 death condition |
| DC-6 | `poc_death_date` 過期後專案繼續豁免 | 還是 POC | 沒死期的 POC 就是 production | guard 每次 planning 都比對 today；過期 → spec path，豁免不可續期（要延只能改 kickoff 重新記錄） |
| DC-7 | 實作中結構偏離 spec，後續 task 仍被注入過期片段 | dispatch context 看似權威 | spec 已 stale | reviewer drift 三類中的「未申報新邊界」「承諾未兌現」即偵測器；修正歸 iteration（spec 修訂或 code 修正），implement 期間不就地改 spec |
| DC-8 | 機制落地讓 instruction surface 失控膨脹 | 功能都在 | 噪音殺死訊號，重演減法 branch 修掉的病 | 北極星 sub-metric：新增 loaded-context ≤ 200 行；validate 時實測 |

### 減法紀律約束（非 placement，全 task 適用）

- Auto Mode Gate 維持指針段落形式，禁止因新 gate 需求重新膨脹。
- 新 skill 文字優先擴充既有段落/表格，禁止新開平行章節重述 canonical 內容。
- structure-spec.yaml 模板含註解總行數 ≤ 60 行。

## File Map

| 動作 | 路徑 | 責任 |
|---|---|---|
| Create | `skills/planning/templates/structure-spec.yaml` | spec schema 模板（單一 schema 擁有者） |
| Modify | `skills/planning/SKILL.md` | 入口 guard（D3）＋ Step 2.75 spec 生成步驟 ＋ File Map 從 spec 推導 |
| Modify | `skills/planning/task-format.md` | task 必填 `structure_refs` 段（D4） |
| Modify | `skills/research/templates/kickoff.md` | 可選 `poc_death_date` 欄位 |
| Modify | `skills/implement/SKILL.md` | dispatch 前 structure_refs 檢查（DC-3）＋注入規則引用 |
| Modify | `skills/implement/dispatch-template.md` | implementer/reviewer dispatch 增 spec 片段段落（D4/M2） |
| Modify | `agents/code-quality-reviewer.md` | 雙模式（M3）＋ drift items 輸出 schema（D5） |
| Modify | `skills/iteration/SKILL.md` | Step 1 聚合 `structural_drift`（與 signal_lost 並列） |
| Modify | `skills/validate-and-ship/SKILL.md` | reconciliation 結構維度＋evidence 0-dangling 終局抽查 |
| Create | `tests/test_skills/test_structure_spec_contract.py` | 新 artifact/skill 文字的 doc-contract 測試 |
| Modify | `tests/conftest.py` + `tests/fixtures/` | FIXTURE_VERSION bump ＋ fixtures regen（I2） |
| Regen | `dist/`（不入版控） | `samsara-cli convert` 供應鏈同步 |

## File Map Consistency Check（STOP gate）

| Key Decision | 分類 | 對照 |
|---|---|---|
| KD-1: structure-spec.yaml 是 workflow artifact，schema 模板由 planning skill 擁有 | **matches** | template 在 `skills/planning/templates/`，實例在 `changes/<feature>/`（templates 目錄即 schema 擁有者的既有慣例，同 scar-schema.yaml） |
| KD-2: 機制是平台無關 workflow 行為，受益者是使用 samsara 的專案 | **matches** | 全部改動在 `skills/` + `agents/`（converter 自動轉換到各平台）；無任何 `samsara_cli/` code 路徑（Primary evaluator 是 agent artifact inspection，不新增 CLI 面） |
| KD-3: 零新 agent（D5） | **matches** | agents/ 只有 modify（code-quality-reviewer.md），無 create |
| KD-4: drift 聚合歸 iteration、終局對照歸 validate-and-ship | **matches** | 兩個 SKILL.md 各自 modify，職責不交叉 |
| KD-5: 減法紀律（≤200 行 loaded-context、gate 不膨脹） | **out of scope** | 非 placement 決策，以 acceptance + 北極星 sub-metric 約束 |

**結論：無 contradicts，通過 → 進入 task decomposition。**

## Task Decomposition

6 tasks，依賴鏈：task-1 →（task-2, task-3 可平行）→ task-4 → task-5 → task-6。
task-6 即 Primary evaluator 的執行（mini-feature 證據鏈演練），不是額外發明的成功標準。

詳見 `tasks/task-N.md`。
