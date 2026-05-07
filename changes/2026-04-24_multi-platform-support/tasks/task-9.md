# Task 9: Integration Tests — Pipeline, Format Validation, Snapshot

## Context

Read: overview.md

This task creates integration tests that verify the full conversion pipeline works end-to-end. Three layers:

1. **Pipeline tests**: Source → convert → validate → verify output structure completeness
2. **Format validation tests**: Converted files are valid for the target platform (TOML parses, JSON schema matches, frontmatter valid, no unconverted patterns)
3. **Snapshot tests**: Convert output matches committed expected output — any change in conversion logic shows as a diff

These tests run in CI (Python only, no Codex needed).

Requires test fixtures: a minimal samsara source directory and expected Codex conversion output.

## Files

- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_pipeline.py`
- Create: `tests/integration/test_format_validation.py`
- Create: `tests/integration/test_snapshot.py`
- Create: `tests/fixtures/source/` — minimal samsara source (2-3 skills, 1 agent, 1 hook, 1 reference, 1 manifest)
- Create: `tests/fixtures/expected/codex/` — expected conversion output for snapshot comparison
- Test: self (these ARE the tests)

## Death Test Requirements

- Test: Pipeline test must fail if output is missing even one expected file — not pass with partial output
- Test: Format validation must fail if .toml file has syntax error — not skip validation
- Test: Snapshot test must fail if conversion output differs from committed snapshot — force explicit snapshot update
- Test: Fixture source must be valid samsara source (passes source validator) — invalid fixtures produce meaningless test results

## Implementation Steps

- [ ] Step 1: Create minimal test fixtures in `tests/fixtures/source/`:
  - `.claude-plugin/plugin.json` — minimal manifest
  - `skills/research/SKILL.md` — skill with transition statement
  - `skills/implement/SKILL.md` — skill with agent dispatch references
  - `skills/implement/dispatch-template.md` — companion file with Agent tool syntax
  - `agents/implementer.md` — agent with tool references
  - `hooks/hooks.json` + `hooks/session-start` — hook with Claude Code output format
  - `references/code-review.md` — reference with tool references
- [ ] Step 2: Run full conversion on fixtures → generate expected output → commit to `tests/fixtures/expected/codex/`
- [ ] Step 3: Write pipeline integration tests (verify file count, structure, naming)
- [ ] Step 4: Write format validation tests (TOML parse, JSON schema, frontmatter, unconverted patterns)
- [ ] Step 5: Write snapshot tests (byte-for-byte comparison with `--update-snapshots` flag)
- [ ] Step 6: Run all integration tests — verify they pass
- [ ] Step 7: Write scar report

## Expected Scar Report Items

- Potential shortcut: Minimal fixtures may not cover all edge cases (e.g., skills with Graphviz diagrams, large agent files, skills with multiple companion files). May need to expand fixtures later.
- Assumption to verify: Snapshot comparison is platform-independent (no line-ending differences between macOS and Linux CI)
- Potential shortcut: `--update-snapshots` flag implementation — need to decide: separate CLI command or pytest flag? Recommend pytest fixture with `UPDATE_SNAPSHOTS=1` env var.

## Acceptance Criteria

- Covers: "Success - full convert pipeline" (end-to-end verification)
- Covers: "Success - validate converted output" (format validation)
- Covers: all death_path scenarios (integration tests should catch any regression)
