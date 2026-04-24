# IaC Review Reference — Infrastructure as Code Behavioral Patterns

> 陽面的 infrastructure review 問「這個資源有沒有設定正確」。
> 陰面問的是「這個基礎設施在什麼條件下靜默漂移，而 apply 永遠不知道」。

---

## Applicability

**Domain:** `iac`

**Applies to:** Infrastructure as Code in Terraform (`.tf`, `.tf.json`, `.tfvars`, `.tofu`).
These are files where the execution model is: resources declared, state tracked, changes planned and applied.
The unit of review is the *resource*, not the function. Failure modes are state drift, misconfigured defaults,
and naming that promises security properties the configuration does not deliver.

**Excluded principles:** None. All five review steps apply to IaC files.

**Does not apply to:** Container definitions, pipeline configurations, orchestration manifests, or
general-purpose imperative code. If you are reviewing one of those file types with this reference,
the router selected incorrectly — return UNKNOWN.

---

## Purpose

This reference guides `samsara:code-reviewer` in applying domain-specific behavioral patterns when
reviewing Infrastructure as Code. It provides the detection patterns for Steps 1, 2, 3, and 5 of
the review procedure. Step 4 (Scar Report Integrity) is domain-agnostic and lives in the agent
definition — not here.

The Three Mother Rules (also in the agent definition) supply the cross-domain judgment standard.
This reference translates those rules into concrete IaC patterns:

- Mother Rule 1 maps to resource lifecycle and cost — a resource no one depends on is actively spending money.
- Mother Rule 2 maps to resource names vs. actual configuration — a resource name that promises security properties the config does not have is fraud.
- Mother Rule 3 maps to state drift visibility — configuration that makes drift harder to detect is protecting rot.

---

## Step 1: Deletion Analysis — What to Look For

**The core question:** Can this resource be deleted? If it disappeared from the infrastructure and nothing felt pain — and nothing stopped billing — it shouldn't exist.

**Patterns to detect:**

### Orphaned Resources

A resource block present in Terraform state but removed from `.tf` files, or a resource that exists
in `.tf` files but is referenced by nothing else in the codebase — no other resource, no output, no module.

- Look for: resources with no `depends_on` reference, no output referencing them, and no other resource
  attribute referencing their ID or ARN
- Ask: if `terraform destroy` removed this resource today, what would break? If the honest answer is
  "nothing," this resource is orphaned — and it is incurring cost

**Orphaned resources are Critical** — they cost money and mislead the next operator into believing they serve a purpose.

### Unused Data Sources

A `data` block declared in Terraform but whose output (`data.<type>.<name>.<attribute>`) is never
referenced anywhere in the module.

- Look for: every `data "<type>" "<name>"` block — verify that `data.<type>.<name>` appears at least
  once outside of the `data` block itself
- Unused data sources execute at plan time and consume API calls — they are waste that cannot be
  detected without tracing the reference graph

**Unused data sources are Critical** — they execute on every plan, create dependency on the data API,
and if the data source query fails (permissions, missing resource), the entire plan fails for code that
never used the data.

### Dead Outputs

A `output` block defined in the module but consumed by no parent module or external consumer.

**How to determine module type:** A root module is one called directly by `terraform apply` — it has
a `terraform {}` block or is the entry point. A child module is called via `module "<name>" { source = ... }`.
If you cannot determine the module type from the diff, treat it as root module (apply the more lenient severity).

- Look for: output blocks in a child module where the parent module's `module.<name>.<output>` reference
  does not appear elsewhere
- Root module outputs (for human consumption or CI) are exceptions — flag as Important, not Critical,
  when consumer cannot be determined within this diff

**Dead outputs in child modules are Critical.** Dead outputs in root modules are Important when no
consumer is visible. When module type is ambiguous, classify as Important and note the ambiguity.

### Zombie Security Group Rules

A security group rule (`aws_security_group_rule`, inline `ingress`/`egress` blocks) attached to a
security group that is no longer associated with any compute resource (EC2, ECS task, Lambda, RDS, etc.).

- Look for: security groups with no resource referencing their ID via `vpc_security_group_ids`,
  `security_groups`, or equivalent attribute
