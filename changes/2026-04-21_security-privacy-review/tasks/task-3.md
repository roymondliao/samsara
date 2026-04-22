# Task 3: Version bump + MEMORY.md update

## Context

Read: overview.md

After task-1 (new skill) and task-2 (routing updates) are complete, update version and project status.

## Files

- Modify: `.claude-plugin/plugin.json` — version bump (0.6.1 → 0.7.0, minor bump for new skill)
- Modify: `MEMORY.md` — update Phase 5 status from NOT STARTED to DONE, add component table

## Death Test Requirements

- Test: version in plugin.json must be higher than current (0.6.1)
- Test: MEMORY.md Phase 5 section must accurately list all created/modified files

## Implementation Steps

- [ ] Step 1: Read current `plugin.json` version
- [ ] Step 2: Bump version to 0.7.0 (new skill = minor version bump)
- [ ] Step 3: Update MEMORY.md:
  - Change Phase 5 status from NOT STARTED to DONE with date
  - Add component table listing: security-privacy-review skill, bootstrap update, implement transition update, iteration transition update, version bump
  - Update Directory Structure section to include new skill directory
- [ ] Step 4: Write scar report
- [ ] Step 5: Commit

## Expected Scar Report Items

- Potential shortcut: forgetting to update the Directory Structure tree in MEMORY.md
- Assumption to verify: that 0.7.0 is the correct version (no other changes between 0.6.1 and now)

## Acceptance Criteria

- Covers: version reflects the new capability
- Covers: MEMORY.md accurately documents Phase 5 completion
