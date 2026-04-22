# Kickoff: samsara-code-quality-reviewer

## Problem Statement

Samsara 的既有 agent 體系在 system-level 有完整的 yin-side 審視（`samsara:code-reviewer` 負責 silent rot、dishonest naming、deletable dead code），但在 code-level 沒有任何 agent 負責傳統 clean-code 品質把關——可讀性、可維護性、可擴展性、易 debug、reuse、結構明確、優雅邏輯、無冗餘。結果是：samsara 產出的 code 可以通過 yin review，但在底層結構上經常呈現 junior-level 風格（扁平 main()、stringly-typed contracts、silent failures、over-classed OOP 等）。

這份 kickoff 提議建立 `samsara:code-quality-reviewer` agent 和配套的 `samsara/references/code-quality.md`，作為既有 `samsara:code-reviewer` 的 parallel sibling，在每個 implementer task 結束後並行 dispatch，兩者都 pass 才 commit。

## Evidence

### 靜態讀 code 的證據

`hooks/scripts/observe-learnings.py`（215 行）展現 junior-level 症狀：
- 8+ 個 silent `except ... pass` 區塊
- `main()` 單一函數做六件事（stdin parse、field extract、project dir resolve、observation build、file append、bridge、auto-purge）
- `state_paths() -> dict` 回傳 stringly-typed 契約
- 通過 samsara:code-reviewer 的 yin 審視，因為這些問題**不在 yin reviewer 的 scope 裡**（yin reviewer 關注 naming honesty、silent rot path，但不關注 function decomposition、contract explicitness 這類 clean-code 議題）

### 實驗證據

`experiment/` 進行了 2×2 factorial 實驗（language × mood，各 3 次 replication，共 12 runs）：
- 主題：refactor `hooks/scripts/observe-learnings.py` 依據不同語氣/語言的 guide
- 結果矩陣詳見 `experiment/experiment-report-phase2.md`
- 關鍵發現：
  - **12/12 runs 都沒有加 observable logging**——這是所有 cell 的共同 blind spot，說明 guide 本身無法完整 cover
  - **en-must cell 3/3 runs 保留原 docstring 幾近逐字**——典型 compliance theater
  - **Cell effect 弱，run-to-run variance 大**——guide 不能獨立保證品質

### samsara 自身的記錄

`samsara/issue.md` 已明確記錄：
> "Root Cause 3: Code reviewer scope does not include architectural compliance."

這個 gap 是 samsara 自己已察覺但尚未填補的已知缺口。

## Risk of Inaction

- samsara 繼續 ship system-level review，但 code-level quality 留給運氣
- 未來 samsara 產出的 code 持續 junior-level，越到後期累積的重構債越重
- 下游 code reviewer（人類）持續承擔「每個 PR 都要從基本面開始指導」的成本
- 「通過 samsara review」和「可維護」之間的信心落差會擴大，最終削弱 samsara review 的可信度

## Scope

### Must-Have (with death conditions)

- **`samsara:code-quality-reviewer` agent definition** (`samsara/agents/code-quality-reviewer.md`, ~100 行 system prompt)
  - Death condition: 若 samsara 架構轉向 generalist agent（反 specialist composition 原則），此 agent 應合併或刪除
- **`samsara/references/code-quality.md`** — 8 條 criteria + 從實驗 outputs 精選的 good/bad examples（en-must-1 的 clean Pythonic = good；en-is-1 的 8-class over-OOP = bad 的代表）
  - Death condition: 若未來採用外部 canonical style guide（Google Python Style Guide、PEP 8 as enforced linter），此 reference 應被外部取代而非自維護
- **修改 `samsara/skills/implement/SKILL.md`** — 在既有 `samsara:code-reviewer` dispatch 旁加入 parallel dispatch `samsara:code-quality-reviewer`
  - Death condition: 若 samsara review 流程改為 single-pass sequential，此 parallel 結構應重構
- **修改 `samsara/skills/iteration/SKILL.md`** — 同上，在 iteration fix 後也並行 dispatch
  - Death condition: 同上
- **更新 `samsara/skills/implement/dispatch-template.md`** — 加入 code-quality-reviewer dispatch template
  - Death condition: 如果 dispatch-template 被廢除，template 隨之消失

### Nice-to-Have

- **Lightweight anchor in implement**：在 `samsara:implementer` 的 system prompt 或 implement skill 的 task prompt 加一句提示：「寫完後自問：這段 code 會過得了 code-quality + yin-side 兩種 review 嗎？」——錨點，不是規範
- **README 更新** — samsara README 的 Agent 表格加入新 agent 的說明

### Explicitly Out of Scope

- **不動既有 `samsara:code-reviewer`** — 保持其 yin 純度，不混入 conventional quality criteria
- **不建立 yin-evaluator 獨立角色** — 先前討論過，但 scope 擴張；封存為 future work
- **不做 statistical validation** — Phase 2 replication (N=3 per cell) 已足夠支撐決策；不擴大到 N=7 或跨檔案驗證
- **不覆蓋其他 review dimensions**（security、performance、API contract）— 同樣的「新 agent」pattern 未來可套用，但這次只做 code quality
- **不處理 guide variance 問題** — Phase 2 暴露的 run-to-run variance 無法單靠 reviewer 消除，但 parallel review 提供 safety net；完整解法（evaluator、human review loop）不在 scope
- **不寫 "陰面 coding 精神" 哲學文件** — 對話中討論過的「精神式 guide」方向被實驗否證（variance 大），改採 reference-driven 具體 criteria