- Zombie rules are not only waste — they are an open surface that attackers can reuse if the security
  group ID is recycled or the VPC is shared

**Zombie security group rules are Critical** when the full association graph is visible in the diff
and no consumer is found. When the full graph is not visible (diff-only review, module boundary),
downgrade to Important and note "Unable to verify security group consumers within this diff."

---

## Step 2: Naming Honesty — What to Look For

**The core question:** Does the resource name accurately describe what the resource IS — not what it was INTENDED to be?

A resource name makes a promise about the security posture, access model, or lifecycle of the resource.
If the configuration does not deliver on that promise, the name is lying.

**Critical patterns (classify all findings as Critical):**

### Security-Promising Names With Open Configurations

The most dangerous pattern: a name that implies restriction while the configuration is open.

- `allow_https` security group with `from_port = 0, to_port = 0, protocol = "-1"` and
  `cidr_blocks = ["0.0.0.0/0"]`: name promises HTTPS-only ingress, configuration allows all traffic
  on all ports from any source — this is not an `allow_https` rule, it is `allow_everything`
- `allow_ssh_internal` with `cidr_blocks = ["0.0.0.0/0"]`: name promises internal-only SSH,
  configuration allows SSH from the public internet
- `restricted_sg` or `limited_access_sg` with wide-open ingress rules: name implies restriction,
  configuration contradicts it

**How to verify:** Read the `from_port`, `to_port`, `protocol`, and `cidr_blocks`/`ipv6_cidr_blocks`
of every security group rule. If these values collectively allow broader access than the name implies,
the name is lying.

### Private Network Names With Public Routes

- `private_subnet` with a route to an internet gateway (`0.0.0.0/0 → igw-*`): a subnet with a
  public route is a public subnet regardless of what the name says
- `private_route_table` associated with the above subnet: inherits the lie
- `isolated_vpc` with VPC peering to a publicly-reachable VPC: not isolated

**How to verify:** Read the route table associated with the named subnet. If any route targets an
internet gateway or NAT gateway, the subnet is not private — flag the name as dishonest.

### Encryption-Promising Names Without Encryption Configuration

- `encrypted_bucket` S3 bucket with no `server_side_encryption_configuration` block or with
  `sse_algorithm = "AES256"` when the name implies KMS encryption: name promises encryption,
  configuration may rely on bucket default or miss KMS-specific settings
- `encrypted_rds` without `storage_encrypted = true` or with `storage_encrypted = false`
- `secure_parameter` SSM parameter with `type = "String"` instead of `type = "SecureString"`

**How to verify:** For each resource with an encryption-implying name, verify the specific encryption
attribute is present and set to a value consistent with the name's promise.

### Lifecycle-Misleading Names

- `production_db` with `lifecycle { prevent_destroy = false }` and no snapshot policy: name implies
  production-grade durability, lifecycle allows silent destruction with no backup
- `development_bucket` with `retention_policy = "forever"` and billing enabled: name implies
  temporary/disposable, lifecycle contradicts it

---

## Step 3: Silent Rot Paths — What to Look For

**The core question:** Does this configuration make infrastructure state drift easier or harder to detect?

Silent rot in IaC is configuration that allows reality to diverge from declared state — without
Terraform reporting a diff on the next plan.

**Severity:** `ignore_changes = all` is Critical. Named `ignore_changes` lists are Important
(the scope of silencing matters — broader scope = greater rot surface).

### `ignore_changes` — Drift Masking

`ignore_changes` in a `lifecycle` block tells Terraform to stop tracking changes to specified attributes.
Any change made outside Terraform (in the console, by another tool, by a human) to an ignored attribute
will never appear in `terraform plan` output. The configuration and reality diverge permanently and silently.

**Severity by scope:**

- `ignore_changes = all` — **Critical**: Terraform stops tracking all attributes of this resource.
  The resource can be completely reconfigured outside Terraform and the plan will show "No changes."
  This is a permanent silent rot path. Every change made manually to this resource is invisible.

- `ignore_changes = [tags]` or `ignore_changes = [description]` — **Important**: Terraform stops
  tracking the named attributes. If tags encode compliance metadata (cost center, environment, owner),
  tag drift is silent compliance drift. Named ignore_changes is not as severe as `all`, but it
  establishes a permanent blind spot for the named attributes. Flag and document the rationale.

