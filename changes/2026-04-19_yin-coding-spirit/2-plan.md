# Plan: samsara-code-quality-reviewer

## Architecture

建立一個 sibling reviewer agent，與既有 `samsara:code-reviewer`（yin focus）平行運作，在 `samsara:implement` 和 `samsara:iteration` 的現有 review 觸發點並行 dispatch。兩個 reviewer 各自獨立審視（無共享 state、無順序依賴），兩者都 PASS 才允許 commit。

```
          (既有)                                  (新增)
          samsara:code-reviewer                   samsara:code-quality-reviewer
          焦點: yin / system-level                  焦點: clean-code / code-level
          reads: (implicit scope in prompt)        reads: samsara/references/code-quality.md
              │                                       │
              └───────── parallel dispatch ───────────┘
                              │
                      main agent aggregates
                              │
                   both PASS → commit；任一 FAIL → block
```

## Technical Specification

### I/O Contract

**Input**（與既有 code-reviewer 相同格式）：
- `task_title`: string
- `task_goal`: string
- `diff`: string (git diff unified format)
- `files_changed`: list of absolute paths
- `fixture_mode`: bool（可選；用於 Task 5 的 validation fixtures）

**Output States**（三態，不是兩態）：

```yaml
output_states:
  PASS:
    meaning: "所有 8 條 criteria 都滿足，或只有 Suggestion 級別的 issue"
    requires: "每個 criterion 主動確認（不能因為 'agent 沒看到' 就當作滿足）"

  FAIL:
    meaning: "至少一個 Critical 或 Important issue"
    requires: "列出違反的 criterion + file:line + 為什麼是違反"

  UNKNOWN:
    meaning: "無法對此 diff 應用 code-quality review（例如: 純 config / doc / 資料檔）"
    requires: "明確回報 'N/A - diff contains no reviewable code'；不可當作 PASS"
```

**違反 unknown-as-pass 是 defect**：agent 必須明確辨識「這個 diff 不在我的 review 範圍內」，而不是沈默通過。

### 8 條 Criteria（code-level）

| # | Criterion | 陰面問法（判斷用） |
|---|---|---|
| 1 | 可讀性 (Readability) | 下一個接手的人，30 秒內讀懂這段 code 的意圖嗎？ |
| 2 | 可維護性 (Maintainability) | 三個月後 bug fix 時，改一個地方不會踩雷嗎？ |
| 3 | 易拓展 (Extensibility) | 下一個類似的需求，能不能插入而不改動現有 code？ |
| 4 | 易 debug (Debuggability) | 出錯時，錯誤訊息能指向正確位置嗎？ |
| 5 | Reuse | 相同 logic 是否重複？還是有抽出 shared helper？ |
| 6 | 結構明確 (Clear Structure) | module / function 邊界能說出 "why here, not there"? |
| 7 | 優雅邏輯 (Elegant, no extras) | 有沒有多餘的抽象、暫時的變數、未用的參數？ |
| 8 | 無冗餘 (No Redundancy) | 兩處 code 在說同樣的事嗎？改一處不改另一處會分裂嗎？ |

每條 criterion 在 reference 檔中附：
- 陰面判斷問題
- 1+ good example（from en-must-1 / zh-is-1 experiment outputs）
- 1+ bad example（from en-is-1 / hooks/scripts/observe-learnings.py）
- 決策規則（什麼時候 Critical、什麼時候 Important、什麼時候 Suggestion）

### Death Cases（不是 edge cases）

以下是**系統會看起來成功但實際是錯的**條件：

#### Death Case 1: Silent False PASS
- **Trigger**: agent 被餵給明顯 junior-level 的 code（類似 observe-learnings.py），但 agent 沒抓到
- **Lie**: 「這份 code 品質 OK，通過 review」
- **Truth**: code 有 3+ Critical issues，實際是 junior-level
- **Detection**: 用 `hooks/scripts/observe-learnings.py` 作為 known-bad fixture，若 agent 回 PASS → reviewer 本身失效

#### Death Case 2: Compliance Theater
- **Trigger**: implementer 為了過 reviewer，寫出「技術上過 8 條但違反精神」的 code
- **Example**: 為了 "結構明確" 造一次性 class 只被呼叫一次；為了 "無冗餘" 過度抽象讓 code 變難懂
- **Lie**: 「這段 code 過了 Criterion 6，所以結構是好的」
- **Truth**: Criterion 被字面滿足但精神被違反
- **Detection**: Corruption signature——人類 spot-check PASSed code，若 20%+ 被標為 junior-level

#### Death Case 3: Scope Violation (Yin Duplication)
- **Trigger**: reviewer 開始報告 silent rot / dishonest naming 這類 yin issues
- **Lie**: 「我找到一個 Critical: silent except」
- **Truth**: 這是既有 code-reviewer 的 scope，應該由那邊負責；本 reviewer 只應在**結構面**提意見
- **Detection**: 兩個 reviewer 的 issue list 是否出現重複（同一個 file:line 的 issue）；>10% 重複就是 scope 滲透

#### Death Case 4: Unknown-as-PASS
- **Trigger**: diff 內容是 config file / documentation / data fixture / binary
- **Lie**: 「沒看到 code violation，所以 PASS」
- **Truth**: Agent 根本沒有適用的 criteria 可判斷
- **Detection**: Output 應明確標示 `UNKNOWN (N/A)`，而不是 PASS

