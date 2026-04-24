# Samsara — Project State

> 向死而驗 — Toward death, through verification.

## What is Samsara

Samsara 是一個 Claude Code plugin，基於「向死而驗」哲學打造的 AI harness engineering。它是 kaleidoscope-tools monorepo 內的獨立子 plugin，用來完全取代 superpowers 作為核心 workflow engine。

**哲學基底**：`docs/samsara/` 目錄下的 5 份文件定義了完整的思想體系：
- `philosophy.md` — 向死而驗的哲學起源
- `thinking.md` — 陽面 vs 陰面思維對照
- `design.md` — 開發流程設計（陽面）
- `develop.md` — 開發流程設計（陰面）
- `example.md` — Negative Space Engineering 規範

**核心公理**：存在即責任，無責任即無存在。

## Architecture

- **Plugin 形式**：Claude Code plugin（僅 Claude Code）
- **位置**：`kaleidoscope-tools/samsara/`，可獨立安裝
- **入口機制**：獨立 skills + 鏈式流轉，session-start hook 自動注入 bootstrap
- **流程描述**：所有 SKILL.md 內部流程使用 Graphviz digraph 格式

### Skill Chain

```
research → planning → implement (含 Level 1 task iteration) → iteration (Level 2, 可選) → validate-and-ship
   (每個階段之間有 human gate，使用者確認後才流轉)
```

### Directory Structure

```
samsara/
├── .claude-plugin/plugin.json
├── skills/
│   ├── samsara-bootstrap/SKILL.md      # session start 注入（公理 + agent 約束 + skill 清單）
│   ├── research/                        # Phase 0 + Step 1: Interrogate + Scope + North Star
│   │   ├── SKILL.md
│   │   ├── problem-autopsy.md           # 支援文件
│   │   └── templates/
│   ├── planning/                        # Step 2 + 3: Spec + Task Decompose
│   │   ├── SKILL.md
│   │   ├── death-first-spec.md          # 支援文件：死路先行 BDD
│   │   ├── task-format.md               # 支援文件：self-contained task 格式
│   │   └── templates/
│   ├── implement/                       # Step 4: Death Test First + Scar Report + Level 1 Self-Iteration
│   │   ├── SKILL.md
│   │   ├── scar-report.md              # 支援文件
│   │   ├── dispatch-template.md        # subagent dispatch 模板
│   │   └── templates/
│   │       └── scar-schema.yaml        # scar report schema（single source of truth）
│   ├── iteration/                       # Step 4.5: Level 2 Feature-Level Iteration
│   │   ├── SKILL.md
│   │   └── templates/
│   │       └── iteration-log.yaml      # iteration log 模板
│   ├── security-privacy-review/        # Step 4.75: Security & Privacy Review Gate
│   │   └── SKILL.md
│   ├── validate-and-ship/              # Step 5 + 6: Validation + Ship
│   │   ├── SKILL.md
│   │   ├── ship-manifest.md            # 支援文件
│   │   └── templates/
│   └── writing-skills/SKILL.md         # Meta: 用向死而驗寫新 skill
├── agents/
│   └── code-reviewer.md                # 陰面 code review（先問能不能刪）
├── hooks/
│   ├── hooks.json
│   └── session-start                   # Bash: 注入 bootstrap 到 session context
└── MEMORY.md                           # 本文件
```

## Current Status

### Phase 1: Core Lifecycle — DONE (2026-04-02)

完整的 Research → Planning → Implementation → Validation → Ship 生命週期。

| Component | Status | Files |
|-----------|--------|-------|
| Plugin scaffold | done | plugin.json, hooks.json |
| Session-start hook | done | hooks/session-start |
| samsara-bootstrap | done | skills/samsara-bootstrap/SKILL.md |
| research | done | SKILL.md + 1 support + 2 templates |
| planning | done | SKILL.md + 2 support + 3 templates |
| implement | done | SKILL.md + 1 support + 1 template |
| validate-and-ship | done | SKILL.md + 1 support + 1 template |
| writing-skills | done | SKILL.md |
| code-reviewer agent | done | agents/code-reviewer.md |

### Phase 2: Fast Track + Debugging — DONE (2026-04-07)

- **Fast Track**：獨立 skill，入口 gate + 4 步簡化流程。產出 `changes/` 下的 `fast-track.yaml`。
- **Debugging**：四階段陰面 debugging（Interrogate → Root Cause → Hypothesis & Death Test → Fix）。產出 `bugfix/` 目錄。

| Component | Status | Files |
|-----------|--------|-------|
| fast-track | done | SKILL.md + 1 template |
| debugging | done | SKILL.md + 1 support + 3 templates |
| bootstrap update | done | Added fast-track + debugging to skill list |
| version bump | done | 0.1.1 → 0.2.0 |

### Phase 3: Codebase Map — DONE (2026-04-08)

獨立 skill `samsara:codebase-map` + 3 個 explorer agents + bootstrap hook 檢查。

