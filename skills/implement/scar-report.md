# Scar Report — Format Guide

Every completed task leaves a scar report. This is the yin-side output of implementation — it records what the code cannot say about itself.

> 如果 AI 完成任務後宣告「完成」但不附帶 scar report，該完成狀態標記為 `completion_unverified`。

## Format

The canonical scar report schema is defined in `templates/scar-schema.yaml`. Read that file for the full schema, rules, and a verbatim example.

Scar reports are written as YAML at `scar-reports/task-N-scar.yaml`.

**For inline/cowork execution:** read `templates/scar-schema.yaml` before writing any scar report.

**For subagent dispatch:** the schema is injected into the dispatch prompt via `dispatch-template.md`. See the Scar Report Format section in the template.

## Anti-Pattern: The Clean Scar

A scar report that says "no shortcuts, no silent failures, no assumptions" is suspicious. It usually means the author didn't look hard enough, not that the code is perfect. Challenge it.
