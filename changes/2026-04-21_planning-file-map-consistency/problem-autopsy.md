# Problem Autopsy: Research ↔ Planning Bidirectional Completeness Gate

## original_statement

"Planning template allows File Map to contradict Key Decisions"

(From samsara/issue.md ISSUE-001, 2026-04-17)

## reframed_statement

Samsara's "禁止靜默補全" axiom is not applied when Planning reads Research. Planning is expected to proceed from Research output, but has no mechanism to validate that Research is complete enough to proceed without self-deriving missing constraints. When Research delivers a Key Decision as a principle without constraint derivation (e.g., "shared" without "therefore: not inside any plugin directory"), Planning silently fills the gap using environmental bias. The contradiction between Key Decisions and File Map is a symptom; the mechanism failure is the absence of a bidirectional reject-and-complete loop between Research and Planning.

## translation_delta

```yaml
translation_delta:
  - original: "Planning template allows File Map to contradict Key Decisions"
    reframed: "Planning has no completeness validation for Research input — it proceeds even when Research is insufficient to constrain Planning decisions"
    delta: "Original implies a template fix (add a consistency check). Reframe points to a mechanism failure — the direction of responsibility is wrong. It's not Planning's job to check consistency; it's Research's job to deliver complete constraints, enforced by a reject gate."

  - original: "File Map contradicted Key Decision 'shared'"
    reframed: "Research defined a principle ('shared') without deriving the constraint it places on file structure; Planning self-derived the constraint incorrectly"
    delta: "Original implies Planning made an error. Reframe shows Planning had insufficient input and filled a gap — the error was in Research's completeness, not Planning's execution."

  - original: "Code reviewer did not catch it"
    reframed: "Code reviewer has no architectural placement dimension, but more fundamentally: a late-stage catch is not the right fix for an upstream completeness gap"
    delta: "Original implies adding a reviewer check solves the problem. Reframe says reviewer is the wrong place to fix an input completeness problem — it's a last-resort catch, not a root-cause fix."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Research template is redesigned to structurally enforce constraint derivation — e.g., Key Decisions are a schema that auto-generates file placement rules, making manual derivation impossible to omit"
    rationale: "If Research completeness is structurally guaranteed, the validation gate in Planning becomes vacuous — no gaps can exist to reject"

  - condition: "Samsara adopts schema-driven planning where file paths are generated from Key Decision values, not written by the agent"
    rationale: "If the derivation step is automated, the bias that the gate is protecting against cannot enter"

  - condition: "Key Decisions are removed from the Research phase entirely — Research only defines problem scope, not architectural decisions"
    rationale: "If there are no Key Decisions with architectural scope, there is nothing to derive constraints from and no gap to catch"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Research agents (and human confirming Research)"
    cost: "Must push Key Decisions to constraint granularity before human gate — more thorough work required at Research stage, not deferred to Planning"

  - who: "Planning agents"
    cost: "Must perform explicit completeness validation before proceeding — if gaps exist, must produce a structured gap report rather than self-deriving"

  - who: "Human at Research stage"
    cost: "Must confirm not just 'is the direction correct?' but 'is this complete enough for Planning to execute without design latitude?' — higher cognitive load at confirmation"

  - who: "Samsara framework maintainer"
    cost: "Must update both Research skill (kickoff template) and Planning skill (completeness gate) together — partial fix is worse than no fix, because it creates false confidence"
```

## observable_done_state

After this fix, when a Planning agent reads a Research document where Key Decisions contain architectural scope ("shared," "plugin-specific," "service-level"), it performs an explicit completeness check — if any decision lacks constraint derivation, Planning stops and returns a structured gap report to Research rather than proceeding. Research (human or agent with human confirmation) fills the gap. When Research is complete, Planning proceeds with no design latitude on the constrained dimensions. The next incident of the ISSUE-001 type is caught at the Research ↔ Planning gate, not post-implementation by the user.
