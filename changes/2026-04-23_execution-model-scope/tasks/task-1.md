# Task 1: Router + Applicability mechanism for code-quality-reviewer

## Context

Read: overview.md

Samsara's `code-quality-reviewer` agent currently hardcodes a single reference file path (`samsara/references/code-quality.md`). This task adds two mechanisms:

1. **Step 0 — Execution model router**: A two-pass detection step that determines the domain of the file(s) under review, then selects the appropriate reference file.
2. **Applicability enforcement**: After loading a domain reference file, the reviewer reads its `## Applicability` section and skips excluded principles with an UNKNOWN verdict.

The router uses the same logic that will later be shared with `code-reviewer` (Task 3), but each agent has its own copy in markdown (no shared code — agents are markdown documents interpreted by an LLM).

### Router specification

**Pass 1 (deterministic — extension + directory):**

| Pattern | Domain |
|---------|--------|
| `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`, `.java`, `.rb`, `.c`, `.cpp`, `.cs`, `.kt`, `.swift` | code |
| `.tf`, `.tf.json`, `.tfvars`, `.tofu` | iac |
| `Dockerfile`, `*.dockerfile`, `Containerfile` | container |
| `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `Jenkinsfile`, `.gitlab-ci.yml` | pipeline |
| `k8s/**/*.yaml`, `helm/**/*.yaml`, `charts/**/*.yaml` | orchestration |
| All other files | → proceed to Pass 2 |

**Pass 2 (content heuristic — first ~20 lines):**

| Keyword patterns | Domain |
|-----------------|--------|
| `resource "`, `data "`, `variable "`, `terraform {`, `provider "` | iac |
| `FROM `, `RUN `, `COPY `, `ENTRYPOINT`, `CMD [` | container |
| `apiVersion:`, `kind: Deployment`, `kind: Service`, `kind: ConfigMap` | orchestration |
| `on:` + `jobs:` + `steps:` (combination) | pipeline |
| `dag = DAG(`, `@task`, `with DAG(`, `@dag` | pipeline (Airflow) |
| No match | → UNKNOWN |

**Reference file resolution**: `samsara/references/{domain}-quality.md`

**Three failure modes:**
- Domain = UNKNOWN → return UNKNOWN verdict: "unable to determine execution model for this file"
- Domain determined but reference file doesn't exist → return UNKNOWN verdict: "no reference file for execution model: {domain}"
- Domain determined and reference file exists → proceed to Step 1 (read reference)

### Applicability specification

Each reference file has a `## Applicability` section:

```markdown
## Applicability

domain: iac
excluded_principles:
  - principle: I — Ghost Promises
    reason: "IaC modules have outputs but no interface contracts in the OOP sense."
  - principle: DRY — Duplication Is a Lie Splitting
    reason: "IaC duplication across environments is often intentional for blast-radius isolation."
```

When the reviewer reaches a principle listed in `excluded_principles`:
- Verdict: `UNKNOWN`
- Observation: `Excluded by domain reference: {reason}`
- The reviewer does NOT attempt to apply the principle.

When `## Applicability` section is missing from a reference file:
- Treat all 9 principles as applicable (safe default)
- Note: "Applicability section not found — assuming all principles applicable"

## Files

- Modify: `agents/code-quality-reviewer.md` — insert Step 0 (router) before existing Step 1, modify Step 1 to use router's domain selection, add applicability enforcement to Step 3
- Modify: `references/code-quality.md` — add `## Applicability` section after existing `## Scope` section declaring `domain: code` with no excluded principles

## Death Test Requirements

- Test: Router receives `.tf` file → must select domain `iac`, not `code`
- Test: Router receives `.yaml` with no recognizable content patterns → must return UNKNOWN, never default to `code`
- Test: Reference file missing for detected domain → must return UNKNOWN with specific message, never fall back to `code-quality.md`
- Test: Principle listed in `excluded_principles` → must output UNKNOWN with exclusion reason, never attempt to apply the principle
- Test: `.py` file reviewed after changes → must behave identically to pre-change behavior (no regression)

## Implementation Steps

- [ ] Step 1: Write death tests (scenarios for each failure mode above)
- [ ] Step 2: Run death tests — verify they fail (current agent has no router)
- [ ] Step 3: Add `## Applicability` section to `references/code-quality.md`
- [ ] Step 4: Add Step 0 (router) to `agents/code-quality-reviewer.md`
- [ ] Step 5: Modify Step 1 (reference loading) to use router's domain selection
- [ ] Step 6: Add applicability enforcement to Step 3 (principle application)
- [ ] Step 7: Run all tests — verify they pass
- [ ] Step 8: Write scar report
- [ ] Step 9: Commit

## Expected Scar Report Items

- Potential shortcut: Router patterns are hardcoded in agent markdown — adding new domains requires editing the agent definition. Acceptable for now (external config explicitly out of scope).
- Assumption to verify: Pass 2 content heuristics (first ~20 lines) are sufficient for domain detection. May miss files with long header comments before first recognizable pattern.
- Assumption to verify: `## Applicability` section format is parseable by the LLM without ambiguity. YAML within markdown code block vs. bare YAML may be interpreted differently.

## Acceptance Criteria

- Covers: "Success - .tf file routed to iac-quality.md"
- Covers: "Degradation - reference file missing for detected domain"
- Covers: "Degradation - both passes fail to determine domain"
- Covers: "Degradation - applicability section missing from reference file"
- Covers: "Success - code-quality.md Applicability section backward-compatible"
- Covers: "Success - ambiguous .yaml resolved by content inspection"
- Covers: "Silent failure - router misclassifies ambiguous YAML as IaC"
