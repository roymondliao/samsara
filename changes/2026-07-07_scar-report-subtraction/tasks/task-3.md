# Task 3: validate_format.py 長度預算／legacy-form／槽位必填檢查＋行為測試

## Context

Read: overview.md（seam: format-vs-judgment、Key Decisions D2＋預算數值）

validate_format.py 現有 6 類機械檢查（scar-parse/dual-face/forced-by-resolves/seam-resolves/systemic-ref/debt-consistency），零長度檢查 —「寫長不會被抓」是冗長的誘因根源。本 task 加上牙齒。**格式與 judgment 的邊界不動**：行數/字元數是機械事實可進 validator；「夠不夠白話」是 judgment 永不進。

新格式（task-2 已定案於 schema）：`what`/`bites_when`/`where` 必填槽位、`accepted_because` 可選；`systemic_ref` 條目形不變；`assumptions_made` 三欄不變；`structural_decisions` 不變。validator 只在新 feature 的 implement handoff 執行（main 吃單一 feature-dir，無全歷史掃描），故新檢查可嚴格、不需 grandfather 邏輯。

## Files

- Modify: `skills/implement/scripts/validate_format.py`
- Test: `tests/test_skills/test_format_validators.py`

## Death Test Requirements

- Test: over-budget 各型 fixture 必產 `length-budget` finding（exit 1）：item 7 行、欄位 250 chars、narrative 11 行、report 91 行、structural entry 11 行 — 每型至少一例
- Test: folded scalar（`>`）塞 400 chars 單欄位 → char cap finding（DC-E：char 上限兜底行數計法差異）
- Test: 新 report 的 known_shortcuts 用 `description` dict 或 plain string → `legacy-form` finding（DC-A 預算逃逸封死）；`systemic_ref` 條目**不**觸發 legacy-form
- Test: 槽位必填缺失（有 `what` 無 `bites_when`／無 `where`）→ finding（沿 dual-face 檢查風格）
- Test: 既有 clean fixture（SCAR_OK）與新格式 clean fixture 均 exit 0 — 新檢查零誤傷
- Test: exit 2（unknown）路徑不退化：無 scar-reports/ 目錄仍 CANNOT VALIDATE
- Test: 預算數值防漂移 — schema 預算表（skills/implement/templates/scar-schema.yaml）宣告的五個數值必須與 validate_format.py 模組層常數一致（從 schema 文本解析數字比對常數；兩處必須同值是機械事實，可進 validator 測試）— 任一處單獨改動即紅

## Unit Test Contract

- Contract source: validate_format.py 的 emitted output（`FINDING <class>: <msg>` 行格式＋exit code 0/1/2）— 既有測試同款：importlib 載入、對 findings 列表做 `any(substring)` 斷言，不釘內部函式
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫 death tests（上列六組，fixtures 用 tmp_path 合成，沿 SCAR_OK 模式）
- [ ] Step 2: 跑 death tests — 確認紅
- [ ] Step 3: 寫 unit tests（clean 新格式 fixture 過檢、finding 訊息含實測值與上限）
- [ ] Step 4: 跑 unit tests — 確認紅
- [ ] Step 5: 實作：`length-budget` 檢查（欄位 char 上限 what/bites_when/accepted_because/resolution/note ≤200、where ≤120；item ≤6 實體行；structural entry ≤10；narrative ≤10；report 總行數 ≤90 — 數值寫成模組層常數，與 schema 預算表同值）；`legacy-form` 檢查（新 report 的 shortcuts/silent 條目含 `description` 鍵或為 plain string → finding，systemic_ref 條目豁免）；槽位必填檢查。docstring 檢查類清單同步更新
- [ ] Step 6: `uv run pytest tests/` 全綠
- [ ] Step 7: 寫 scar report（新槽位格式；本 task 起 validator 有預算牙齒，跑 validator 自檢）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Potential shortcut: 「實體行」的計法（YAML 原始行 vs 解析後值）需擇一 — 記錄選擇與其被 folded/literal scalar 影響的邊界（char cap 是兜底）
- Assumption to verify: legacy-form 檢查不影響 `assumptions_made`（其本就用 `assumption` 鍵非 `description`）
- Assumption to verify: report 總行數計的是檔案實體行（含註解與空行）— 若計非空行，schema 預算表措辭需一致（與 task-2 同值同義）
- Potential silent failure: item 行數以 YAML dump 重算會與檔案原始行不符 — 必須從原始文本計，或明確以欄位 char cap 為主、行數為輔

## Acceptance Criteria

- Covers: "Silent failure - over-budget report passes validator"
- Covers: "Silent failure - budget evasion via legacy description blob"
- Covers: "Silent failure - folded scalar defeats line counting"
- Covers: "Degradation - validator cannot validate is unknown, never pass"
- Covers: "Success - clean slot-form report validates clean"
