# Task 2: implement dispatch 注入 — structure_refs 檢查（缺失=FAIL）+ spec 片段定向注入規則

## Context

Read: overview.md

本 task 建立「注入」環節。前置事實（task-1 已完成，此處直接給定，勿假設未讀）：
- `changes/<feature>/structure-spec.yaml` 存在（machine-parsable；entries 有唯一 id 如 SS-1/SP-1/SD-1）
- task-N.md 有必填 `structure_refs: [<spec-entry-id>]` 欄位（空陣列 = 純行為 task；欄位缺失 = 漏標）

本 task 的規則（pre-thinking D4 + DC-2/DC-3 定案）：
1. **Dispatch 前檢查**：implement 主 agent 讀 task 檔時，`structure_refs` 欄位缺失 → **FAIL（schema violation），不得派發**，回 planning 補標。空陣列 → 正常派發、不注入。
2. **定向注入**：`structure_refs` 有值 → 主 agent 從 structure-spec.yaml 取出對應 id 的條目（含其 evidence 與 boundary_rationale）貼入 implementer dispatch 與兩個 reviewer dispatch。只貼 id 指到的條目，不是整份 spec。
3. **50% 訊號**：單 task 注入量超過 spec 全文 50% = 定向失效訊號，記入該 task scar（不是硬 block，是 M2 death condition 的量測證據）。
4. spec 檔本身不存在（exempt_poc 或舊 feature）→ 注入步驟跳過且在 dispatch 記錄註明 `structure_spec: absent`，與「有 spec 但漏注入」可區分。

減法紀律：dispatch-template.md 用一個新小節（≤ 20 行）；SKILL.md 修改嵌入既有 Per-Task Execution Order 與 Red Flags，不新開章節。

## Files

- Modify: `skills/implement/SKILL.md`（Subagent Context 段加 structure_refs 檢查規則；Red Flags 加「欄位缺失照發」「全量注入」兩條）
- Modify: `skills/implement/dispatch-template.md`（新增 Structure Spec Fragments 小節：注入格式 + absent 註記格式）
- Modify: `tests/test_skills/test_structure_spec_contract.py`（追加測試類，檔已存在）

## Death Test Requirements

追加到 `tests/test_skills/test_structure_spec_contract.py`：

- Test: implement SKILL.md 必含「欄位缺失 = FAIL/schema violation、不得派發」語句，且與空陣列語意可區分（DC-3）
- Test: dispatch-template.md 必含「只注入 structure_refs 指到的條目」與 50% 訊號語句（DC-2）
- Test: dispatch-template.md 必含 `structure_spec: absent` 註記格式（無 spec 與漏注入可區分）
- Test: implement SKILL.md 的 Red Flags 必含對應兩條新紅旗

## Unit Test Contract

- Contract source: **documented artifact shape** —— `skills/implement/dispatch-template.md` 的 Structure Spec Fragments 小節格式（注入條目結構、absent 註記）與 `skills/implement/SKILL.md` 的具名檢查規則語句。測試斷言文件化 shape/語句，不斷言實作細節。

## Implementation Steps

- [ ] Step 1: Write death tests（上列 4 項，追加到既有測試檔）
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 50% 注入量的計算方式（行數？字元數？）若未精確定義，agent 各自解讀 —— 定義並寫死一種，或如實記 assumption
- Assumption to verify: inline mode C（主 agent 自己實作）時注入規則同樣適用 —— SKILL.md 既有的 inline-mode 條款需涵蓋，漏了就是 mode C 的靜默缺口
- Potential shortcut: dispatch 記錄的持久化位置（何處可供 task-6 演練檢查「注入」環節）—— 若只存在對話中，證據鏈第 2 環節不可稽核

## Acceptance Criteria

- Covers: "Silent failure - task 檔缺 structure_refs 欄位被當純行為 task 派發"
- Covers: "Degradation - 定向注入退化為全量注入"
