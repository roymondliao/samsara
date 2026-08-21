# Pre-thinking: codex-global-companion-runtime

## Session: 2026-07-22T00:00:00+08:00

## Step 1 — Locate the work

**Type(s):** infra / external-integration / refactor
**Depth:** deep thinking
- Uncertainty: Runtime provenance, manifest migration, and converter/installer ownership cross process and installation boundaries.
- Blast radius: Every Codex companion command in project and global installs sits on this seam; false success blocks validation across multiple workflow layers.

## Step 2 — Assumptions, scope frame, and core identity

### Assumptions

#### A1: durable-tool-runtime
**Assumption:** A global adapter may depend on a separately installed Samsara CLI only when installer preflight proves the executable is durable and dependency-complete.
**Boundary:** Holds for a runner outside the source tree that can execute `version` and every converted companion; does not hold for `uv run` or source `.venv` launchers.
**If it breaks:** All installed files remain present but workflow validators cannot start; the first project invoking a companion notices.
**Basis:** `bugfix/2026-07-22_codex-global-companion-runtime/root-cause.yaml`
**Confidence:** confident

#### A2: absolute-command-resolution
**Assumption:** Installed artifacts must use a verified absolute runner rather than process PATH.
**Boundary:** Holds while the recorded executable exists; an external tool uninstall or relocation requires update to fail visibly.
**If it breaks:** Terminal launches may work while GUI/IDE Codex launches fail, producing environment-dependent behavior.
**Basis:** `samsara_cli/installer/install.py:467` and the observed missing global command
**Confidence:** confident

#### A3: companion-syntax-floor
**Assumption:** Distributed Python companions must remain parseable below the CLI runtime version even though dependency execution stays runner-owned.
**Boundary:** Applies to `skills/*/scripts/*.py` and `agents/*/scripts/*.py`; it does not authorize direct interpreter fallback.
**If it breaks:** A missing-runner failure is obscured by a syntax failure, and artifact inspection depends on the host Python minor version.
**Basis:** Python 3.13 grammar reproduction against `skills/codebase-map/scripts/validate_codebase_map.py`
**Confidence:** confident

#### A4: manifest-migration
**Assumption:** Existing schema-1 install manifests must update in place to the runtime-aware schema without deleting user-owned files.
**Boundary:** Applies when the old manifest has the currently supported ownership fields; malformed or unknown schemas still fail loud.
**If it breaks:** Existing global users cannot apply the repair without manual cleanup or risk stale ownership.
**Basis:** `samsara_cli/installer/install.py` ownership reconciliation and `~/.samsara/install-manifest.codex.json`
**Confidence:** confident

### Domain core identity (codebase-craft)
**Decision ID:** PT-CI
**Canonical label:** executable-install-contract
**Core identity:** A Samsara installation is an executable, dependency-complete runtime contract with owned artifacts—not a successful file copy.
**Operability check:** This identity rejects writing a success manifest when companion files exist but the runner cannot execute them from a foreign cwd.

## Step 3 — Multi-lens evidence

### Lens: structure
**Assumptions covered:** A1, A2, A4
**Evidence surface:** CLI entrypoint, converter output, installer rewriting, and manifest lifecycle.
**Why this lens:** A file-copy view hides the runtime edge between generated instructions and the executable that consumes them.
**Facts found:** Converter emits `samsara-cli run-companion`; installer resolves companion directories but not the runner; schema 1 records no runtime identity — sources: `samsara_cli/config/platform/codex.yaml`, `samsara_cli/installer/install.py`.
**Side-path discoveries:** Installer unit tests inject converted output and therefore do not prove the actual launcher survives process exit.
**Not found / gaps:** none

### Lens: operability
**Assumptions covered:** A1, A2, A3
**Evidence surface:** PATH inheritance, uv tool layout, source virtualenv, foreign project cwd, Python grammar, and dependency availability.
**Why this lens:** Converter correctness can pass while GUI/IDE process environment makes runtime commands disappear.
**Facts found:** `~/.local/bin/samsara-cli` is absent; the only command is source `.venv/bin/samsara-cli`; Python 3.13 grammar rejects the installed validator.
**Side-path discoveries:** Merely restoring parentheses would still leave dependency ownership unresolved.
**Not found / gaps:** none

### Lens: evolution
**Assumptions covered:** A4
**Evidence surface:** Recent installer commits and existing global manifest.
**Why this lens:** Runtime fields must join, not replace, the existing owned-file reconciliation contract.
**Facts found:** `989d3d5` introduced companion installation and schema-1 owned paths; the live global manifest uses that schema.
**Side-path discoveries:** A strict schema-2-only reader would strand the installation that exposed the bug.
**Not found / gaps:** none

