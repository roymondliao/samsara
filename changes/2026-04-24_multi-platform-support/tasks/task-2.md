# Task 2: Transformation Rules Engine — Scoped Regex/Literal Pattern Replacement

## Context

Read: overview.md

The rules engine is the core conversion machinery. It takes a list of TransformationRule objects (from platform config) and applies them to text content. Rules are scoped (frontmatter vs body), typed (regex vs literal), and ordered.

This engine is generic — it doesn't know about skills, agents, or hooks. It just transforms text according to rules. Each converter module will use this engine.

## Files

- Create: `samsara_cli/converter/__init__.py`
- Create: `samsara_cli/converter/rules.py`
- Test: `tests/test_converter/test_rules.py`

## Death Test Requirements

- Test: Rule scoped to 'body' must NOT modify frontmatter content — even if the pattern matches
- Test: Regex rule with capture group must substitute correctly — `\1` must reference the first group
- Test: Overlapping rules (rule A matches text that rule B already transformed) must produce deterministic output — order matters
- Test: Literal rule must NOT interpret regex metacharacters — 'Read tool' must not match 'Read tools' if using word boundaries
- Test: Empty input text must return empty text, not raise error
- Test: Rule with match pattern not found in text must return text unchanged, not raise error

## Implementation Steps

- [ ] Step 1: Write death tests for scope violation, overlapping rules, literal vs regex confusion
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for regex rules with capture groups, literal exact matches, multiple rules in sequence
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement RulesEngine class in rules.py:
  - `apply(text: str, rules: list[TransformationRule], scope: str) -> str`
  - Parse SKILL.md into frontmatter + body sections
  - Apply rules only to matching scope
  - Regex rules use `re.sub` with capture group support
  - Literal rules use `str.replace` (exact match)
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report

## Expected Scar Report Items

- Potential shortcut: Word boundary matching for literal rules — `'Read tool'` should not match `'ReadTool'` or `'Preread tool'`. May need `\b` wrapper for literal rules too.
- Assumption to verify: Order of rules in config is preserved when loaded by Hydra/Pydantic — YAML list order must be deterministic.
- Potential shortcut: SKILL.md frontmatter parsing — using simple `---` delimiter split vs a proper YAML frontmatter parser. Edge case: `---` appearing in body content.

## Acceptance Criteria

- Covers: "Silent wrong mapping - transformation rule matches unintended text"
- Covers: "Silent wrong mapping - frontmatter corrupted by body transformation"
