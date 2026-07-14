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
  `accepted_risks` empty.

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