Default lens decisions: boundary and contract facts are covered by structure and operability; no independent additional evidence surface remains.

## Step 4 — Design decisions

### Decision: runner provenance
**Decision ID:** PT-D1
**Box:** evidence-decided
**Decision:** Global install accepts only an absolute runner outside the Samsara source tree after executable and companion smoke checks; otherwise it stops with the exact `uv tool install` command.
**Basis / derivation chain:** Observed source-venv disappearance path + explicit global lifecycle boundary.
**Reversal cost:** Low if another package manager later supplies an equally durable executable; provenance check can generalize without changing artifacts.

### Decision: command resolution owner
**Decision ID:** PT-D2
**Box:** evidence-decided
**Decision:** Converter emits a scope-agnostic runner token; Installer owns replacement with the verified absolute runner after scope and provenance are known.
**Basis / derivation chain:** Converter cannot know the install root or executable lifecycle; Installer already owns companion placeholder and hook path resolution.
**Reversal cost:** Moderate because moving this into conversion would bake one machine's path into reusable output.

### Decision: runtime-aware manifest
**Decision ID:** PT-D3
**Box:** self-derived
**Decision:** Manifest schema 2 records runtime command, package version, and Python version; schema 1 is accepted only for one-way migration during update.
**Basis / derivation chain:** Samsara existence-is-responsibility → installed commands depend on a runtime → runtime identity must be durable evidence beside owned paths.
**Reversal cost:** Low through a future schema migration; runtime fields are additive authority.

### Decision: fallback behavior
**Decision ID:** PT-D4
**Box:** evidence-decided
**Decision:** Converted instructions treat missing runner as `CANNOT VALIDATE` and explicitly prohibit Python, uv, or inferred-runtime fallback.
**Basis / derivation chain:** The observed fallback changed one visible missing-command failure into a misleading syntax failure.
**Reversal cost:** Low; target-native executable packaging can replace the prohibition with a new explicit runner.

### Decision: syntax compatibility
**Decision ID:** PT-D5
**Box:** self-derived
**Decision:** Distributed companion sources target Python 3.11 syntax through Ruff per-file configuration and grammar tests; dependency execution remains CLI-owned.
**Basis / derivation chain:** Portable distributed source + cheap syntax compatibility + no authorization for direct execution.
**Reversal cost:** Low; raise the floor only with explicit platform evidence.

### Real seams (codebase-craft — a named decision category)

#### Seam: runtime-provenance
**Decision ID:** PT-S1
**Box:** evidence-decided
**What it is:** Boundary between the invoking CLI process and an installation allowed to persist its command as a runtime dependency.
**Evidence tier:** already-happened (git history)
**Basis:** `989d3d5` created installed run-companion dependencies without recording the executable lifecycle.

#### Seam: command-materialization
**Decision ID:** PT-S2
**Box:** evidence-decided
**What it is:** Boundary where scope-agnostic converted commands become machine-specific absolute installed commands.
**Evidence tier:** already-happened (git history)
**Basis:** Installer already materializes hook and companion directory paths after conversion.

#### Seam: installation-evidence
**Decision ID:** PT-S3
**Box:** self-derived
**What it is:** Install manifest boundary between files copied and executable dependencies proven.
**Evidence tier:** domain-essential
**Basis:** Update can reconcile only responsibilities recorded by the installation owner.

## Step 5 — External-call answers

No external calls remain. The user explicitly selected the complete durable-runtime solution and authorized implementation; package-manager self-install and direct interpreter fallback remain outside scope.

## Step 6 — Honest handoff

### L1 (handoff to planning — Key Decisions single source)
**Decision refs:**
- PT-CI (executable-install-contract)
- PT-S1 (runtime-provenance)
- PT-S2 (command-materialization)
- PT-S3 (installation-evidence)

### Evaluation Contract

**Contract ID:** PT-EVAL
**Canonical label:** evaluation-contract
**Primary evaluator:** Clean-environment global companion execution
**Agent can perform it by:** Install from a durable test runner, remove source virtualenv paths from PATH, switch to a foreign Git cwd, and invoke every installed companion through the manifest-recorded command.
**Pass signal:** Every command exits through its declared format contract, all runner paths are absolute and resolvable, and no fallback interpreter is invoked.
**Fail signal:** Install succeeds with an ephemeral/unrecorded runner, any companion cannot start, or execution changes when source virtualenv paths leave PATH.
**Feedback loop:** Inspect runner provenance and installed-command materialization before changing a companion script.
**Out of scope validation:** Long-term behavior after a user manually deletes the uv tool environment; update must detect it, but the installer cannot prevent external deletion.

### Commitment

**Date:** 2026-07-22T00:00:00+08:00
**Decision:** Proceed
**Accepted gaps:** none
**Residual list:** none
