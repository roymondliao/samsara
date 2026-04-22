# 陰面軟體開發流程

> 陽面問「怎麼讓它成功」，陰面問「它怎麼在成功的外表下悄悄壞掉」。
>
> 本流程的每一條規範使用正向語法（告訴你「做什麼」），但思維方向是陰面的（關注失敗、腐爛、靜默與責任）。

---

## 唯一公理

**存在即責任，無責任即無存在。**

這一條吃掉所有其他原則。任何 folder、file、module、function、variable 存在的前提是：它能回答「如果我消失，什麼東西會痛？」。回答不了的，標記為待刪除候選。

---

####################
kickoff 要有 **elimination structure** 的設計
implement
- 每個 module 必須附帶「死亡條件」：在什麼情況下這個模塊應該被移除
- 每個檔案命名必須暴露它的**責任邊界**，而不只是它做什麼——清楚知道它**拒絕**處理什麼
- UML design pattern 的選用必須附帶「驗屍可行性聲明」：當這個 pattern 內部腐爛時，外部能在幾步之內定位到兇手

####################

---

## 翻譯問題的陰面重新定義

軟體開發本質上是一個**損耗暴露**問題：

```
Human 的意圖（模糊的、隱含的、會變的）
            ↓
      翻譯損失（這裡的損失必須被命名、被量化、被追蹤）
            ↓
Machine 可執行的指令（精確的、明確的、固定的）
            ↓
      執行偏差（指令正確不代表行為正確，行為正確不代表結果正確）
            ↓
      靜默腐爛（系統在跑，但你不知道它為什麼在跑 = 最危險的狀態）
```

大多數項目失敗不是因為「寫錯代碼」，也不只是因為「一開始就沒理解對問題」——
**而是因為每一層翻譯損失都在假裝自己不存在。**

---

# Research — 消除階段

## 1. Interrogate（審問）— 先審問問題本身，再審問答案

陽面問「這個問題怎麼解決」，陰面先問：

- **問題的形狀是誰給的？** 重述問題的來源。如果問題來自利害關係人，記錄原始措辭與你理解的措辭之間的差異。差異本身就是翻譯損失的第一層。
- **這個問題在什麼條件下不應該被解決？** 列出至少兩個「即使技術上可行，也應該拒絕實作」的情境。
- **誰會因為這個問題被解決而受損？** 任何解決方案都有成本轉移——找到承受者並記錄。
- **這個問題的「解決」狀態長什麼樣？** 如果你無法在三句話內描述「解決」和「沒解決」之間的可觀測差異，代表問題還沒被真正理解。

**產出：Problem Autopsy Report**
```
problem_autopsy.md
├── original_statement    # 問題的原始措辭（逐字）
├── reframed_statement    # 你理解的版本
├── translation_delta     # 兩者之間的差異，逐條列出
├── kill_conditions       # 在什麼條件下這個問題應該被放棄
├── damage_recipients     # 解決後誰承受成本
└── observable_done_state # 「解決了」的可觀測證據是什麼
```

重點：太多項目是「解決方案在找問題」。陰面的第一步是**先嘗試殺死問題本身**。問題活下來了，才值得往下走。

## 2. Scope（範圍）— 最小責任邊界，而非最小可行

陽面的 scope 問「最少要做什麼才能交付」。
陰面的 scope 問：

- **如果這個功能明天消失，系統的哪個部分會痛？** 痛的部分就是真正的 scope。不痛的部分是裝飾。
- **每個 must-have 都必須附帶它的死亡條件：** 在什麼度量指標低於什麼閾值時，這個 must-have 應被降級為 nice-to-have，並最終移除。
- **減法的終點不是「功能少」，而是「剩下的每一個東西都有人為它的腐爛負責」。**

## 3. 北極星指標 — 附帶「北極星失效條件」

- 目標確認後，同時定義：**在什麼條件下這個目標本身是錯的？**
- main metrics 必須附帶 **corruption signature**：如果這個指標被 game 了（數字上升但實質惡化），你怎麼偵測到？
- proxy metrics 必須標記為 `proxy_confidence: high | medium | low`，並定義：**proxy 和 main 之間脫鉤的偵測機制**。proxy 指標上升但 main 指標沒動，是比兩個都沒動更危險的狀態。

---

