# Overview: Samsara Phase 4 — Auto Iteration (Dual-Level)

## Goal

建立雙層 iteration：task-level（implementer 自修 scar items）+ feature-level（跨 task 系統面問題），讓 scar report 從靜態文件變成 resolution pipeline。

## Architecture

兩層 iteration 對應兩個陰面觀察點：
- **Level 1 (task-level)**：融入 implement flow — implementer 完成 task 後自我審視 scar items，修 task scope 內的 actionable items。修改 `implementer.md` + `implement/SKILL.md`。
- **Level 2 (feature-level)**：新 skill `samsara:iteration` — 所有 tasks 完成後，aggregate 剩餘 scars，處理 cross-task patterns。在 implement 和 validate-and-ship 之間。

Flow: `implement (含 Level 1 per-task iteration) → commit → Level 2 feature iteration → validate-and-ship`

## Tech Stack

- Pure markdown skills（SKILL.md + support files + templates）
- YAML for structured output（iteration-log.yaml, scar reports）
- Graphviz digraph for flow description

## Key Decisions

- **Dual-level iteration**: task-level 在 implement 內，feature-level 在 implement 後
- **Level 1 scope 限制**: implementer 只修 task scope 內的 items，不跨 task files
- **Level 2 commit strategy**: per-fix commit（fixes 互相獨立）
- **Level 2 safety valve**: max 3 rounds, signal_lost 停滯偵測
- **Backward compatible**: Level 2 entry gate 可 skip，等同原本 flow
- **No new agents**: 復用 implementer + code-reviewer
- **Scar schema 擴展**: 加入 resolved_items + deferred_to_feature_iteration

## Death Cases Summary

1. **Cargo-cult self-iteration (L1)**: implementer 全部 defer 不做任何修復 — code reviewer 應質疑
2. **Cargo-cult triage (L2)**: 所有 items 標 accept — accept > 80% warning
3. **Level 1 over-scope**: implementer 修改其他 tasks 的 files — code reviewer 檢查

## File Map

- `samsara/agents/implementer.md` — 加入 self-iteration 步驟（Level 1）
- `samsara/skills/implement/SKILL.md` — 更新 per-task execution order + transition
- `samsara/skills/implement/templates/scar-schema.yaml` — 擴展 schema（resolved_items, deferred flag）
- `samsara/skills/iteration/SKILL.md` — 新建 feature-level iteration skill（Level 2）
- `samsara/skills/iteration/templates/iteration-log.yaml` — iteration log 模板
- `samsara/skills/samsara-bootstrap/SKILL.md` — 更新 skill chain + routing graph
- `samsara/MEMORY.md` — 更新 Phase 4 status + directory structure
