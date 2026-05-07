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

### Phase 6: Execution Model Scope — DONE (2026-04-24)

Both reviewer agents now route by file domain (code/iac/container/pipeline/orchestration), load domain-specific reference files, and return UNKNOWN for unrecognized domains. Spirit-first review layering ensures agent philosophy drives principle application.

**Architecture**: Single agent + reference routing (Option D). Reference files declare `excluded_principles`. Router: extension+directory first, content inspection for ambiguous files, UNKNOWN if still ambiguous.

**Key design insight**: Agent spirit (philosophy) is the upper layer; reference file principles are the foundation/base layer. Spirit drives, koans illustrate — not the inverse. This was a Round 2 iteration fix (commit be2dc6d).

| Component | Status | Files |
|-----------|--------|-------|
| code-quality-reviewer routing | done | agents/code-quality-reviewer.md |
| code-reviewer routing | done | agents/code-reviewer.md |
| code-quality reference | done | references/code-quality.md |
| code-review reference | done | references/code-review.md |
| iac-quality reference | done | references/iac-quality.md |
| iac-review reference | done | references/iac-review.md |
| spirit-first layering | done | all agents + references |
| version bump | done | 0.7.0 → 0.8.0 |

**Ship manifest**: `changes/2026-04-23_execution-model-scope/ship-manifest.yaml`
**Kill switch**: Revert to commit ac9409b (removes Step 0 routing + reference protocol)
**Silent failure surface**: high (11 known conditions across 4 scar reports)

### Phase 6: Deferred Items & Accepted Risk Expiry

以下項目在 Phase 6 iteration 中被 defer 或 accept，需要後續處理：

**Deferred (需要外部 trigger)：**
- I/DRY excluded_principles 移除 — 需 real IaC review 驗證 coverage transfer（iteration-log #3, #4, #5）
- Theoretical koans → production patterns — 需 real Terraform review data
- OpenTofu divergence — 需 OpenTofu adoption trigger
- Provider-specific patterns — 超出 Phase 6 scope
- Output format pipeline validation — 需下游 pipeline

**Accepted risk expiry dates：**
- **2026-07-24**：LLM compliance, scar report domain-agnostic, DRY exclusion breadth, DRY coverage transfer, applicability section default
- **2026-10-24**：I coverage transfer, ignore_changes severity distinction

### Phase 7: Multi-Platform Support — DONE (2026-04-28, Codex-first)

Codex 平台的完整 conversion + installation pipeline，以 Python CLI 實作（非原計劃的 bash scripts）。

**實作架構（`samsara_cli/`）：**
- Pydantic schema + Hydra config loader（`config/`）
- Transformation rules engine，支援 scope/type/priority filtering（`converter/`）
- Skill、agent、reference、hook 個別 converter
- `ConversionEngine` orchestrator：all-or-nothing output，SourceValidator + TargetValidator
- Installer：dual-scope（user/project），Codex native layout（`.codex/`）
- Typer CLI：`convert`, `install`, `update`, `validate`, `version` 命令

**測試規模**：512 tests，169 death tests，10 scar reports，35 known silent failure conditions。

**Ship manifest**：`changes/2026-04-24_multi-platform-support/ship-manifest.yaml`

**Known failure modes（未解決）：**
- Literal transformation rules apply inside fenced code blocks（silent corruption）
- Codex runtime behavior assumptions unverified（hooks.json format 等）
- config.toml comment stripping on global install（tomllib roundtrip loses comments）

**Accepted risks expiry：2026-07-28**（Codex runtime behavior, code block unawareness, symlink-following, 14 unverified assumptions）

**Post-ship fixes（Level 2 iteration + follow-up）：**
- `31ac517` — Codex native layout fix（`.codex/` 而非 `.codex-plugin/`）
- `9b2a845` — JSON output trailing newline（POSIX convention）
- `cb45da6` — duplicate agent names → EngineError with casefold（DC-7-6）
- `fde0020` — reject `$N` backrefs in regex replace strings（DC-14）
- `211148d` — shlex.split for version_cmd（DC-8-6）

**Gemini CLI / Windsurf**：尚未實作（Phase 7 = Codex-first）。

## Design Documents

- **Phase 1 Spec**: `docs/superpowers/specs/2026-04-01-samsara-harness-design.md`
- **Phase 1 Plan**: `docs/superpowers/plans/2026-04-02-samsara-harness-phase1.md`
- **Phase 2 Spec**: `docs/superpowers/specs/2026-04-07-samsara-phase2-design.md`
- **Phase 2 Plan**: `docs/superpowers/plans/2026-04-07-samsara-phase2.md`

## Key Design Decisions

1. 完全取代 superpowers，不共存
2. Phase 1-6 僅支援 Claude Code；Phase 7 擴展至 Codex（done），Gemini CLI / Windsurf（未實作）
3. Monorepo 子模組（可獨立安裝）
4. 陰面約束內建在各 skill，通用約束透過 bootstrap 注入
5. 狀態追蹤全部用 YAML（不用 markdown table）
6. 流程用 Graphviz digraph 描述（不用 ASCII art）
7. Implement 支援三種執行模式（parallel/sequential subagent, inline）
8. 每個階段之間有 human gate
9. Dispatch-template as context injection pattern — subagent 無法讀取 skill support files，所以 shared artifacts（schema, templates）由主 agent 透過 dispatch-template 注入到 subagent prompt 中。Canonical source 存為獨立檔案（如 `scar-schema.yaml`），dispatch-template 指示主 agent 讀取並 paste。此 pattern 已被 overview.md + task files 的注入驗證可行。
