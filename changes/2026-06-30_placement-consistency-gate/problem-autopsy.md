# Problem Autopsy: placement-consistency-gate (ISSUE-001 / A4)

## original_statement

> From `issue.md` ISSUE-001 (2026-04-17): "Planning template allows File Map to contradict Key Decisions." Required Fixes: (1) add a File Map consistency check step to the planning skill; (2) add architectural compliance to code-reviewer (requires the reviewer to receive the plan's Key Decisions); (3) add an anti-bias prompt to planning.

> User framing this session: "agent 在寫檔案的時候出現路徑不正確的狀況，因為沒有遵守規範所造成的 drift" — then corrected to: "不是 agent 違規，是 plan 自相矛盾、而且沒有 gate 去抓"; "多一道檢查手續是為了防止 agent 自己的判斷而忽略 planning 的內容，導致整個 codebase drift"; design choice "(b)，但 reviewer 具有更可靠的判斷"; agreed scope = placement/ownership decisions only.

## reframed_statement

`overview.md` Key Decisions and File Map are written independently with no consistency gate, so a plan can decide a placement/ownership fact (e.g. "shared, not samsara-exclusive") and then contradict it in the File Map paths — undetected because planning has no cross-check, the implementer correctly executes the wrong paths, and the code-reviewer has no placement dimension and never receives the Key Decisions. Fix it with two independent gates scoped to placement/ownership: a lightweight planning self-check (cheap first pass, same-agent judgment), and an independent code-reviewer placement dimension fed the plan's Key Decisions (the reliable backstop, because a fresh agent does not share the planner's path-of-least-resistance bias). Guard each landed rule — especially the Key-Decisions→reviewer data flow — with a doc-contract test, because this防線 already rotted once (planned, never landed).

## translation_delta

```yaml
translation_delta:
  - original: "agent 沒有遵守規範造成 drift"
    reframed: "the plan self-contradicted; the implementer FOLLOWED the (wrong) plan correctly"
    delta: "Crucial: the drifting agent was the PLANNING agent (File Map vs its own Key Decisions), not a disobedient implementer. The fix is a consistency check between two parts of the spec, not 'make agents obey'."
  - original: "File Map to contradict Key Decisions" (issue.md, all decisions)
    reframed: "placement/ownership Key Decisions vs File Map paths"
    delta: "Narrowed: not every Key Decision maps to a file location (e.g. 'use churn not mtime' is path-irrelevant). Checking ALL decisions creates noise that gets ignored — scope only to placement/ownership."
  - original: "add a consistency check (issue.md fix #1) — 'if any path contradicts, stop'"
    reframed: "lightweight planning self-check (option b), and the RELIABLE check is the independent reviewer (fix #2)"
    delta: "issue.md left 'contradicts' undefined → risk of LLM-judges-its-own-prose = confirmation bias re-introduced. User's resolution: escape the bias via INDEPENDENCE (a fresh reviewer), not a structured field. Weight shifts from planning to review; fix #2 becomes the core, not a duplicate of #1."
  - original: "fix #1 and fix #2 (possible duplication concern raised in interrogation)"
    reframed: "two independent gates = defense-in-depth, not duplication"
    delta: "#1 guards decision→plan drift (at planning); #2 guards plan→implementation drift (at review). Same principle, two stages. Only fails if both miss."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "If the solution is built as 'the planning agent re-reads its own plan and judges consistency' with NO independent check"
    rationale: "Same biased agent judging its own output = the exhortation that already failed, dressed up as a gate. The independent reviewer (fix #2) is what makes it real; without it, do not ship a fake check."
  - condition: "If the planning self-check fires on non-contradictions (high false-positive friction)"
    rationale: "A gate that stops planning on path questions that are not real contradictions becomes noise, gets skipped, and is worse than no gate (Q2-C)."
  - condition: "If placement/ownership decisions turn out to be essentially never contradicted in practice"
    rationale: "Then the two gates are ceremony with no payload — the mechanism should not exist (north-star invalidation condition)."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Every planning run (agent or human)"
    cost: "An extra self-check step at end of planning; friction grows if it false-positives"
  - who: "The planning author"
    cost: "Forced to reconcile a flagged 'contradiction' that may not be one"
  - who: "Future maintainers"
    cost: "A new check + a reviewer dimension + a Key-Decisions→reviewer data-flow change to keep working across planning, implement, and iteration dispatch"
  - who: "The reviewer dispatch payload"
    cost: "Grows to carry Key Decisions — and if that data flow silently breaks, the placement dimension checks against nothing (the corruption signature)"
```

## observable_done_state

In a plan whose Key Decisions say "shared" while the File Map places files under a plugin directory: **not solved** → the contradiction passes every stage and reaches the human only after implementation. **Solved** → planning's end-of-step self-check walks each File Map path against the placement/ownership decisions and STOPs on a genuine contradiction before task decomposition, AND the code-reviewer — now given the plan's Key Decisions and an architectural-placement dimension — independently flags placement that does not match the decisions. The bar is defense-in-depth: at least one of the two independent gates stops the contradicting plan; it fails only if both miss.
