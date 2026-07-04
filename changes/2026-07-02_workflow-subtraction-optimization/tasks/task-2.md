# Task 2: expiry 移除 — iteration accept 與 ship-manifest rule 2 改為訊號驅動重審

## Context

Read: overview.md

現況：iteration 的 accept 分類強制附 `expiry_date`，ship-manifest.md rule 2 規定「accepted_risks must have expiry dates」。但全 repo（hooks、CLI、tests、skills）沒有任何機制檢查過期——時間驅動的重審承諾是永遠不響的鬧鐘，給虛假安全感。User 決定：刪除 expiry，改為訊號驅動——每個 accept 必須寫明「誰、在什麼可觀測訊號出現時重審」。

## Files

- Modify: `skills/iteration/SKILL.md` —
  - Step 2 triage 的 accept 格式：`(A) Accept — 已知風險，接受（必須附 expiry date + rationale）` 改為 `（必須附 re-review signal：什麼可觀測訊號出現時重審＋誰負責＋rationale）`。
  - Yin-Side Constraints 的「Accept requires expiry」改為「Accept requires re-review signal」——風險接受仍然不是永久的，重審條件從日期改為訊號。
  - Red Flags／範例段中的 expiry 措辭同步。
  - 向後相容條款：舊 iteration-log 的 `expiry_date` 欄位讀取時容忍、不報錯、不要求補填。
- Modify: `skills/validate-and-ship/ship-manifest.md` — rule 2 全文改寫：accepted risks 必附 `re_review_signal`（可觀測條件）與 `owner`；刪除到期日要求；說明理由（本 repo 從無 expiry 消費者，時間驅動已證明是空承諾）。
- Modify: `skills/validate-and-ship/templates/ship-manifest.yaml` — accepted_risks 條目欄位：移除 expiry 類欄位（若存在），加入 `re_review_signal` 與 `owner`；模板註解說明空值不允許。
- Test: `tests/test_skills/test_accept_rereview_signal.py`（新）

## Death Test Requirements

- Test: iteration SKILL.md 缺「accept 必附 re-review signal」條款時轉紅（防 accept 退化成無條件永久豁免——這比舊 expiry 更糟）
- Test: ship-manifest.md rule 2 若同時殘留「expiry」要求與「signal」要求（兩處各說各話）時轉紅（DC8 同型：文件自相矛盾）
- Test: iteration SKILL.md 缺「舊 expiry_date 容忍」條款時轉紅（防舊 log 讀取報錯）

## Unit Test Contract

- Contract source: 文件化 artifact shape——`ship-manifest.md` rule 2 的條款概念（re-review signal ＋ owner ＋ 非永久豁免）、`templates/ship-manifest.yaml` 的 accepted_risks 欄位結構、iteration SKILL.md accept 分類格式。concept-token 斷言，遵循 references/test-contract.md（斷言方向性：必須「要求 signal」而非僅「提到 signal」——防 presence-not-polarity）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal doc changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 「訊號驅動」的訊號本身無 runtime 監測（沒有機制在訊號出現時主動提醒）——與被刪的 expiry 相比，優勢僅在訊號綁定可觀測事件而非流逝的時間；此限制屬 `systemic_ref: doc-instruction-no-code-enforcement`
- Assumption to verify: 歷史 iteration-log 中 expiry_date 的出現位置只在 accept 條目內（若還出現在其他欄位，容忍條款要涵蓋）
- Assumption to verify: 沒有既有測試斷言「expiry」字樣存在（有則同步改寫該測試的斷言目標，不是刪測試）

## Acceptance Criteria

- Covers: "Silent failure - 舊格式 scar 聚合靜默歸零"（舊 expiry_date 容忍部分）
- Covers: happy path 逐項條件之「expiry 移除且 rule 2 改訊號驅動」
