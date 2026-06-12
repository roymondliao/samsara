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

### 多平台支援

Samsara 以 Claude Code 插件的形式撰寫，但 `samsara-cli` 可以把它轉換並安裝到其他 agent 平台（例如 Codex）：

```bash
source .venv/bin/activate
uv run samsara-cli list-platforms              # 列出支援的目標平台
uv run samsara-cli convert --platform codex    # 轉換輸出到 ./dist/codex/
uv run samsara-cli install codex --scope project
uv run samsara-cli validate --platform codex   # 驗證轉換結果
```

Converter 會把 skills、agents、hooks、references 轉換成目標平台的格式；`update` 可更新既有安裝。

## 工作流程

Samsara 提供從研究到交付的結構化流程。每個階段產生特定的產出物，餵入下一階段。

```
research ──> pre-thinking ──> planning ──> implement ──> iteration（可選）
                                               │              │
                                               v              v
                                       security-privacy-review ──> validate-and-ship

fast-track（小型低風險改動）──────> 完成
debugging（production 故障）──> 小 fix 走 fast-track / 大 fix 走 implement
```

每個階段轉換都是 human gate（auto mode 下則由 `auto-gatekeeper` 決策）。

## Auto Mode

在 `samsara:research` 之前，Samsara 會先詢問 execution mode：`human-in-the-loop` 或 `auto`。`human-in-the-loop` 保留現有的 human gate；`auto` 仍然完整跑同一條 workflow：`research -> pre-thinking -> planning -> implement -> iteration -> security-privacy-review -> validate-and-ship`，但原本要問 human 的問題與確認，會交給 `samsara:auto-gatekeeper` 回答。

這個 gatekeeper 是可重用的 principle-level reviewer，帶有 project context、architecture judgment、first-principles reasoning。每一個 auto decision 都會 append 到 `changes/<feature>/auto-decisions.md`，這是一份 append-only 記錄，保留原始 `workflow_prompt`、`gatekeeper_answer`、rationale、uncertainty、consequences。

第一版 scope 刻意只做 session-level：不支援 `samsara_config.yaml`。Auto run 啟動後，同一輪 run 不會重新請 user 接手 gate；不確定性會記錄在 `auto-decisions.md`，security/privacy unknown 會成為 high-uncertainty reject decision。

### Skills

| Skill | 使用時機 | 關鍵產出 |
|-------|---------|---------|
| `samsara:research` | 開始新功能或調查問題 | Kickoff 文件 + 問題解剖報告 |
| `samsara:pre-thinking` | 研究完成後、planning 前——恆被 invoke | User–LLM assumption gap 的 pre-thinking audit log |
| `samsara:planning` | Pre-thinking commitment 後（Proceed / Accept gap） | Death-first 規格 + 帶驗收條件的任務 |
| `samsara:implement` | Plan 與 tasks 就緒 | 帶 death test 的程式碼 + scar reports |
| `samsara:iteration` | Implement 完成後（可選）——feature-level scar resolution | Cross-task patterns + 系統級腐爛修復的 iteration log |
| `samsara:security-privacy-review` | Implement/iteration 完成後、交付前 | Security & privacy review gate 結果 |
| `samsara:validate-and-ship` | Security review 通過（或風險已被接受） | 帶失敗預算的交付清單 |
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
| `samsara:code-quality-reviewer` | 結構品質審查：九個陰面原則（S/O/L/I/D + 內聚、耦合、DRY、pattern），附 file:line 證據 | sonnet |
| `samsara:auto-gatekeeper` | Auto mode 下回答 workflow gate 問題；記錄 append-only 決策 | sonnet |
| `samsara:structure-explorer` | 掃描模組邊界、依賴關係、公開介面 | sonnet |
| `samsara:infra-explorer` | 掃描建構系統、設定來源、外部依賴 | sonnet |
| `samsara:yin-explorer` | 分析靜默失敗路徑、隱性耦合、未驗證假設 | sonnet |

