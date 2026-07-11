# Lens Report — Searcher Return Format

Return shape only; dispatch procedure lives in `../flow.md` §3.

```markdown
## Lens: <name>

### Facts found
- <fact> — source: <file:line / test / config / commit / doc>
- (or: none)

### Side-path discoveries
- <off-list finding> — source: <file:line / test / config / commit / doc>
- (or: none)

### Not found / gaps
- <specific fact that could not be verified>
- (or: none)
```
