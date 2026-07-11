# Pre-thinking Lenses — Default Catalog

Catalog and lifecycle only; derivation procedure lives in `../flow.md` §3.

## Default lenses

| Lens | Question | Fact kind |
|---|---|---|
| **structure** | What module or abstraction boundaries exist here? What is coupled? | boundaries, dependency edges, existing patterns |
| **evolution** | How has this area changed? | git history and already-happened seam evidence |
| **boundary** | Where does this feature end and another owner begin? | ownership, side-effect, and responsibility edges |
| **operability** | What breaks operationally if this is wrong? | config and secret sources, permissions, rollback surface |
| **contract** | Which upstream and downstream interfaces apply? | public interfaces, live signatures, tests, evaluators |

## Promote / retire

- **Promote:** add a recurring side-path lens only with links to the runs that
  showed the catalog missed it.
- **Retire:** remove a lens only after multiple runs show it returns no useful
  facts or is never selected.
- Record every promotion or retirement so the catalog's evolution remains
  attributable.
