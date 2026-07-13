# Scar Report — Format Guide

Every completed task leaves a scar report. This is the yin-side output of implementation — it records what the code cannot say about itself.

If implementation reports completion without a scar report, record
`completion_unverified`, not `done`.

## Format

The canonical scar report schema is defined in `templates/scar-schema.yaml`. Read that file for the full schema, rules, and a verbatim example.

Scar reports are written as YAML at `changes/<feature>/scar-reports/task-N-scar.yaml` — inside the feature's `changes/` directory, not at the project root.

Implement owns new wound facts and stable IDs. Iteration owns Level 2
`status`/`iteration` updates on those items. Validate & Ship is read-only. This
single-writer split keeps the same scar file authoritative without rewriting
its original evidence.

**For inline/cowork execution:** read `templates/scar-schema.yaml` before writing any scar report.

**For subagent dispatch:** the schema is injected into the dispatch prompt via `dispatch-template.md`. See the Scar Report Format section in the template.

## Write Filter

Before adding any item — to `known_shortcuts`, `silent_failure_conditions`, `assumptions_made`, or `narrative` — apply the write filter question in `templates/scar-schema.yaml`'s `write-filter` anchor.

Under the schema's `direct-bullets` anchor, write each scar as one YAML bullet
with one actionable fact. Lead with the result, name the trigger and location
directly, and move rationale or verification detail to the destinations
defined by the schema's `go-elsewhere` anchor.

## Anti-Pattern: The Clean Scar

A scar report that says "no shortcuts, no silent failures, no assumptions" is suspicious. It usually means the author didn't look hard enough, not that the code is perfect. Challenge it.

## Anti-Pattern: The Review Diary Narrative

`narrative` is not a review-round log — see `templates/scar-schema.yaml`'s `no-review-diary` anchor.