#### Death Case 5: Parallel Dispatch Silent Skip
- **Trigger**: implement skill 改動後有 bug，只 dispatch 了 code-reviewer，沒 dispatch code-quality-reviewer
- **Lie**: Main agent 看到「code review 通過」就推進
- **Truth**: 只有一個 reviewer 真的跑過，另一個靜默缺席
- **Detection**: Main agent 必須收到**兩份** review output 才能判定 PASS；收到一份就 FAIL with "missing reviewer"

#### Death Case 6: Rubber-Stamp PASS
- **Trigger**: Agent 對每個 diff 都無條件回 PASS（no Critical, no Important）以縮短回應時間或模仿 "看起來 friendly"
- **Lie**: 「這份 code OK」
- **Truth**: Agent 沒真的分析，只是輸出 PASS boilerplate
- **Detection**: PASS rate > 85% 三個月持續；或 PASS output 缺乏具體 file:line 引用

### File Map

| Path | Action | Responsibility |
|---|---|---|
| `samsara/references/code-quality.md` | **Create** | 8 條 criteria + good/bad examples + 決策規則 |
| `samsara/agents/code-quality-reviewer.md` | **Create** | Agent frontmatter + system prompt + output format |
| `samsara/skills/implement/SKILL.md` | **Modify** | 在 step 115 + 142 附近改為 parallel dispatch 兩個 reviewer（兩個區塊分別對應 subagent mode B 和 inline mode A） |
| `samsara/skills/implement/dispatch-template.md` | **Modify** | 在 L72-80 附近加入 code-quality-reviewer dispatch template |
| `samsara/skills/iteration/SKILL.md` | **Modify** | 在 L100 附近改為 parallel dispatch |
| `samsara/skills/fast-track/SKILL.md` | **Modify** | Step 4 checklist 對稱化（加 quality 問題）；fast-track.yaml schema 加 quality_checklist 欄位 |
| `tests/samsara/code-quality-reviewer/fixtures/` | **Create** | 3 個 fixture files (junior / clean / over-engineered) |
| `tests/samsara/code-quality-reviewer/validation-procedure.md` | **Create** | 手動 dispatch 驗證步驟（因 LLM dispatch 難以 CI 化） |

### Path Coverage Matrix

所有可 ship code 的路徑整合狀態：

| 路徑 | 覆蓋方式 | 對應 Task |
|---|---|---|
| `samsara:implement` Mode B (subagent) | Parallel dispatch 兩個 reviewer subagent | Task 3（Line 115 區塊） |
| `samsara:implement` Mode A (inline) | Parallel dispatch 兩個 reviewer subagent（review 階段即使 inline impl 也 dispatch） | Task 3（Line 142 區塊） |
| `samsara:iteration` | Parallel dispatch 兩個 reviewer subagent | Task 4 |
| `samsara:fast-track` | **不 dispatch subagent**；Step 4 inline checklist 加 3-4 條 quality 問題 + yaml schema 加 quality_checklist | Task 6 |
| `samsara:debugging` 小 fix (< 100 行) | **Known gap**——此路徑不加 review（scope 外，debugging 是 regression-focused，非 quality-focused） | 無（明確 out of scope） |
| `samsara:debugging` 大 fix | 自動走 samsara:implement，經 Task 3 覆蓋 | Task 3 間接覆蓋 |

### Dependencies

```
Task 1 (reference)
    │
    ├── Task 2 (agent — uses reference)
    │       │
    │       ├── Task 3 (wire implement — dispatches agent)
    │       │       │
    │       │       └─── ↓
    │       └── Task 4 (wire iteration — dispatches agent)
    │                   │
    │                   └── Task 5 (validation — runs on all fixtures)
    │
    └── Task 6 (fast-track inline checklist — no dispatch, only references)
```

Tasks 3 & 4 can be done in parallel (different files, no shared state).
Task 6 can be done in parallel with Task 2/3/4/5 (depends only on Task 1).

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Reviewer overlap with code-reviewer | High | Explicit scope statement in agent prompt: "Do NOT check for silent rot, dishonest naming — that's the yin reviewer's job" |
| Compliance theater by implementer | Medium | 紀錄 corruption signature in north star；定期 human spot-check |
| Parallel dispatch token cost 上升 | High (and expected) | 接受為設計成本；兩 reviewer 都是 ~100 行 prompt，增量可控 |
| Reference drift over time | Low (initially) | 決定每 3 個月 review 一次 examples 是否仍代表 target quality |
| Reviewer rubber-stamps | Medium | PASS output 必須包含 ≥ 1 具體 file:line 觀察（即使是 Suggestion 層級）；無具體引用 = compliance theater signal |

## Out of Scope (Explicit)

- **不改動既有 `samsara:code-reviewer`**（保持 yin 純度）
- **不自動化 reviewer dispatch 的 CI test**（手動 validation-procedure 即可；自動化是 future work）
- **不做跨專案 generalization**（這次只針對此專案的 samsara 設定；其他專案若採用 samsara 時另議）
- **不寫 anchor in implementer prompt**（Nice-to-have；不阻塞 MVP）
- **不擴充 samsara:debugging 小 fix 路徑**——debugging 本質是 regression-focused (< 100 行 inline fix)，加 review 會破壞 debugging rhythm；此路徑被明確標為 **known gap**，後續若 audit 顯示小 fix 引入 quality 債再重審
