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

### Phase 3: Auto Iteration Implementation — NOT STARTED

自動迭代實作。基於北極星指標的數據驅動優化循環。見 `docs/samsara/design.md` 的迭代章節。

### Phase 4: Multi-Platform Support — NOT STARTED

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
2. Phase 1-3 僅支援 Claude Code；Phase 4 擴展至 Codex、Gemini CLI、Windsurf
3. Monorepo 子模組（可獨立安裝）
4. 陰面約束內建在各 skill，通用約束透過 bootstrap 注入
5. 狀態追蹤全部用 YAML（不用 markdown table）
6. 流程用 Graphviz digraph 描述（不用 ASCII art）
7. Implement 支援三種執行模式（parallel/sequential subagent, inline）
8. 每個階段之間有 human gate
