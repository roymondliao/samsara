# Ship Manifest — Evidence Contract

The manifest proves why one committed candidate is or is not ready for
delivery. `templates/ship-manifest.yaml` is the sole shape authority. This file
defines field meaning only.

## Evidence Rules

- `snapshot` freezes the base and candidate commits validated by every step.
  Any code or test change invalidates the results and requires a new snapshot.
- `delivered_capability.summary` is the only narrative summary. Its
  `source_refs` point to the PT, PL, or AC authority that defines the delivery.
- Validation sections record status plus evidence refs. Do not copy Scar,
  acceptance, planning, or review text into the manifest.
- Empty exposure lists are valid after inspection. Never invent a failure mode
  to make the manifest look complete.
- `accepted_refs` and `deferred_refs` cite final Scar dispositions. `open_refs`,
  `blocked_refs`, and unresolved legacy items prevent `ready_for_delivery`.
- Security or privacy risk acceptance is human-only. Each accepted risk
  requires a finding ref, rationale, `re_review_signal`, and owner. Re-review
  is signal-driven; do not add calendar expiry. Auto mode leaves
  `accepted_risks` empty. This rule is defined by Validate & Ship Step 0.

## Validation Findings

`validation.findings` is the durable handoff for every failed or unknown result
returned to another layer. The template is the shape authority. Each finding
inherits `snapshot.candidate_commit`; do not copy the commit into every item.

- Allocate the ID from `next_finding_number`, then increment the counter. The
  counter is feature-scoped: preserve it when findings clear and never reset or
  reuse a number across candidates.
- Use one stable `VF-*` ID and name the validation step, result, owner,
  observable result, and non-empty evidence refs.
- Use `path` and `location` for a code, test, or artifact surface. Use
  `source_ref` for authority drift. At least one locator form is required.
- Severity is optional. Record it only when the source evidence provides it;
  never infer severity to fill the field.
- A `blocked` manifest has at least one finding; a `ready_for_delivery`
  manifest has none.

A Scar cites a finding as
`ship-manifest.yaml@<manifest-commit>#VF-N`. Resolve the file from that blocked
manifest commit, not `snapshot.candidate_commit` or the working tree. The
manifest commit preserves the finding after a later candidate clears the
current list.

## Operational Controls

Monitoring and rollback use an explicit status:

- `available` — a real mechanism exists; mechanism and evidence refs are
  required.
- `absent` — no mechanism exists. Keep the absence visible.
- `not_applicable` — the feature has no applicable runtime control surface.
- `unknown` — evidence is insufficient. Unknown is never rewritten as
  available.

Operational control status is evidence, not an automatic shipping verdict.
The Primary evaluator, acceptance contract, or a recorded exposure determines
whether an absence blocks delivery.

## Delivery

`delivery.action` records the selected action. Validate & Ship prepares the
commands or instructions in `preparation`; it does not merge, create a PR, or
discard a branch. Auto mode also records the matching decision-log ref.
