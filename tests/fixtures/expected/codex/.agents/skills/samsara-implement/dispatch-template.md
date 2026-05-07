# Implementer Dispatch Template

Use this template when dispatching an implementer subagent via the Subagent dispatch:

```
Subagent dispatch:
  agent named "samsara-implementer"
  description: "Implement Task N: [task title]"
  prompt: |
    [paste task context here]
```

## Rules

1. Always paste full text of the task file — the subagent cannot read files.
2. Include relevant scar reports from prior tasks.
