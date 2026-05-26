# Kickoff: extract-pre-thinking-step

## Problem Statement

把目前埋在 `samsara:planning` skill Step 1.5 的 pre-thinking 流程，**抽出成獨立 skill `samsara:pre-thinking`**，並把 samsara chain 從 `research → planning` 改為 `research → pre-thinking → planning`。目的是讓「surface user-LLM assumption gap」這個動作擁有單一語意的容器、單一 writer 的 artifact、與其他兩個階段對映清晰的責任邊界（呼應軟體工程的 PRD → system design → plan 流程）。

## Evidence

1. **既有 Step 1.5 累積的多項痛點**（部分來自先前 fast-track 的 SCAR 與本次 research 對話）：
   - LLM 把多題 dump 到 chat → user 認知負擔過載，常草率作答
   - dual-mode（chat / file-edit）方案會引入「同一份 artifact 被多 writer 寫入」的 race 與 K3b 跨 session 半成品狀態
   - C5（user 想 global thinking 卻被迫一題一題答）在 Step 1.5 框架下沒乾淨解
2. **責任邊界錯位**：planning skill 同時負責「surface gap」與「translate to spec」兩種不同節奏的工作，違反 single-purpose。
3. **歷史紀錄**：本次需求原以「small patch」進入，fast-track 已交付過一次（dual-mode），但於 research 階段被推翻、revert。同一問題反覆出現 = 結構性問題。

## Risk of Inaction

- Planning skill 維持當前 Step 1.5 設計 → user 持續被 chat dump 多題 → plan 帶未顯化 assumption → implement 階段返工
- 後續 skill 設計者（不論 debugging 或新 skill）若仿照 Step 1.5 結構，會擴散 anti-pattern
- 「research 結束但 assumption 未對齊」的場景永遠無家可歸——要嘛 user 自己頂、要嘛 LLM 默默吞

## Scope

### Must-Have (with death conditions)

- **新 skill `samsara:pre-thinking` 存在於 `skills/pre-thinking/`**
  Death condition: 若連續 3 個 feature 跑完 research 後皆未 invoke pre-thinking（LLM 永遠 quick-pass 無問題直接 Proceed），代表抽得不對，應降級為 nice-to-have 並評估併回 planning。

- **`samsara-bootstrap` 的 Skill Matching dot graph 更新**：chain 改為無條件 research → pre-thinking → planning（pre-thinking 恆被 invoke，由 pre-thinking 自行判斷是否有 gap；無 gap 時 quick-pass 直接 Proceed，minimal pre-thinking.md 仍建立作為 audit trail）
  Death condition: 若 user 反映「不知道有這個 skill」≥2 次，代表 bootstrap 揭露不夠，需重新設計 entry point。

- **`samsara:planning` SKILL.md 的 Step 1.5 段落完全移除**
  Death condition: 若 Step 1.5 被後續 contributor 加回來，代表本 patch 沒在文件上 enforce 邊界，需追加 lint 或 review gate。

- **`samsara:planning` SKILL.md 的 prerequisites 新增 `pre-thinking.md`**（when present；planning 讀取 pre-thinking.md 的 commitment 結論，並在 Tech Spec assumptions 區引用）
  Death condition: 若 planning 產出的 2-plan.md 未引用 pre-thinking.md 結論，代表 pre-thinking 輸出未被 planning 消化、chain 斷鏈。

- **新 `skills/pre-thinking/SKILL.md` 完整流程**：3-step (Step A → Step B → Step C)
  - **Step A**: 一次性將所有問題寫入 `pre-thinking.md`（single-writer、append-only）；若無 gap，寫 minimal pre-thinking.md（`gaps: none identified`）直接跳到 Step C（Proceed）
  - **Step B**: 按問題相似度分 group；每 group ≤3 題透過 AskUserQuestion 詢問；若某 group > 3 題則切為 3+(N≤3) 兩輪；每輪答完後 append 答案到 pre-thinking.md（同時偵測 user 是否直接編輯 file，若有則讀取並納入）；若 user 答案顯示不確定或對問題本身有疑慮，agent 額外提供 AskUserQuestion：「Continue（接受不確定性）/ Return to Research（先回去釐清問題定義）」；選 Return to Research 時 agent 列出未解決 gap list 並停止，user 重新 invoke samsara:research
  - **Step C**: 所有 group 完成後，最終 commitment via AskUserQuestion（Proceed / Accept gap / Return to Research）
  Death condition: 若 LLM 在單一 group 中違反 ≤3 題上限 ≥3 次，代表紀律未內化、需 runtime enforcement。

