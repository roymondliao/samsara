# Pre-thinking: codebase-map-churn-autoregen

## Session: 2026-06-28

## Step A — Design and Gap Map

### Atomic Context Boundary (live facts derived)

- **Hook layer** (`hooks/hooks.json`, `hooks/check-codebase-map`): `check-codebase-map` is a bash script run on `SessionStart` (matcher `startup|clear|compact`, **timeout 3000ms**). It computes staleness from file **mtime** vs hardcoded `-gt 7` days, and only injects a context message. It does NOT read the map's `last_updated`, does NOT use git, has NO behavioral test.
- **Regeneration is an agent workflow** (`skills/codebase-map/SKILL.md`): regenerating the map dispatches 3 subagents (structure-explorer, infra-explorer, yin-explorer) + synthesis + a **Phase 4 human-review gate**. It is driven by the main agent, invoked via `/samsara:codebase-map`. A bash script cannot perform it.
- **Config**: `staleness_threshold_days: 7` lives in the generated `.samsara/codebase-map.yaml` (and its template) but is **read by no live code** — dead config. The hook hardcodes 7.
- **Cross-platform**: hooks are rewritten for codex/gemini by `samsara_cli` converter (`tests/test_converter/test_hook.py`). Any hook rewrite must survive conversion.
- **Map role** (confirmed in research): preview/navigation aid; live codebase wins on conflict. `pre-thinking` Atomic Context Boundary already says to treat the map as derived context and surface drift — but nothing executes regeneration.

### Information Gaps

#### Gap I1: git availability + honest fallback
**Question:** Is the target project always a git repo, and what must the mechanism show when churn cannot be computed (no git history / shallow clone / detached HEAD)?
**Hypothesis:** Not guaranteed git. When churn is uncomputable, the mechanism must report an explicit "churn unknown" state and NOT claim fresh — this is forced by research kill condition #1, so it is a floor, not a preference. Treated as a design constraint unless the user overrides.

### Design Decision Gaps

#### Gap D1: what trigger (a) session-start can actually do
**Question:** Given the bash hook cannot regenerate the map, what should happen at session start when churn is over threshold?
**Hypothesis:** Hook (bash, git churn) detects over-threshold and injects a directive-grade message; the agent does NOT auto-run a heavy 3-agent regen at session start (intrusive, before the user has asked for anything). Actual regeneration is deferred to pre-thinking entry (trigger b). Session start = honest strong signal; pre-thinking = the real auto-regen point.
**Planning impact:** Determines whether we modify agent session-start behavior, how intrusive the hook is, and whether regen can fire before the user does anything. Changes which artifacts are touched (hook only vs hook + a session-start agent behavior rule).

#### Gap D2: auto-regen vs the codebase-map human-review gate (in human-in-the-loop)
**Question:** When pre-thinking auto-triggers regeneration, does the codebase-map skill's Phase 4 human review still apply, or is regen fully unattended?
**Hypothesis:** Auto = the agent *initiates* regen without being asked, but the existing Phase 4 human review still applies in human-in-the-loop mode (agent regenerates, user confirms the result). "Auto" removes the need for the human to *remember to trigger*, not the human's review of correctness.
**Planning impact:** Changes whether the codebase-map skill needs a new non-interactive/auto-initiated path, and the failure modes (a wrong auto-map landing unreviewed vs reviewed).

#### Gap D3: churn threshold — signal(s) and value
**Question:** Should staleness use changed-file count, commit count, or both, and at what default threshold?
**Hypothesis:** Primary = changed source-file count since `last_updated` (excluding `changes/`, `docs/`, `bugfix/`); default ~30 files. Commit count is a weak secondary, optional. Single honest signal beats a precise multi-signal formula (research out-of-scope: per-file-type classification).
**Planning impact:** Detection logic shared by the hook and pre-thinking; the threshold field replaces the dead `staleness_threshold_days` in the map schema/template.

#### Gap D4: detection/regen ownership + config location (resolved by hypothesis)
**Question:** Which artifact owns churn detection vs regeneration, and where does the threshold config live?
**Hypothesis:** Detection logic is duplicated-but-trivial in two honest places (bash hook for session-start signal; agent/pre-thinking for the regen decision) since they run in different runtimes; regeneration is owned solely by the codebase-map skill. Threshold config replaces `staleness_threshold_days` with a churn-threshold field in `.samsara/codebase-map.yaml` (backward compatible: old field removed from template, new field added). Proceeding on this unless D1/D2 answers move ownership.
**Planning impact:** File ownership map; map schema change; converter coverage for the rewritten hook.

