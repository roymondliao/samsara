# Overview: Multi-Platform Support (Phase 7)

## Goal

Build a config-driven Python CLI (`samsara-cli`) that converts samsara's Claude Code plugin into target platform formats, starting with Codex.

## Architecture

Python CLI using Typer + Hydra `compose` API (no `@hydra.main` — avoids CLI conflict). Platform differences defined in YAML configs via Hydra config groups. Content transformations use scoped regex/literal rules. Format conversions use Jinja2 templates. All-or-nothing error handling — no partial output.

## Tech Stack

- **CLI**: Typer + Rich (already in pyproject.toml)
- **Config**: Hydra-core + Pydantic (already in pyproject.toml)
- **Templates**: Jinja2 (already in pyproject.toml)
- **YAML**: PyYAML (already in pyproject.toml)
- **Testing**: pytest (already in pyproject.toml)
- **TOML output**: tomli-w (new dependency — for writing agent .toml files)

## Key Decisions

- **Config-driven**: Platform differences are data (YAML), not code. New platform = new config + templates, zero code change for basic cases.
- **Structured rules for content, Jinja2 for format**: Text transformations use scoped regex/literal rules (deterministic, testable). Format changes (md→toml, JSON schema differences) use Jinja2 templates.
- **All-or-nothing**: Partial conversion is worse than no conversion (broken workflow chain). Converter writes to temp dir, moves on full success only.
- **No state tracking**: Install/update are idempotent. User manages their own installations.
- **Unified version**: samsara version = CLI version = plugin.json version.
- **Source format config**: `claude-code.yaml` defines source format, enabling future bidirectional conversion.
- **Hydra compose API**: Use `hydra.compose()` + `initialize()` for config loading — Typer manages CLI args, Hydra manages config composition. No `@hydra.main` decorator.

## Death Cases Summary

1. **Transformation rule matches unintended text** — rule scoped to `body` accidentally modifies non-tool-reference text. Mitigated by: scoped rules + word boundary matching + negative test cases.
2. **Chain break from unconverted transition** — one skill's `invoke samsara:X` not converted, Codex user hits dead end. Mitigated by: target validator scans all output for remaining source patterns.
3. **Agent dispatch name mismatch** — skill references agent name that doesn't match converted agent filename. Mitigated by: cross-validation in target validator.

## File Map

### New files (samsara_cli/)
- `samsara_cli/__init__.py` — package init
- `samsara_cli/main.py` — Typer CLI entry point (convert, install, update, validate, list-platforms)
- `samsara_cli/config/__init__.py` — config package
- `samsara_cli/config/schema.py` — Pydantic models: PlatformConfig, TransformationRule, PathsConfig, InstallConfig, FormatsConfig
- `samsara_cli/config/loader.py` — Hydra compose API config loading with platform selection
- `samsara_cli/config/config.yaml` — Hydra base config (defaults + source paths)
- `samsara_cli/config/platform/claude-code.yaml` — Source platform definition (Hydra config group)
- `samsara_cli/config/platform/codex.yaml` — Codex platform config with transformation rules (Hydra config group)
- `samsara_cli/config/templates/codex/agent.toml.j2` — Agent md → toml template
- `samsara_cli/config/templates/codex/hook.sh.j2` — Hook script template
- `samsara_cli/config/templates/codex/manifest.json.j2` — Plugin manifest template
- `samsara_cli/config/templates/codex/hooks.json.j2` — Hooks config template
- `samsara_cli/converter/__init__.py` — converter package
- `samsara_cli/converter/engine.py` — Conversion orchestrator: load config → validate source → run converters → validate target → write output
- `samsara_cli/converter/rules.py` — Transformation rules engine: parse rules from config, apply scoped regex/literal replacements
- `samsara_cli/converter/skill.py` — SKILL.md converter: parse frontmatter, apply body rules, rename skill (: → -)
- `samsara_cli/converter/agent.py` — Agent converter: parse md, extract body, render toml via Jinja2
- `samsara_cli/converter/hook.py` — Hook converter: adapt script output format, transform hooks.json
- `samsara_cli/converter/manifest.py` — Manifest converter: .claude-plugin → .codex-plugin, add extra fields
- `samsara_cli/converter/reference.py` — Reference converter: apply body transformation rules to reference files
- `samsara_cli/installer/__init__.py` — installer package
- `samsara_cli/installer/detect.py` — Platform detection: check if CLI installed, find install paths
- `samsara_cli/installer/install.py` — Install logic: copy converted output to platform path, output instructions
- `samsara_cli/validators/__init__.py` — validators package
- `samsara_cli/validators/source.py` — Source validator: check plugin structure, required files, frontmatter
- `samsara_cli/validators/target.py` — Target validator: check converted output against platform spec, detect unconverted patterns

### New files (tests/)
- `tests/test_config/test_schema.py` — Config Pydantic model tests
- `tests/test_config/test_loader.py` — Hydra config loading tests
- `tests/test_converter/test_rules.py` — Transformation rules engine tests
- `tests/test_converter/test_skill.py` — Skill converter tests
- `tests/test_converter/test_agent.py` — Agent converter tests
- `tests/test_converter/test_hook.py` — Hook converter tests
- `tests/test_converter/test_manifest.py` — Manifest converter tests
- `tests/test_converter/test_reference.py` — Reference converter tests
- `tests/test_converter/test_engine.py` — Engine orchestration tests
- `tests/test_installer/test_detect.py` — Platform detection tests
- `tests/test_installer/test_install.py` — Install logic tests
- `tests/test_validators/test_source.py` — Source validator tests
- `tests/test_validators/test_target.py` — Target validator tests
- `tests/integration/test_pipeline.py` — Full convert pipeline tests
- `tests/integration/test_format_validation.py` — Converted output format tests
- `tests/integration/test_snapshot.py` — Snapshot comparison tests
- `tests/integration/test_smoke_codex.py` — Codex smoke tests (@pytest.mark.integration, local only)
- `tests/fixtures/source/` — Minimal samsara source for testing
- `tests/fixtures/expected/codex/` — Expected conversion output snapshots

### Modified files
- `pyproject.toml` — Add tomli-w dependency, CLI entry point
