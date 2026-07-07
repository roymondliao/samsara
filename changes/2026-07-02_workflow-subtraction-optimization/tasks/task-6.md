# Task 6: fast-track quality checklist 改為只記違規 + reviewed 聲明

## Context

Read: overview.md

現況：`fast-track.yaml` 的 `quality_checklist` 要求四個固定條目（C5/C6/C7/C8）各附 `checked` 與 `note`，且每個 note 都要警告「must be specific, not a template copy」——需要防呆警語的模板欄位，就是它在產生 boilerplate 的證據。改法：只記錄**發現的違規**；空違規清單＝檢查過且乾淨——但必須伴隨一行 reviewed 聲明（列出被檢查的準則），否則無法區分「查過沒問題」與「根本沒查」（DC7）。

## Files

- Modify: `skills/fast-track/SKILL.md` — Step 4 的 quality 檢查敘述與 Output 範例改為新結構：
  ```yaml
  quality_review:
    reviewed_criteria: [C5, C6, C7, C8]   # 必填——聲明檢查發生過；缺此行 = 未檢查
    violations: []                        # 只記違規；空 = 檢查過且乾淨
    # 有違規時：
    # violations:
    #   - criterion: C5
    #     finding: "<具體觀察>"
  ```
  並明文：「缺 `reviewed_criteria` 的空 violations 清單視為未檢查，不得 commit」。Yin-Side Constraints 的 Quality symmetry 條款同步措辭。
- Modify: `skills/fast-track/templates/fast-track.yaml` — quality_checklist 區塊替換為上述 quality_review 結構。
- Test: `tests/test_skills/test_fast_track_quality_review.py`（新）

## Death Test Requirements

- Test: SKILL.md 缺「缺 reviewed_criteria 的空清單＝未檢查」條款時轉紅（DC7：空清單的雙義性未被封死）
- Test: 模板若同時殘留舊 quality_checklist 與新 quality_review 結構時轉紅（兩套並存）
- Test: SKILL.md 的 Quality symmetry 約束（fast-track review 必須同時查 yin 與 quality 兩面）被刪時轉紅（防減法誤殺守護）

## Unit Test Contract

- Contract source: 文件化 artifact shape——`templates/fast-track.yaml` 的 quality_review 欄位結構（reviewed_criteria 必填、violations 列表）、SKILL.md Step 4 的條款。concept-token 斷言
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal doc/template changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 「reviewed_criteria 列了但沒真查」在 doc 層無法防（`systemic_ref: doc-vs-runtime-obedience`）；kickoff 死亡條件：違規紀錄率長期為零且出現 C5–C8 回歸時回退為顯式勾選
- Assumption to verify: 歷史 fast-track.yaml（如 changes/2026-06-27、2026-06-29 等 fast-track 記錄）不需回填新格式——舊格式容忍條款是否需要寫進 SKILL.md（讀取端只有人眼，可能不需要；記錄判斷）

## Acceptance Criteria

- Covers: "Silent failure - fast-track 空違規清單無法區分「查過」與「沒查」"
