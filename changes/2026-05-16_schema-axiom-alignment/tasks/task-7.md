# Task 7: Cross-doc grep death test verification script

## Context

Read: `../overview.md`、`../2-plan.md` 與 `../acceptance.yaml`

本 task 是 feature 的最終 verification——把 task-1~6 各自的 grep 死路測試**整合為單一可重跑的 verification script**。

設計 invariant：
- 腳本必須**包含 anti-test**——驗證自己的 grep 規則能抓到舊詞彙。沒 anti-test 的 grep script 是 silent_failure 候選
- 腳本必須**指明檔名 + 行號**——對齊 Samsara「驗屍可被執行」（每次 failure 留下可定位的證據）
- 腳本必須**幾秒內完成**——對齊 develop.md「Fast Track」精神（驗證不該是負擔）

## Files

- Create: `tests/cross_doc_grep.sh` — 主驗證腳本
- Create: `tests/cross_doc_grep_fixtures/` — anti-test fixtures 目錄
- Create: `tests/cross_doc_grep_fixtures/should_fail.txt` — 故意含 `type: death_path` 字串
- Create: `tests/cross_doc_grep_fixtures/should_pass.txt` — 故意只含新 enum

## Death Test Requirements

本 task 的 verification 是 **meta-verification**——script 自己的死路測試：

- Test (anti-test): `bash tests/cross_doc_grep.sh tests/cross_doc_grep_fixtures/should_fail.txt` 必須以 exit 1 結束並印出 fixture file:line
- Test (anti-test): `bash tests/cross_doc_grep.sh tests/cross_doc_grep_fixtures/should_pass.txt` 必須以 exit 0 結束
- Test (real): `bash tests/cross_doc_grep.sh` （無參數 = 跑全 repo）必須以 exit 0 結束（前提：task-1~6 已完成）
- Test (boundary fail): 若 script 被執行於 task-1~6 未完成狀態，必須以 exit 1 結束並明確指出哪些 task 漏改

## Implementation Steps

- [ ] Step 1: 寫 anti-test fixtures
  - `should_fail.txt`: 內含 `type: death_path` literal、`death path` prose 等故意違規字串
  - `should_pass.txt`: 內含 `type: silent_failure`、`type: boundary_fail`、`boundary_fail_conditions` 等合規字串
- [ ] Step 2: 寫 `tests/cross_doc_grep.sh` 主邏輯，覆蓋以下檢查：
  - **Check 1 (skills/)**: `grep -rn "type: death_path" skills/` 必須 0 hits
  - **Check 2 (skills/ prose)**: `grep -rn -i "death.path" skills/` 必須 0 hits（無視 case / 連字號）
  - **Check 3 (scar-schema parallel)**: `grep "silent_failure_conditions" skills/implement/templates/scar-schema.yaml` 與 `grep "boundary_fail_conditions" skills/implement/templates/scar-schema.yaml` 都必須 ≥1 hit
  - **Check 4 (develop.md self-application)**: `grep -i "self.application" docs/develop.md` 與 `grep "L97" docs/develop.md` 都 ≥1
  - **Check 5 (develop.md workaround cases)**: 3 個 case 名稱字串 grep 都 ≥1
  - **Check 6 (README 中英對應)**: `grep -c "silent_failure\|silent failure\|靜默失敗" README*.md` 兩檔案差距 ≤ 2
  - **Check 7 (legacy markers)**: enumerate `changes/2026-*` 每個目錄（除本 feature 外）必須含 `_LEGACY_IMPRECISE.md`
  - **Check 8 (本 feature 不含 marker)**: `changes/2026-05-16_schema-axiom-alignment/` 不可含 `_LEGACY_IMPRECISE.md`
  - **Check 9 (acceptance.yaml self-bootstrap)**: 本 feature 的 acceptance.yaml 不可含 `type: death_path`
- [ ] Step 3: Script 每個 check 失敗時必須 print 明確 message：`FAIL [Check N]: <file>:<line> - <reason>`
- [ ] Step 4: Script 最後印 summary：`PASS: all N checks passed` 或 `FAIL: M of N checks failed`
- [ ] Step 5: 跑 anti-test fixtures——確認 should_fail.txt 觸發 exit 1，should_pass.txt 觸發 exit 0
- [ ] Step 6: 跑全 repo 驗證——確認 task-1~6 完成狀態下 exit 0
- [ ] Step 7: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 8: 寫 scar report → `../scar-reports/task-7-scar.yaml`，附 script 跑出的全 repo 驗證輸出

## Expected Scar Report Items

- Potential shortcut: Script 只 cover 9 checks，但若 task-1~6 改動範圍超出本 plan 預估（例如新加了 skill），script 不會自動 cover 新檔——必須在 scar 標記「script 範圍 == 本 plan File Map 範圍，超出需手動擴展」
- Potential shortcut: grep 規則太嚴（false positive）或太鬆（false negative）。Anti-test 只能 cover 兩個極端 case，中間地帶（例如「kill path」、「dead lock」這類無關詞彙）需 manual review
- Potential shortcut: Script 用 bash 寫——若團隊未來改用 python 測試框架，bash script 可能變孤兒。本 task 預設「bash 是最低依賴」
- Assumption to verify: `tests/` 目錄是否已存在？若不存在，本 task 同時建立此目錄。預設「不存在則建立，不破壞既有 conventions」
- Assumption to verify: Script 是否需要加入 pre-commit hook？預設「不在本 task 範圍」——pre-commit 整合屬於下一階段
- Assumption to verify: Script 跑時間是否符合「幾秒內」期待？預設「在 repo 規模下足夠快」——若實測 > 5s 視為設計失敗候選

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - grep 死路測試自身偽 pass"（本 task 是此 death case 的直接修復——anti-test 即為防範機制）
- Covers: "Happy path - 全部 7 task 完成 + cross-doc grep 全綠"（本 task 是 happy path 的終點驗證）
- Covers: "Happy path - acceptance.yaml self-bootstrap 驗證"（Check 9 直接驗證此 scenario）
