# Unit Tests — code-reviewer (Task 3)

These tests verify the structural correctness of the refactored agent and reference file.
Each test has a clear pass/fail criterion checkable by reading the output files.

---

## UT-1: Reference File Has Applicability Section

**Checks:** `references/code-review.md` contains an `## Applicability` section.

**Pass criterion:**
- Section exists with at minimum: `domain: code`
- Section notes any excluded principles (or states "none")

**Fail criterion:** Section is absent or empty.

---

## UT-2: Reference File Contains Step 1 Patterns (Deletion Analysis)

**Checks:** `references/code-review.md` contains Deletion Analysis behavioral patterns.

**Pass criterion:** Reference file contains guidance on:
- Dead code detection
- Uncalled functions detection
- Abstractions serving no current purpose

**Fail criterion:** Any of these three patterns is absent.

---

## UT-3: Reference File Contains Step 2 Patterns (Naming Honesty)

**Checks:** `references/code-review.md` contains Naming Honesty behavioral patterns.

**Pass criterion:** Reference file contains guidance on all three canonical examples:
- `is_done` meaning more than "done"
- `is_success` including uncertain outcomes
- `handle_error` swallowing errors

**Fail criterion:** Any of these three examples is absent.

---

## UT-4: Reference File Contains Step 3 Patterns (Silent Rot Paths)

**Checks:** `references/code-review.md` contains Silent Rot Paths behavioral patterns.

**Pass criterion:** Reference file contains guidance on all five patterns:
- Errors caught but not re-raised or logged
- Fallbacks without degraded state marking
- Default values turning unknown into known
- Retry without idempotency guarantees
- Timeouts with silent continuation

**Fail criterion:** Any of the five patterns is absent.

---

## UT-5: Reference File Contains Step 5 Patterns (Correctness)

**Checks:** `references/code-review.md` contains Correctness behavioral patterns.

**Pass criterion:** Reference file contains guidance on:
- Logic errors
- Off-by-one errors
- Race conditions
- Security vulnerabilities

**Fail criterion:** Any of these patterns is absent.

---

## UT-6: Agent Contains Reference File Protocol Section

**Checks:** `agents/code-reviewer.md` contains a Reference File Protocol section.

**Pass criterion:**
- Section instructs agent to read `samsara/references/{domain}-review.md` before review
- Section specifies UNKNOWN behavior on read failure
- Section matches pattern from `code-quality-reviewer.md`

**Fail criterion:** Section is absent or does not specify UNKNOWN-on-failure.

---

## UT-7: Agent Contains Step 0 Router

**Checks:** `agents/code-reviewer.md` contains Step 0 Router with two-pass detection.

**Pass criterion:**
- Pass 1 table present with extension → domain mappings for code/iac/container/pipeline/orchestration
- Pass 2 content heuristics present for ambiguous files
- Three failure modes documented (UNKNOWN domain / missing reference / success)

**Fail criterion:** Router is absent, or Pass 1 or Pass 2 is missing, or failure modes are absent.

---

## UT-8: Agent Step 0 Router Pass 1 — Code Extensions

**Checks:** The router table covers the required code extensions.

**Pass criterion:** Pass 1 table includes `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.rs`,
`.java`, `.rb`, `.c`, `.cpp`, `.cs`, `.kt`, `.swift` as domain `code`.

**Fail criterion:** Any of the listed extensions is absent from the table.

---

## UT-9: Agent Step 0 Router Pass 1 — IaC Extensions

**Checks:** The router table covers the required IaC extensions.

**Pass criterion:** Pass 1 table includes `.tf`, `.tf.json`, `.tfvars`, `.tofu` as domain `iac`.

**Fail criterion:** Any of the listed extensions is absent.

---

## UT-10: Agent Step 0 Router Pass 2 — Content Heuristics

**Checks:** Pass 2 covers required keyword patterns.

**Pass criterion:** Pass 2 heuristics include:
- IaC keywords: `resource "`, `data "`, `variable "`, `terraform {`, `provider "`
- Container keywords: `FROM `, `RUN `, `COPY `, `ENTRYPOINT`, `CMD [`
- Orchestration keywords: `apiVersion:`, `kind: Deployment`, `kind: Service`, `kind: ConfigMap`
- Pipeline keywords: `on:` + `jobs:` + `steps:` combination, and Airflow patterns
- No match → UNKNOWN

**Fail criterion:** Any keyword group is absent.

---

## UT-11: Agent References Domain Reference File (Not Hardcoded Path)

**Checks:** Agent references `{domain}-review.md` dynamically, not `code-review.md` hardcoded.

**Pass criterion:** The Reference File Protocol uses the pattern `samsara/references/{domain}-review.md`
where `{domain}` comes from the router output.

**Fail criterion:** Agent hardcodes `samsara/references/code-review.md` as the always-used path.

---

## UT-12: Issue Classification Stays in Agent

**Checks:** Issue classification (Critical/Important/Suggestion) stays in agent definition, not moved to reference.

**Pass criterion:** `agents/code-reviewer.md` contains the Issue Classification section with
all three levels and their definitions.

**Fail criterion:** Issue Classification is absent from agent definition.

---

## UT-13: Output Format Stays in Agent

**Checks:** Output format (markdown template) stays in agent definition.

**Pass criterion:** `agents/code-reviewer.md` contains the Output Format section
with the markdown template.

**Fail criterion:** Output Format is absent from agent definition.

---

## How to Run These Tests

All tests are static file verification — read the output files and check content.

For each test, the pass criterion should be satisfied by reading:
- `/Users/yuyu_liao/personal/samsara/references/code-review.md` (UT-1 through UT-5)
- `/Users/yuyu_liao/personal/samsara/agents/code-reviewer.md` (UT-6 through UT-13)

---

## Pre-refactoring Test Run (Step 5)

**UT-1:** FAIL (code-review.md doesn't exist)
**UT-2:** FAIL (code-review.md doesn't exist)
**UT-3:** FAIL (code-review.md doesn't exist)
**UT-4:** FAIL (code-review.md doesn't exist)
**UT-5:** FAIL (code-review.md doesn't exist)
**UT-6:** FAIL (no Reference File Protocol in agent)
**UT-7:** FAIL (no Step 0 Router in agent)
**UT-8:** FAIL (no router)
**UT-9:** FAIL (no router)
**UT-10:** FAIL (no router)
**UT-11:** FAIL (no router)
**UT-12:** PASS (Issue Classification present in current agent)
**UT-13:** PASS (Output Format present in current agent)

Post-refactoring target: ALL tests PASS.
