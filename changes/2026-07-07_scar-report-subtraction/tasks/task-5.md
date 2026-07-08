# Task 5: Golden re-expression fixture＋誠實無損對照＋三代混合聚合測試

## Context

Read: overview.md（seam: write-read-boundary、Death Cases DC-B、Key Decision D6）

decision-002 的附帶義務：以歷史最惡劣 scar report（`changes/2026-07-02_workflow-subtraction-optimization/scar-reports/task-4-scar.yaml`，232 行，單條目最長 60 行）用第三代槽位格式重寫，證明「預算不傷誠實」（kill condition #3 的實證）。原檔**只讀不改**。

同時補 DC-B 防線：aggregator 三代格式（plain string／description dict／槽位形）的計數行為測試 — 斷言對象是 `skills/iteration/SKILL.md` Step 1 成文的世代識別契約（task-1 產物）。

第三代格式參考（task-2 定案的 schema）：`what`/`bites_when`/`where` 必填 ≤200/200/120 chars、item ≤6 行、narrative ≤10 行、report ≤90 行。

## Files

- Create: `tests/fixtures/scar_reports/golden_task4_slot_form.yaml`
- Create: `tests/fixtures/scar_reports/mixed_generation/`（三代混合 fixture：plain-string、description-dict、slot-form 各含 deferred 條目）
- Create: `changes/2026-07-07_scar-report-subtraction/golden-re-expression.md`（誠實無損對照清單）
- Test: `tests/test_skills/test_format_validators.py`（golden 過 validator clean）
- Test: `tests/test_skills/test_scar_schema_noise_rules.py` 或同目錄新檔（三代聚合計數測試）

## Death Test Requirements

- Test: 三代混合 fixtures 依世代識別契約計數 — 任何一代的 items（含 deferred）被丟失 → 紅（DC-B；計數必須等於實際條目數）
- Test: golden fixture 若超任何預算（>90 行、item >6 行、欄位超 char cap）→ validator 紅（golden 本身被預算約束，不得特赦）
- Test: 槽位形 `deferred_to_feature_iteration: true` 與 `status: resolved` 條目在聚合語意下與第二代行為一致（resolved 排除於 remaining、deferred 納入）

## Unit Test Contract

- Contract source: (a) validate_format.py 的 emitted output（golden → exit 0）；(b) `skills/iteration/SKILL.md` Step 1 成文世代識別契約（documented artifact shape）— 聚合測試以合成讀取器對照該契約行為，不釘 iteration 內部措辭細節
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫 death tests（三代計數、golden 預算約束）
- [ ] Step 2: 跑 — 確認紅（fixtures 尚不存在）
- [ ] Step 3: 重寫 golden：逐條分類原 232 行內容 —— (a) 真疤 → 槽位條目；(b) review 裁決史／HONESTY CORRECTION → 對照清單標「→ review-record.md」；(c) 行數統計表 → 標「→ commit message」；(d) 驗證過程 → verified assumption 的 pointer note；(e) 無讀者辯護文 → 標「刪除＋一行理由」。產出 fixture（≤90 行）＋ golden-re-expression.md 對照清單（原報告**每一條**內容都有去向，零靜默丟棄）
- [ ] Step 4: 建三代混合 fixtures＋聚合計數測試
- [ ] Step 5: 實作至全綠；跑 `validate_format.py` 於 golden fixture 所在測試目錄結構驗證 clean
- [ ] Step 6: `uv run pytest tests/` 全綠
- [ ] Step 7: 寫 scar report（新槽位格式，過 validator）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Assumption to verify: 對照清單「誠實無損」的判定含 judgment 成分 — 這正是 supporting artifact 非 Primary 的原因（decision-002）；scar 記錄哪些條目的取捨最接近邊界
- Potential shortcut: 三代混合 fixture 的聚合測試是「測試層模擬讀取」，非真跑 iteration skill — 契約文字與模擬讀取器之間仍有 doc-vs-runtime 縫隙，考慮 systemic_ref: doc-vs-runtime-obedience
- Potential silent failure: golden 若把原文某條「真疤」錯分類為「辯護文刪除」— 對照清單的逐條可追溯性就是偵測面，reviewer 抽查

## Acceptance Criteria

- Covers: "Silent failure - third-generation items dropped from aggregation"
- Covers: "Success - golden re-expression proves honesty survives budget"
