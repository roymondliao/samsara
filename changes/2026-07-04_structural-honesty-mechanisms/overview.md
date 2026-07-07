# Overview: structural-honesty-mechanisms

## Goal

把結構品質從 review-time gate 提升為 generation-time 規格：結構決策在 planning 被顯式承諾（附證據的變動理由）、在 implement 被定向注入、在 review 被對照驗證、在 iteration/reconciliation 被度量漂移。

## Architecture

新 artifact `changes/<feature>/structure-spec.yaml`（machine-parsable，schema 模板由 planning skill 擁有）是唯一新增物；其餘全部是既有管道的擴充 —— planning 入口 guard、task 檔 `structure_refs` 欄位、dispatch 片段注入、code-quality-reviewer 雙模式、iteration 聚合、reconciliation 對照。零新 agent、零 samsara_cli code 變更。

## Tech Stack

Markdown skills + agent 定義（平台無關，經 samsara-cli convert 到 dist/）；pytest doc-contract 測試（`tests/test_skills/`）；YAML artifacts。

## Key Decisions

- **KD-1 spec 擁有權**：structure-spec.yaml 實例住 `changes/<feature>/`，schema 模板住 `skills/planning/templates/`（同 scar-schema.yaml 慣例）—— planning 是唯一生成者。
- **KD-2 平台無關**：受益者是使用 samsara 的專案；全部改動在 `skills/` + `agents/`，無任何 samsara_cli code 路徑。
- **KD-3 零新 agent**：drift 回報由既有 code-quality-reviewer 承擔（雙模式），不新增 structural-auditor。
- **KD-4 職責分工**：drift 聚合歸 iteration（`structural_drift` 與 signal_lost 並列不混計）；終局對照歸 validate-and-ship reconciliation；終局 0-dangling 抽查歸 validate-and-ship。
- **KD-5 減法紀律**：新增 loaded-context ≤ 200 行；spec 模板 ≤ 60 行；Auto Mode Gate 指針段落不得膨脹。
- **D2 證據三態**：`git_history`/`planned_task` 機器解析（resolved/failure/unknown 三態，dangling = parse failure）；`domain_boundary` 顯式 `machine_verifiable: false`，不假裝可驗證。
- **D3 豁免規則**：kickoff `poc_death_date` 未過期 → exempt_poc（記錄而非跳過）；過期 → 強制 spec path；格式不可解析 → unknown 過 gate。fast-track 完全不觸及。
- **D4 上游標注**：task-N.md 必填 `structure_refs`（空陣列 ≠ 欄位缺失；缺失 = dispatch 前 FAIL）。

## Death Cases Summary

1. **DC-1 cargo-cult 證據**：agent 為結構投資生成解析不到的假引用 —— typed ref 機器解析（reviewer per-task + validate 終局 0-dangling）是唯一防線；此防線失效即 kill condition 2。
2. **DC-4 spec 不可讀時靜默降級**：spec 存在但損壞，reviewer 若退回 principles mode 給 PASS，結構承諾就沒人對照 —— 必須 UNKNOWN blocking。
3. **DC-5 drift 恆零假象**：`drift_items` 欄位缺失 ≠ 零漂移；顯式空陣列才是「查過且乾淨」，缺欄位是 parse failure。

## File Map

- `skills/planning/templates/structure-spec.yaml`（create）— spec schema 模板，單一 schema 擁有者
- `skills/planning/SKILL.md`（modify）— 入口 guard + Step 2.75 spec 生成 + File Map 從 spec 推導
- `skills/planning/task-format.md`（modify）— 必填 `structure_refs` 段
- `skills/research/templates/kickoff.md`（modify）— 可選 `poc_death_date` 欄位
- `skills/implement/SKILL.md`（modify）— dispatch 前 structure_refs 檢查
- `skills/implement/dispatch-template.md`（modify）— spec 片段注入段落
- `agents/code-quality-reviewer.md`（modify）— 雙模式 + drift_items 輸出
- `skills/iteration/SKILL.md`（modify）— structural_drift 聚合
- `skills/validate-and-ship/SKILL.md`（modify）— reconciliation 結構維度 + 0-dangling 抽查
- `tests/test_skills/test_structure_spec_contract.py`（create）— doc-contract 測試
- `tests/conftest.py` + `tests/fixtures/`（modify/regen）— FIXTURE_VERSION bump + fixtures
- `dist/`（regen，不入版控）— samsara-cli convert 供應鏈同步
