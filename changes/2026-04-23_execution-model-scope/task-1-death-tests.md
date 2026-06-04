# Task 1 — Death Tests: Router + Applicability Mechanism

These are scenario-based tests for the `code-quality-reviewer` agent's Step 0 router
and applicability enforcement. Each test defines: the input the agent receives, the
exact behavior the agent MUST produce, and the failure signal if it does not.

"Death tests" target silent failure paths — cases where the agent could produce a
plausible-looking result that is actually wrong. Each test is walked through
against the agent markdown to verify the instructions force the correct outcome.

---

## DC-1: Router receives `.tf` file — must select domain `iac`, not `code`

**Input:** Agent is dispatched to review a file with path `main.tf`

**Required behavior:**
- Pass 1 extension match: `.tf` → domain `iac`
- Agent selects reference file: `samsara/references/iac-quality.md`
- Agent does NOT read `samsara/references/code-quality.md`

**Silent failure this guards against:**
If the agent ignores the extension and falls through to reading the hardcoded
`code-quality.md`, it applies code-domain principles (including I — Ghost Promises
and DRY) to Terraform that may have intentional module duplication for blast-radius
isolation. The reviewer would flag legitimate IaC patterns as violations.

**Verification against agent markdown (BEFORE implementation):**
FAIL — Current agent Step 1 says: "Read `samsara/references/code-quality.md`."
No routing logic exists. The agent will always read code-quality.md regardless
of file extension.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 Pass 1 table must include `.tf → iac`. Step 1 must say:
"Read the reference file determined by Step 0" (not a hardcoded path).

---

## DC-2: Router receives `.yaml` with no recognizable content patterns — must return UNKNOWN

**Input:** Agent is dispatched to review a file with path `config.yaml` whose
first 20 lines contain only:

```yaml
# Configuration for local development
database_host: localhost
database_port: 5432
feature_flags:
  new_ui: true
  beta_mode: false
```

**Required behavior:**
- Pass 1: `.yaml` extension does not match any deterministic domain — proceed to Pass 2
- Pass 2: No patterns match (`apiVersion:`, `kind:`, `on:` + `jobs:`, `resource "`, etc.)
- Agent returns UNKNOWN verdict: "unable to determine execution model for this file"
- Agent does NOT fall back to `code-quality.md`
- Agent does NOT attempt to apply any of the 9 principles

**Silent failure this guards against:**
A fallback-to-code behavior would apply code-domain principles (S, O, L, I, D, etc.)
to a config file. Config files have no interfaces, no inheritance, no modules — most
principles would produce garbage UNKNOWN verdicts or, worse, spurious Pass verdicts
with fabricated file:line observations.

**Verification against agent markdown (BEFORE implementation):**
FAIL — Current agent has no Pass 2 logic and no UNKNOWN-on-no-match behavior.
The agent would attempt Step 1 with the hardcoded `code-quality.md` path.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 Pass 2 must explicitly state: "If no pattern matches → UNKNOWN.
Return immediately with verdict: unable to determine execution model for this file.
Do NOT proceed to Step 1."

---

## DC-3: Reference file missing for detected domain — must return UNKNOWN with specific message

**Input:** Agent is dispatched to review a file with path `main.tf`.
File `samsara/references/iac-quality.md` does NOT exist.

**Required behavior:**
- Step 0: domain = `iac`, reference path = `samsara/references/iac-quality.md`
- Agent attempts to read `samsara/references/iac-quality.md`
- Read fails (file not found)
- Agent returns UNKNOWN verdict: "no reference file for execution model: iac"
- Agent does NOT fall back to `samsara/references/code-quality.md`
- Agent does NOT attempt to apply any principles from memory

**Silent failure this guards against:**
A silent fallback to `code-quality.md` would apply code-domain principles to
Terraform files. The reviewer would produce a structured, plausible-looking review
output applying Ghost Promises and DRY to infrastructure declarations — categories
that the IaC domain explicitly excludes. This is worse than UNKNOWN: it is a
confidently wrong review.

**Verification against agent markdown (BEFORE implementation):**
FAIL — Current agent's "Reference File Protocol" only covers failure to read
`samsara/references/code-quality.md`. It does not address domain-routing failure
modes because routing doesn't exist yet.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 must explicitly list all three failure modes:
1. Domain = UNKNOWN → return UNKNOWN immediately
2. Domain determined but reference file read fails → return UNKNOWN with
   "no reference file for execution model: {domain}" — do NOT fall back
3. Domain determined and reference file readable → proceed to Step 1

---

## DC-4: Principle listed in `excluded_principles` — must output UNKNOWN with exclusion reason

**Input:** Agent reviews a Terraform file, `iac-quality.md` exists and contains
an `## Applicability` section that excludes `I — Ghost Promises`:

```yaml
excluded_principles:
  - principle: I — Ghost Promises
    reason: "IaC modules have outputs but no interface contracts in the OOP sense."
```

**Required behavior:**
- When the agent reaches principle I in Step 3:
  - Verdict: `UNKNOWN`
  - Observation: `Excluded by domain reference: IaC modules have outputs but no interface contracts in the OOP sense.`
- Agent does NOT attempt to apply the Ghost Promises judgment questions to the Terraform
- Agent does NOT produce `Pass` or `Concern` for principle I

