# Task 5: 供應鏈同步 — doc-contract 測試完備 + FIXTURE_VERSION bump + fixtures regen + dist regen + 全測試綠

## Context

Read: overview.md

前四個 task 已修改：`skills/planning/`（SKILL.md、task-format.md、templates/structure-spec.yaml 新增）、`skills/research/templates/kickoff.md`、`skills/implement/`（SKILL.md、dispatch-template.md）、`agents/code-quality-reviewer.md`、`skills/iteration/SKILL.md`、`skills/validate-and-ship/SKILL.md`，並累積了 `tests/test_skills/test_structure_spec_contract.py`。

本 task 是多平台供應鏈的同步收尾（pre-thinking I2 的吸收點）：
1. **既有測試套件全綠**：skill 文字改動可能觸發 `tests/test_contract_bound_tests/`（planning/reviewer 契約 token）、`tests/test_skills/test_planning_placement_check.py`、`test_placement_review_dataflow.py` 等既有 doc-contract 測試 —— 逐一修復（更新 token 清單/斷言，**不得為過測而弱化既有守護行為**）。
2. **Fixtures regen**：`tests/fixtures/source/` 若鏡像了被改的 skill 檔需同步；`tests/fixtures/expected/{codex,gemini-cli}/` 重生（新 template structure-spec.yaml 會出現在轉換輸出中）；`tests/conftest.py` 的 `FIXTURE_VERSION = "0.8.0"` bump 到 `0.9.0`。
3. **dist regen**：`source .venv/bin/activate && uv run samsara-cli convert --platform codex && uv run samsara-cli convert --platform gemini-cli`（dist/ 不入版控，regen 是驗證轉換不炸）。
4. **converter 驗證**：`uv run samsara-cli validate --platform codex`（注意 ISSUE-002：main 上已有 42 個既有 issues，本 task 的通過標準是**不新增** issue，不是歸零）。

環境紀律（AGENTS.md 強制）：`uv run pytest <path>`，先 `source .venv/bin/activate`；pre-commit 於 commit 時跑（主 agent 負責 commit，本 task 不 commit）。

## Files

- Modify: `tests/conftest.py`（FIXTURE_VERSION bump）
- Modify/Regen: `tests/fixtures/source/`、`tests/fixtures/expected/codex/`、`tests/fixtures/expected/gemini-cli/`
- Modify: 既有 doc-contract 測試中因 skill 文字改動而紅的檔案（以實測為準，預期集中在 `tests/test_contract_bound_tests/`、`tests/test_skills/`）
- Regen: `dist/codex/`、`dist/gemini-cli/`（不入版控）

## Death Test Requirements

- Test: fixtures regen 後，`tests/fixtures/expected/codex/` 內必須出現轉換後的 structure-spec 模板（新 template 靜默缺檔 = 多平台輸出不完整 —— I2 的死法）
- Test: 全測試套件跑 `uv run pytest -m "not requires_codex and not requires_gemini"`（CI 同款指令）必須綠 —— 混雜紅測 = 供應鏈斷裂
- 驗證（非新測試）：`samsara-cli validate --platform codex` 的 issue 數不高於基線 42

## Unit Test Contract

- Contract source: **emitted output** —— converter 對新 template 的轉換輸出（`dist/<platform>/` 與 `tests/fixtures/expected/<platform>/` 的實際檔案存在性與格式）。測試斷言轉換輸出的可觀測結果，不斷言 converter 內部實作。

## Implementation Steps

- [ ] Step 1: Write death tests（fixtures 完整性斷言）
- [ ] Step 2: Run death tests — verify they fail（regen 前 expected/ 無新檔）
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source（若 Step 1 已覆蓋則標明）
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement：修既有紅測 → regen fixtures → bump FIXTURE_VERSION → regen dist → 跑 validate 比對基線
- [ ] Step 6: Run all tests — verify they pass（CI 同款指令全綠）
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 修既有紅測時「放寬斷言讓它過」—— 每個被修的測試必須記錄修改理由；為過測而刪除守護行為 = 北極星 invalidation condition 的觸發樣態
- Assumption to verify: validate 基線 42 是否仍準確（自 ISSUE-002 登記後 main 可能又漂移）—— 實測記錄當下基線
- Potential shortcut: gemini-cli 平台的 fixtures 若倚賴本機未裝的 CLI，`requires_gemini` marker 測試被 skip —— skip 不是 pass，如實記錄哪些驗證未執行

## Acceptance Criteria

- Covers: "Success - 儀式淨增量在預算內"（實測 loaded-context 淨增 ≤ 200 行，於此 task 一併量測記錄）
