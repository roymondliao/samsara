---
name: implement
description: Use when a plan with tasks exists and you need to execute implementation
---

# Implement — Death Test First, Scar Report Always

Execute tasks with death tests before unit tests.

## Process

Use task planning and task planning for progress tracking.

On entry, read index.yaml to analyze task dependencies.

## Subagent Context

Use `subagent named "samsara-implementer"` for agent dispatch.
See dispatch-template.md for the Gemini subagent dispatch: template.

After all tasks complete, activate the `samsara-security-privacy-review` skill skill.
