# Task 2: Update routing — bootstrap, implement, iteration transitions

## Context

Read: overview.md

The new `samsara:security-privacy-review` skill must be inserted into the skill chain. The routing principle is backward: find all edges that currently point to `validate-and-ship`, insert `security-privacy-review` before each.

Currently affected transitions:
1. `implement/SKILL.md` — option (B) transitions directly to validate-and-ship
2. `iteration/SKILL.md` — transitions directly to validate-and-ship
3. `samsara-bootstrap/SKILL.md` — routing graph and skill list need the new node

## Files

- Modify: `skills/samsara-bootstrap/SKILL.md` — add security-privacy-review to routing graph (between iteration and validate) + add to skill list (Chain Skills section)
- Modify: `skills/implement/SKILL.md` — change transition option (B) from validate-and-ship to security-privacy-review
- Modify: `skills/iteration/SKILL.md` — change transition from validate-and-ship to security-privacy-review

## Death Test Requirements

- Test: after routing update, there must be NO direct edge from implement/iteration to validate-and-ship (all paths go through security-privacy-review)
- Test: bootstrap routing graph must include security-privacy-review node with correct edges
- Test: bootstrap skill list must include security-privacy-review in Chain Skills section with correct description

## Implementation Steps

- [ ] Step 1: Write death tests (grep for direct validate-and-ship transitions that bypass security-privacy-review)
- [ ] Step 2: Modify `skills/samsara-bootstrap/SKILL.md`:
  - Add `security_review [label="samsara:security-privacy-review"]` node to digraph
  - Add edge: `iteration -> security_review` and `implement -> security_review` (option B)
  - Add edge: `security_review -> validate`
  - Remove direct edge: `implement -> validate` (option B)
  - Remove direct edge: `iteration -> validate`
  - Add to Chain Skills list: `samsara:security-privacy-review` — implement/iteration 完成後。平台 security & privacy review gate
- [ ] Step 3: Modify `skills/implement/SKILL.md`:
  - In Transition section: change option (B) from `invoke samsara:validate-and-ship` to `invoke samsara:security-privacy-review`
  - Update the transition prompt text accordingly
- [ ] Step 4: Modify `skills/iteration/SKILL.md`:
  - In Transition section: change `invoke samsara:validate-and-ship` to `invoke samsara:security-privacy-review`
  - Update the transition prompt text accordingly
- [ ] Step 5: Verify no remaining direct paths to validate-and-ship that bypass security-privacy-review
- [ ] Step 6: Write scar report
- [ ] Step 7: Commit

## Expected Scar Report Items

- Potential shortcut: only updating the transition text but not the graphviz digraph (or vice versa) — both must be consistent
- Assumption to verify: that fast-track does NOT go through validate-and-ship (if it does, it also needs routing update)
- Assumption to verify: that debugging's fix path (大 fix → implement) will naturally flow through security-privacy-review via implement's transition

## Acceptance Criteria

- Covers: all paths to validate-and-ship pass through security-privacy-review (structural verification)
