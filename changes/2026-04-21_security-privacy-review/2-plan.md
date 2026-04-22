# Plan: Security & Privacy Review Gate

## Technical Specification

### Position in Skill Chain

```
implement → (A) iteration → security-privacy-review → validate-and-ship
         → (B) security-privacy-review → validate-and-ship
```

All paths to `validate-and-ship` must pass through `security-privacy-review`. No bypass.

### I/O

**Input:**
- Committed changes from implement/iteration (already committed)
- `git diff` against base branch (typically `main`) to get full feature diff

**Output (three states):**
- `pass` — no security/privacy issues detected → transition to validate-and-ship
- `fail` — issues detected → present to human with fix suggestions → human gate
- `unknown` — review tool unavailable, timed out, or returned partial results → must NOT be treated as pass. Present to human: "review 無法完成，原因：___。(A) 重試 (B) 手動確認後繼續 (C) 停止"

### Review Mechanism

Platform-agnostic description. The skill instructs the agent to:
1. Compute the diff (committed changes vs base branch)
2. Use the platform's built-in security & privacy review capability to analyze the diff
3. Present results to human

The skill does NOT name a specific tool (e.g., no "invoke `security-review` skill"). The executing agent determines HOW based on the current platform.

### Human Gate + Fix Loop

When issues are found:
1. Present issue list with severity, location, and fix suggestions
2. Human reviews and confirms which issues to fix
3. Agent performs inline fix (no subagent dispatch — scope is small, targeted fixes)
4. Re-run security review on updated diff
5. Repeat until pass or human decides to accept remaining risks

**Fix loop safety valve:** Max 3 rounds. If still failing after 3 rounds, present remaining issues and ask human to decide: fix more or accept risk.

### Death Cases

1. **Silent skip** — review tool silently ignores certain file types (e.g., YAML, shell scripts, config files). Appears to pass but coverage is incomplete. Detection: skill must report which file types were reviewed.
2. **Empty diff** — no changes to review (unexpected state since implement/iteration just committed). Skill must flag this as unusual, not silently pass.
3. **Platform capability absent** — current platform has no built-in security review. Skill must make degradation visible, not silently skip the entire step.
4. **Partial review** — tool times out or returns incomplete results. Must be treated as `unknown`, never as `pass`.

### Assumptions

- implement and iteration both commit before transitioning (confirmed by reading both skills)
- The base branch for diff is determinable (feature branch vs main)
- Undocumented assumption (accepted gap): we cannot verify which file types the platform's built-in review actually covers — this is a platform black box

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `skills/security-privacy-review/SKILL.md` | Create | New chain skill — process, human gate, fix loop, transition |
| `skills/samsara-bootstrap/SKILL.md` | Modify | Add security-privacy-review to routing graph + skill list |
| `skills/implement/SKILL.md` | Modify | Change transition: (B) → security-privacy-review instead of validate-and-ship |
| `skills/iteration/SKILL.md` | Modify | Change transition: → security-privacy-review instead of validate-and-ship |
| `.claude-plugin/plugin.json` | Modify | Version bump |
| `MEMORY.md` | Modify | Phase 5 status update |
