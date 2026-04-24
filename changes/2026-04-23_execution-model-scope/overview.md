# Overview: Execution Model Scope (Phase 6)

## Goal

Make samsara's two reviewer agents (code-quality-reviewer, code-reviewer) honest about what they can and cannot review, by adding execution model detection and domain-specific reference files.

## Architecture

Both reviewer agents gain the same two-pass router (Step 0: extension+directory → content inspection for ambiguous files). The router selects which domain-specific reference file to load. Each reference file contains domain-appropriate principles/patterns and declares which principles are excluded for that domain.

```
code-quality-reviewer → references/{domain}-quality.md (structural: 9 yin principles)
code-reviewer         → references/{domain}-review.md  (behavioral: 5-step review)
```

Reference files for Phase 6: `code` (imperative, existing) and `iac` (new, Terraform-focused).

## Tech Stack

- Markdown agent definitions (no executable code — LLM interprets routing instructions)
- YAML for applicability declarations within reference files
- Graphviz for flow documentation

## Key Decisions

- **Option D over A/B/C**: Principle-level abstraction with domain reference files — not universal (A), not sibling agents (B), not linter wrappers (C)
- **Single agent + reference routing**: Both reviewers keep one agent definition each, domain adaptation comes from reference files
- **Two-pass detection**: Extension+directory (deterministic) first, content inspection (~20 lines) only for ambiguous files
- **Reference file declares excluded_principles**: Boundary explicit in the file, not model interpretation
- **code-reviewer gets B-2 (reference file protocol)**: Full domain adaptation, not just a gate. Three Mother Rules stay in agent (domain-agnostic), behavioral patterns extracted to reference files
- **No linter integration**: Standard dev practice, LLMs already know to use them
- **UNKNOWN over fallback**: Missing reference or unrecognized domain → UNKNOWN verdict, never silent fallback to code domain

## Death Cases Summary

1. **Router misclassification**: Ambiguous content keyword matches wrong domain (e.g., YAML `resource:` key misidentified as Terraform `resource "`). Mitigated by multi-keyword heuristics with syntax-specific patterns.
2. **Extraction regression**: Behavioral patterns lost during code-reviewer refactoring. Existing imperative code review quality silently degrades. Mitigated by before/after comparison.
3. **Excluded principle masking real issue**: DRY excluded for IaC, but harmful within-environment duplication passes undetected. Mitigated by specific exclusion rationale that distinguishes intentional from harmful duplication.

## File Map

### New files
- `references/code-review.md` — behavioral review patterns for imperative code (extracted from current code-reviewer agent)
- `references/iac-quality.md` — 9 yin principles reframed for IaC (7 applicable, 2 excluded: I, DRY)
- `references/iac-review.md` — 5-step behavioral review patterns for IaC

### Modified files
- `references/code-quality.md` — add `## Applicability` section (all 9 applicable, baseline)
- `agents/code-quality-reviewer.md` — add Step 0 (router), modify Step 1 (load domain reference), add applicability enforcement
- `agents/code-reviewer.md` — add Reference File Protocol, add Step 0 (router), extract behavioral patterns to reference file
