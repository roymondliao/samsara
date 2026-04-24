# Task 4: Write references/iac-review.md

## Context

Read: overview.md

This task creates the IaC-specific behavioral review reference file for `code-reviewer`. It adapts the 5-step review procedure for Infrastructure as Code, with Terraform as the primary validation target.

The `code-reviewer` agent (refactored in Task 3) keeps the 5-step framework and Three Mother Rules in its definition, but loads domain-specific patterns from the reference file. This file provides IaC-specific patterns for Steps 1, 2, 3, and 5. Step 4 (Scar Report Integrity) is domain-agnostic and stays in the agent.

### IaC behavioral patterns by step

**Step 1 — Deletion Analysis (IaC):**
- Orphaned resources: resource in state file but no longer in code (terraform state shows it, code doesn't define it)
- Unused data sources: `data` block queried but output never referenced
- Dead outputs: module output defined but no consumer reads it
- Zombie security group rules: rules attached to security groups no longer used by any resource
- Mother rule 1: If this resource disappears from the infrastructure, what breaks? If nothing — it shouldn't exist, and it's actively costing money.

**Step 2 — Naming Honesty (IaC):**
- `allow_https` security group that actually allows all traffic (0.0.0.0/0 on all ports)
- `private_subnet` that has a route to an internet gateway (not actually private)
- `encrypted_bucket` with no SSE configuration (name promises encryption, resource doesn't deliver)
- `production_db` used for development (name promises production-grade, lifecycle doesn't match)
- Mother rule 2: Does the resource name accurately describe what the resource IS, not what it was INTENDED to be?

**Step 3 — Silent Rot Paths (IaC):**
- `default` values in variable blocks that silently fill missing input (caller doesn't know they got a default)
- `ignore_changes` lifecycle that masks state drift (resource changes in production, Terraform pretends nothing changed)
- `count = 0` or `for_each = {}` silently removing resources without explicit deletion
- Provider version unconstrained (`>= 3.0` means any future breaking change auto-applies)
- `depends_on` missing when implicit dependency order is wrong (resource created before its dependency, intermittent failures)
- `terraform plan` shows no changes but `terraform apply` fails (state/reality divergence)
- Mother rule 3: Does this configuration make infrastructure state drift easier or harder to detect?

**Step 5 — Correctness (IaC):**
- Provider version constraint correctness (pessimistic constraint `~> 3.0` vs open `>= 3.0`)
- State locking configuration (DynamoDB for S3 backend, proper lock table)
- Resource dependency ordering (implicit vs explicit `depends_on`)
- Data source timing (data source read at plan time vs apply time, stale data risk)
- Backend configuration (remote state, encryption at rest, access controls)

## Files

- Create: `references/iac-review.md`

## Death Test Requirements

- Test: IaC reviewer Deletion Analysis on Terraform with a `data` block whose output is never referenced → must identify as Critical (dead resource costing money)
- Test: IaC reviewer Naming Honesty on `allow_https` security group with `cidr_blocks = ["0.0.0.0/0"]` and `from_port = 0, to_port = 0` → must identify as Critical (dishonest name)
- Test: IaC reviewer Silent Rot on `ignore_changes = [tags]` → must identify as Important (masking drift, but tags-only is lower severity than `ignore_changes = all`)
- Test: IaC reviewer Silent Rot on `ignore_changes = all` → must identify as Critical (complete drift masking)

## Implementation Steps

- [ ] Step 1: Write death tests (specific Terraform patterns for each step)
- [ ] Step 2: Run death tests — verify they fail (no iac-review.md exists yet)
- [ ] Step 3: Write `references/iac-review.md` with full structure (Purpose, Scope, Applicability, each step's patterns, Mother Rule IaC translations)
- [ ] Step 4: Run death tests — verify behavioral patterns produce correct findings
- [ ] Step 5: Write scar report
- [ ] Step 6: Commit

## Expected Scar Report Items

- Potential shortcut: Step 5 (Correctness) patterns for IaC are vast — this reference covers common Terraform patterns but misses cloud-provider-specific correctness issues (e.g., AWS-specific IAM policy evaluation order, GCP-specific resource manager hierarchy). Scope intentionally limited to Terraform-generic patterns.
- Assumption to verify: Step 4 (Scar Report Integrity) truly needs no IaC adaptation. If IaC implementations produce scar reports with different patterns (e.g., "assumed provider X would handle Y"), the domain-agnostic Step 4 may miss domain-specific scar quality issues.
- Assumption to verify: `ignore_changes = [tags]` severity (Important) vs `ignore_changes = all` severity (Critical) distinction is correct. In some contexts, tag drift can indicate larger drift that tags are just the canary for.

## Acceptance Criteria

- Covers: "Success - .tf file routed to iac-review.md"