**核心理念**：不只「系統長什麼樣」（陽面），更回答「系統在哪裡假裝健康」（陰面）。

| Component | Status | Files |
|-----------|--------|-------|
| codebase-map skill | done | SKILL.md + 2 templates |
| structure-explorer agent | done | agents/structure-explorer.md |
| infra-explorer agent | done | agents/infra-explorer.md |
| yin-explorer agent | done | agents/yin-explorer.md |
| check-codebase-map hook | done | hooks/check-codebase-map |
| hooks.json update | done | Added second SessionStart command |
| bootstrap update | done | Added codebase-map to skill list (8 total) |
| version bump | done | 0.2.0 → 0.3.0 |

### Phase 4: Auto Iteration (Dual-Level) — DONE (2026-04-19)

雙層 iteration 機制，讓 scar report 從靜態文件變成 resolution pipeline。

**核心設計**：兩層 iteration 對應兩個陰面觀察點：
- **Level 1 (task-level)**：融入 implement — implementer 完成 task 後自我審視 scar items，修 task scope 內的 actionable items。產出接近完善的 partial function。
- **Level 2 (feature-level)**：新 skill `samsara:iteration` — 所有 tasks 完成後，aggregate 剩餘 scars，處理 cross-task patterns 和 system composition 的 emergent rot。

**Flow**：`implement (含 Level 1) → commit → Level 2 iteration (可選) → validate-and-ship`

**Safety valve**：max 3 rounds, signal_lost 停滯偵測, net rot increase 偵測

**終止條件**：繼續修的代價超過 rot 本身的風險（human judgment via gate）

| Component | Status | Files |
|-----------|--------|-------|
| scar-schema.yaml 擴展（resolved_items, deferred flag） | done | templates/scar-schema.yaml |
| implementer.md Level 1 self-iteration | done | agents/implementer.md |
| implement SKILL.md 更新（execution order + transition） | done | skills/implement/SKILL.md |
| iteration skill (Level 2) | done | skills/iteration/SKILL.md |
| iteration-log template | done | skills/iteration/templates/iteration-log.yaml |
| bootstrap routing update | done | skills/samsara-bootstrap/SKILL.md |
| version bump | done | 0.5.1 → 0.6.0 |

### Phase 5: Security & Privacy Review — DONE (2026-04-22)

獨立 chain skill `samsara:security-privacy-review`，位於 implement/iteration 之後、validate-and-ship 之前。Platform-agnostic — 使用平台內建 security & privacy review 能力，不自建工具。Human gate on issues + inline fix loop (max 3 rounds)。

| Component | Status | Files |
|-----------|--------|-------|
| security-privacy-review skill | done | skills/security-privacy-review/SKILL.md |
| bootstrap routing update | done | skills/samsara-bootstrap/SKILL.md |
| implement transition update | done | skills/implement/SKILL.md |
| iteration transition update | done | skills/iteration/SKILL.md |
| version bump | done | 0.6.1 → 0.7.0 |

### Phase 6: Execution Model Scope — DESIGN DECIDED (2026-04-23)

**發現日期**：2026-04-21（在 `2026-04-19_yin-coding-spirit` feature ship 前夕討論中浮現）

**觀察**：整套 samsara skills 和 agents（含 `samsara:code-reviewer`、`samsara:code-quality-reviewer`、9 yin principles、8 outcome criteria C1-C8）都是以 imperative code（Python / TS / Go / Rust 等）為預設 execution model 設計的。現代軟體工程包含多種 execution model，每種的「悄悄失敗」死法不同：

| Execution Model | 例子 | 與 code 不同的死法 |
|----------------|-----|------------------|
| Imperative code | Python, Go, TS | Stack trace 可追、exception model 明確 |
| Declarative IaC | Terraform, Pulumi, CloudFormation | State drift、provider lock、apply blast radius |
| Container specs | Dockerfile, OCI | Base image tag drift、layer cache poisoning、secrets in layers |
| Orchestration | Kubernetes YAML, Helm, Kustomize | Template render 出空值被 K8s 接受、values cascade 悄悄覆蓋 |
| Data pipelines | Airflow DAG, dbt, Dagster | 上游 schema 變動但 task 不失敗、partial batch |
| CI/CD | GitHub Actions, Jenkinsfile | Secret exposure、runner drift、step 順序依賴 |
| ML configs | Hydra, W&B sweeps | Hyperparameter interaction、reproducibility |

**為什麼這是框架層級的問題而非內容缺口**：Samsara 的唯一公理「存在即責任」在 declarative 系統中意義不同 — 一個 unused Terraform resource 不是 dead weight，是每月燒 cloud cost 的活損失 + security surface。這改變了 yin principles 的權重，不是補幾個 worked example 就能解決。

**選定方向：Option D — Principle-Level Abstraction + Domain Reference Files**

