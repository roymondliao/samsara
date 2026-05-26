# Problem Autopsy: extract-pre-thinking-step

## original_statement

> 我現在要做一個小 patch 的優化處理，是針對在 @skills/planning/SKILL.md 的 "Step 1.5: Pre-thinking — Information Assumptions" 的優化處理。
>
> 原因：目前的方式在 Samsara:planning step 會根據 LLM 來判斷是否需要 user 提供更多 information，因為從 research 來的內容可能還缺少一些細節的內容，而導致 planning 時的內容不完整、或是過多的假設、導致最終實作時偏移最一開始的需求。這次要優化的是跟 user 在 planning 的 pre-thinking 交互部分，原因如下：
> - 現在是直接將問題回到 session window 上，如果需要 user 回答的問題很多時，user 很難在 session window 來回覆
>
> 優化方案：
> 提供 user 更好的交互方式：
> 1. 將問題根據類似 QA format 的 template 寫到 `pre_thinking_qa.md` 在 change 的項目底下，可以讓 user 直接 edit，然後等 user 編輯完後，再讓 agent 來 review。
> 2. Agent 將需要詢問的問題根據問題的相似度，一次最多三題的方式，採用 AskUserQuestion 的方式，來一輪一輪的問 user，最終將內容寫入到 `pre_thinking.md` 內

## reframed_statement

把目前埋在 `samsara:planning` Step 1.5 的 pre-thinking 階段抽出為獨立 skill `samsara:pre-thinking`，samsara chain 從 `research → planning` 升級為 `research → pre-thinking → planning`。Pre-thinking skill 採 single-writer / event-sourced 設計：LLM 是 pre-thinking.md 唯一 writer，user 透過 AskUserQuestion ≤3 題分批作答；commitment 也走 AskUserQuestion（Proceed / Accept gap / Return to Research）。Async deliberation 不在 planning chain 內處理，改由「Return to Research」escape hatch + user 自身責任承接。

## translation_delta