# Planning — 預謀失敗階段

## 1. Technical Specification — 先寫死法，再寫活法

陽面的 spec 定義「系統應該做什麼」。
陰面的 spec 先定義「系統會怎麼死」。

- **Input/Output 定義：** 除了正常的 I/O，每個 interface 必須定義 `unknown_output` 狀態。任何輸出只有三種合法狀態：`success`、`failure`、`unknown`。把 `unknown` 塞進 `success` 或 `failure` 視同缺陷。
- **Edge cases → Death cases：** 改名為 death cases。不只是「邊界情況」，而是「在什麼條件下這個功能靜默產出看起來正確但實際錯誤的結果」。
- **Acceptance criteria → Failure acceptance criteria：** 除了「通過 = 功能正確」，加上「這些是已知的、被接受的失敗模式，以及它們被接受的理由與時效」。

```gherkin
# 陰面 BDD：不只測活路，先測死路

Feature: User Login

  # --- 死路先行 ---
  Scenario: Silent failure - session appears valid but auth token expired
    Given a registered user "test@example.com" with a session created 23h 59m ago
    When the system checks session validity at the boundary
    Then the session state must be exactly one of: "valid", "expired", "unknown"
    And "unknown" must trigger re-authentication, never silent pass-through
    And the auth check must log the decision path with timestamp

  Scenario: Unknown outcome - auth service timeout
    Given a registered user "test@example.com"
    When the auth service does not respond within 3 seconds
    Then the login result must be recorded as "outcome_unknown"
    And the user must see explicit "unable to verify" message
    And the system must never fall back to cached auth state silently

  # --- 活路附帶證據鏈 ---
  Scenario: Successful login with evidence chain
    Given a registered user "test@example.com"
    When they enter correct password and click login
    Then they should see the Dashboard
    And session should be valid for 24 hours
    And the success event must include: auth_method, token_issued_at, verification_source
    And any future audit must be able to reconstruct this login decision from logs alone
```

## 2. Specify（規範）— 可驗屍的定義

陽面的規範確保「功能可以被測試」。
陰面的規範確保「三年後腐爛時可以被定位、被歸責、被截肢」。

- **Testing plan 的第一部分永遠是 failure path tests：** timeout unknown、partial write、duplicate event、stale cache。只有 success case 的測試計畫視同祈禱，標記為 `coverage_type: prayer`。
- **每個 acceptance criterion 必須回答：** 「如果這條通過了但系統實際上是壞的，那是因為什麼？」——這個問題的答案就是你漏掉的 test case。

**產出結構：**
```
<date>_<plan_name>_plan/
├── overview.md                # Goal, Architecture, Tech Stack
├── problem_autopsy.md         # 問題審問記錄（新增）
├── death_cases.md             # 靜默失敗場景目錄（新增）
├── acceptance.feature         # 可執行的 Gherkin 規範（死路先行）
├── failure_budget.md          # 已知且被接受的失敗模式 + 時效 + 負責人（新增）
├── index.md                   # Task 列表 + 狀態
└── tasks/
    ├── task-1.md
    ├── task-2.md
    └── ...
```

---

# Implementation — 留疤階段

## 1. Self-contained + Accountable

- 每個 task 可以獨立執行（同陽面）。
- **新增要求：** 每個 task 完成後的 output 必須包含一份 `scar_report`：
  - `known_shortcuts`: 這個實作走了哪些捷徑？
  - `silent_failure_conditions`: 這個實作在以下條件下會靜默失敗：______
  - `assumptions_made`: 這個實作依賴了哪些未被驗證的假設？
  - `debt_registered`: 技術債是否已記錄？記錄在哪裡？

如果 AI 完成任務後宣告「完成」但不附帶 scar_report，該完成狀態標記為 `completion_unverified`。

## 2. 小批量 + 持續驗屍

```
Task 1: 實現 → Death Test → Unit Test → Integration Test → Scar Report → ✓ Commit
Task 2: 實現 → Death Test → Unit Test → Integration Test → Scar Report → ✓ Commit
Task 3: 實現 → Death Test → Unit Test → Integration Test → Scar Report → ✓ Commit
```

