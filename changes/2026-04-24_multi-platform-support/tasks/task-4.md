# Task 4: Agent Converter — Markdown to TOML Format Conversion

## Context

Read: overview.md

The agent converter transforms 6 agent `.md` files into Codex `.toml` format. This is a structural format change, not just content transformation.

Samsara agents to convert:
- code-quality-reviewer, code-reviewer, implementer, infra-explorer, structure-explorer, yin-explorer

Source format (Claude Code agent .md):
```markdown
(markdown body with instructions, no frontmatter)
```

Target format (Codex agent .toml):
```toml
name = "samsara-code-quality-reviewer"
description = "..."
developer_instructions = """
(converted markdown body)
"""
```

Steps per agent:
1. Parse .md file — extract the full body as instructions
2. Apply transformation rules to the body (tool references, dispatch syntax)
3. Generate agent name from filename: `code-quality-reviewer` → `samsara-code-quality-reviewer`
4. Generate description from first meaningful line or section
5. Render .toml via Jinja2 template (`agent.toml.j2`)

## Files

- Create: `samsara_cli/converter/agent.py`
- Test: `tests/test_converter/test_agent.py`

## Death Test Requirements

- Test: Agent body with triple-quoted TOML string containing `"""` must be escaped — raw embed would break TOML parsing
- Test: Agent body with tool references (Read, Grep, Glob, Bash) must have rules applied — not just copied verbatim
- Test: Generated .toml must parse correctly with a TOML parser (tomli) — not just string concatenation
- Test: Agent name in .toml must match the naming convention used in skill dispatch references — mismatch breaks dispatch
- Test: Agent body exceeding 8KB (some samsara agents are large) must be handled — verify no TOML length truncation

## Implementation Steps

- [ ] Step 1: Write death tests for TOML escaping, tool reference transformation, name matching
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for each of the 6 agents' conversion
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement AgentConverter class:
  - `convert(source_agent_path: Path, rules: list[TransformationRule], naming_config: NamingConfig, template: Template) -> ConvertedAgent`
  - Read .md body
  - Apply transformation rules to body
  - Extract description (first line or heading)
  - Escape body for TOML triple-quote embedding
  - Render via agent.toml.j2 template
  - Validate output parses as valid TOML
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report

## Expected Scar Report Items

- Potential shortcut: Description extraction from agent .md — some agents start with a heading, others with prose. Heuristic may not work for all 6.
- Assumption to verify: TOML triple-quoted strings (`"""..."""`) handle all markdown content including code blocks with backticks, YAML embedded in markdown, etc.
- Potential shortcut: Some agents reference Claude Code-specific tools in structured formats (e.g., `(Tools: Read, Glob, Grep, Bash)`) — these are not natural language but structured tool lists. Regex rules may not match this format.

## Acceptance Criteria

- Covers: "Agent dispatch mismatch - name not found"
- Covers: "Template rendering with missing field"
- Covers: "Success - full convert pipeline" (agent portion)
