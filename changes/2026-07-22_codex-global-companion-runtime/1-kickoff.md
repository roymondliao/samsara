# Kickoff: codex-global-companion-runtime

## Execution Mode

Execution mode: human-in-the-loop

## Problem Source

`problem-autopsy.md`

Diagnosis evidence:

- `../../bugfix/2026-07-22_codex-global-companion-runtime/bug-report.yaml`
- `../../bugfix/2026-07-22_codex-global-companion-runtime/root-cause.yaml`

## Problem Essence (named handoff to pre-thinking)

Global Codex installations must retain an executable, dependency-complete
companion runtime after the installation process and source environment exit.

## Scope Contract (sole scope authority)

- **What must be solved:** Installed companion commands currently depend on an ephemeral source virtualenv and permit an unsafe interpreter fallback path.
- **Areas involved:** CLI distribution prerequisite, Codex installer, install manifest, companion command conversion, companion syntax compatibility, documentation, and runtime-contract tests.

### Must-Have (with death conditions)

- **Durable runner identity** — Death condition: remove when Codex natively packages agent/skill executables with dependencies.
- **Absolute installed commands** — Death condition: remove when Codex supplies a verified runner resolver independent of process PATH.
- **Fail-loud install and validation** — Death condition: never; a global install cannot honestly succeed with an unresolvable runtime.
- **No inferred interpreter fallback** — Death condition: remove only if every supported target defines an equivalent dependency-complete runner contract.
- **Companion syntax floor** — Death condition: remove when companions cease to be distributed as Python source.

### Nice-to-Have

- A separate `doctor` command for auditing an installation after external environment changes.

### Not solved now

- **Installer silently invokes `uv tool install` on itself** — Reason: package-manager mutation needs an explicit user command and must not be hidden inside adapter installation.
- **Bundling a private Python distribution under `.samsara/`** — Reason: uv tool already owns an isolated executable environment and dependency lifecycle.
- **Supporting direct system-Python execution** — Reason: it defeats the dependency-complete runner authority.

## Evidence

- `bugfix/2026-07-22_codex-global-companion-runtime/root-cause.yaml`
- Global manifest installs companion files but records no runtime command.
- `~/.local/bin/samsara-cli` is absent while the only executable is under the source `.venv`.
- Python 3.13 grammar rejects the installed Codebase Map validator's Python 3.14-only exception syntax.

## Risk of Inaction

Every successful global install can become a false success when Codex starts in
another project: validation and publication stop, while models may improvise an
unmanaged interpreter and produce a different failure.

## Accepted Research Gaps

none

## North Star

```yaml
metric:
  name: "Globally resolvable companion commands"
  definition: "Share of installed companion commands that execute through the manifest-recorded runner from a foreign cwd with source virtualenv paths removed from PATH."
  current: 0
  current_basis: "Observed Codebase Map publication failure and absent durable CLI executable"
  target: 1
  target_basis: "Every installed companion is a required runtime dependency"
  invalidation_condition: "Codex owns native dependency-aware companion packaging"
  corruption_signature: "File-existence tests pass while a clean-environment execution fails"

sub_metrics:
  - name: "Companion syntax-floor compliance"
    current: 0
    current_basis: "Python 3.13 grammar rejects validate_codebase_map.py"
    target: 1
    target_basis: "All distributed Python companions must parse at the declared floor"
    proxy_confidence: high
    decoupling_detection: "Run grammar parsing and a real run-companion smoke test separately"
```

## Delivery Stakeholders

- **Decision maker:** Samsara maintainer
- **Impacted teams:** Codex global-install users and maintainers of agent/skill companions