- **新 `skills/pre-thinking/templates/pre-thinking.md`**：append-only audit log 格式、LLM single-writer（user 直接 edit 屬宣告式違反，不阻止；Step B 每輪 append 後會偵測並納入 user 修改）
  Death condition: 若 Step B 的 file-edit detection 在 user 直接編輯後未感知（append 成功但 user 修改被靜默覆蓋），代表 append 邏輯設計錯誤。

- **死亡測試先寫**（implement 階段必須在程式碼前產出，至少涵蓋以下 silent failure：無 gap 時 minimal 建檔並直接 Proceed（不問任何問題）、≤3 題分批上限 enforce、append-only 不覆蓋舊內容、file-edit detection 感知 user 修改、commitment via AskUserQuestion、Return to Research 時 invoke path 明確（列出 gap list + 停止））
  Death condition: 若任一條死亡測試在 implement 階段被跳過或追加，代表 implementation 違反 samsara TDD 公理。

- **`samsara:writing-skills` 加 single-writer artifact 不變式**
  Death condition: 若未來新增的 skill 仍出現 dual-writer artifact，代表此不變式未被引用、需更顯著揭露。

### Nice-to-Have

- 把 single-writer 不變式提升為 framework 公理（寫進 samsara-bootstrap）
- Pre-thinking skill 可獨立 invoke（不從 research 觸發）的場景設計

### Explicitly Out of Scope

- **不處理 user 的 async deliberation 需求**：若 user 想離線思考，選擇「Return to Research」即可，async 屬於 user 自身責任（呼應 Phase 0 Q3 user 回應）
- **不額外實作 codex / gemini 的 AskUserQuestion adapter**：兩個 client 均已驗證支援等效 primitive（kill condition #1 不觸發）；API 細節差異（header 長度等）由 SKILL.md 的 authoring guidance 覆蓋，不需額外 adapter code
- **不為「全局思考型 user」設計 file-edit mode**：Step A 一次列出全部問題已提供預覽能力，足夠
- **不改 implement / iteration / validate-and-ship skill**：本 patch 只動 research → pre-thinking → planning 三段

## North Star

```yaml
metric:
  name: "implement_scar_unhidden_assumption_count"
  definition: "Implement 階段 scar 報告中『assumption 未顯化導致需重做』類別出現次數，per feature 計算"
  current: "未量測（pre-thinking 抽出前無基線；fast-track SCAR-1/2 屬此類別徵兆）"
  target: "新 chain 啟用後第 N 個 feature，此類別 scar 趨近 0"
  invalidation_condition: "若 implement scar 報告本身不會記此類別、或 user 在 implement 內默默吞 assumption error，此 metric 失效"
  corruption_signature: "metric=0 但 implement 仍頻繁返工 → scar 沒記下、或返工原因被歸到別類；同時 pre-thinking commitment 永遠是 Proceed 也是 corruption 訊號"

sub_metrics:
  - name: "pre_thinking_invocation_rate"
    definition: "research 跑完後實際 invoke pre-thinking 的比例（chain 無條件執行，正常應 ≈ 100%）"
    current: 0
    target: "≈ 100%；若 rate < 100%，代表 pre-thinking 被跳過，需調查原因"
    proxy_confidence: medium
    decoupling_detection: "若 invocation rate ≈ 100% 但多數 pre-thinking.md 的 Q 數 = 0（永遠 quick-pass），代表 LLM 在做空跑或 research 品質不足；若 Q 數分布異常（永遠 0 或永遠 ≥10），皆為 corruption 訊號"

  - name: "pre_thinking_commitment_distribution"
    definition: "三種 commitment（Proceed / Accept gap / Return to Research）的分布比例"
    current: 0
    target: "三種皆有出現；任何一種 = 100% 都是 corruption 訊號"
    proxy_confidence: high
    decoupling_detection: "永遠 Proceed → LLM 在 lead 答案；永遠 Return to Research → research 沒做完就 invoke pre-thinking；永遠 Accept gap → user 放棄對話"
```

## Stakeholders

- **Decision maker:** yuyu_liao (本次 patch 的 owner，今天 2026-05-20 完成 Path B 決議)
- **Impacted teams:** 所有使用 samsara framework 的 contributor / 跑 samsara chain 的 user
- **Damage recipients:**
  - 想 async 離線思考的 user → 被導回 Return to Research（已接受成本）
  - `samsara:research` skill → 接收 async deliberation 的轉嫁壓力（已接受）
  - 多人協作回答的團隊 → chat-only 不支援，需透過 research stage 整合多人結論（已接受，非核心 use case）
  - codex / gemini 環境上的 user → 已驗證：Codex CLI 有 `ask_user_question` tool，Gemini CLI v0.29.0+ 有 `ask_user` tool（API 形狀微有差異，pre-thinking SKILL.md 中 header 欄位建議 ≤12 chars 以維持最廣相容性）
