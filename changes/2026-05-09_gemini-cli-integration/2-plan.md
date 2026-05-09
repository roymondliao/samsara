# Technical Plan: Gemini CLI Integration

## Planning Pre-thinking: Information Assumptions

To write this plan, I am assuming:
- Research established the integration path: Gemini CLI must be added through `samsara-cli`, matching the Codex convert/install/update lifecycle.
- Research established native Gemini output paths: project scope uses `.gemini/skills/`, `.gemini/agents/`, and `.gemini/settings.json`; global scope uses `~/.gemini/skills/`, `~/.gemini/agents/`, and `~/.gemini/settings.json`.
- Research established `.agents/skills` alias output is out of scope; Gemini output must use `.gemini/skills`.
- Research established the core runtime contract: file generation is not enough; bootstrap context, skill discovery, subagent discovery, and workflow chain behavior must be verified as far as Gemini CLI permits.
- Existing code establishes the implementation boundary: platform YAML, templates, converters, target validation, installer, detector, CLI tests, and integration fixtures.

Gaps I cannot resolve from Research:
- None.

Uncertainties (I cannot determine if more information is needed):
- None. Gemini CLI runtime smoke depth may vary by local CLI capabilities, but this is an implementation constraint already covered by skip/degradation requirements, not a research blocker.

## Technical Specification

### Architecture

Add `gemini-cli` as a first-class platform target in the existing `samsara-cli` conversion framework. The canonical source remains the current samsara Claude Code-style tree (`skills/`, `agents/`, `hooks/`, `references/`, `.claude-plugin/plugin.json`). Conversion emits Gemini-native files:

```text
dist/gemini-cli/
├── .gemini/
│   ├── agents/
│   │   └── samsara-*.md
│   ├── hooks/
│   │   └── samsara-session-start.sh
│   ├── settings.json
│   └── skills/
│       └── samsara-*/
│           ├── SKILL.md
│           └── companion files
└── .agents/
    └── references/
```

The implementation should preserve existing Codex behavior. Shared abstractions can be extended, but Codex snapshots and tests must keep passing.

### Interfaces

#### `samsara-cli convert --platform gemini-cli`

Inputs:
- `platform`: `gemini-cli`
- `source`: samsara source root, default CWD
- `output`: output directory, default `./dist/gemini-cli`

Outputs:
- `success`: output directory contains complete Gemini-native files and passes target validation.
- `failure`: conversion aborts before final output is committed, with a specific error message.
- `unknown`: target validation cannot determine whether Gemini output is structurally loadable. Unknown must fail conversion or mark the relevant smoke result skipped/degraded; it must never be treated as success.

#### `samsara-cli install gemini-cli --scope project`

Inputs:
- converted or source samsara directory
- project CWD

Outputs:
- `success`: `.gemini/skills`, `.gemini/agents`, `.gemini/hooks`, and `.gemini/settings.json` are merged into CWD without touching `~/.gemini`.
- `failure`: invalid converted output, invalid existing JSON, or CLI detection failure aborts before unsafe writes.
- `unknown`: if a settings merge cannot prove the final JSON includes samsara hook entries exactly once, installation must fail.

#### `samsara-cli install gemini-cli --scope global`

Inputs:
- converted or source samsara directory
- user home directory from `HOME`

Outputs:
- `success`: files are installed under `~/.gemini`, existing `settings.json` is backed up, and hook config is idempotently merged.
- `failure`: invalid settings JSON, backup failure, or write failure aborts with actionable error.
- `unknown`: partial copy or indeterminate settings merge must not be reported as installed.

### Platform Config

Create `samsara_cli/config/platform/gemini-cli.yaml` with:
- `platform.name`: `gemini-cli`
- `platform.version_cmd`: `gemini --version`
- `paths.plugin_dir`: `.gemini`
- `paths.skills_dir`: `.gemini/skills`
- `paths.agents_dir`: `.gemini/agents`
- `paths.hooks_file`: `settings.json`
- `paths.references_dir`: `.agents/references`
- `install.global.config_path`: `~/.gemini/settings.json`
- `formats.agent.type`: `markdown`
- `formats.agent.template`: `agent.md.j2`
- `formats.hook_output.context_injection_field`: `hookSpecificOutput.additionalContext`
- `formats.hook_output.template`: `settings.json.j2`
- `formats.hook_output.script_template`: `hook.sh.j2`
- `formats.manifest.enabled`: `false`
- `naming.skill_prefix`: `samsara`
- `naming.separator`: `-`
- `permissions.feature_flags`: empty

### Conversion Rules

Gemini transformation rules should cover:
- skill chaining: source `invoke \`samsara:X\`` becomes Gemini-facing instruction to activate/use the `samsara-X` skill.
- subagent dispatch: source `subagent_type: "samsara:X"` becomes Gemini-facing instruction to use the `@samsara-X` subagent or the subagent tool named `samsara-X`.
- tool names: Claude/Codex-specific tool references become Gemini tool language (`read_file`, `grep_search`, `run_shell_command`, or neutral wording where exact names are not stable).

### Agent Conversion

Gemini agents are markdown files, not TOML. The converted file must start with YAML frontmatter:

