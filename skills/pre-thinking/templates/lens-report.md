# Lens Report — Searcher Return Format

This is **not** a file the searcher writes. It is the shape the main agent expects a Step 3 searcher to **return** (in its final message). The main agent is the sole writer of `pre-thinking.md`; searchers only return results (`flow.md` §3).

A searcher is dispatched with: the lens (question to answer) + thinking scope (Step 2's box) + starting points (entry files — a *start*, not "only search these") + this return format.

## Return shape

```
## Lens: <name>   (assumption: <A?>)

### Facts found
- <fact> — source: <file:line / test / config / commit / doc>
- <fact> — source: <...>

### Side-path discoveries
<!-- Things surfaced along the way that were NOT on the dispatched list. This is the real blind-spot value — do not omit. -->
- <off-list finding> — source: <...>
- (or: "none")

### Not found / gaps
<!-- What was asked for but could not be verified. Never invent to fill this. -->
- <thing that could not be found or verified>
- (or: "none")
```

## Hard rules

- **No "recommendation" field.** Searchers gather facts; they do not judge. A returned "we should do X" / "put a seam here" violates the fact/judgment split (many searchers judging → contradictory advice on different premises; facts don't fight, judgment does).
- **Every fact carries a source.** A fact with no pointable source is a feeling, not a fact — put it under gaps instead.
- **A blank return is a gap, not a pass.** If the lens found nothing, say so under "Not found / gaps"; the main agent records it as an unverified gap and does not carry on as if nothing happened.
- **codebase-map is a starting hypothesis, not truth.** Where the map and live code disagree, live code wins — report the drift as a fact.
