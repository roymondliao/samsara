# Auto Mode Reference

Auto mode replaces human gate answers with a reusable principle-level gatekeeper.
It does not remove Samsara workflow gates. Every question or confirmation that
would normally pause for a human must produce an append-only decision record in
`changes/<feature>/auto-decisions.md`.

## Decision Log Contract

`auto-decisions.md` is an append-only event log, not a final summary. The log must
preserve the original workflow prompt and the gatekeeper's question-specific
answer so an audit can reconstruct why each gate moved the workflow forward.

Existing decision entries must not edit prior records. If a later judgment
corrects an earlier one, append a new entry that names the superseded decision.
The superseded decision remains in place so the run history stays auditable.

generic approval is invalid. A decision that only says "approved", "looks good",
or "continue" without answering the stage prompt is not a gate decision.

## Required Fields

Each decision entry must include:

- `decision_id`
- `stage`
- `prompt_type`
- `workflow_prompt`
- `gatekeeper_answer`
- `decision`
- `rationale`
- `principles_used`
- `architecture_considerations`
- `evidence_checked`
- `uncertainty`
- `consequences`
- `timestamp`

Allowed `prompt_type` values:

- `question`
- `confirmation`

Allowed `decision` values:

- `proceed` - the stage can continue because the gatekeeper answered the prompt
  with enough evidence.
- `revise` - the owning workflow or main agent must change the current artifact
  or stage result before the same gate can be evaluated again.
- `reject` - the workflow must not continue on this path.
- `accept_gap` - the workflow can continue while preserving an explicitly named
  gap for later validation or iteration.

Output states:

- `success` - all former human questions or confirmations have one append-only
  decision entry with the required fields.
- `failure` - a required entry is missing, malformed, generic, or contradicts
  the next workflow action.
- `unknown` - the gatekeeper cannot determine whether the gate can pass from
  available principles/evidence, or the log exists but cannot be matched to
  workflow gates. Unknown is not success and must not transition as if the gate
  passed.

## Entry Template

```md
## Decision 001 - <stage>.<gate-id>
- decision_id: decision-001
- timestamp: <ISO timestamp>
- stage: <research | pre-thinking | planning | implementation | iteration | security-privacy-review | validation>
- prompt_type: <question | confirmation>
- workflow_prompt: "<original workflow prompt>"
- gatekeeper_answer: "<principle-level subagent answer>"
- decision: <proceed | revise | reject | accept_gap>
- rationale: "<why this answer is acceptable for the workflow>"
- principles_used:
  - "<project prior, principle, or convention>"
- architecture_considerations:
  - "<system boundary, coupling, reversibility, or operational concern>"
- evidence_checked:
  - "<artifact, observation, or verification>"
- uncertainty:
  level: <low | medium | high>
  notes: "<remaining uncertainty>"
- consequences:
  - "<what this decision causes the workflow to do next>"
```

## Validation Rules

- A valid entry must preserve the original workflow prompt.
- A valid entry must provide a question-specific `gatekeeper_answer`.
- A valid entry must name evidence checked before the decision.
- A valid entry must name architecture considerations when architecture judgment
  influenced the decision.
- A valid entry must name uncertainty even when the level is low.
- A valid entry must make the next workflow consequence explicit.
- A correction must append a new decision and reference the superseded decision.

## Security And Privacy Unknowns

Auto mode cannot treat security/privacy unknown as accepted risk. If the
gatekeeper cannot establish review pass evidence, it records a high-uncertainty
`reject` decision with the evidence gap and the workflow does not continue as if
security/privacy passed.
