# Task 6: Manifest + Reference Converter

## Context

Read: overview.md

This task handles two simpler conversion modules:

### Manifest Converter
Transform `.claude-plugin/plugin.json` → `.codex-plugin/plugin.json`. Differences:
- Directory name: `.claude-plugin/` → `.codex-plugin/`
- Extra fields: Codex requires `"skills": "./skills/"` field
- Optional fields: `interface` block for Codex marketplace metadata

Source:
```json
{
  "name": "samsara",
  "description": "...",
  "version": "0.8.0",
  "author": { "name": "Roymond Liao" }
}
```

Target:
```json
{
  "name": "samsara",
  "version": "0.8.0",
  "description": "...",
  "author": { "name": "Roymond Liao" },
  "skills": "./skills/"
}
```

### Reference Converter
4 reference files (`references/*.md`): code-quality.md, code-review.md, iac-quality.md, iac-review.md.

These are content files loaded by agents during review. They may contain tool name references that need transformation rules applied. Copy to output with body rules applied.

## Files

- Create: `samsara_cli/converter/manifest.py`
- Create: `samsara_cli/converter/reference.py`
- Test: `tests/test_converter/test_manifest.py`
- Test: `tests/test_converter/test_reference.py`

## Death Test Requirements

- Test: Manifest missing required fields (name, version) in source must fail at source validation, not produce incomplete target
- Test: Manifest with extra unknown fields from source must be preserved (not dropped) — future-proof
- Test: Reference file with tool references (e.g., "use the Grep tool") must have rules applied, not copied verbatim
- Test: Reference file with code blocks containing tool names must NOT have rules applied inside code blocks — `\`\`\`yaml\n  tool: Read\n\`\`\`` must be preserved

## Implementation Steps

- [ ] Step 1: Write death tests for manifest field preservation, reference code block protection
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for manifest transformation, reference rule application
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement ManifestConverter:
  - `convert(source_manifest: Path, platform_config: PlatformConfig, template: Template) -> dict`
  - Read source JSON, render target via manifest.json.j2, preserve unknown fields
- [ ] Step 6: Implement ReferenceConverter:
  - `convert(source_ref: Path, rules: list[TransformationRule]) -> str`
  - Apply body rules to .md content, skip code blocks
- [ ] Step 7: Run all tests — verify they pass
- [ ] Step 8: Write scar report

## Expected Scar Report Items

- Potential shortcut: Code block detection in references — simple regex for triple backtick blocks may miss indented code blocks or code spans
- Assumption to verify: Reference files are pure markdown — no YAML frontmatter. If any have frontmatter, parser must handle it.
- Potential shortcut: Manifest version field — should converter update version to indicate "codex-adapted" or keep original? Decision: keep original (unified version).

## Acceptance Criteria

- Covers: "Success - full convert pipeline" (manifest + reference portions)
- Covers: "Degradation - source has new skill not in platform config" (reference converter handles unknown files generically)
