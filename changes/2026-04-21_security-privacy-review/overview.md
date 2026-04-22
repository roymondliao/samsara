# Overview: Security & Privacy Review Gate

## Goal

Add an independent chain skill `samsara:security-privacy-review` between implement/iteration and validate-and-ship that uses the platform's built-in security review capability to gate pushes.

## Architecture

New chain skill inserted before validate-and-ship. All paths that currently end at validate-and-ship must pass through security-privacy-review first. The skill is platform-agnostic — it describes intent (review committed changes for security/privacy issues), not mechanism (specific tool invocations). Fix loop is inline (main agent), not subagent-dispatched.

## Tech Stack

- Samsara skill (SKILL.md markdown)
- Git diff for input (committed changes vs base branch)
- Platform's built-in security & privacy review capability

## Key Decisions

- **Platform-agnostic**: skill describes WHAT, not HOW — no binding to specific coding agent tools. Reason: Phase 7 multi-platform support
- **Independent skill (not embedded in validate-and-ship)**: security review has blocking + fix loop semantics that would pollute validate-and-ship's forward-only pipeline. Reason: clean skill boundaries
- **Inline fix**: no subagent dispatch for security fixes — scope is small, targeted. Reason: simplicity, security fixes shouldn't need full implementer machinery
- **No artifact initially**: pass/fail in conversation context only. Reason: start simple, add persistence later if needed
- **Backward routing**: find all edges → validate-and-ship, insert security-privacy-review before each. Affected: implement (option B), iteration

## Death Cases Summary

1. Review tool silently skips file types → appears to pass but coverage is incomplete
2. Empty diff treated as pass → unexpected state after implement/iteration commit
3. Platform has no security review capability → entire step silently skipped

## File Map

- `skills/security-privacy-review/SKILL.md` — new chain skill (create)
- `skills/samsara-bootstrap/SKILL.md` — routing graph + skill list (modify)
- `skills/implement/SKILL.md` — transition option (B) → security-privacy-review (modify)
- `skills/iteration/SKILL.md` — transition → security-privacy-review (modify)
- `.claude-plugin/plugin.json` — version bump (modify)
- `MEMORY.md` — Phase 5 status update (modify)
