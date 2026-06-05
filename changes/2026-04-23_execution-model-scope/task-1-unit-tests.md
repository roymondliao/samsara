# Task 1 — Unit Tests: Router + Applicability Mechanism

These unit tests verify the positive-path behaviors of the router and applicability
mechanism. Each test describes the expected agent behavior for a valid, non-edge input.

---

## UT-1: All code-domain extensions route to `code-quality.md`

For each of the following extensions: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`,
`.rs`, `.java`, `.rb`, `.c`, `.cpp`, `.cs`, `.kt`, `.swift`

**Input:** Agent receives a file with one of the above extensions.

**Required behavior:**
- Pass 1 matches the extension
- Domain = `code`
- Reference file = `samsara/references/code-quality.md`
- Review proceeds normally through Steps 1–5

**Verification:** Step 0 Pass 1 table in the agent must list all 14 extensions
mapping to `code`.

---

## UT-2: All IaC extensions route to `iac-quality.md`

For each of: `.tf`, `.tf.json`, `.tfvars`, `.tofu`

**Required behavior:**
- Pass 1 matches the extension
- Domain = `iac`
- Reference file = `samsara/references/iac-quality.md`

**Verification:** Step 0 Pass 1 table lists these extensions mapping to `iac`.

---

## UT-3: Container file patterns route to `container-quality.md`

For: `Dockerfile`, `*.dockerfile`, `Containerfile`

**Required behavior:**
- Pass 1 matches the filename pattern
- Domain = `container`
- Reference file = `samsara/references/container-quality.md`

**Verification:** Step 0 Pass 1 table lists these patterns mapping to `container`.

---

## UT-4: Pipeline file patterns route to `pipeline-quality.md`

For: `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `Jenkinsfile`,
`.gitlab-ci.yml`

**Required behavior:**
- Pass 1 matches the path/filename pattern
- Domain = `pipeline`
- Reference file = `samsara/references/pipeline-quality.md`

**Verification:** Step 0 Pass 1 table lists these patterns mapping to `pipeline`.

---

## UT-5: Orchestration path patterns route to `orchestration-quality.md`

For files in paths matching: `k8s/**/*.yaml`, `helm/**/*.yaml`, `charts/**/*.yaml`

**Required behavior:**
- Pass 1 matches the directory pattern
- Domain = `orchestration`
- Reference file = `samsara/references/orchestration-quality.md`

**Verification:** Step 0 Pass 1 table lists these path patterns mapping to `orchestration`.

---

## UT-6: `code-quality.md` Applicability section backward-compatible

**Input:** Agent reviews a `.py` file. Reads `code-quality.md` which now has an
`## Applicability` section with `domain: code` and empty `excluded_principles`.

**Required behavior:**
- All 9 principles are considered applicable
- No principle is skipped with UNKNOWN due to exclusion
- Output format identical to pre-change reviews

**Verification:** `references/code-quality.md` must have an `## Applicability`
section. The section must either have an empty `excluded_principles` list or
explicitly state "no principles excluded." The agent's Step 3 logic must interpret
an empty exclusion list as "apply all principles."

---

## UT-7: Applicability section missing → all principles applicable (safe default)

**Input:** Agent reads a reference file that has no `## Applicability` section.

**Required behavior:**
- Agent notes: "Applicability section not found — assuming all principles applicable"
- All 9 principles are applied
- No principle is silently skipped

**Verification:** Step 0 or Step 1 must explicitly describe this fallback behavior.
The note must appear in the review output (not just internal agent reasoning).

---

## UT-8: Pass 2 Terraform HCL patterns match correctly

**Input:** File with path `variables.tf.json`, but content inspection needed
(suppose extension is ambiguous `.json`). File first 20 lines contain:
```
{
  "terraform": {},
  "variable": {}
}
```

Wait — `.tf.json` is already deterministic in Pass 1. Let's use a genuinely
ambiguous case: file with no extension whose first 20 lines contain:
```
terraform {
  required_providers {
    aws = { version = "~> 4.0" }
  }
}
```

**Required behavior:**
- Pass 1: no extension match → proceed to Pass 2
- Pass 2: `terraform {` pattern matches → domain `iac`
- Reference file = `samsara/references/iac-quality.md`

**Verification:** Step 0 Pass 2 table must list `terraform {` as an IaC pattern.

---

## UT-9: Pass 2 pipeline pattern requires combination match

**Input:** File with no extension, first 20 lines contain:
```yaml
on:
  push:
    branches: [main]
jobs:
  build:
    steps:
      - uses: actions/checkout@v3
```

**Required behavior:**
- Pass 1: no match
- Pass 2: `on:` AND `jobs:` AND `steps:` all present → domain `pipeline`
- NOT triggered by a file that has only `on:` or only `jobs:`

**Verification:** Step 0 Pass 2 must specify the pipeline pattern requires the
combination of all three keywords (`on:` + `jobs:` + `steps:`), not any single one.

---

## Summary: Pre-implementation state

All unit tests FAIL against current agent (no router exists). After implementation,
all must PASS by reading the agent markdown and confirming the behaviors are
explicitly instructed.
