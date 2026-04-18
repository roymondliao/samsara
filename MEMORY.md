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
research → planning → implement → validate-and-ship
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
│   ├── implement/                       # Step 4: Death Test First + Scar Report
│   │   ├── SKILL.md
│   │   ├── scar-report.md              # 支援文件
│   │   └── templates/
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

### Continuous Learning — External (not samsara-owned)

Continuous-learning is **shared infrastructure at kaleidoscope-tools root**, NOT
a samsara component. Knowledge belongs to the project, not the tool.

Location: `hooks/`, `agents/learnings-observer.md`, `skills/recall-learnings/`,
`skills/review-learnings/`, `scripts/`, `tests/` — all at repo root.

This session discovered **ISSUE-001** (planning template allows File Map to
contradict Key Decisions) as a samsara framework bug. See `samsara/issue.md`.

Design docs: `changes/2026-04-15_continuous-learning/`

### Phase 4: Auto Iteration — NOT STARTED (概念已定義)

> 陰面的精神，陽面的框架，太極混元的意識。

**重新定義**：不是「數據驅動的優化循環」（design.md 的陽面描述）。而是：

> 一個自動化的系統自我審問機制 — 從「系統哪裡在假裝健康」出發，附帶陽面的指標改善。

**核心哲學**：
- 陽面 iteration 問「系統變好了嗎」
- 陰面 iteration 問「系統還能出賣自己嗎」
- 太極混元：每次改善同時記錄代價（cost_of_improvement + signal_lost + degradation_conditions）

**自動化迴圈（半自動，Phase 4 v1）**：
```
陰面診斷（系統哪裡假裝健康）→ 排序（最危險的腐爛點）→ 提出修改方案 → [Human Gate] → 實作 → 雙面驗證（陽面指標 + 陰面代價）→ 保留/丟棄 → 更新 codebase-map + iteration-log → 下一輪
```

**終止條件（陰面版）**：
- signal_lost 累積過高（系統看不見自己的失敗）
- 陰面代價超過陽面收益
- rot_risks 歸零但 confidence 全是 low（看起來完美但判斷不可靠）

**演進路徑**：B（半自動 + human gate）→ A（全自動 + 事後 review）→ C（全自動 + 終止條件 human gate）

**Reference**：Karpathy autoresearch（陽面自動化原型），反轉為陰面出發

### Phase 5: Multi-Platform Support — NOT STARTED

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
2. Phase 1-4 僅支援 Claude Code；Phase 5 擴展至 Codex、Gemini CLI、Windsurf
3. Monorepo 子模組（可獨立安裝）
4. 陰面約束內建在各 skill，通用約束透過 bootstrap 注入
5. 狀態追蹤全部用 YAML（不用 markdown table）
6. 流程用 Graphviz digraph 描述（不用 ASCII art）
7. Implement 支援三種執行模式（parallel/sequential subagent, inline）
8. 每個階段之間有 human gate
9. Dispatch-template as context injection pattern — subagent 無法讀取 skill support files，所以 shared artifacts（schema, templates）由主 agent 透過 dispatch-template 注入到 subagent prompt 中。Canonical source 存為獨立檔案（如 `scar-schema.yaml`），dispatch-template 指示主 agent 讀取並 paste。此 pattern 已被 overview.md + task files 的注入驗證可行。
