# Task 5: Integration validation — run reviewer on 3 fixtures, document results

## Context

Read: overview.md

此 task 執行整個 feature 的 end-to-end validation：實際 dispatch 新建的 `samsara:code-quality-reviewer` on 3 個 fixture files（junior / clean / over-engineered），收集 output，對照 acceptance.yaml 的 scenarios 判斷是否符合 spec。

此 task **不** 試圖自動化 agent dispatch（Claude Code subagent 難以在 CI 可重現 dispatch）——而是用 manual validation procedure + 人工判讀結果 + 書面記錄。

若驗證結果和 acceptance.yaml 不符，代表 Task 1 (reference) 或 Task 2 (agent prompt) 或 wiring (Task 3/4) 有問題，需回頭修。此 task 是整個 feature 的 gate。

## Files

- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/tests/samsara/code-quality-reviewer/fixtures/junior.py`
  - Source: copy from `hooks/scripts/observe-learnings.py`
- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/tests/samsara/code-quality-reviewer/fixtures/clean.py`
  - Source: copy from `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-must-output.py`
- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/tests/samsara/code-quality-reviewer/fixtures/over_engineered.py`
  - Source: copy from `changes/2026-04-19_yin-coding-spirit/experiment/outputs/en-is-output.py`
- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/tests/samsara/code-quality-reviewer/validation-procedure.md`
  - Manual dispatch steps, expected outcomes, result recording template
- Create: `/Users/yuyu_liao/personal/kaleidoscope-tools/tests/samsara/code-quality-reviewer/validation-results.md`
  - Actual dispatch output from 3 fixtures + pass/fail judgment per acceptance scenario

## Death Test Requirements

- **Fixture content immutability**: 三個 fixture 必須和 source code 完全相同（byte-for-byte）；用 md5 verify
- **Dispatch recording completeness**: validation-results.md 必須記錄每個 fixture 的完整 reviewer output（不可只記 PASS/FAIL summary）
- **Acceptance mapping test**: 每個 acceptance scenario 必須有明確的 fixture 對應 + 實際結果 + 判斷
- **Scope boundary verification**: 在 junior fixture 上，reviewer output 不得出現 "silent except"（應由 yin reviewer 抓，不應 duplicate）
- **PASS evidence test**: 在 clean fixture 上，reviewer 若回 PASS 必須附具體 file:line 觀察

## Implementation Steps

- [ ] Step 1: 建立 `tests/samsara/code-quality-reviewer/` 目錄結構
- [ ] Step 2: Copy 三個 fixture files (bash `cp`)，記錄 md5 hash
- [ ] Step 3: 寫 `validation-procedure.md`：對每個 fixture 的 dispatch 步驟 + 預期結果（引用 acceptance.yaml）
- [ ] Step 4: 用 Agent tool dispatch `samsara:code-quality-reviewer` on fixture 1 (junior.py)
  - 預期: FAIL + Critical ≥ 3 (main() 職責過多 + contract 不明 + silent except 無 rationale)
- [ ] Step 5: Dispatch on fixture 2 (clean.py)
  - 預期: PASS，至少 1 具體 file:line 觀察
- [ ] Step 6: Dispatch on fixture 3 (over_engineered.py)
  - 預期: Important ≥ 1 (over-abstraction for single-script)
- [ ] Step 7: 把 3 個 output 貼進 `validation-results.md`，逐項對照 acceptance.yaml
- [ ] Step 8: **判斷 gate**：
  - 若 3 個 fixture 都符合預期 → feature 驗證通過，標記 index.yaml status=done
  - 若任一不符 → 寫 scar report 記錄差異，回頭修對應的 task (不要在此 task 嘗試 fix)
- [ ] Step 9: 寫 scar report
- [ ] Step 10: Commit (含 fixture files + procedure + results)

## Expected Scar Report Items

- Potential shortcut: dispatch 只跑 1 次；該跑至少 2 次確認 output 一致性（variance check）
- Potential shortcut: 貼 output 但沒逐條對照 acceptance.yaml，只寫「大致符合」
- Potential shortcut: 在 clean fixture 上 agent 回 PASS 無 file:line；被視為通過（實應視為 malformed output = FAIL）
- Potential shortcut: 碰到 acceptance 不符時，在此 task 直接修 agent prompt（scope 外，應 route 回 Task 2）
- Assumption to verify: `samsara:code-quality-reviewer` 被 Agent tool 正確辨識（Claude Code agent registry 更新）
- Assumption to verify: 三個 fixture 的 expected outcomes 在實際 dispatch 下穩定復現（可能需要 2-3 次 dispatch 取 majority）

## Acceptance Criteria

Covers:
- "Silent false PASS on known-junior code" — fixture 1 驗證
- "Success - clean Pythonic refactor PASSes with evidence" — fixture 2 驗證
- "Success - known over-engineered code flagged correctly" — fixture 3 驗證
- "Scope violation — duplicating yin reviewer" — fixture 1 同時檢查（scope boundary verification）
- "Rubber-stamp PASS without evidence" — fixture 2 同時檢查（PASS evidence requirement）
