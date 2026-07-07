# Pre-thinking: <feature-name>

## Session: <ISO timestamp>

<!-- Steps 1-4 and the L1/Evaluation/Commitment parts of Step 6 are written by the main agent. -->
<!-- Step 5 answer groups are appended only after AskUserQuestion / gatekeeper responses. -->
<!-- Do not pre-create Step 5 answer headings; their absence is session state (see flow.md §9 K3b). -->

## Step 1 — Locate the work

**Type(s):** <feature / perf / infra / refactor / external-integration / data-structure — one or more>
**Depth:** <deep thinking (default) | fast-track — if fast-track, prove BOTH axes ~0 below>
- Uncertainty: <unresolved design questions, or "none — basis: ...">
- Blast radius: <how far damage spreads if wrong; INCLUDE the codebase/seam dimension — does this land on a load-bearing seam?>

## Step 2 — Assumptions, scope frame, and core identity

### Assumptions
<!-- Only write an assumption if "wrong → design changes" is yes. Confident REQUIRES a written basis. -->

#### A1: <short label>
**Assumption:** <what this run takes to be true>
**Boundary:** <when it holds / when it does not>
**If it breaks:** <what rots, who notices first>
**Basis:** <file:line / existing test / research finding / existing contract — or "none → not confident">
**Confidence:** <confident (basis above) | not confident → Step 3>

### Domain core identity (codebase-craft)
**Core identity:** <one or two lines — what this system, in feature scope, essentially is>
**Operability check:** <name one concrete structural decision this identity adjudicates; if two opposite choices both "serve" it, rewrite>

## Step 3 — Multi-lens evidence
<!-- Lens count is emergent from Step 2's not-confident-assumption count. 0 not-confident → 0 searchers (write "none dispatched"). -->
<!-- Searchers return facts only; the main agent records the returned facts here. -->

### Lens: <name> (for assumption <A?>)
**Facts found:** <fact + source>
**Side-path discoveries:** <off-list things surfaced, or "none">
**Not found / gaps:** <unverified gaps, or "none">

## Step 4 — Design decisions
<!-- Every dimension lands in ONE of three boxes. No fourth "I feel" box. -->

### Decision: <dimension label>
**Box:** <evidence-decided | self-derived | needs-external-call>
**Decision:** <the call made, or "→ Step 5" if needs-external-call>
**Basis / derivation chain:** <cite source (evidence-decided) | write the chain to a named root (self-derived) | the preference the agent can't invent (needs-external-call)>
**Reversal cost:** <how painful to change later; flag pseudo-reversible if semantics lock>

### Real seams (codebase-craft — a named decision category)
<!-- Only seams this feature sits on/creates. Feature-scope, not the whole project. -->

#### Seam: <name>
**Box:** <evidence-decided | self-derived | needs-external-call>
**What it is:** <the module/abstraction boundary; down to function/module/abstraction boundary, no lower>
**Evidence tier:** <already-happened (git history) | domain-essential — pre-thinking cannot mark planned-change; planning adds that later>
**Basis:** <the fact or chain that makes this a real seam, not imagination>

## Step 5 — External-call answers
<!-- Appended only after responses. Each answer is a real multiple-choice recorded as a trace. -->
<!-- ### Group N: <theme> [(round K)] -->
<!-- **Q:** <question with ≥2 options + trade-offs> -->
<!-- **A:** <chosen> — why not others: <...> — assumes: <...> — rots first if that breaks: <...> -->

## Step 6 — Honest handoff

### L1 (handoff to planning — Key Decisions single source)
<!-- Core identity + real seams above ARE the L1 design decisions. Planning cites, does not re-derive or add placement decisions. -->
**Core identity:** <restate from Step 2>
**Real seams:** <list from Step 4 with their evidence tiers>

### Evaluation Contract

**Primary evaluator:** <one canonical method>
**Agent can perform it by:** <command / browser flow / artifact inspection / snapshot comparison / log check / stable rubric>
**Pass signal:** <observable condition>
**Fail signal:** <observable condition>
**Feedback loop:** <what the agent should do first if it fails>
**Out of scope validation:** <what the user may care about but the agent cannot reliably evaluate, or "none">

### Commitment

**Date:** <ISO timestamp>
**Decision:** <Proceed | Accept gap | Return to Research>
**Accepted gaps:** <labels + consequences, or "none">
**Residual list:** <unsolvable-here items handed to planning or later, or "none">
