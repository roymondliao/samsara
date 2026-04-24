# Task 2: Write references/iac-quality.md

## Context

Read: overview.md

This task creates the first domain-specific structural quality reference file for IaC (Infrastructure as Code), focused on Terraform as the primary validation target. This file follows the exact same structure as the existing `references/code-quality.md` but with:

- IaC-specific axiom reframings, koans (violation shapes), and judgment questions for 7 applicable principles
- 2 excluded principles (I — Ghost Promises, DRY) with rationale in the Applicability section
- C1-C8 outcome criteria cross-reference (criteria definitions unchanged, mapping adjusted for IaC)

### Principle mapping for IaC

**S — Death Responsibility**: A resource is responsible for exactly one reason to exist in the infrastructure. Koans: orphaned resource (exists in state, nothing depends on it, costs money), multi-purpose module (one module manages networking + compute + IAM — three unrelated lifecycle reasons).

**O — The Marked Bet**: `lifecycle { prevent_destroy = true }`, `ignore_changes`, pinned provider versions are all marked bets. Koans: unmarked provider constraint (no version pin — betting latest will always be compatible), implicit lifecycle (no lifecycle block but resource has destroy-time dependencies no one documented).

**L — Silent Breach**: Module replacement must not silently change resource behavior. Koans: module version bump that changes default values (caller doesn't know their security group rules changed), provider upgrade that reinterprets resource arguments differently.

**I — Ghost Promises**: EXCLUDED. IaC modules have outputs, not interface contracts. Module output misuse is covered by L (Silent Breach).

**D — The Soundproof Wall**: Module wrapping must not make state drift harder to detect. Koans: wrapper module that swallows plan warnings, abstraction layer that translates resource-level errors into generic "apply failed."

**Cohesion**: Resources in a module share a single lifecycle reason. Koans: module containing S3 bucket + Lambda function + IAM role for three different features — delete the module and three teams lose different things.

**Coupling**: Cross-module dependencies must be visible. Koans: two modules reading same SSM parameter without declaring the dependency, remote_state data source buried inside a helper module.

**DRY**: EXCLUDED. IaC duplication across environments is often intentional for blast-radius isolation.

**Pattern**: "We use this module pattern" assumes your infra problem matches the original. Koans: using a multi-AZ module for a dev environment that only needs single-AZ, applying a production-grade encryption module pattern to a throwaway test bucket.

## Files

- Create: `references/iac-quality.md`

## Death Test Requirements

- Test: IaC-quality reviewer uses S principle judgment question on a Terraform resource with multiple unrelated dependents → must identify as Concern, not Pass
- Test: Excluded principle I → must produce UNKNOWN with rationale, not attempt to apply
- Test: Excluded principle DRY → must produce UNKNOWN with rationale, not attempt to apply
- Test: Cohesion judgment on a Terraform module with mixed lifecycle resources → must identify as Concern

## Implementation Steps

- [ ] Step 1: Write death tests (specific Terraform patterns that should trigger each applicable principle)
- [ ] Step 2: Run death tests — verify they fail (no iac-quality.md exists yet)
- [ ] Step 3: Write `references/iac-quality.md` with full structure (Purpose, Scope, Applicability, How to use, 9 principle sections, cross-reference table, Closing)
- [ ] Step 4: Run death tests — verify applicable principles produce correct verdicts
- [ ] Step 5: Verify excluded principles produce UNKNOWN with rationale
- [ ] Step 6: Write scar report
- [ ] Step 7: Commit

## Expected Scar Report Items

- Potential shortcut: Koans written from theoretical IaC patterns rather than real-world Terraform review experience. May not match actual violation shapes encountered in production codebases.
- Assumption to verify: Excluding DRY entirely is correct. There may be intra-environment duplication patterns in IaC that are genuinely harmful and should be flagged. The exclusion rationale should be revisited after real Terraform reviews.
- Assumption to verify: The I principle exclusion rationale ("covered by L instead") is accurate. Need to verify that L's koans actually catch the scenarios I would have caught.

## Acceptance Criteria

- Covers: "Success - .tf file routed to iac-quality.md"
- Covers: "Silent failure - excluded principle masks harmful duplication in IaC"