## North Star

```yaml
metric:
  name: "first_pass_rate_on_code_quality_review"
  definition: "samsara:implement 每個 task 的 code，第一次 dispatch samsara:code-quality-reviewer 時直接回 PASS（無 Critical issues）的比例"
  current: "N/A（reviewer 尚未建立；目前所有 task 不經過 code-quality review）"
  target: "40%–65% first-pass rate"
  invalidation_condition: "若 first-pass rate > 85%，reviewer 太寬鬆（rubber-stamping）；若 < 20%，reviewer 太嚴苛（criteria 不實用或 implementer 完全跟不上）。兩端都代表此 metric 本身需修正。"
  corruption_signature: "implementer 學會用「技術上過 8 條但違反精神」的 code 通過——例如為了 'no redundancy' 過度抽象、為了 '結構明確' 造一次性 class。用 human spot-check 抽驗：通過的 code 中有多少會被人類 reviewer 標為 junior-level？>20% 就是 corruption signal。"

sub_metrics:
  - name: "tasks_with_silent_except_blocks"
    current: "未量測；hooks/scripts/ 樣本顯示 ~100% 的 script 有 silent except"
    target: "新 task 中 < 10% 帶有 unmarked silent except（即使刻意 silent 也必須有 rationale comment）"
    proxy_confidence: high
    decoupling_detection: "若 silent except 數降但其他 silent-failure pattern 增加（例如 dict.get(key, default) 濫用），代表 proxy 和 main metric 脫鉤"

  - name: "tasks_with_stringly_typed_contracts"
    current: "未量測；hooks/scripts/ 樣本顯示 state_paths() 等多處使用"
    target: "內部模組間 contracts < 20% 使用 dict[str, Any] 或分隔字串協定"
    proxy_confidence: medium
    decoupling_detection: "若 dataclass 使用增加但 internal dict 轉移到新位置（例如 **kwargs 濫用），代表迴避而非修正"

  - name: "main_function_line_count"
    current: "hooks/scripts/observe-learnings.py main()=111 行"
    target: "新寫的 entry-point function < 30 行，階段清晰可讀"
    proxy_confidence: medium
    decoupling_detection: "若 main() 變短但 helper functions 出現 mega-function（>50 行），代表只是位移"
```

## Stakeholders

- **Decision maker:** User（samsara 主維護者）
- **Impacted teams:**
  - 任何使用 `samsara:implement` / `samsara:iteration` skill 產出 code 的 session
  - 未來擴充其他 review dimension（security、performance）的開發者——這次建立的 pattern 會被複製
- **Damage recipients:**
  - **samsara:implement 的每個 task**：dispatch 成本增加（2 個 parallel reviewer，token cost ~2x）
  - **短期：implementer re-work cycles 增加**——code-quality-reviewer 會抓出原本通過的問題，implementer 必須修
  - **維護者**：多一個 agent definition 和 reference 要維護（總增量約 1-2 份小 markdown 檔）

## Decision Trail

此 kickoff 的關鍵決策在 research 階段通過以下 pivot 形成：

1. **從「寫一份 yin-coding 精神 guide」→「建 samsara:code-quality-reviewer agent」**
   - 觸發：Phase 2 實驗暴露 guide 無法獨立保證 code quality（variance 大、common blind spots）
   - 同時：使用者明確 reframe「samsara 不負責 code quality，要加 layer」

2. **從「擴充既有 samsara:code-reviewer」→「新建獨立 agent」**
   - 觸發：讀 `samsara/agents/code-reviewer.md` 確認它是 fully-built yin reviewer，非 stub
   - 既有 constraints（"Focus on what the code DOES, not what it LOOKS LIKE"）和 conventional quality review 直接衝突

3. **Wiring 選擇 parallel dispatch**
   - 觸發：既有 samsara:implement / samsara:iteration 已有 code-reviewer dispatch infrastructure
   - 新 agent 作為 sibling 並行，不干擾既有 flow

此 trail 記錄以供未來 kill condition 判斷參考：若上述某一個觸發前提被證偽，對應決策應重審。

## Artifacts

- `experiment/guides/v-{zh,en}-{must,is}.md` — 實驗用的四份 guide 變體
- `experiment/outputs/{cell}-{output,run2,run3}-output.py` — 12 份 refactor 產出
- `experiment/experiment-report.md` — Phase 1 報告（含 single-run overclaims，保留作 audit trail）
- `experiment/experiment-report-phase2.md` — Phase 2 replication 報告（修正 Phase 1 過度宣稱）
- `problem-autopsy.md` — 翻譯損失 + kill conditions + damage recipients

## Next Step

進入 Planning：產出 `plan.md` + `spec/` + `tasks/` + `acceptance/`。