---

### Group 1: auto-regen mechanism (round 1)

**Q1 (Gap D1 — session-start behavior):** What should session start do when churn is over threshold?
**A:** Detect + strong signal; regeneration deferred to pre-thinking. The bash hook computes git churn honestly and injects a directive-grade message at session start, but does NOT run the heavy 3-agent regen. The actual auto-regen happens at pre-thinking entry (trigger b). Resolves the architectural impossibility: detection is scriptable, regeneration is agent-only.

**Q2 (Gap D2 — regen vs human review):** Does the codebase-map Phase 4 human review still apply to auto-triggered regen?
**A:** Auto-initiate, keep human review. The agent regenerates without needing the user to remember to trigger, but the existing Phase 4 human review still applies in human-in-the-loop mode. "Auto" removes the trigger-dependency, not the correctness review.

**Q3 (Gap D3 — threshold signal + value):** What signal and default threshold?
**A:** Changed-file count primary, default ~30, stored as a configurable field in `.samsara/codebase-map.yaml` (replacing the dead `staleness_threshold_days`). Per-project override allowed. Resolves Gap D4's config-location question in the same decision.

### Gaps resolved by hypothesis (no user question needed)
- **Gap I1 (git fallback):** Floor, not preference — when churn is uncomputable (no git / shallow / detached), report explicit "churn unknown" and never claim fresh. Forced by research kill condition #1.
- **Gap D4 (ownership):** Detection logic lives in two honest runtimes (bash hook for the session-start signal; agent/pre-thinking for the regen decision); regeneration owned solely by the codebase-map skill. Confirmed consistent with Q1/Q3 answers.

---

## Evaluation Contract

**Primary evaluator:** A pytest behavioral suite over fixture git repositories.
**Agent can perform it by:** `uv run pytest <staleness-test-path>` (per AGENTS.md: activate `.venv`, use `uv run pytest`). Fixtures cover repo states: fresh (churn under threshold), churn-over-threshold, mtime-gamed (file `touch`ed but `last_updated` old), and git-absent/uncomputable.
**Pass signal:** All of these hold — (1) a `touch` of the map file does NOT change the freshness verdict (mtime is not the signal); (2) churn over threshold produces a stale/over-threshold verdict, churn under threshold produces fresh; (3) when churn is uncomputable (no git), the verdict is an explicit "churn unknown" and never "fresh"; (4) a forced regeneration failure leaves the map marked stale with a recorded reason, never silently reused as fresh.
**Fail signal:** Any of: mtime touch flips the verdict to fresh; over-threshold churn reports fresh; git-absent reports fresh; regen failure leaves no stale mark / no reason / silent reuse.
**Feedback loop:** If the suite fails, first re-run the single failing fixture in isolation and inspect the actual verdict vs expected before changing code — do not broadly edit the detection logic on a red suite.
**Out of scope validation:** The agent-behavioral parts — pre-thinking actually auto-initiating regen in a live session, and the codebase-map Phase 4 human review firing — are validated by skill-artifact inspection as supporting evidence, not by the Primary evaluator (they are SKILL.md instruction changes, not unit-testable code paths).

## Step C — Commitment

**Date:** 2026-06-28
**Decision:** Proceed
**Accepted gaps:** none
**System design constraints carried to planning:**
- Session start = detection + strong signal only (bash hook, git churn); regeneration deferred to pre-thinking entry (agent).
- Auto-regen initiates without human trigger, but Phase 4 human review is retained in human-in-the-loop mode.
- Staleness signal = changed-source-file count since `last_updated` (exclude `changes/`, `docs/`, `bugfix/`), default ~30, configurable field in `.samsara/codebase-map.yaml` replacing the dead `staleness_threshold_days`.
- Git-uncomputable → explicit "churn unknown", never "fresh" (floor).
- Rewritten hook must survive `samsara_cli` converter for codex/gemini.
- Map schema change is backward compatible (remove old field from template, add churn-threshold field).
