# Overview: Gemini CLI Integration

## Goal

Add `gemini-cli` as a `samsara-cli` target that converts and installs canonical samsara content into Gemini-native `.gemini/` files.

## Architecture

The implementation extends the existing platform-configured conversion pipeline used by Codex. Gemini differs from Codex in two important places: subagents remain markdown files with YAML frontmatter, and hooks are merged into `.gemini/settings.json` instead of a standalone `hooks.json`.

## Tech Stack

Python, Typer, Pydantic, Jinja2 `StrictUndefined`, stdlib `json`/`tomllib`, pytest, existing `samsara_cli` converter/installer/validator modules.

## Key Decisions

- Use `.gemini/skills` only: `.agents/skills` alias output is out of scope for this integration.
- Keep canonical source unchanged: Gemini-specific behavior lives in platform config, templates, converter dispatch, installer merge logic, and validators.
- Treat settings merge as a first-class death path: losing or duplicating hooks is worse than failing install.
- Runtime smoke tests must skip cleanly when Gemini CLI is missing: structural tests still provide deterministic coverage.

## Death Cases Summary

1. Existing `.gemini/settings.json` is overwritten or duplicate hooks are appended while install reports success.
2. SessionStart hook emits valid-looking output but fails to inject bootstrap into `hookSpecificOutput.additionalContext`.
3. Converted output exists but uses wrong Gemini formats: TOML agents, `.agents/skills`, or leaked `subagent_type:` / `invoke samsara` source syntax.

## File Map

- `samsara_cli/config/platform/gemini-cli.yaml` — Gemini platform registry entry.
- `samsara_cli/config/templates/gemini-cli/agent.md.j2` — Gemini markdown subagent template.
- `samsara_cli/config/templates/gemini-cli/hook.sh.j2` — Gemini JSON-only SessionStart hook script.
- `samsara_cli/config/templates/gemini-cli/settings.json.j2` — Gemini settings hook template.
- `samsara_cli/converter/agent.py` — markdown agent conversion path.
- `samsara_cli/converter/hook.py` — Gemini settings and hook script conversion.
- `samsara_cli/converter/engine.py` — platform-specific artifact dispatch and output paths.
- `samsara_cli/installer/detect.py` — Gemini CLI detection metadata.
- `samsara_cli/installer/install.py` — JSON settings merge and global backup behavior.
- `samsara_cli/validators/target.py` — platform-aware Gemini validation.
- `samsara_cli/main.py` — validator API wiring if platform argument is required.
- `tests/test_config/` — Gemini config and template tests.
- `tests/test_converter/` — Gemini converter and engine tests.
- `tests/test_installer/` — Gemini install merge and isolation tests.
- `tests/test_validators/` — Gemini target validation tests.
- `tests/test_cli/` — CLI platform coverage.
- `tests/fixtures/expected/gemini-cli/` — Gemini snapshot fixture.
- `tests/integration/test_smoke_gemini_cli.py` — skip-safe Gemini smoke tests.