**Silent failure this guards against:**
If the exclusion is ignored, the agent applies Ghost Promises to Terraform output
declarations. Terraform `output {}` blocks look exactly like phantom methods — they
declare a value but no "caller" exists in the code itself (callers are remote
modules). The reviewer would flag every `output {}` block as a Ghost Promise
violation, producing a FAIL verdict on structurally correct Terraform.

**Verification against agent markdown (BEFORE implementation):**
FAIL — Current agent Step 3 does not check applicability before applying principles.
No `## Applicability` section exists in any reference file.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 3 must say: "Before applying each principle, check whether it appears
in `excluded_principles` from the reference file's `## Applicability` section.
If excluded: verdict = UNKNOWN, observation = 'Excluded by domain reference: {reason}'.
Do not apply the judgment questions."

---

## DC-5: `.py` file reviewed after changes — must behave identically to pre-change behavior

**Input:** Agent is dispatched to review a Python file `auth/service.py`.

**Required behavior:**
- Step 0 Pass 1: `.py` → domain `code`
- Agent reads `samsara/references/code-quality.md` (same as before)
- `## Applicability` section in `code-quality.md` declares `domain: code` with no
  `excluded_principles`
- All 9 principles are applied as before
- No principles are skipped
- Output format is identical to pre-change output

**Silent failure this guards against:**
A regression where `.py` files accidentally fall through to Pass 2 (because the
extension table is missing `.py`), then fail Pass 2 matching, then return UNKNOWN
for all reviews of Python files. This would silently break the agent's primary use
case — the one it was built for — while appearing to work for exotic file types.

**Verification against agent markdown (BEFORE implementation):**
FAIL — No router exists. The current behavior routes all files to code-quality.md,
which is coincidentally correct for `.py` files but for the wrong reason.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 Pass 1 table must include `.py → code`. Step 1 reads whatever file
Step 0 determined. `code-quality.md` Applicability section must declare no
excluded_principles, so all 9 principles apply. Output format is unchanged.

---

## DC-6: Ambiguous `.yaml` resolved by content inspection

**Input:** Agent is dispatched to review a file with path `deploy.yaml` whose
first 20 lines contain:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
```

**Required behavior:**
- Pass 1: `.yaml` extension — no deterministic domain match → proceed to Pass 2
- Pass 2: `apiVersion:` matched → domain `orchestration`
- Agent selects `samsara/references/orchestration-quality.md`
- If that file doesn't exist → UNKNOWN with "no reference file for execution model: orchestration"

**Silent failure this guards against:**
If Pass 2 is not implemented and the agent falls back to UNKNOWN for all `.yaml`
files regardless of content, then Kubernetes manifests get no review. But more
dangerously: if Pass 2 pattern matching is too broad and matches `apiVersion:` in
a non-Kubernetes YAML (e.g., an OpenAPI spec), the agent would route to
orchestration domain and apply incorrect principles.

**Verification against agent markdown (BEFORE implementation):**
FAIL — No Pass 2 content inspection exists. Agent would use hardcoded code-quality.md.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 must describe Pass 2 with specific keyword patterns including
`apiVersion:` → orchestration. Must examine first ~20 lines of file content.

---

## DC-7: YAML with `resource:` key (not Terraform) must NOT be misclassified as IaC

**Input:** Agent is dispatched to review a file with path `cloudformation.yaml`
whose first 20 lines contain:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: My stack
Parameters:
  Env:
    Type: String
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
```

Note: `Resources:` key appears (YAML key, capitalized), but NOT `resource "` (Terraform HCL syntax with quote).

**Required behavior:**
- Pass 1: `.yaml` extension — no deterministic domain match → proceed to Pass 2
- Pass 2: `resource "` pattern (with quote) must NOT match `Resources:` (YAML key)
- If `apiVersion:` is absent, orchestration pattern does not match
- No pattern matches → UNKNOWN: "unable to determine execution model for this file"

**Silent failure this guards against (DC-1 mitigation):**
If the IaC pattern is `resource` (without quote), a CloudFormation YAML with
`Resources:` would match IaC. The reviewer would apply IaC principles to
CloudFormation, which is a different execution model. The quote in `resource "` is
the exact disambiguation.

**Verification against agent markdown (BEFORE implementation):**
FAIL — No Pass 2 logic exists.

**Verification against agent markdown (AFTER implementation):**
PASS — Step 0 Pass 2 must explicitly specify `resource "` (with the opening quote)
as the IaC pattern, not `resource` alone. This is the DC-1 mitigation.

---

## Summary: Pre-implementation state

All 7 death tests FAIL against the current `agents/code-quality-reviewer.md`:

| Test | Reason for FAIL |
|------|----------------|
| DC-1 | No router. Hardcoded `code-quality.md` for all files. |
| DC-2 | No Pass 2 logic. No UNKNOWN-on-no-match. |
| DC-3 | No domain routing failure modes. Only code-quality.md failure is handled. |
| DC-4 | No applicability enforcement. No `## Applicability` section in any reference. |
| DC-5 | No explicit `.py → code` routing (works by accident via hardcoded path). |
| DC-6 | No content inspection. |
| DC-7 | No Pass 2 logic. No pattern specificity. |
