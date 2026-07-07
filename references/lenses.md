# Pre-thinking Lenses — Default List + Promote/Retire Rules

A **lens** is an angle a Step 3 searcher is sent along to gather facts for a not-confident assumption. This list is a **reminder, not a cap**: derive the lenses this run needs from where the evidence is scattered, then check this list for known-important angles you missed. Deliberately skipping a listed lens needs a written reason (adding a lens is free; dropping a known one needs a reason).

Searchers on any lens return **facts only** (with sources), side-path discoveries, and gaps — never judgment or a recommendation (return shape: `templates/lens-report.md`). The judgment happens later, in Step 4.

## Default lenses (draft — validate against real repos before treating as settled)

| Lens | The question it answers | Gathers (fact kind) |
|---|---|---|
| **structure** | What module/abstraction boundaries already exist here? What's coupled to what? | existing boundaries, dependency edges, existing patterns in the area |
| **evolution** | How has this area changed over time? | git-history facts — the **already-happened** evidence tier (design note 2 §4.2); used to judge whether a seam is stable/real |
| **boundary** | Where does this feature's scope end and someone else's begin? | ownership edges, side-effect boundaries, who-touches-what |
| **operability** | What breaks operationally if this is wrong? | config/secret sources, blast radius incl. permissions, placeholder-value lifecycle, rollback surface |
| **contract** | What upstream/downstream interfaces must this honor? | public interfaces, live signatures, existing tests/evaluators that define current behavior |

### Codebase-craft note

The **structure / evolution / boundary** lenses are the ones that feed the **real-seam decision** in Step 4:
- structure / boundary gather the *facts* about existing and needed boundaries;
- evolution gathers the **already-happened** tier that tells you whether a candidate seam is real (historically load-bearing) or imagined.

They still only gather facts. Whether something *is* a real seam, and which evidence tier it carries, is a Step 4 judgment — keep the fact/judgment split (design note 2 §4.2). A searcher that returns "we should put a seam here" has violated the no-recommendation rule.

## Promote / retire rules (learning mechanism)

The lens list is meant to evolve. Two directions, both evidence-driven:

- **Promote** — a side-path angle that, across multiple runs, keeps surfacing facts the fixed lenses missed earns a place on this list. Record which run's discovery justified it.
- **Retire** — a lens that goes multiple runs returning nothing useful is a candidate to drop; a listed lens that no run ever selects is a dead entry. (Health signal, checked at release: a lens consistently returning nothing → retire; a new lens never used → the learning mechanism is dead. Design direction / pre-thinking redesign §5.)

Do not silently grow or shrink this list. A promote/retire is itself a small recorded decision, so the list's shape stays legible to the next maintainer.
