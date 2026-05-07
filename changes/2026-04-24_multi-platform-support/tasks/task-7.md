# Task 7: Conversion Engine — Orchestrator + Source/Target Validators

## Context

Read: overview.md

The conversion engine is the central orchestrator that ties all converter modules together. It also includes the source and target validators that enforce all-or-nothing semantics.

Flow:
1. Load platform config via Hydra
2. Validate source structure (source validator)
3. Create temp output directory
4. Run each converter module: skills, agents, hooks, manifest, references
5. Validate converted output (target validator)
6. If all pass: move temp dir to final output path
7. If any fail: delete temp dir, report error

### Source Validator
Checks that the samsara source directory has the expected structure:
- `.claude-plugin/plugin.json` exists and has required fields
- `skills/` directory exists with expected skill subdirectories
- `agents/` directory exists with expected .md files
- `hooks/` directory exists with hooks.json and script files
- All SKILL.md files have valid frontmatter

### Target Validator
Checks that converted output is valid for the target platform:
- No remaining source patterns (e.g., `invoke \`samsara:` or `subagent_type:`)
- All .toml files parse correctly
- All SKILL.md frontmatter is valid (only name + description for Codex)
- Manifest has required platform-specific fields
- Cross-validation: every agent name referenced in skills exists as a converted agent file
- Skill naming: no `:` separator in output

## Files

- Create: `samsara_cli/converter/engine.py`
- Create: `samsara_cli/validators/__init__.py`
- Create: `samsara_cli/validators/source.py`
- Create: `samsara_cli/validators/target.py`
- Test: `tests/test_converter/test_engine.py`
- Test: `tests/test_validators/test_source.py`
- Test: `tests/test_validators/test_target.py`

## Death Test Requirements

- Test: Engine must NOT produce partial output — if agent converter fails after skills are done, output dir must be empty
- Test: Target validator must detect unconverted `invoke \`samsara:` pattern in any output file — this is a hard error
- Test: Target validator must detect agent name mismatch — skill references "samsara-implementer" but agent file is named "implementer.toml" (missing prefix)
- Test: Source validator must fail if a required skill directory is missing — not silently skip it
- Test: Engine with source that has extra (unknown) files must NOT delete them from output — preserve unknown files with warning

## Implementation Steps

- [ ] Step 1: Write death tests for partial output prevention, unconverted pattern detection, name mismatch
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for source validation, target validation, engine orchestration
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement SourceValidator:
  - `validate(source_dir: Path) -> ValidationResult`
  - Check directory structure, file existence, frontmatter validity
- [ ] Step 6: Implement TargetValidator:
  - `validate(output_dir: Path, platform_config: PlatformConfig) -> ValidationResult`
  - Scan all files for unconverted patterns
  - Parse and validate format-specific files (.toml, .json)
  - Cross-validate agent references
- [ ] Step 7: Implement ConversionEngine:
  - `convert(source_dir: Path, platform: str, output_dir: Path) -> ConversionResult`
  - Load config, validate source, run converters in temp dir, validate target, move or abort
- [ ] Step 8: Run all tests — verify they pass
- [ ] Step 9: Write scar report

## Expected Scar Report Items

- Potential shortcut: Unconverted pattern detection — regex for `invoke \`samsara:` may miss variant patterns like `invoke\n\`samsara:` (newline between invoke and backtick)
- Assumption to verify: `tempfile.mkdtemp` + `shutil.move` is atomic enough for all-or-nothing on all platforms (macOS, Linux)
- Potential shortcut: Cross-validation of agent names requires parsing dispatch-template.md, not just SKILL.md — dispatch template is a support file that references agents

## Acceptance Criteria

- Covers: "All-or-nothing violation - partial output on failure"
- Covers: "Agent dispatch mismatch - name not found"
- Covers: "Partial chain break - transition statement not converted"
- Covers: "Degradation - source has new skill not in platform config"