- **Death Test 先於 Unit Test：** 先確認「這個東西怎麼死」已被測試，再確認「這個東西怎麼活」。
- 驗證層級（重新排序）：
  a. **death test:** 靜默失敗路徑、unknown outcome 路徑、降級狀態標記
  b. **unit test:** 單個函數/類的行為
  c. **integration test:** 模塊間的交互——特別關注：模塊 A 認為成功但模塊 B 認為失敗的不一致狀態

- `index.md` 更新時機：每個 task commit 後立即更新。**新增欄位：**
  - `task_status`: done | blocked | unknown
  - `scar_count`: 該 task 的 scar_report 中有多少項
  - `unresolved_assumptions`: 未驗證假設數量

---

# Feature Validation — 驗屍階段

- 驗證層級（重新排序）：
  a. **Failure budget review:** 已知失敗模式是否仍在預算內？有沒有新的靜默失敗被發現？
  b. **Acceptance feature:** 功能是否符合規範（含死路測試）
  c. **E2E:** 整個系統的行為
  d. **Reconciliation check（新增）:** 系統的實際行為與 spec 之間是否有漂移？漂移量是否在容許範圍內？

- **Code Review 的陰面問法：**
  - 第一個問題：「這段 code 可以刪掉嗎？」
  - 第二個問題：「這段 code 裡有沒有在說謊的命名？」（變數名暗示 `is_done` 但實際上 unknown outcome 也被歸為 done）
  - 第三個問題：「三年後接手的人，在哪裡會詛咒你？」
  - 最後才問：「這段 code 對嗎？」

---

# Ship（交付）— 帶著傷疤交付

交付物除了功能本身，必須附帶：

```
ship_manifest.md
├── delivered_capability     # 交付了什麼
├── known_failure_modes      # 已知的失敗模式清單
├── accepted_risks           # 被接受的風險 + 接受者 + 時效
├── silent_failure_surface   # 靜默失敗的攻擊面有多大
├── monitoring_hooks         # 腐爛時會觸發什麼警報
└── kill_switch              # 如果這個功能開始腐爛，怎麼一鍵截肢
```

---

## 責任分工（陰面重新定義）

```
Human 負責：
├── 審問問題本身（Interrogate）
├── 定義責任邊界（Scope as accountability boundary）
├── 定義失敗預算（Failure Budget）
├── 最終判斷 + 風險接受簽名（Verify + Accept Risk）
└── 決定何時截肢（Kill Decision）

AI 負責：
├── 生成實現方案 + 該方案的死法清單
├── 寫代碼 + 寫 scar report
├── 先寫 death test，再寫 unit/integration test
├── 執行驗證 + 標記所有 unknown outcome（絕不把 unknown 偽裝為 success）
└── 完成報告必須附：「這個實作在以下條件下會靜默失敗：______」
```

---

# Fast Track（低風險路徑）— 陰面版

| 步驟 | 內容 | 說明 |
|------|------|------|
| 1 | **Quick Autopsy** | 一句話描述要做什麼 + 一句話描述「這個改動怎麼可能悄悄壞掉」 |
| 2 | **Inline Spec + Death Clause** | 驗收標準直接寫在 task 內，附帶一條 death clause：「如果 _____ 發生，此改動視為失敗」 |
| 3 | **Implement + Death Test + Unit Test** | death test 仍然先行，即使是 fast track |
| 4 | **Quick Review + Scar Tag + Ship** | 簡化的 review，但每個 fast track commit 必須帶 `[scar:none]` 或 `[scar:N items]` tag |

**適用情況：**
- Bug fix（已知原因 + 已確認根因不在更深處）
- Config 修改（已確認修改不會觸發隱式行為變更）
- Dependency 更新（已確認 changelog 中無 breaking change 且無靜默行為變更）
- 小型 refactor（< 100 行 + 已確認沒有消費者依賴被移除的行為）

**陰面的額外判斷：** 如果你無法確認括號中的條件，這個任務退出 Fast Track，進入完整流程。Fast Track 的入口本身就是一個 gate——通過 gate 的條件是你能證明風險確實低，而不是你感覺風險低。

---

## 陰面流程的一句話總結

> 陽面的流程讓你把東西做出來。
> 陰面的流程確保做出來的東西壞掉時，你知道它壞了、知道它怎麼壞的、知道誰該負責、知道怎麼截肢。
>
> **兩者都需要。只有陽面是祈禱。只有陰面是癱瘓。**
