####################
kickoff 要有 folder structure 的設計
implement
- 要有 modules 的設計，列出需要哪些模塊，該模塊負責什麼功能
- 實作檔案的命名，清楚知道每個 script 負責的任務
- UML design pattern

####################

軟體開發本質上是一個翻譯問題：
Human 的意圖（模糊的、隱含的、會變的）
            ↓
        翻譯損失
            ↓
Machine 可執行的指令（精確的、明確的、固定的）
大多數項目失敗不是因為「寫錯代碼」，而是因為「一開始就沒理解對問題」。


# Research
1. Understand（理解）— 不是收集需求，是理解「為什麼」
- 這個問題真的存在嗎？證據是什麼？
- 為什麼現在要解決它？
- 如果不解決會怎樣？
- 有沒有更簡單的解決方案（甚至不需要寫代碼）？

重點：太多項目是「解決方案在找問題」，而不是「問題在找解決方案」。

2. Scope（範圍）— 最小可行，不是最完整
- 什麼是 must-have？什麼是 nice-to-have？
- 減法思考

3. 北極星指標
- 要先想清楚產品的目標是什麼，確定好目標
- 對應這個目標要用什麼指標來表示 main metrics
- 根據 main metrics 是否有需要 proxy metrics 來輔助達到 main metrics 的提升


# Planning
1. Technical Specification
- 明確的 Input/Output 定義
- Edge cases 列舉
- Acceptance criteria（可測試的）
```gherkin
# 不只是文字描述，而是可自動執行的規範
Feature: User Login

Scenario: Successful login
  Given a registered user "test@example.com"
  When they enter correct password and click login
  Then they should see the Dashboard
  And session should be valid for 24 hours
```


2. Specify（規範）— 可執行的定義，不是文檔
- Testing plan
- 直接寫可執行的驗收規範（Executable Specification）
- 參考 BDD 方式: 這既是需求文檔，也是自動化測試。


**產出結構：**
```
<date>_<plan_name>_plan/
├── overview.md           # Goal, Architecture, Tech Stack
├── acceptance.feature    # 可執行的 Gherkin 規範（取代 testing-plan.md）
├── index.md              # Task 列表 + 狀態
└── tasks/
    ├── task-1.md      # Task 1 完整內容
    ├── task-2.md      # Task 2 完整內容
    └── ...



# Implementation

1. Self-contained
- AI 不需要「記住」其他 context
- 每個 task 可以獨立執行
- 降低 Context Window 壓力
- 更容易平行處理

2. 小批量 + 持續集成
- 每個 task 完成後立即驗證
```
Task 1: 實現 → Unit Test → Integration Test → ✓ Commit
Task 2: 實現 → Unit Test → Integration Test → ✓ Commit
Task 3: 實現 → Unit Test → Integration Test → ✓ Commit
```

- 驗證層級
	a. unit test: 單個函數/類的行為
	b. integration test: 模塊間的交互

- `index.md` udpate 時機：每個 task commit 後立即更新狀態

# Feature Validation
- 驗證層級
	a. Acceptance feature: 功能是否符合規範
	b. E2E: 整個系統的行為
- Code Review

# Ship（交付）


-----
```
Human 負責：
├── 定義問題（Understand）
├── 設定約束（Scope）
├── 定義驗收標準（Specify）
└── 最終判斷（Verify - User level）

