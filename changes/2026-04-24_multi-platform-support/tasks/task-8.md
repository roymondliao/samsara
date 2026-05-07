# Task 8: CLI + Installer — Typer App, convert/install/update/validate Commands

## Context

Read: overview.md

The CLI is the user-facing interface. Built with Typer + Rich for output formatting. The installer handles platform detection and file placement.

Commands:
- `samsara-cli convert --platform codex [--source ./] [--output ./dist/codex/]`
- `samsara-cli install <platform> [--scope project|global] [--source ./dist/codex/]`
- `samsara-cli update <platform> [--scope project|global]`
- `samsara-cli validate --platform codex [--source ./dist/codex/]`
- `samsara-cli list-platforms`

Source discovery: convention-based (cwd) + `--source` override. If cwd has `.claude-plugin/plugin.json`, it's recognized as samsara source.

Install logic (`--scope project`, default):
1. Detect if target platform CLI is installed (via `version_cmd` from config)
2. If not installed: abort with clear error + install URL
3. Convert (if `--source` not provided, run convert first)
4. Copy `.codex-plugin/` to CWD
5. Output post-install instructions (e.g., "Add codex_hooks = true to config.toml")

Install logic (`--scope global`):
1. Detect if target platform CLI is installed (via `version_cmd` from config)
2. If not installed: abort with clear error + install URL
3. Convert (if `--source` not provided, run convert first)
4. Create marketplace source dir (`~/.codex/plugins/samsara/samsara/.codex-plugin/`)
5. Copy converted files to marketplace source dir
6. Backup `config.toml` → `config.toml.bak`
7. Register marketplace + enable plugin + set feature flags in `config.toml`
8. Output post-install instructions (restart Codex)

Update = re-convert + re-install (idempotent). Scope must match original install.

## Files

- Create: `samsara_cli/main.py`
- Create: `samsara_cli/installer/__init__.py`
- Create: `samsara_cli/installer/detect.py`
- Create: `samsara_cli/installer/install.py`
- Modify: `pyproject.toml` — add CLI entry point `[project.scripts] samsara-cli = "samsara_cli.main:app"`
- Test: `tests/test_installer/test_detect.py`
- Test: `tests/test_installer/test_install.py`

## Death Test Requirements

- Test: `install codex` when Codex CLI not installed must abort with clear error — not silently write files to non-existent path
- Test: `install codex` (default, project scope) must NOT modify user's `~/.codex/config.toml` — only output instructions
- Test: `install codex --scope global` must backup `config.toml` before modification — no backup = abort
- Test: `install codex --scope global` must register marketplace + enable plugin + set feature flags in `config.toml`
- Test: `install codex --scope global` repeated must NOT duplicate registration entries in `config.toml` (idempotent)
- Test: `convert` with invalid `--platform` must fail with list of available platforms — not generic error
- Test: `convert` with `--source` pointing to non-samsara directory must fail at source validation — not at converter

## Implementation Steps

- [ ] Step 1: Write death tests for platform not found, invalid source, config modification prevention
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for CLI commands, platform detection, install logic
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement PlatformDetector:
  - `detect(platform_name: str, platform_config: PlatformConfig) -> DetectionResult`
  - Run `version_cmd`, check platform CLI exists
- [ ] Step 6: Implement Installer with scope support:
  - `install(converted_dir: Path, platform_config: PlatformConfig, scope: str) -> InstallResult`
  - `scope="project"`: copy `.codex-plugin/` to CWD
  - `scope="global"`: create marketplace source dir, copy files, backup + register in config.toml
  - Both: output post-install instructions
- [ ] Step 7: Implement Typer CLI app:
  - `convert` command: load engine → run convert → output summary
  - `install` command: detect → convert (if needed) → install with scope → instructions
  - `update` command: convert → install with scope (idempotent)
  - `validate` command: load validator → run → report
  - `list-platforms` command: scan config/platform/ → list available
- [ ] Step 8: Add CLI entry point to pyproject.toml
- [ ] Step 9: Run all tests — verify they pass
- [ ] Step 10: Write scar report

## Expected Scar Report Items

- Potential shortcut: Package is `samsara_cli` (underscore) but CLI command is `samsara-cli` (hyphen). Verify `pyproject.toml` `[project.scripts]` correctly maps hyphenated command to underscore package import.
- Assumption to verify: Codex marketplace source dir structure (`~/.codex/plugins/samsara/samsara/.codex-plugin/`) matches how Codex discovers local marketplace plugins — verify with actual Codex plugin loading
- Potential shortcut: `update` command with no `--platform` flag — should it update all installed platforms? Currently undefined. Decide: require explicit platform.
- Potential shortcut: Global install modifies `config.toml` — TOML write must preserve existing formatting and comments. Consider using `tomlkit` (preserves style) instead of `tomli-w` (does not) for config.toml modification.
- Assumption to verify: Codex `config.toml` `[features]` section accepts `codex_hooks = true` — or is it under a different key path?

## Acceptance Criteria

- Covers: "Degradation - Codex CLI not installed"
- Covers: "Success - project install to Codex"
- Covers: "Success - global install to Codex"
- Covers: "Success - validate converted output"
- Covers: "Success - idempotent update"
