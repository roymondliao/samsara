# Samsara (向死而驗)

> 向死而驗。

[English README](./README.md)

Samsara 是一個 [Claude Code 插件](https://code.claude.com/docs/en/plugins)，執行以死亡為先的開發流程。不問「它能動嗎？」，而問「**當它靜默地壞掉時，誰會知道？**」

每一個 function、module、設計決策都必須能回答：**「如果你消失了，什麼東西會感到痛？」** 回答不了的，不應該存在。

## 哲學

傳統開發走的是陽面 — 建功能、驗證它會動、交付。Samsara 反轉這個順序，以**陰面**為先：找出哪裡會靜默失敗、在無人察覺的情況下腐爛、或在假裝健康的狀態下退化。

三個核心原則：

1. **Death test 先於 unit test** — 先測試靜默失敗的路徑，再測試成功的路徑
2. **Scar report 先於完成宣告** — 每次實作都必須記錄它的傷疤：假設、靜默失敗路徑、邊界條件
3. **STEP 0 先於任何實作** — 三個前置問題，防止確認偏誤：
   - 找出最直覺的實作方式。先不要走那條路。
   - 這個需求在什麼條件下根本不應該被實作？
   - 如果這個實作靜默地失敗了，誰會是第一個發現的人？發現之前，損害已經擴散到哪裡？

## 安裝

Samsara 是 Claude Code 插件。在你的專案中啟用：

```bash
# 在專案的 .claude/settings.json 中
{
  "plugins": {
    "samsara": true
  }
}
```

或從本機路徑安裝：

```bash
claude plugins add /path/to/samsara
```

安裝後，Samsara 會透過 `SessionStart` hook 在每次對話開始時注入公理和約束。

## 工作流程

Samsara 提供從研究到交付的結構化流程。每個階段產生特定的產出物，餵入下一階段。

```
research  ──>  planning  ──>  implement  ──>  validate-and-ship
                                  ^
                                  │
fast-track（小改動）───────────────┘
debugging（production 故障）──────┘
```

### Skills

| Skill | 使用時機 | 關鍵產出 |
|-------|---------|---------|
| `samsara:research` | 開始新功能或調查問題 | Kickoff 文件 + 問題解剖報告 |
| `samsara:planning` | 研究完成後 | Death-first 規格 + 帶驗收條件的任務 |
| `samsara:implement` | Plan 與 tasks 就緒 | 帶 death test 的程式碼 + scar reports |
| `samsara:validate-and-ship` | 所有任務完成 | 帶失敗預算的交付清單 |
| `samsara:fast-track` | 小型低風險改動（< 100 行） | 簡化流程，death test 仍先行 |
| `samsara:debugging` | 既有程式碼的 production 故障 | 四階段陰面根因分析 |
| `samsara:codebase-map` | 進入新專案或程式碼大幅變動後 | 結構地圖 + 靜默失敗面評估 |
| `samsara:writing-skills` | 建立或修改 samsara skills | 以 death-first TDD 開發 skill |

### Agents

Samsara 包含專門的 subagent，陰面約束寫死在 agent 定義中 — 不依賴 prompt 注入來維持框架精神。

| Agent | 用途 | Model |
|-------|------|-------|
| `samsara:implementer` | Death-test-first 實作，產出 scar reports | sonnet |
| `samsara:code-reviewer` | 陰面 code review：先問能否刪除、命名是否誠實、靜默腐爛路徑 | sonnet |
| `samsara:structure-explorer` | 掃描模組邊界、依賴關係、公開介面 | sonnet |
| `samsara:infra-explorer` | 掃描建構系統、設定來源、外部依賴 | sonnet |
| `samsara:yin-explorer` | 分析靜默失敗路徑、隱性耦合、未驗證假設 | sonnet |

## 實作流程

執行含多個 task 的 plan 時，implement skill 協調 subagent：

```
主 agent                              Subagent（samsara:implementer）
    │                                        │
    ├─ 讀取 index.yaml                       │
    ├─ 分析 task 依賴                         │
    ├─ Dispatch（貼上完整內容）──────────────>│
    │                                        ├─ STEP 0（三個前置問題）
    │                                        ├─ 寫 death tests
    │                                        ├─ 跑 death tests（紅燈）
    │                                        ├─ 寫 unit tests
    │                                        ├─ 跑 unit tests（紅燈）
    │                                        ├─ 實作（綠燈）
    │                                        ├─ 寫 scar report
    │<────────────── 回報結果 ────────────────┤
    │               （不 commit）             │
    ├─ Dispatch code-reviewer ──────────────>│（samsara:code-reviewer）
    │<────────────── Review 結果 ────────────┤
    ├─ 更新 index.yaml                       │
    ├─ 下一個 task...                         │
    │   ...                                  │
    ├─ 全部 task 完成                         │
    ├─ Commit                                │
    └─ 進入 validate-and-ship                │
```

關鍵設計決策：
- **Subagent 不 commit** — 只有主 agent 在全部 task 完成且 review 通過後才 commit
- **貼上完整內容，不給檔案路徑** — 主 agent 策展 context 後注入 subagent prompt。Subagent 不自己讀 task 檔案。
- **Samsara 約束是結構性的** — 寫死在 agent 定義中，不透過 prompt 注入。Implementer agent「本身就是」samsara implementer，而非被告知要遵守 samsara 規則的通用 agent。

## Agent 約束

以下約束對所有在 Samsara 下運作的 agent 強制執行。

### 禁止行為

1. **禁止靜默補全** — 輸入不完整時，不准自動補假設值繼續。必須停下標記「輸入不完整，缺少：___」
2. **禁止確認偏誤實作** — 不准只實作符合需求描述的路徑。必須同時標記「當___不成立時，會___」
3. **禁止隱式假設** — 任何假設必須明確寫出：「本實作假設：___。若不成立，___會發生」
4. **禁止樂觀完成宣告** — 未知副作用或邊界條件必須在完成報告中列出
5. **禁止吞掉矛盾** — 需求存在矛盾時，不准選一個解釋繼續。必須先指出矛盾，請求釐清

### 強制行為

1. 每次實作完成後附：「這個實作在以下條件下會靜默失敗：___」
2. 每次提出設計方案時附：「這個設計假設了___永遠成立。若不再成立，最先腐爛的是___」
3. 每次被要求優化時先問：「值得優化嗎？還是不應該存在？」
4. 遇到模糊需求時，不選最合理解釋繼續——讓模糊本身可見

## 專案結構

```
samsara/
├── .claude-plugin/
│   └── plugin.json              # 插件定義（名稱、版本）
├── agents/
│   ├── code-reviewer.md         # 陰面 code review
│   ├── implementer.md           # Death-test-first 實作
│   ├── infra-explorer.md        # 基礎設施分析
│   ├── structure-explorer.md    # 程式碼結構掃描
│   └── yin-explorer.md          # 靜默失敗分析
├── hooks/
│   ├── hooks.json               # SessionStart hook 註冊
│   ├── session-start            # 注入 samsara-bootstrap
│   └── check-codebase-map       # 提醒生成 codebase map
├── skills/
│   ├── samsara-bootstrap/       # Session 初始化（公理 + 約束）
│   ├── research/                # 問題調查 + kickoff
│   ├── planning/                # Death-first 規格 + 任務生成
│   ├── implement/               # Subagent 協調 + scar reports
│   │   ├── SKILL.md
│   │   ├── dispatch-template.md # Subagent dispatch 的 prompt 模板
│   │   └── scar-report.md      # Scar report 格式參考
│   ├── validate-and-ship/       # 驗證 + 交付清單
│   ├── fast-track/              # 小改動的簡化流程
│   ├── debugging/               # 四階段陰面 debugging
│   ├── codebase-map/            # 專案結構 + 失敗面掃描
│   └── writing-skills/          # Skill 開發的 TDD
└── MEMORY.md                    # 插件記憶索引
```

## 產出物

Samsara 在工作流程中產出結構化的產出物：

| 階段 | 產出物 | 格式 | 用途 |
|------|--------|------|------|
| Research | Kickoff | Markdown | 問題框定 + 範圍 |
| Research | 問題解剖報告 | Markdown | Death cases + 靜默失敗分析 |
| Planning | Overview | Markdown | 給 subagent 的架構 context |
| Planning | Tasks | Markdown | 個別任務規格，含 death test 需求 |
| Planning | 驗收條件 | YAML | 成功 + 失敗條件 |
| Planning | Index | YAML | 任務清單，含依賴關係 |
| Implement | Scar report | YAML | 每個任務的傷疤：假設、靜默失敗、邊界條件 |
| Validate | Ship manifest | YAML | 交付摘要，含失敗預算 |

## 版本

目前版本：**0.5.0**

## 授權

MIT
