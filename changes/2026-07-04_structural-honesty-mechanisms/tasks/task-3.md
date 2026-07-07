# Task 3: code-quality-reviewer 雙模式（spec/principles/UNKNOWN）+ drift_items 輸出 schema

## Context

Read: overview.md

本 task 建立「消費」環節。前置事實（task-1 已完成，此處直接給定）：
- `changes/<feature>/structure-spec.yaml` 存在時含 entries（id: SS-n/SP-n/SD-n），每條有 boundary_rationale/serves_change_reason 與 typed evidence
- reviewer dispatch 會收到 task 觸及的 spec 片段（含 id）

本 task 的規則（pre-thinking D5 + M3 + DC-1/DC-4/DC-5 定案）：
1. **模式三態**：dispatch 含 spec 片段且可讀 → **spec mode**；dispatch 註明 `structure_spec: absent` → **principles mode**（現行 9 原則不變）；spec 應存在但不可讀/損壞 → **UNKNOWN（blocking）**，沿用 agent 既有 UNKNOWN 語意。verdict 必須聲明所用模式。
2. **Spec mode 職責**（在 9 原則之上疊加，非取代）：
   - 對照實作與注入的 spec 條目：引用 entry id 逐條判定
   - 解析每條 evidence 的 ref（`planned_task` → index.yaml 有此 task id；`git_history` → repo 路徑存在）；dangling → 列為 finding（DC-1 防線第一層）
   - `domain_boundary` 型：只驗 rationale 非空 + `machine_verifiable: false` 標記存在
3. **drift_items 輸出**（必含欄位）：三類 —— `undeclared_boundary`（實作出現 spec 未承諾的新邊界）/ `violated_boundary`（spec 承諾的邊界被跨越）/ `abandoned_commitment`（spec 條目實作未兌現）。**顯式空陣列 = 查過無漂移；欄位缺失 = 未檢查（下游讀作 parse failure）**（DC-5）。
4. 每個 drift item 引用 spec entry id（undeclared 型無 id 可引，改引檔案路徑）。

減法紀律：agent 定義修改 ≤ 60 行淨增；疊加在既有 9 原則結構上，不重寫。

## Files

- Modify: `agents/code-quality-reviewer.md`（模式選擇三態 + spec mode 職責 + drift_items 輸出 schema + verdict 模式聲明）
- Modify: `tests/test_skills/test_structure_spec_contract.py`（追加測試類，檔已存在）

## Death Test Requirements

追加到 `tests/test_skills/test_structure_spec_contract.py`：

- Test: agent 定義必含「spec 存在但不可讀 → UNKNOWN」語句，且不得含「退回 principles mode」的降級路徑（DC-4）
- Test: agent 定義必含 drift_items 三類名稱與「欄位缺失 ≠ 空陣列」語句（DC-5）
- Test: agent 定義必含 evidence ref 解析職責與 dangling → finding 語句（DC-1）
- Test: agent 定義必含 verdict 模式聲明要求（spec mode / principles mode 必須寫明）

## Unit Test Contract

- Contract source: **documented artifact shape** —— `agents/code-quality-reviewer.md` 的 drift_items 輸出 schema（三類名 + 空/缺失語意）與模式三態語句。測試斷言文件化 shape/語句存在，不斷言實作細節。

## Implementation Steps

- [ ] Step 1: Write death tests（上列 4 項）
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: evidence 解析由 LLM reviewer 執行（讀 index.yaml 比對 id），非 code 執法 —— cargo-cult 證據的防線本身是 prose-executed，這是 kill condition 2 的殘餘風險，如實記錄
- Assumption to verify: reviewer 同時收到 spec 片段與 index.yaml 內容才可能解析 planned_task ref —— dispatch 是否供給 index.yaml？缺了就是解析的靜默盲區（需與 task-2 的 dispatch 格式對齊，若缺記 assumption）
- Potential shortcut: drift 判定的「邊界被跨越」對 markdown/skill 類 codebase 如何觀測 —— 判準模糊處如實記錄

## Acceptance Criteria

- Covers: "Silent failure - spec 存在但不可讀時 reviewer 靜默降級為 principles mode"
- Covers: "Silent failure - cargo-cult 證據通過審查"（reviewer 層防線）
- Covers: "Silent failure - drift 欄位缺失被讀作零漂移"（生產端語意）
