# Overview: Research ↔ Planning Bidirectional Completeness Gate

## Goal

Add a pre-thinking step to Planning that forces the agent to surface its information assumptions as a visible artifact before writing any plan content — enabling the human gate to catch gaps that Planning's LLM cannot self-detect.

## Architecture

Single file modification: `samsara/skills/planning/SKILL.md`. Insert Step 1.5 between reading Research and writing Tech Spec. Step 1.5 produces a mandatory "Information Assumptions" artifact. Human reviews this artifact at the gate — confirms or returns to Research with specific questions.

Research template is unchanged. The fix is entirely in Planning's behavior.

## Tech Stack

- Markdown: skill file modification only
- No runtime code, no new files

## Key Decisions

- **Fix is in Planning only, not Research template**: Research produces what it produces. Planning is responsible for identifying what it needs and surfacing gaps — not Research for pre-enumerating all possible information types.
  - Architectural constraint: only `samsara/skills/planning/SKILL.md` is modified. No new files created. Research template untouched.

- **Pre-thinking over rigid spec**: Framework guarantees the floor (assumption list must be produced and visible), LLM capability determines the ceiling (quality of gap identification). Rigid sub-fields lock the ceiling; pre-thinking scales with LLM.
  - Architectural constraint: Step 1.5 must not contain a checklist of information types — it must be a reasoning instruction that produces a feature-specific output.

- **Assumption list is a mandatory artifact**: Absence of assumption list = Step 1.5 was skipped. This is the only structural enforcement the framework provides.
  - Architectural constraint: assumption list format defined inline in SKILL.md, not in a separate file.

## Death Cases Summary

1. **Silent pass — pre-thinking misses unknown unknowns**: LLM says "no gaps" but a gap exists it didn't know to look for. Mitigation: human gate reviews assumption list and can spot what LLM missed.
2. **Human gate skips reviewing assumption list**: Gap list present but human confirms without reading. Detect: cross-check post-implementation — any plan decision listed as a gap that was never resolved signals gate bypass.
3. **Step 1.5 omitted entirely**: No assumption list in Planning output. Hard stop: missing artifact = step not done.

## File Map

- `samsara/skills/planning/SKILL.md` — Add Step 1.5 Pre-thinking with assumption list format, gap handling, uncertainty handling, hard stop instruction