```yaml
---
name: samsara-implementer
description: ...
kind: local
---
```

The body must contain transformed agent instructions. Empty bodies, missing names, invalid slug names, and unconverted `subagent_type:` patterns are hard failures.

### Hook Conversion

Gemini hooks live in `.gemini/settings.json` under `hooks`. `SessionStart` must run a shell script stored in `.gemini/hooks/samsara-session-start.sh`. The script must:
- read Gemini hook JSON from stdin without printing logs to stdout
- emit JSON only on stdout
- inject bootstrap content through `hookSpecificOutput.additionalContext`
- optionally include `systemMessage`
- fail closed: if bootstrap cannot be read, return JSON that marks degraded context rather than printing plain text

Settings merge must preserve unrelated settings and append samsara hook entries only if absent.

### Installer Behavior

The installer currently has Codex-oriented TOML config handling. It must become config-file-type aware:
- JSON settings files use JSON parse/merge/write.
- TOML config files keep existing Codex behavior.
- Project install merges native tree into CWD and never touches home.
- Global install backs up the configured user settings file before modifying it.

### Target Validation

`TargetValidator` must become platform-aware enough to validate both Codex and Gemini:
- no unconverted source skill invocation patterns in `.md`/`.txt`
- no unconverted `subagent_type:` patterns
- Gemini agent `.md` files have parseable frontmatter with `name` and `description`
- Gemini settings JSON parses and contains a `SessionStart` hook entry
- Gemini skill directories live under `.gemini/skills`, not `.agents/skills`
- Codex TOML validation keeps existing behavior

### Death Cases

| Death case | Trigger | Lie | Truth | Detection |
| --- | --- | --- | --- | --- |
| Settings overwrite | Installing into a project/user with existing `.gemini/settings.json` | Install reports success | User settings or unrelated hooks are lost | Test existing settings survive byte/semantic merge |
| Duplicate hook | Re-running install/update | Hooks are "idempotent" | `SessionStart` contains duplicate samsara entries | Test repeated install yields one equivalent hook |
| Bootstrap stdout pollution | Hook script prints logs/plain text to stdout | Hook ran | Gemini ignores or fails JSON parsing | Test hook stdout is valid JSON only |
| Wrong context field | Hook emits Codex-style or display-only field | Session shows a message | Model never receives bootstrap context | Test `hookSpecificOutput.additionalContext` exists |
| Agent format mismatch | Gemini converter emits `.toml` or invalid `.md` frontmatter | Agent file exists | Gemini cannot load subagent | Test markdown frontmatter schema |
| Skill alias drift | Output uses `.agents/skills` | Skills exist somewhere | Gemini target violates project decision and may confuse install | Test `.gemini/skills` only |
| Pattern leakage | Rules miss `invoke samsara` or `subagent_type:` | Conversion passes | Runtime instructions point to dead syntax | Target validator scans converted text |
| Codex regression | Shared converter changes for Gemini | Gemini works | Existing Codex path breaks | Codex unit/integration/snapshot tests still pass |

## File Map

- `samsara_cli/config/platform/gemini-cli.yaml` — Gemini platform registry entry.
- `samsara_cli/config/templates/gemini-cli/agent.md.j2` — Gemini markdown agent template.
- `samsara_cli/config/templates/gemini-cli/hook.sh.j2` — Gemini SessionStart hook script template.
- `samsara_cli/config/templates/gemini-cli/settings.json.j2` — Gemini settings hook template.
- `samsara_cli/config/template_env.py` — unchanged unless template lookup needs tests only.
- `samsara_cli/converter/agent.py` — add markdown agent conversion path or split a Gemini-specific converter behind format dispatch.
- `samsara_cli/converter/hook.py` — add Gemini settings JSON and hook script conversion support.
- `samsara_cli/converter/engine.py` — dispatch platform-specific agent/hook output names and write Gemini settings.
- `samsara_cli/installer/detect.py` — register Gemini CLI install URL and detection.
- `samsara_cli/installer/install.py` — add JSON settings merge/backup behavior without regressing Codex TOML merge.
- `samsara_cli/validators/target.py` — make validation platform-aware for Gemini markdown agents/settings JSON.
- `samsara_cli/main.py` — pass platform into validation if validator API changes.
- `tests/test_config/` — Gemini config/schema/template tests.
- `tests/test_converter/` — Gemini agent/hook/engine death and happy-path tests.
- `tests/test_installer/` — Gemini project/global install merge tests.
- `tests/test_validators/` — Gemini target validation tests.
- `tests/test_cli/` — CLI list/convert/install/validate coverage for `gemini-cli`.
- `tests/fixtures/expected/gemini-cli/` — committed snapshot for Gemini output.
- `tests/integration/test_smoke_gemini_cli.py` — skip-safe Gemini smoke validation.

## Validation Plan

Commands must follow project rules:

```bash
source .venv/bin/activate
uv run pytest tests/test_config tests/test_converter tests/test_installer tests/test_validators tests/test_cli
uv run pytest tests/integration
uv run pre-commit run --all-files
```

Gemini runtime smoke tests must skip cleanly when `gemini --version` is unavailable. They must never write to real `~/.gemini` unless testing global install against a patched `HOME`.