Review agents 會從 `references/` 載入 domain-specific checklists（code review、code quality、IaC review、test contracts），遇到不支援的 domain 會回傳 `UNKNOWN` 而不是猜測。

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
│   ├── plugin.json              # 插件定義（名稱、版本）
│   └── marketplace.json         # Release 版本的 source of truth
├── agents/
│   ├── auto-gatekeeper.md       # Auto mode 的 gate 決策（append-only 記錄）
│   ├── code-reviewer.md         # 陰面 code review
│   ├── code-quality-reviewer.md # 結構品質審查（九個陰面原則）
│   ├── implementer.md           # Death-test-first 實作
│   ├── infra-explorer.md        # 基礎設施分析
│   ├── structure-explorer.md    # 程式碼結構掃描
│   └── yin-explorer.md          # 靜默失敗分析
├── hooks/
│   ├── hooks.json               # SessionStart hook 註冊
│   ├── session-start            # 注入 samsara-bootstrap
│   └── check-codebase-map       # 提醒生成 / 更新過期的 codebase map
├── skills/
│   ├── samsara-bootstrap/       # Session 初始化（公理 + 約束）
│   ├── research/                # 問題調查 + kickoff
│   ├── pre-thinking/            # User–LLM assumption gap 審計
│   ├── planning/                # Death-first 規格 + 任務生成
│   ├── implement/               # Subagent 協調 + scar reports
│   ├── iteration/               # Feature-level scar resolution
│   ├── security-privacy-review/ # 交付前的 security & privacy gate
│   ├── validate-and-ship/       # 驗證 + 交付清單
│   ├── fast-track/              # 小改動的簡化流程
│   ├── debugging/               # 四階段陰面 debugging
│   ├── codebase-map/            # 專案結構 + 失敗面掃描
│   └── writing-skills/          # Skill 開發的 TDD
├── references/                  # Review agents 載入的 domain checklists
├── samsara_cli/                 # Release 工具 + 多平台 converter/installer
├── tests/                       # 插件測試（pytest）
├── docs/                        # 設計、哲學、開發筆記
├── changes/                     # 每個 feature 的 workflow 產出物（kickoff → ship manifest）
├── issue.md                     # 實際使用中發現的框架缺陷
├── roadmap.md                   # 規劃中的能力增強
└── MEMORY.md                    # 插件記憶索引
```

## 產出物

Samsara 在工作流程中產出結構化的產出物：

| 階段 | 產出物 | 格式 | 用途 |
|------|--------|------|------|
| Research | Kickoff | Markdown | 問題框定 + 範圍 |
| Research | 問題解剖報告 | Markdown | Death cases + 靜默失敗分析 |
| Pre-thinking | Pre-thinking audit log | Markdown | User–LLM assumption gaps + commitment 決定 |
| Planning | Overview | Markdown | 給 subagent 的架構 context |
| Planning | Tasks | Markdown | 個別任務規格，含 death test 需求 |
| Planning | 驗收條件 | YAML | 成功 + 失敗條件 |
| Planning | Index | YAML | 任務清單，含依賴關係 |
| Implement | Scar report | YAML | 每個任務的傷疤：假設、靜默失敗、邊界條件 |
| Iteration | Iteration log | YAML | Feature-level scar 分類 + 解決記錄 |
| Auto mode | Auto decisions | Markdown | Append-only gate 決策，含 rationale 與 uncertainty |
| Fast-track | Fast-track record | YAML | 小改動的簡化流程記錄 |
| Validate | Ship manifest | YAML | 交付摘要，含失敗預算 |

所有產出物都存放在 `changes/<feature>/` 之下——per-feature 目錄是 workflow 的 authoritative record。

## Release

`.claude-plugin/marketplace.json` 的 `metadata.version` 是 release 的 source of truth，也是唯一版本來源。

準備 release 時請執行：

```bash
source .venv/bin/activate
uv run samsara-cli release sync-version
uv run samsara-cli release check-version
```

`sync-version` 會把 `.claude-plugin/plugin.json` 與 `pyproject.toml` 同步到 marketplace metadata；`check-version` 會在 CI 或 release workflow 建 tag 前擋下任何版本漂移。

GitHub release workflow 會在 PR merge 進 `main`、並且 PR 被 closed 後執行。前提是假設 branch protection 已要求該 PR 的 CI 必須先通過才能 merge。

## Issues 與 Roadmap

Samsara 把自己的哲學套用在自己身上——傷口被記錄，而非隱藏：

- **[issue.md](./issue.md)** — 實際使用中發現的框架缺陷，含 error chain 與根因分析（例如 ISSUE-001：planning 的 File Map 與 Key Decisions 矛盾）。
- **[roadmap.md](./roadmap.md)** — 透過分析識別出的能力增強規劃。目前記錄 loop engineering 差距分析（RM-001 ~ RM-005）：排程心跳、auto-mode loop driver、worktree 平行化、全域 loop state、對外 connectors。

## 授權

MIT
