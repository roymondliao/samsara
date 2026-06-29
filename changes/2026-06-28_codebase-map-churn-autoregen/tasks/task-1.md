# Task 1: Map schema — replace dead staleness_threshold_days with staleness_churn_threshold

## Context
Read: overview.md

The map template currently declares `staleness_threshold_days: 7` (codebase-map.yaml:3). This field is **read by no live code** — the hook hardcodes its own 7-day check and never reads it. The new churn mechanism needs a configurable threshold field that the hook (Task 2) and pre-thinking (Task 3) will actually read. This task only changes the schema/template — it does not write detection logic.

## Files
- Modify: `skills/codebase-map/templates/codebase-map.yaml:3` (remove `staleness_threshold_days`, add `staleness_churn_threshold`)

## Death Test Requirements
- Test (DC — dead-field resurrection): assert no live source file other than docs/historical reads `staleness_threshold_days` after this change — i.e., the removed field has no silent consumer that would break. (grep-based assertion over `hooks/`, `skills/`, `samsara_cli/`.)
- Test (unknown-outcome): a map rendered from the template parses as valid YAML and contains exactly one threshold field (`staleness_churn_threshold`), not both — prevents two-sources-of-truth.

## Unit Test Contract
- Contract source: the rendered template artifact shape — the documented YAML schema (a public artifact contract). A unit test asserts the parsed template dict has key `staleness_churn_threshold` (int) and does NOT have `staleness_threshold_days`.
- A unit test must assert this artifact shape, not the file's byte layout or comment text.

## Implementation Steps
- [ ] Step 1: Write death tests (dead-field has no live consumer; template has exactly one threshold field)
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit test asserting the parsed template has `staleness_churn_threshold: <int>` and no `staleness_threshold_days`
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Edit the template: remove `staleness_threshold_days`, add `staleness_churn_threshold: 30` with a comment documenting it = changed source files since last_updated (exclude changes/ docs/ bugfix/)
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items
- Potential shortcut: editing the template but leaving the live `.samsara/codebase-map.yaml` (this repo's own map) still carrying the old field — that is intentional (downstream dogfood), record it so it is not mistaken for an oversight.
- Assumption to verify: that nothing outside docs/changes actually reads `staleness_threshold_days` (the grep death test verifies this — do not assume, prove it).

## Acceptance Criteria
- Covers: "Success - threshold read from map, default when absent" (defines the field that task-2 consumes)
