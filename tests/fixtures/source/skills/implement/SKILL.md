---
name: implement
description: Use when a plan with tasks exists and you need to execute implementation
---

# Implement — Death Test First, Scar Report Always

Execute tasks with death tests before unit tests.

## Process

Use TaskCreate and TaskUpdate for progress tracking.

On entry, read index.yaml to analyze task dependencies.

## Subagent Context

Use `subagent_type: "samsara:implementer"` for agent dispatch.
See dispatch-template.md for the Agent tool: template.

After all tasks complete, invoke `samsara:security-privacy-review` skill.
