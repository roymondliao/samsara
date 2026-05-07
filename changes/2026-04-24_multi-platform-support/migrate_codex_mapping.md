| Category | Claude Code Reference | Codex Environment Reality | Migration Recommendation | Priority |
|----------|----------------------|---------------------------|--------------------------|----------|
| Shell execution | Bash | exec_command | Keep using exec_command for shell operations | Low |
| File read | Read | No dedicated read tool; use exec_command + cat/sed/nl | Use exec_command with shell tools to read files | Medium |
| File listing | LS | No dedicated list tool; use exec_command + ls/find/rg --files | Use exec_command to list files via ls, find or ripgrep | Medium |
| File pattern search | Glob | No dedicated glob tool; use exec_command + find/glob/rg --files | Use find or ripgrep to match file patterns | Medium |
| Code search | Grep | No dedicated search tool; use exec_command + rg | Use exec_command with ripgrep for code searches | Medium |
| File edit | Edit / Write | apply_patch | Use apply_patch for patch-based file modifications | Medium |
| Skill | Skill tool / skill_name | Host-specific (e.g. $skill-name if supported) | Convert to target runtime's skill invocation syntax | High |
| Agent / subagent | Agent tool with subagent_type | Host-specific | Map subagent dispatch to target runtime's mechanism | High |
| Planning / tasks | TodoWrite / TaskCreate / TaskUpdate | update_plan | Use update_plan only for planning, not execution | Medium |
| Hooks | Hook schemas and lifecycle | Host-specific | Rewrite hooks to match target runtime's schema | High |
| Permissions / sandbox | Claude Code permission model | Host-specific | Revalidate and adjust to target runtime's permission model | High |
