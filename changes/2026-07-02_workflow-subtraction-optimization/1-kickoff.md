# Kickoff: workflow-subtraction-optimization

## Problem Statement

Samsara 的結構壓力目前是單向的：處處防「少做」（不准空 scar、不准跳 review、不准漏 gate），幾乎沒有防「多做」的壓力。結果是產出膨脹——scar reports 平均 113 行且大量重複系統性事實、Auto Mode Gate 段落在 9 個 skill 裡逐字複製、同一份 scar 清單被三道流程重複審視、以及一個永遠不會響的 expiry date 鬧鐘。噪音會靜默地殺死訊號：沒人讀的 scar 等於沒有 scar。本次工作依減法原則對框架本身做三個方向的優化：(1) scar report 噪音削減、(2) pre-thinking dynamic redesign 設計文件的修訂與刪減、(3) workflow 層級的減法。

## Evidence

來自 2026-07-02 對整個 codebase 的完整 review（含 73 份實際 scar reports、10 份 iteration logs、全部 skills/agents/references）：

- **Scar 膨脹**：73 份 scar 共 8,239 行（平均 ~113 行）。202 個 assumptions 中 140 個 `verified: true` 且附長 note，但 iteration 的 `signal_lost` 只計 `verified: false`——下游不消費這些內容。`resolved_items` 把原 item 描述完整重抄。「doc-presence ≠ runtime obedience」這類系統性事實在跨 feature scar 中反覆重述。
- **expiry 無警報**：iteration accept 的 items 全部標 `expiry_date`，但 codebase 中沒有任何機制檢查過期——違反框架自己的「寧可要會發警報的失敗」原則。
- **Auto Mode Gate 重複**：9 個 SKILL.md 各含 30–60 行幾乎相同的 gatekeeper dispatch 段落，而 `references/auto-mode.md` 已是 canonical schema。implementer.md 明文寫「restatement is itself DRY rot」，skill 文件卻大面積違反。
- **三道 scar 審視**：Level 1 self-iteration → Level 2 iteration triage → validate-and-ship failure budget。實際資料（2026-06-28 iteration log）顯示 Level 2 是 15 項中 10 accept / 2 fix / 3 defer，accept rationale 多為「本來就是誠實的設計取捨」——這些項目在 Level 1 就該被過濾。
- **設計文件開放項**：`changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md` 第 8 節的「pre-thinking → planning 交棒」是承重牆卻未定案；「輕想」層的進入條件（證明 main agent 沒有盲點）不可證偽；第五步「少數意見安全網」與「搜尋者只回傳事實」的設計自相矛盾；第 5 節健康指標無 owner/trigger。
- **fast-track checklist 防呆警語**：template 每個欄位都需要「must be specific, not a template copy」警語——需要警告使用者別複製模板的模板欄位，設計上已經輸了。

## Risk of Inaction

- Scar reports 持續膨脹 → 人類停止閱讀 → failure budget review 變成橡皮圖章 → 框架的核心承諾（傷口可見）靜默失效。這正是 secondsight 533→16 行退化曲線的同型：沒人消費的深度必然腐化。
- Auto Mode Gate 的 9 份複本各自漂移（已有先例：churn definition 曾在 pre-thinking 與 codebase-map 之間漂移，靠 task-3 修補）。
- expiry date 持續累積過期而無人知曉，accept 分類淪為永久豁免。
- 0-design-direction.md 的交棒格式不定案，正式重寫 pre-thinking 時會把 ISSUE-001 的病灶形狀（同一決定存在於兩處、無 cross-check）複製到 doc 層。

## Scope

### Must-Have (with death conditions)

- **W1: Scar schema 噪音過濾** — systemic-scar registry（repo 層級登記一次、scar 內以 ID 引用）、`verified: true` 壓縮為單行、`resolved_items` 改為原 item 上標 `status: resolved` 不重抄、narrative 禁止 review 輪次流水帳（reviewer checklist 加牙齒）。
  Death condition: 改版後最近三個 feature 的 scar 平均行數若未下降 ≥30%，或 `signal_lost` 計算因格式改動失真，回退 schema 變更。
- **W2: expiry date 二選一** — 加過期掃描（掛在 validate-and-ship 或 session-start hook）或刪除欄位。留著沒人讀的欄位違反公理。
  Death condition: 若選擇加掃描器，一年內未曾發出任何一次過期警報 → 代表 accept 流程本身無活性，掃描器與 expiry 欄位一併重新評估存廢。
- **W3: Auto Mode Gate 去重** — 每個 skill 壓成指向 `references/auto-mode.md` 的最小段落（本階段的 workflow_prompt 為何 + gate 覆蓋哪些決策點），canonical 行為只存在一處。
  Death condition: 去重後若 auto mode 行為漂移（gatekeeper 未被 dispatch、decision schema 不符、任一 auto-mode 測試轉紅），該 skill 回退為完整段落。
