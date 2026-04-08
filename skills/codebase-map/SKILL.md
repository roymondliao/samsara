---
name: codebase-map
description: Use when entering a new project for the first time, or when the codebase has changed significantly — generates a yin-side codebase map with structural analysis and silent failure surface assessment
---

# Codebase Map — Yin-Side Project Analysis

Generate a map of the project that answers both "what is this system?" (yang) and "where is this system pretending to be healthy?" (yin).

> 一般的 codebase map 是陽面的 —「系統長什麼樣」。Samsara 的 codebase map 回答「系統在哪裡假裝健康」。

## Process

```dot
digraph codebase_map {
    node [shape=box];

    start [label="使用者執行 /samsara:codebase-map\n或 bootstrap 提醒後觸發" shape=doublecircle];
    check [label="檢查 .samsara/codebase-map.yaml\n是否已存在？" shape=diamond];
    mode [label="生成 or 更新？" shape=diamond];

    explore_parallel [label="Phase 1: 平行探索\nAgent 1 (結構) + Agent 3 (基礎設施)\n同時派出"];
    explore_yin [label="Phase 2: 陰面探索\nAgent 2 拿到 Phase 1 結果\n分析 rot risks + hidden coupling"];
    synthesize [label="Phase 3: 合成\n匯總三個 explorer 的產出\n生成 codebase-map.yaml + modules/*.yaml"];
    review [label="Human Review\n呈現摘要，確認或修正\n（特別是 confidence: low 的項目）" shape=diamond];
    write [label="寫入 .samsara/\ncodebase-map.yaml + modules/*.yaml"];
    done [label="完成" shape=doublecircle];

    start -> check;
    check -> mode [label="exists"];
    check -> explore_parallel [label="not exists"];
    mode -> explore_parallel [label="full regenerate"];
    mode -> explore_yin [label="incremental update\n(結構沒大變，只更新陰面)"];
    explore_parallel -> explore_yin;
    explore_yin -> synthesize;
    synthesize -> review;
    review -> write [label="confirmed"];
    review -> synthesize [label="revise"];
    write -> done;
}
```

## Phase 1: Parallel Exploration

Dispatch two agents simultaneously:

1. **structure-explorer** — modules, paths, dependencies, interfaces
2. **infra-explorer** — build system, config sources, data flow, external services

These two agents have no dependencies on each other. Dispatch in parallel.

## Phase 2: Yin-Side Exploration

After Phase 1 completes, dispatch:

3. **yin-explorer** — receives Phase 1 results as context. Analyzes rot risks, hidden coupling, assumptions, death impact for each module.

## Phase 3: Synthesis

After all three agents report back:

1. Merge structure-explorer output (modules, deps) + infra-explorer output (build, config, data flow) + yin-explorer output (rot risks, coupling, assumptions)
2. Generate summary: count rot_hotspots (top 3 by failure_level), count high_risk_coupling, count assumptions
3. Compute `silent_failure_surface`: low (<3 rot risks), medium (3-7), high (>7 or any level 4)
4. Generate `codebase-map.yaml` (Layer 1+2) from templates
5. Generate one `modules/<name>.yaml` (Layer 3) per module from templates

## Phase 4: Human Review

Present to user:
- Summary: module count, silent failure surface, top 3 rot hotspots
- List all `confidence: low` items — ask user to confirm or correct
- Ask: "Anything missing or wrong?"

After user confirms → write files to `.samsara/`

## Update Modes

When `.samsara/codebase-map.yaml` already exists, ask user:

> 「Codebase map 已存在（上次更新：YYYY-MM-DD）。選擇更新方式：
> (A) Full regenerate — 重跑三個 agent，完整重建
> (B) Incremental update — 只重跑陰面分析，保留結構不變」

## Output

Files written to target project:

```
project/.samsara/
├── codebase-map.yaml      # Layer 1+2: summary + module index + infrastructure
└── modules/               # Layer 3: per-module detail (yang + yin)
    ├── <module-1>.yaml
    ├── <module-2>.yaml
    └── ...
```

Use templates at `templates/codebase-map.yaml` and `templates/module.yaml`.