```yaml
translation_delta:
  - original: "我現在要做一個小 patch 的優化處理"
    reframed: "不是小 patch — 是抽出獨立 skill 的 framework chain 結構改動"
    delta: "Research 階段 Path A/B/C first-principle 推導判定 Path A（修 Step 1.5）違反公理（責任薄弱、未來不存活、吞掉矛盾），Path B 才通過。Scope 從『optimize step』升為『extract step』，user 已於 2026-05-20 確認接受 scope 擴展。"

  - original: "Step 1.5: Pre-thinking — Information Assumptions 的優化處理"
    reframed: "完全移除 planning Step 1.5，新增 samsara:pre-thinking 獨立 skill"
    delta: "原 user 預設動 Step 1.5（in-place patch），但 Path B 推導出『正確設計是抽出』而非『修補』。Step 1.5 不只是優化、而是被外科切除。"

  - original: "從 research 來的內容可能還缺少一些細節"
    reframed: "research 與 pre-thinking 是兩個不同 gate：research 答『該不該做』、pre-thinking 答『往下還需要什麼共識』"
    delta: "原句把鍋推給 research 不夠仔細。User 於 Phase 0 Q1 澄清：research 是『判斷該不該做』gate，pre-thinking 才是『surface 未顯化 assumption』gate。兩者責任分離，不是 research 沒做完。"

  - original: "將問題根據類似 QA format 的 template 寫到 pre_thinking_qa.md，可以讓 user 直接 edit"
    reframed: "pre-thinking.md 是 LLM single-writer，user 不直接 edit；user 透過 AskUserQuestion 答題，LLM append 到 pre-thinking.md"
    delta: "原方案是 dual-writer（user 與 LLM 都寫同檔），Path B research 推導出『single-writer for persisted artifact』是 framework-level 不變式；dual-writer 違反此不變式，且引入 K3b 跨 session 半成品狀態的 silent rot 風險。"

  - original: "Agent 將需要詢問的問題……採用 AskUserQuestion 的方式，來一輪一輪的問 user"
    reframed: "AskUserQuestion ≤3 題/批、按相似度分組、每輪 append 答案到 pre-thinking.md"
    delta: "原方案概念相符，但缺『按相似度分組』、『≤3 題上限的理由（cognitive load + 留 1 題 headroom，而非 AskUserQuestion 上限 4）』、『append-only audit log』這三個 invariant；本次補齊。"

  - original: "提供 user 更好的交互方式"
    reframed: "交互方式只是表象 — 真正在做的是『user-LLM assumption alignment』有自己的容器與責任歸屬"
    delta: "原措辭把這當成 UX 改善；reframe 後其實是 framework chain 結構修正。UX 改善是副產品，不是目的。"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "若未來出現主流 samsara client 完全不支援 AskUserQuestion-like primitive，且無 fallback 設計"
    rationale: "當前主流 client 均已驗證支援（Codex CLI: ask_user_question；Gemini CLI v0.29.0+: ask_user）。Kill condition 適用於新進入 client；若新 client 加入時仍無 fallback，patch 應降級或增設 file-mode fallback path"

  - condition: "若 research output 加上 gaps_present 訊號後，實際跑 ≥3 個 feature 都標 gaps_present: no"
    rationale: "代表 pre-thinking 在實務上根本不被觸發 → 抽出沒有意義，應併回 planning 並改用更輕量的內聯設計"

  - condition: "若 implement 階段死亡測試先行的紀律無法被本 patch 遵守（即本 patch 自己違反 implement-first-death-test）"
    rationale: "歷史前車：fast-track 階段死亡測試 retroactive 寫（SCAR-1）。若本 patch 重蹈覆轍，代表 samsara 紀律對自身改動失效，應停下做更深層的 process 修正"

  - condition: "若 single-writer for persisted artifact 不變式無法被 framework 接受（譬如 writing-skills owner 拒絕收這條規矩）"
    rationale: "Path B 的 framework-level 收益失效 → patch 退化為純 chain 結構調整，需重新評估 ROI"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "想 async 離線思考的 user"
    cost: "Planning chain 不再提供 in-place async 出口；需走 Return to Research 路徑（改 kickoff + 重跑流程）"
    acceptance_status: "accepted — Phase 0 Q3 已確認屬 user 自身責任"

  - who: "samsara:research skill 與其使用者"
    cost: "原本可推給 pre-thinking 處理的 async deliberation 被轉嫁回 research，research 階段壓力變大"
    acceptance_status: "accepted — healthy pressure，research 本來就該扎實"

  - who: "多人協作回答的團隊"
    cost: "Chat-only 不支援多人分頭審閱；需在 research 階段整合多人結論再回來"
    acceptance_status: "accepted — samsara 目前單人開發者導向"

  - who: "想全局審視所有 gap 的 user"
    cost: "每輪只看 ≤3 題，無法整體 review"
    mitigation: "Step A 一次列出全部問題於 pre-thinking.md，user 進 chat 前可先讀整份檔"
    acceptance_status: "accepted with mitigation"

  - who: "codex / gemini 環境的 user"
    cost: "API 形狀略有差異（Codex CLI: ask_user_question；Gemini CLI v0.29.0+: ask_user，header ≤16 chars vs Claude Code 的 ≤12 chars）"
    acceptance_status: "verified — kill condition #1 不觸發。Pre-thinking SKILL.md 中 header 欄位建議 ≤12 chars 以維持最廣相容性"

  - who: "future skill writer"
    cost: "Single-writer for persisted artifact 不變式限制未來設計選項"
    acceptance_status: "accepted — single-writer 是 LLM-agent framework 普遍正解；理論上的限制換取實際的 anti-pattern 預防"

  - who: "existing planning skill SKILL.md 的 reader"
    cost: "Step 1.5 被移除後，舊的 mental model（『planning 自己處理 gap』）需被取代為新 model（『pre-thinking 處理 gap，planning 只負責 spec』）"
    acceptance_status: "accepted — 透過 SKILL.md 與 bootstrap dot graph 同步更新揭露新 model"
```

## observable_done_state

`samsara-bootstrap` 的 chain graph 出現 `samsara:pre-thinking` 節點，且 research → pre-thinking → planning 的 invocation rule 明確（research output 帶 `gaps_present: yes` 才 invoke pre-thinking）。`skills/planning/SKILL.md` 的 Step 1.5 段落被完全移除，取而代之的是 `skills/pre-thinking/SKILL.md` 自己的完整流程；planning 從此只負責「sync 翻譯 pre-thinking 對齊結論為可執行 spec」。真實跑一次有 ≥3 gap 的 feature，`changes/<feature>/` 底下出現 `pre-thinking.md` 含完整 audit log（LLM 問題 + hypothesis + user 答案 + 最終 commitment），且 planning 的 `2-plan.md` 在 Tech Spec assumptions 區明確引用 pre-thinking.md 結論。
