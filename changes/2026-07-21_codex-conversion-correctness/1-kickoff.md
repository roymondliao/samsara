# Kickoff: codex-conversion-correctness

## Execution Mode
Execution mode: human-in-the-loop

## Problem Source
`problem-autopsy.md`

## Problem Essence (named handoff to pre-thinking)

`samsara-cli` must convert the live Claude Code source into Codex artifacts whose
identities, hooks, agents, companion executables, validators, and installed file
ownership remain resolvable at runtime—not merely parseable on disk.

## Scope Contract (sole scope authority)

- **What must be solved:** Codex conversion currently reports success while core workflow links are unresolved or model-invisible.
- **Areas involved:** `samsara_cli/`, Codex templates/config, converter and installer tests, live conversion tests, Gemini live support removal.

### Must-Have (with death conditions)

- **Codex identity graph resolves** — Death condition: Codex changes skill identity away from `SKILL.md.name`; replace this mapping only with runtime evidence.
- **Hooks inject model-visible context and preserve source consumers** — Death condition: Codex retires the current hook-specific additional-context protocol.
- **Agent authority survives conversion** — Death condition: Codex removes custom-agent sandbox or reasoning fields; fail conversion rather than invent an equivalent.
- **Installed files have one ownership record** — Death condition: Codex provides a native transactional package ownership/uninstall mechanism that supersedes it.

### Nice-to-Have

- A future target adapter interface for Antigravity CLI or Pi.

### Not solved now

- **Implementing Antigravity CLI or Pi output** — Reason: neither target contract is part of the current evidence set.
- **Changing source skill names to match target directories** — Reason: Codex resolves skills by `SKILL.md.name`; directory prefix is packaging, not identity.
- **Rewriting historical `changes/` records mentioning Gemini** — Reason: committed history remains evidence of prior decisions, not live platform support.

## Evidence

- Live conversion completed successfully but Codex `debug prompt-input` registered
  `research`, `planning`, and other frontmatter names while converted instructions
  referenced nonexistent `$samsara-research` and `$samsara-planning` IDs.
- Converted bootstrap hook emits `systemMessage`, which Codex exposes as UI/event
  output rather than model-visible additional context.
- Converted output omits `agents/auto-gatekeeper/scripts/validate_auto_decisions.py`
  and the source `check-codebase-map` hook.
- Existing focused Codex conversion tests pass despite these failures.

## Risk of Inaction

Users receive a successful conversion/install signal, but the first cross-skill
transition, auto decision append, Codebase Map freshness check, or bootstrap
context dependency can fail silently. Update also leaves retired files active.

## Accepted Research Gaps

none

## North Star

```yaml
metric:
  name: "Codex runtime contract resolution"
  definition: "Every generated skill, agent, hook, companion command, and installer-owned path resolves through Codex-observable integration tests."
  current: "conversion succeeds while core runtime refs fail"
  current_basis: "live conversion plus codex debug prompt-input"
  target: "zero unresolved runtime refs and zero stale owned files after update"
  target_basis: "Codex artifact graph and installer reconciliation tests"
  invalidation_condition: "Codex removes the native skills, custom agents, or hook contracts used by Samsara"
  corruption_signature: "tests assert files or strings but do not observe Codex discovery/model input"

sub_metrics:
  - name: "live Codex conversion"
    current: "false-positive pass"
    current_basis: "existing focused test suite"
    target: "runtime-observable pass"
    target_basis: "prompt-input, command resolution, and update reconciliation"
    proxy_confidence: high
    decoupling_detection: "structural tests pass while Codex-visible identities or context differ"
```

## Delivery Stakeholders

- **Decision maker:** repository maintainer
- **Impacted teams:** Samsara CLI users installing into Codex projects or globally