經 multi-level analysis（Senior/Staff/Principal）評估後，排除：
- ~~A（Universal reviewer）~~ — 假裝 universal 會變 rubber stamp，違反框架自身的「禁止隱式假設」
- ~~B（Sibling reviewers）~~ — N× agents 維護成本過高
- ~~C（Linter wrapper）~~ — Linter 是業界標準開發習慣，LLM 已知，不是 samsara 的價值所在

**設計決策（2026-04-23 confirmed）：**

| 問題 | 決策 | 理由 |
|------|------|------|
| Agent 架構 | Single agent + reference routing | 維護成本低，review procedure 統一 |
| Principle 適用性 | Reference file 宣告 excluded_principles | 邊界明確，不依賴 model 詮釋能力 |
| Linter 整合 | 不做 | 業界慣例，LLM 已知 |
| Router 偵測 | Two-pass: extension + directory first, content inspection for ambiguous cases | Deterministic 優先，heuristic 只在需要時啟動 |

**架構：**
```
code-quality-reviewer (現有 agent)
    ↓ Pass 1: extension + directory convention (deterministic)
    ↓ Pass 2: content inspection (only for ambiguous files like .yaml, .py)
    ↓ still ambiguous → UNKNOWN
    ↓ loads domain-specific reference file
references/
├── code-quality.md          ← 現有（imperative code）
├── iac-quality.md           ← 新（Terraform, Pulumi, CloudFormation）
├── container-quality.md     ← 新（Dockerfile, OCI）
├── orchestration-quality.md ← 新（K8s YAML, Helm, Kustomize）
├── pipeline-quality.md      ← 新（Airflow, dbt, GitHub Actions, CI/CD）
└── ...future domains
```

**Reference file 結構變化：** 每份 reference file 新增 applicability declaration — 宣告 `excluded_principles`（含理由）。Reviewer 讀到 excluded principle 直接輸出 `UNKNOWN — excluded by domain reference: {reason}`，不進入判斷。

**實作範圍：**
1. Router 機制加入 `code-quality-reviewer` agent
2. 現有 `code-quality.md` 加入 applicability declaration（全部 applicable，作為 baseline）
3. 第一份 domain reference: `iac-quality.md`（Terraform 為主驗證對象）
4. `code-reviewer` agent 同步加入 execution-model awareness

### Phase 7: Multi-Platform Support — NOT STARTED

支援 Codex、Gemini CLI、Windsurf 三個平台的安裝。

**策略**：採用 agency-agents 的 source → convert → install 模式（非 OpenSpec 的 TypeScript adapter 模式），並補上 agency-agents 缺少的 update 機制。
- 現有 SKILL.md（markdown + YAML frontmatter）作為 single source of truth
- `scripts/convert.sh`：轉換成各平台格式
- `scripts/install.sh`：自動偵測已安裝的工具 + 首次安裝
- `scripts/update.sh`：偵測已安裝的平台 + 比對版本/內容差異 + 同步更新（agency-agents 缺少此功能）

**目標平台格式：**

| 平台 | 路徑 | Scope | 格式差異 |
|------|------|-------|---------|
| Claude Code | `.claude-plugin/` | project | 現有格式，無需轉換 |
| Codex | `~/.codex/skills/` | home | SKILL.md 格式類似 |
| Gemini CLI | `~/.gemini/extensions/` | home | Extension model，最小 frontmatter |
| Windsurf | `.windsurf/` 或 `.windsurfrules` | project | 可能需合併成單一 rules 文件 |

**Reference：**
- `reference_opensource/OpenSpec` — 24 平台 adapter pattern，程式化生成
- `reference_opensource/agency-agents` — 11 平台 convert + install scripts，Bash

## Design Documents

- **Phase 1 Spec**: `docs/superpowers/specs/2026-04-01-samsara-harness-design.md`
- **Phase 1 Plan**: `docs/superpowers/plans/2026-04-02-samsara-harness-phase1.md`
- **Phase 2 Spec**: `docs/superpowers/specs/2026-04-07-samsara-phase2-design.md`
- **Phase 2 Plan**: `docs/superpowers/plans/2026-04-07-samsara-phase2.md`

## Key Design Decisions

1. 完全取代 superpowers，不共存
2. Phase 1-4 僅支援 Claude Code；Phase 7 擴展至 Codex、Gemini CLI、Windsurf
3. Monorepo 子模組（可獨立安裝）
4. 陰面約束內建在各 skill，通用約束透過 bootstrap 注入
5. 狀態追蹤全部用 YAML（不用 markdown table）
6. 流程用 Graphviz digraph 描述（不用 ASCII art）
7. Implement 支援三種執行模式（parallel/sequential subagent, inline）
8. 每個階段之間有 human gate
9. Dispatch-template as context injection pattern — subagent 無法讀取 skill support files，所以 shared artifacts（schema, templates）由主 agent 透過 dispatch-template 注入到 subagent prompt 中。Canonical source 存為獨立檔案（如 `scar-schema.yaml`），dispatch-template 指示主 agent 讀取並 paste。此 pattern 已被 overview.md + task files 的注入驗證可行。