- **W4: 0-design-direction.md 修訂** — (a) 交棒格式定案：pre-thinking 的設計決定是 planning Key Decisions 的唯一來源，planning 只消費不重推；(b) 刪「輕想」層，搜尋者數量改為第二步沒把握假設數量的湧現結果（0..n），深度閘門只剩 fast-track 一個；(c) 刪第五步「少數意見安全網」（與搜尋者只回傳事實的設計矛盾）；(d) 第 5 節健康指標補 owner/trigger（掛 release 或 validate-and-ship 節奏）+ 補「深度過剩」方向的腐化指標；(e) 中斷重啟明定沿用現行 flow.md K3b 機制。
  Death condition: 若與後續正式重寫 `skills/pre-thinking/` 的工程產生衝突，以重寫工程的結論為準，本次修訂讓位。
- **W5: iteration 進入條件資料驅動化** — 由「optional、預設詢問」改為：cross-task pattern 存在或 signal_lost 超過閾值才建議進入，否則預設 skip、由 validate-and-ship failure budget 做唯一一次 triage。
  Death condition: 若後續兩個 feature 中出現「被 skip 的 iteration 本應抓到的 system-level rot 漏到 ship 後」，恢復預設詢問。
- **W6: fast-track quality_checklist 改為只記違規** — 空列表 = 檢查過且乾淨，同樣資訊、一半儀式。
  Death condition: 若違規紀錄率長期為零且 fast-track 產出開始出現 C5–C8 類回歸，代表「只記違規」讓檢查本身被跳過，回退為顯式勾選。

### Nice-to-Have（證據強度只到「值得評估」，需先取證再決定做不做）

- **N1: 雙 reviewer 合併評估** — 先翻 changes/ 歷史：兩個 reviewer 是否曾各自抓到對方沒抓到的 Critical。有 → 不合併；無 → 合併成一個帶雙 checklist 的 reviewer，missing-reviewer 協議整組消失。
- **N2: security-privacy-review 折入 validate-and-ship 當第 0 步** — 它是被刻意建立的獨立 gate，折入與否是 user 決策，不是純技術判斷。
- **N3: index.yaml/TaskCreate 雙記帳語言鬆綁** — TaskCreate 明確降級為 best-effort UI 投影，刪除「never update one without the other」的強制語言。

### Explicitly Out of Scope

- 正式重寫 `skills/pre-thinking/`（那是 0-design-direction.md 的「下一步」，獨立工程；本次只修訂設計文件本身）
- Q4 testing philosophy / fixture provenance（user 未納入此 branch）
- `dist/codex/` 的重新生成與 converter 策略（實作時同步 regenerate 即可，不改策略）
- roadmap.md 的 RM-001 ~ RM-005（loop engineering）

## North Star

```yaml
metric:
  name: "framework instruction surface（skills/ + agents/ + references/ 總行數）"
  definition: "wc -l skills/*/SKILL.md skills/*/*.md agents/*.md references/*.md（不含 templates 與 dist/）"
  current: 5643  # 2026-07-02 實測（agents/*.md + skills/*/SKILL.md + references/*.md）
  target: "下降 >= 12%，且全部既有 death tests 保持綠"
  invalidation_condition: "若行數下降導致任一守護行為消失（death test 被刪或弱化來讓變更過關），目標本身即是錯的——減法的終點是每個存在都有人負責，不是行數少"
  corruption_signature: "內容搬家假減法：skill 行數下降但 references/ 或新檔案等量膨脹，淨 loaded-context 未降。偵測：比較變更前後『單一 session 會被載入的總行數』而非單目錄行數"

sub_metrics:
  - name: "scar report 平均行數（新 schema 下的新 feature）"
    current: 113  # 73 份 / 8239 行
    target: "<= 70"
    proxy_confidence: medium
    decoupling_detection: "若行數下降但 signal_lost 訊號同步消失（unverified assumptions 不再被記錄），proxy 與主目標脫鉤——抽查新 scar 是否仍含全部 verified:false 項目"
  - name: "Auto Mode Gate 重複行數"
    current: "~400（9 skills x 30-60 行）"
    target: "每 skill <= 8 行指針段落"
    proxy_confidence: high
    decoupling_detection: "auto-mode 測試套件全綠 + references/auto-mode.md 未等量膨脹"
  - name: "0-design-direction.md 開放項關閉數"
    current: "第 8 節 4 個待討論/開放項 + 2 個待小設計"
    target: "交棒格式、輕想存廢、少數意見安全網、健康指標 owner 四項關閉"
    proxy_confidence: high
    decoupling_detection: "『關閉』必須是寫入文件的決定＋理由，不是刪掉開放項條目"
```

## Stakeholders

- **Decision maker:** yuyu_liao（solo maintainer）
- **Impacted teams:** 未來所有使用 samsara plugin 的 session（Claude Code / Codex / Gemini CLI 轉換目標）
- **Damage recipients:**
  - 本次實作自身 —— skills 大改會使 `dist/codex/` 全量變動、部分 doc-contract 測試需同步更新（732 個測試的維護成本）
  - 讀歷史 scar 的人 —— 新舊 scar 格式並存，聚合邏輯必須延續 schema 既有的 backward-compat 條款（plain-string、missing-flag 容忍）
  - auto mode —— Gate 去重後若指針段落資訊不足，gatekeeper 行為漂移的第一個受害者是 auto run 的使用者
