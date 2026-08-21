# Problem Autopsy: user-facing-communication-contract

## original_statement

> AI 的回答方式是否可以達到簡潔、明確、具體、清晰的溝通方式讓 User 可以快速理解跟判斷？

> 對於一個在乎細節的 user，改版前的回答是會比較容易接受；一個只在乎結果的 user，改版前對他是多餘冗長的。

## reframed_statement

Samsara needs one user-facing presentation contract that makes the first result
immediately actionable without deleting the file, verification, risk, and
decision evidence needed by detail-oriented readers.

## translation_delta

```yaml
translation_delta:
  - original: "簡潔、明確、具體、清晰"
    reframed: "result-first progressive disclosure with evidence-preserving detail"
    delta: "defines brevity as ordering and deduplication, not arbitrary deletion"
  - original: "兩種 user 的需要不同"
    reframed: "one response serves both through a standalone opening and optional detail"
    delta: "avoids a separate verbosity mode or a second presentation authority"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "The host platform supplies an equally strict project-wide response contract."
    rationale: "Samsara should project the platform contract rather than maintain a duplicate authority."
  - condition: "The contract requires deleting decision-changing evidence to meet a size target."
    rationale: "That would optimize appearance by making uncertainty and risk invisible."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Result-oriented users"
    cost: "Must search through implementation history before finding the outcome."
  - who: "Detail-oriented users"
    cost: "Cannot verify a terse answer when changed files, tests, or unresolved risk are omitted."
  - who: "Workflow agents"
    cost: "May repeat artifact reasoning or expose bare machine IDs instead of explaining their meaning."
```

## observable_done_state

Bootstrap owns one progressive-disclosure contract. Its opening varies by
request shape, later sections preserve applicable evidence, machine IDs always
carry a human-facing label, and semantic tests reject arbitrary brevity rules or
competing authorities.

## decision_refs

```yaml
decision_refs:
  research.problem-source: null
  research.do-not-solve: null
  research.damage-recipient: null
  research.done-state: null
```

## accepted_gaps

- Live response quality still depends on the executing model; this change makes
  the contract explicit and mechanically guards its load-bearing semantics.
