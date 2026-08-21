# Task 1: Own durable runner installation state

**Task ID:** task-1

## Goal

Global install rejects an ephemeral runner before writing files and successful
install/update records and materializes one verified absolute companion runner.

## Source References

- Planning: PL-D1 (durable-runner-install-boundary)
- Design: PT-D1 (runner provenance), PT-D2 (command resolution owner), PT-D3 (runtime-aware manifest), PT-S1 (runtime-provenance), PT-S2 (command-materialization), PT-S3 (installation-evidence)
- Acceptance: AC-1 (ephemeral-runner-rejected), AC-2 (runtime-manifest-migrates)
- Seam: runtime-provenance

## Context Projection

Read the complete Overview and live anchors before writing. Preserve shared
Codex config and user-owned files during schema migration.

## Files

- Modify: `samsara_cli/installer/install.py`
- Modify: `samsara_cli/main.py`
- Modify: `tests/test_installer/test_owned_manifest.py`
- Modify: `tests/test_installer/test_install.py`
- Modify: `tests/test_cli/test_main.py`

## Constraints

- Validate provenance before conversion or target writes for global scope.
- Do not silently invoke `uv tool install`.
- Installer, not Converter, resolves the absolute runtime command.
- Accept schema 1 only as a one-way migration input; always write schema 2.
- Shared `.codex/config.toml` and `.codex/hooks.json` remain non-owned files.

## Death Test Requirements

- A source `.venv/bin/samsara-cli` global runner fails before any manifest or installed file appears.
- Corrupt or unsupported manifests still block update.
- Schema-1 migration preserves foreign files and writes runtime evidence.
- A runtime smoke failure cannot produce a success manifest.

## Unit Test Contract — required observable contract source

- Contract source: Installer output, installed commands, and `.samsara/install-manifest.codex.json`.

## Assumptions to Verify

- The current CLI executable can be resolved independently of process PATH — source: `samsara_cli/main.py` — if false: require an explicit runtime path rather than guessing.
- Companion `--help` is non-mutating — source: companion argparse entrypoints — if false: use a dedicated runner syntax/dependency probe.