AI 負責：
├── 生成實現方案
├── 寫代碼
├── 寫測試
└── 執行驗證（Verify - Unit/Integration/E2E level）
```

# Fast Track（低風險路徑）

| 步驟 | 內容 | 說明 |
|------|------|------|
| 1 | Quick Scope | 一句話描述要做什麼 |
| 2 | Inline Spec | 驗收標準直接寫在 task 內（不需獨立文件） |
| 3 | Implement + Test | 直接執行，不需拆分 |
| 4 | Quick Review + Ship | 簡化的 review |

**適用情況：**
- Bug fix（已知原因）
- Config 修改
- Dependency 更新
- 小型 refactor（< 100 行）


## 新的檔案結構
```
project/
├── .claude/
│   ├── AGENTS.md                 # 共享規範（三種情況共用）
│   ├── north-star.yaml           # 北極星指標（迭代用）
│   ├── schemas/                      # 標準格式定義
│   │   └── acceptance-schema.yaml    # acceptance.yaml 的 schema
│   ├── templates/                    # 模板檔案
│   │   ├── kickoff.md
│   │   ├── acceptance-input.md
│   │   └── task.md
│
│── learning/                     # continuous-learning-v2 產出
│       └── ...
├── changes/                       # 產品開發 + 新需求/優化/
│   ├── [date<YYYY-MM-DD>]_[feature-name]/
│   │   ├── 1-kickoff.md                # Phase 0 + Step 1（Human + AI）
│   │   ├── 2-plan.md                   # Step 2 完整計畫（AI 產出）
│   │   ├── 3-acceptance-input.md       # Human 寫的驗收描述
│   │   ├── acceptance.yaml             # AI 轉化的可執行規範 / 可執行的驗收規範
│   │   ├── overview.md                 # 共享 context（從 2-plan.md 提取）
│   │   ├── index.md                    # Task 列表 + 狀態追蹤
│   │   └── tasks/                      # Self-contained tasks
│   │       ├── task-1.md
│   │       ├── task-2.md
│   │       └── ...
│   ├── v2-improve-onboarding/    # 迭代優化
│   │   ├── iteration-scope.md    # 簡化的 scope
│   │   ├── acceptance-delta.yaml # 只記錄變更
│   │   └── tasks/
│   │
│   └── v3-add-dark-mode/         # 新功能迭代
│       └── ...
│
└── bugfix/                        # Bugfix 專用目錄
    ├── 2026-03-27-login-crash/
    │   ├── bug-report.md
    │   ├── root-cause.md
    │   └── fix-summary.md
    │
    └── 2026-03-28-api-timeout/
        └── ...

```


Phase 0: Understand
    └── 產出: 1-kickoff.md (Problem + Evidence + Risk)

Step 1: Kickoff + Scope
    └── 更新: 1-kickoff.md (加入 Scope)

Step 2: Plan + Spec
    ├── 產出: 2-plan.md (完整計畫)
    ├── Human 寫: 3-acceptance-input.md
    └── AI 轉化: 3-acceptance.yaml

Step 3: Task 拆分
    ├── 產出: overview.md (從 2-plan.md 提取)
    ├── 產出: index.md (task 列表)
    └── 產出: tasks/task-N.md (拆分)

Step 4: Implementation
    └── 更新: index.md (每個 task 完成後)

Step 5: Validation
    └── 讀取: 3-acceptance.yaml (執行驗證)

Step 6: Review + Ship
    └── 完成後 changes/[feature-name]/ 可 archive 或保留
```


# north-star.yaml
metric:
  name: "User Activation Rate"
  definition: "完成首次登入並建立第一個項目的用戶比例"
  current: 45%
  target: 80%

sub_metrics:
  - name: "Login Success Rate"
    current: 92%
    target: 99%
  - name: "First Project Created"
    current: 48%
    target: 85%
```

### 2. 迭代決策依據
```
數據收集 → 分析差距 → 決定優化方向 → 迭代執行
                │
                ▼
        ┌───────────────────┐
        │ 哪個 sub-metric   │
        │ 離目標差距最大？   │
        │ ROI 最高的改善？   │
        └───────────────────┘
```

### 3. 迭代的簡化流程

因為環境和規範都已建立，迭代可以更輕量：
```
迭代流程：
├── 1. 分析指標差距（AI 可自動）
├── 2. 提出優化假設（AI 提案，Human 確認）
├── 3. 定義迭代 scope（小範圍，focused）
├── 4. 執行（走 Fast Track，因為低風險）
├── 5. Ship + 驗證指標變化
└── 6. 回到步驟 1
```

---

## 更新的完整框架
```
Project Lifecycle
│
├── Phase 1: MVP（首次交付）
│   ├── 走完整 Adaptive Development Workflow
│   ├── Scope = MVP（最小可行）
│   ├── 定義北極星指標
│   └── Ship → 開始收集數據
│
├── Phase 2: Iteration（迭代優化）
│   ├── 數據驅動的優化循環
│   ├── AI 自主性提高
│   ├── 多數走 Fast Track
│   └── 持續直到達到北極星指標
│
└── Phase 3: Maintenance（維護）
    ├── Bug fix
    ├── 小優化
    └── 監控指標維持
