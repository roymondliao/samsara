# Task 3: Skill Converter — SKILL.md Content Transformation + Naming

## Context

Read: overview.md

The skill converter handles 11 SKILL.md files + their companion files (support docs, templates). For each skill:
1. Parse frontmatter and body
2. Rename skill directory: `samsara:X` naming convention → `samsara-X` (colon → hyphen in separator)
3. Apply transformation rules to body (via rules engine from task-2)
4. Copy companion files (support docs, templates) with body rules applied
5. Verify no source patterns remain in output

Samsara skills to convert:
- samsara-bootstrap, research, planning, implement, iteration, security-privacy-review, validate-and-ship, fast-track, debugging, codebase-map, writing-skills

Key transformation targets in skills:
- Transition statements: `invoke \`samsara:planning\`` → `$samsara-planning`
- Skill tool references: `using the Skill tool` → `$skill-name` syntax
- Agent dispatch: `subagent_type: "samsara:implementer"` → agent named "samsara-implementer"
- Tool name references: Read/Edit/Write/Bash/Grep/Glob/LS → Codex equivalents
- TaskCreate/TaskUpdate → update_plan

## Files

- Create: `samsara_cli/converter/skill.py`
- Test: `tests/test_converter/test_skill.py`

## Death Test Requirements

- Test: Skill with transition statement `invoke \`samsara:planning\`` must be converted — unconverted pattern in output is a hard error
- Test: Companion file (e.g., `problem-autopsy.md`) must also have body rules applied — not just SKILL.md
- Test: SKILL.md frontmatter `name` field must retain original value (not have rules applied to it)
- Test: SKILL.md frontmatter `description` field must NOT have tool references rewritten (description is for matching, not for instructions)
- Test: Graphviz digraph blocks in SKILL.md body must survive transformation — regex rules must not corrupt dot syntax

## Implementation Steps

- [ ] Step 1: Write death tests for unconverted transitions, frontmatter preservation, companion file transformation
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for each of the 11 skills' key transformation points
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement SkillConverter class:
  - `convert(source_skill_dir: Path, rules: list[TransformationRule], naming_config: NamingConfig) -> ConvertedSkill`
  - Parse SKILL.md frontmatter + body
  - Apply rules to body only
  - Rename skill directory per naming config
  - Process companion files recursively (apply rules to .md files, copy others as-is)
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report

## Expected Scar Report Items

- Potential shortcut: Template YAML files inside skills (e.g., `templates/kickoff.md`) contain markdown — rules should apply. But `templates/scar-schema.yaml` is pure YAML — rules should NOT apply. Need file-type-aware filtering.
- Assumption to verify: All 11 skills have consistent frontmatter format (only `name` + `description`). If any skill has extra frontmatter fields, parser must handle gracefully.
- Potential shortcut: `dispatch-template.md` in implement skill contains literal `Agent tool:` syntax that must be converted. This is a support file, not SKILL.md — verify companion file processing includes it.

## Acceptance Criteria

- Covers: "Partial chain break - transition statement not converted"
- Covers: "Silent wrong mapping - frontmatter corrupted by body transformation"
- Covers: "Success - full convert pipeline" (skill portion)