**How to detect:** Search every `lifecycle` block for `ignore_changes`. For each occurrence, determine
whether the scope is `all` or a named list. Apply severity above.

### `default` Values in Variable Blocks — Silent Input Substitution

A `variable` block with a `default` value will silently substitute that default if the variable is
not provided at plan time. The operator sees no error, no warning — the infrastructure deploys with
the default, which may be wrong for the target environment.

- `variable "environment" { default = "dev" }` — if the caller forgets to pass `-var environment=prod`,
  the infrastructure deploys as `dev` with no signal
- `variable "instance_type" { default = "t2.micro" }` in a production module: cost and capacity
  implications silently fall back to the smallest option
- `variable "enable_deletion_protection" { default = false }` — silently disables protection if unset

**Severity:** Important. The operator must know that deployment will proceed on defaults. Flag every
non-trivial default (non-empty-string, non-false defaults in security or lifecycle variables).

### `count = 0` and `for_each = {}` — Silent Resource Removal

Setting `count = 0` or `for_each = {}` on a resource removes all instances of that resource.
Unlike `terraform destroy`, this produces no explicit deletion plan confirmation — the resource
disappears in the next `terraform apply` without a named destroy in the plan output.

- `count = var.enable_feature ? 1 : 0` where `enable_feature` defaults to `false` silently
  removes the resource when the variable is not explicitly set
- `for_each = {}` hardcoded or resolved from an empty local: resource appears in config but
  creates nothing — and destroys any existing instances

**Severity:** Important when the condition is variable-driven (valid use case but requires attention).
Critical when the empty value is hardcoded or when the removed resource is security-critical
(firewall, WAF rule, encryption key).

### Provider Version Constraints — Breaking Change Exposure

An unconstrained or open-ended provider version constraint allows any future breaking change to
auto-apply on the next `terraform init`.

- `version = ">= 3.0"`: accepts any version ≥ 3.0, including 4.x, 5.x with breaking API changes
- `version = "~> 3.0"` (pessimistic constraint): accepts 3.x only — correct form
- `version = "~> 3.65"` (pessimistic patch): accepts 3.65.x only — more specific, fewer surprises
- No version constraint at all: always resolves to latest

**Severity:** Important for open-ended constraints (`>= N.0`). Important for missing constraints.
The silent failure: a provider upgrade silently changes resource behavior or deprecates attributes,
infrastructure changes without a code diff.

### Missing `depends_on` for Implicit Dependencies

Terraform infers resource ordering from attribute references (`resource_a.name` appearing in `resource_b`
creates an implicit dependency). When a dependency exists logically but is not expressed through an
attribute reference, Terraform may create resources in the wrong order.

- A policy attachment that references a role by name (string literal) rather than `aws_iam_role.name`
  (attribute reference): Terraform may create the attachment before the role exists
- An S3 bucket notification referencing a Lambda function ARN as a string constant: the Lambda may
  not exist when Terraform attempts to create the notification

**Severity:** Important. The failure mode is non-deterministic — may work in most plans, fail
intermittently when parallelism reorders creation.

### Data Source Timing — Stale Data Risk

`data` sources are read at plan time, not apply time. If the data source queries a resource that
is being modified in the same apply, the data source may return stale values.

- A `data "aws_ami" "latest"` that selects the newest AMI: if a new AMI is published between
  plan and apply, the apply uses the plan-time value — can be stale or can cause divergence between
  plan output and actual infrastructure
- A `data "aws_secretsmanager_secret_version"` that reads a secret being rotated: plan-time
  value is the pre-rotation secret, apply-time infrastructure may expect the post-rotation value

**Severity:** Important. Flag data sources that depend on resources with frequent external changes.

---

## Step 5: Correctness — What to Look For

**The core question:** Does this configuration produce the infrastructure it claims to produce, under all deployment conditions?

Apply correctness review ONLY after completing steps 1-4.

**Note:** IaC correctness patterns are domain-specific and vast. This reference covers
Terraform-generic patterns only. Provider-specific semantics (AWS vs GCP vs Azure resource behavior)
are out of scope — flag provider-specific anomalies as Important with a note that provider-level
verification is required.

