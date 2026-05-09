# Task 1: Register Gemini platform config and templates

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

Gemini CLI must become a first-class `samsara-cli` target. This task only registers platform metadata and creates renderable templates; it does not implement full conversion behavior.

## Files

- Create: `samsara_cli/config/platform/gemini-cli.yaml`
- Create: `samsara_cli/config/templates/gemini-cli/agent.md.j2`
- Create: `samsara_cli/config/templates/gemini-cli/hook.sh.j2`
- Create: `samsara_cli/config/templates/gemini-cli/settings.json.j2`
- Modify: `samsara_cli/installer/detect.py`
- Modify: `tests/test_config/test_loader.py`
- Modify: `tests/test_config/test_loader_death.py`
- Modify: `tests/test_config/test_template_env.py`
- Modify: `tests/test_installer/test_detect.py`
- Modify: `tests/test_installer/test_detect_death.py`

## Death Test Requirements

- Test: loading `gemini-cli` fails loudly if required config sections are misspelled or missing.
- Test: template environment for `gemini-cli` uses `StrictUndefined`; missing variables must raise instead of rendering empty content.
- Test: `PlatformDetector.available_platforms()` includes `gemini-cli` and still excludes `claude-code`.
- Test: detector returns `False`, not an exception, when `gemini --version` is unavailable.

## Implementation Steps

- [ ] Step 1: Write death tests for invalid Gemini platform config and missing template variables.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path config and detector tests.
- [ ] Step 4: Run new tests; verify they fail.
- [ ] Step 5: Add Gemini platform YAML and templates with minimal required fields.
- [ ] Step 6: Add Gemini install URL/detection metadata.
- [ ] Step 7: Run all touched tests; verify they pass.
- [ ] Step 8: Write scar report.
- [ ] Step 9: Commit.

## Expected Scar Report Items

- Potential shortcut: copying Codex paths into Gemini config and accidentally emitting `.agents/skills`.
- Potential shortcut: declaring hook fields in config but leaving templates incompatible with Gemini hook JSON protocol.
- Assumption to verify: Gemini CLI binary command is `gemini --version`.

## Acceptance Criteria

- Covers: "Silent failure - output uses .agents/skills alias"
- Covers: "Degradation - Gemini CLI unavailable during smoke tests"
