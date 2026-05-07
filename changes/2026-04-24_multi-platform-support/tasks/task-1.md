# Task 1: Config System — Pydantic Schema + Hydra Loader + Platform Configs

## Context

Read: overview.md

This task builds the foundation for the entire conversion framework. Every other task depends on the config system to know what to convert and how.

Platform differences are defined as data (YAML config), not code. The config system uses Hydra `compose` API for loading (no `@hydra.main` — Typer manages CLI), OmegaConf for composition, and Pydantic for validation.

Hydra config group pattern: `config/platform/` directory, each platform is a YAML file. Base `config.yaml` defines defaults and source paths. Loader uses `initialize()` + `compose()` context manager, then converts to Pydantic via `OmegaConf.to_container()`.

## Files

- Create: `samsara_cli/__init__.py`
- Create: `samsara_cli/config/__init__.py`
- Create: `samsara_cli/config/schema.py`
- Create: `samsara_cli/config/loader.py`
- Create: `samsara_cli/config/config.yaml` — Hydra base config (defaults + source paths)
- Create: `samsara_cli/config/platform/claude-code.yaml` — Source platform (Hydra config group)
- Create: `samsara_cli/config/platform/codex.yaml` — Target platform (Hydra config group)
- Create: `samsara_cli/config/templates/codex/agent.toml.j2`
- Create: `samsara_cli/config/templates/codex/hook.sh.j2`
- Create: `samsara_cli/config/templates/codex/manifest.json.j2`
- Create: `samsara_cli/config/templates/codex/hooks.json.j2`
- Modify: `pyproject.toml` — add tomli-w dependency, add CLI entry point
- Test: `tests/test_config/test_schema.py`
- Test: `tests/test_config/test_loader.py`

## Death Test Requirements

- Test: Config loading with missing required field (platform.name) must raise ValidationError, not silently default
- Test: Config loading with unknown platform name must fail explicitly — Hydra `compose()` with `overrides=["platform=nonexistent"]` must raise, not return empty config
- Test: Transformation rule with invalid regex pattern must fail at Pydantic validation time (after OmegaConf → dict → Pydantic), not at conversion time
- Test: `OmegaConf.to_container()` → Pydantic conversion must fail if platform config has extra unexpected keys (strict mode)

## Implementation Steps

- [ ] Step 1: Write death tests for config schema validation
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for config loading, platform selection, Hydra overrides
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement Pydantic models in schema.py (PlatformConfig, TransformationRule, PathsConfig, InstallConfig, ProjectInstallConfig, GlobalInstallConfig, FormatsConfig, NamingConfig, PermissionsConfig)
- [ ] Step 6: Implement Hydra loader in loader.py — use `initialize()` + `compose()` context manager, convert `DictConfig` → Pydantic via `OmegaConf.to_container(cfg, resolve=True)`
- [ ] Step 7: Write base `config.yaml` (defaults + source paths)
- [ ] Step 8: Write `platform/claude-code.yaml` (source format definition)
- [ ] Step 9: Write `platform/codex.yaml` (full platform config with all transformation rules)
- [ ] Step 10: Write Jinja2 templates for Codex (agent.toml.j2, hook.sh.j2, manifest.json.j2, hooks.json.j2)
- [ ] Step 11: Add tomli-w to pyproject.toml dependencies + CLI entry point
- [ ] Step 12: Run all tests — verify they pass
- [ ] Step 13: Write scar report

## Expected Scar Report Items

- Potential shortcut: Hydra `initialize()` `config_path` is relative to the calling module's file location — verify it resolves correctly when `loader.py` is in `samsara_cli/config/` and configs are siblings
- Assumption to verify: Pydantic v2 and OmegaConf `to_container()` output compatibility — OmegaConf returns plain dicts/lists, Pydantic v2 should accept these, but nested structures may need attention
- Assumption to verify: Hydra `compose()` context manager properly cleans up GlobalHydra state — multiple calls in tests won't leak state
- Assumption to verify: Regex patterns in YAML need proper escaping — double backslash for regex character classes

## Acceptance Criteria

- Covers: "Silent wrong mapping - frontmatter corrupted by body transformation" (rule scope is defined in config)
- Covers: "Template rendering with missing field" (StrictUndefined must be set in Jinja2 env)