**Patterns to detect:**

### Provider Version Constraint Correctness

The pessimistic constraint operator (`~>`) is the correct form for production configurations.
Verify its use and correctness:

- `~> 3.0` allows `3.x` only — correct for locking to a minor version family
- `~> 3.65` allows `3.65.x` only — correct for locking to a patch version family
- `>= 3.0` is NOT a pessimistic constraint — it is an open floor, and must be accompanied by
  a `< 4.0` upper bound to be safe
- `= 3.65.0` is an exact pin — acceptable for strict reproducibility, but blocks security patches

Flag: any provider block without a version constraint, and any `>=` constraint without an upper bound.

### State Locking Configuration

For S3 backends, state locking requires a DynamoDB table. Without it, concurrent Terraform runs
can corrupt state:

```hcl
backend "s3" {
  bucket         = "my-terraform-state"
  key            = "path/to/state.tfstate"
  region         = "us-east-1"
  dynamodb_table = "terraform-state-lock"  # required for locking
  encrypt        = true                    # required for encryption at rest
}
```

- Missing `dynamodb_table`: no state locking — concurrent applies corrupt state silently
- Missing `encrypt = true`: state stored unencrypted — state files often contain secrets
- Missing backend configuration entirely (local state): no locking, no remote collaboration,
  no encryption — flag as Critical in any non-trivial configuration

**Severity:** Critical for missing `dynamodb_table` or missing `encrypt`. Important for local state
in a module that may be used collaboratively.

### Resource Dependency Ordering

Verify that resource creation order matches dependency requirements. The correct form uses
attribute references (implicit dependency) or explicit `depends_on`:

- Prefer: `role = aws_iam_role.this.name` (implicit dependency, creates ordering)
- Over: `role = "my-role-name"` (string literal, no ordering guarantee)
- When implicit references cannot be used: `depends_on = [aws_iam_role.this]` is correct

Flag resource blocks that reference related infrastructure by string literals where attribute
references are available.

### Data Source at Plan vs. Apply Time

Data sources execute at plan time. Verify that the plan-time data is sufficient:

- Data sources querying resources managed by the same Terraform root: may read pre-apply state
- Data sources querying external APIs with frequent updates: may return stale data
- Data sources inside modules with `count` or `for_each`: evaluated for every instance —
  verify that the query parameters are instance-specific, not shared

### Backend Configuration Correctness

Remote state backends should enforce:
- Encryption at rest (`encrypt = true` for S3)
- Access controls (bucket policy restricting state access to Terraform role only)
- Versioning enabled (for recovery from state corruption)

Flag missing encryption or missing versioning on S3 backends as Important.

---

## Pattern Application Notes

These patterns are not a checklist to mechanically scan. Apply them with judgment:

**Severity escalation:** A single `ignore_changes = [tags]` on a non-critical tagging resource is
different from `ignore_changes = [tags]` on a resource where tags encode IAM conditions, compliance
scope, or billing allocation. Apply the Three Mother Rules to assess severity:
- Mother Rule 1 (articulate death): Does this resource know how it dies? Can it be destroyed safely?
- Mother Rule 2 (label assumptions): Does this name label what it assumes about access, encryption, or lifecycle?
- Mother Rule 3 (errors easier to see): Does this configuration make drift easier or harder to detect?

**Context matters:** `ignore_changes = [tags]` on a resource managed by a separate tagging tool
(e.g., AWS Tag Editor, a tagging pipeline) is a documented operational choice — different from
unexplained tag drift suppression. Name the difference in your finding.

**Don't flag what you can't verify:** If you cannot see the full module call graph, note the
limitation rather than producing a false PASS or false FAIL. Use "Unable to verify [pattern]
within this diff — callers or consumers not visible" and classify as Important.

**Provider-specific patterns:** This reference covers Terraform-generic IaC patterns. Provider-specific
resource behavior (e.g., AWS IAM policy evaluation order, GCP project hierarchy propagation delays)
is not covered. If you identify a provider-specific correctness issue, flag it as Important and note
that provider-level verification is required.
