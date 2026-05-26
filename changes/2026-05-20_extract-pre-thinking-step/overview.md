# Overview: extract-pre-thinking-step

## Goal

Extract `samsara:pre-thinking` as an independent skill from `planning/SKILL.md` Step 1.5, changing the samsara chain from `research → planning` to `research → pre-thinking → planning`.

## Architecture

Pre-thinking is a chain skill (not entry skill) — always invoked unconditionally after research completes. It owns a single artifact (`pre-thinking.md`) with LLM as sole writer. User responds via AskUserQuestion only. The skill runs in 3 steps: Step A writes all gaps at once, Step B asks questions in groups of ≤3, Step C collects commitment. Planning is blocked until pre-thinking produces a complete commitment section.

## Tech Stack

Samsara framework — SKILL.md text instructions for LLM agents. No executable code. "Implementation" = writing/modifying SKILL.md files and templates. "Tests" = behavioral scenarios documented in `death-tests.md`.

## Key Decisions

- **Unconditional chain**: Pre-thinking runs after every research, regardless of gap count. LLM determines internally if gaps exist. Quick-pass (no gaps) skips Step B but still creates minimal `pre-thinking.md`.
- **Single-writer invariant**: LLM is sole writer to `pre-thinking.md`. User interaction via AskUserQuestion; LLM appends answers. User direct edits are detected and incorporated, not blocked.
- **K3b detection**: Absence of `## Step C — Commitment` section = interrupted session. New session detects this and offers Resume/Restart.
- **AskUserQuestion compatibility**: Verified on Codex CLI (`ask_user_question`) and Gemini CLI v0.29.0+ (`ask_user`). Keep `header` ≤ 12 chars for broadest compatibility.
- **Return to Research path**: Agent writes gap list to Step C section, stops, does NOT invoke planning. User re-invokes `samsara:research`.
- **File-edit detection**: Read `pre-thinking.md` before each Step B append. Compare to expected content from last write. Difference = user edited → incorporate before appending.

## Death Cases Summary

1. **K3b interrupted session** — `pre-thinking.md` has questions but no commitment; next session doesn't know if Step B finished
2. **Quick-pass overuse** — LLM marks every feature as gap-free; gaps smuggled into planning as silent assumptions
3. **File-edit silent overwrite** — user edits `pre-thinking.md` during Step B; agent overwrites without noticing

## File Map

**Create:**
- `skills/pre-thinking/SKILL.md` — main skill definition
- `skills/pre-thinking/support/flow.md` — detailed flow, group overflow, file-edit detection, K3b recovery
- `skills/pre-thinking/templates/pre-thinking.md` — append-only audit log template
- `changes/2026-05-20_extract-pre-thinking-step/death-tests.md` — behavioral verification scenarios

**Modify:**
- `skills/planning/SKILL.md` — remove Step 1.5; add pre-thinking.md prerequisite guard; update dot graph
- `skills/research/SKILL.md` — update transition to invoke pre-thinking (not planning)
- `skills/samsara-bootstrap/SKILL.md` — add pre_thinking node; update chain
- `skills/writing-skills/SKILL.md` — add single-writer artifact invariant

## Task Execution Order

Task 1 must complete first (death tests). Tasks 2–6 follow; Task 2 (new skill) should complete before Tasks 3–5 (modifications that reference the new skill). Task 6 (writing-skills) is independent.
