# Task 1: structure-spec schema 模板 + planning guard/生成步驟 + kickoff poc_death_date + task-format structure_refs

## Context

Read: overview.md

本 task 建立「生成」環節：結構決策的 machine-parsable 承諾文件。核心設計（pre-thinking D1-D4 定案）：
- structure-spec.yaml 是 planning 的新產出，schema 模板住 `skills/planning/templates/`（同 scar-schema.yaml 慣例）
- 證據三型：`git_history`（ref = repo 路徑）/ `planned_task`（ref = index.yaml task id）/ `domain_boundary`（無 ref，必帶 `machine_verifiable: false`，rationale 非空）
- 解析三態：resolved / failure（dangling = parse failure，比照 scar-schema.yaml Rule 9 systemic_ref 語意）/ unknown（解析基礎不可讀，標記後過 gate）
- planning 入口 guard：kickoff 有未過期 `poc_death_date` → `exempt_poc`（記錄豁免，不寫 modules）；過期 → 強制 spec path；格式不可解析 → unknown 過 execution-mode gate。fast-track 完全不觸及。
- task-format 新增必填 `structure_refs: [<spec-entry-id>]`（空陣列 = 確認無結構觸及；欄位缺失 = 漏標 = schema violation）

減法紀律：模板含註解 ≤ 60 行；SKILL.md 修改優先擴充既有段落，不新開平行章節；本 task 全部新增 loaded-context 行數控制在 ~120 行內（全 feature 預算 200 行）。

## Files

- Create: `skills/planning/templates/structure-spec.yaml`
- Modify: `skills/planning/SKILL.md`（Prerequisites 後加 spec-path guard；Step 2.5 與 Step 3 之間加 Step 2.75: Structure Spec；Step 4 task 要求清單加 structure_refs；Output 清單加 structure-spec.yaml）
- Modify: `skills/planning/task-format.md`（Required Sections 加 `## Structure Refs` 段 + Rule 6）
- Modify: `skills/research/templates/kickoff.md`（Scope 區塊後加可選 `poc_death_date` 欄位與說明一行）
- Create: `tests/test_skills/test_structure_spec_contract.py`（本 task 建檔，後續 task 追加測試類）

## Death Test Requirements

寫入 `tests/test_skills/test_structure_spec_contract.py`（pytest，本 repo doc-contract 慣例）：

- Test: 模板中 `domain_boundary` 型範例必帶 `machine_verifiable: false` —— 防 DC「假裝可驗證」
- Test: 模板文字必含解析三態 resolved/failure/unknown 與「dangling」「parse failure」字樣 —— 防 unknown 被硬塞成 success/failure
- Test: planning SKILL.md 必含「過期」→ spec path 的硬性規則字樣（DC-6：豁免不可永生）
- Test: planning SKILL.md 的 unknown 分支必含 execution-mode gate 字樣（格式不可解析不准靜默選邊）
- Test: task-format.md 必含「欄位缺失」與「空陣列」的區分語句（DC-3）
- Test: 模板總行數 ≤ 60（減法紀律的機器執法）

## Unit Test Contract

- Contract source: **documented artifact shape** —— `skills/planning/templates/structure-spec.yaml` 的 schema 欄位集（feature/spec_path/modules[].id/.boundary_rationale/.evidence.{type,ref,machine_verifiable,note}/patterns/dependency_rules）與 `skills/planning/SKILL.md`、`task-format.md` 的具名規則語句。單元測試斷言這些文件化的 shape/語句存在且一致，不斷言實作細節。

## Implementation Steps

- [ ] Step 1: Write death tests（上列 6 項，先建 test 檔）
- [ ] Step 2: Run death tests — verify they fail（`uv run pytest tests/test_skills/test_structure_spec_contract.py`）
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal changes（模板 + 三個 modify）to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: guard 的日期比較邏輯只寫在 prose（LLM 執行），無 code 執法 —— doc-vs-runtime-obedience 的已知系統性限制，如實記錄勿隱藏
- Assumption to verify: `scope-anchor`（kickoff 條目引用）是否需要規範 anchor 格式 —— 本 task 若未定義，記為 assumption
- Potential shortcut: kickoff template 欄位新增後，舊 features 的 kickoff 無此欄位 —— guard 必須把「欄位不存在」讀作 spec path 預設，不是 unknown

## Acceptance Criteria

- Covers: "Silent failure - 過期 poc_death_date 繼續豁免"
- Covers: "Degradation - domain_boundary 型證據偽裝已驗證"
- Covers: "Degradation - poc_death_date 格式不可解析"
- Covers: "Success - 真 POC 豁免記錄完整"
- Covers: "Success - 儀式淨增量在預算內"（模板 ≤ 60 行部分）
