# IaC Quality Reference — Yin-side Principles

> 陽面的 infrastructure review 回答「這個 Terraform 寫得對不對」。
> 陰面問的是「這個資源在什麼條件下會對繼承它的人說謊，而損害已經蔓延到 state 裡了」。

---

## Purpose

The 9 principles in the agent definition (`samsara:code-quality-reviewer`) supply the
review spirit — the structural judgment standards that define WHAT to look for and WHY.
This reference provides the domain-specific foundation for IaC — what those principles
look like when violated in Terraform/OpenTofu configuration.

This reference is organized around **7 applicable yin-side principles** — 5 SOLID
reframings, 2 structural principles (Cohesion, Coupling), and 1 pattern principle —
each expressed in spirit form (what the principle protects against), not in rule form
(what the configuration must do).

2 principles are excluded for this domain (I — Ghost Promises, DRY — Duplication Is
a Lie Splitting). Their sections appear below with explicit rationale and coverage
transfer notes. Do not apply them; do not omit them from this reference.

Each applicable principle appears with:
- **Axiom** — the one-line spirit statement
- **Why it matters** — the spirit-level reasoning, translated to IaC
- **Violation shapes (koans)** — imagistic descriptions of how the violation appears
  in Terraform configurations, modules, and state. These are illustrative, not
  exhaustive — a violation that matches the principle's spirit but no specific koan
  is still a violation.
- **Judgment questions** — generative questions a reviewer asks the configuration
- **Outcome cross-reference** — which of the 8 outcome criteria surface when this
  principle is broken

This reference is **HCL-primary but tool-agnostic** in principle. Where patterns
differ between Terraform and OpenTofu, the Terraform form is used as the canonical
example. The principles themselves apply to any declarative infrastructure language.

---

## Scope

**In scope:** The 7 applicable principles below. All of them describe **infrastructure
structure** — how responsibilities are divided across resources and modules, how
lifecycle boundaries are drawn, how dependencies are declared, how module abstractions
behave at their seams.

**Out of scope:**

- State drift detection (resource exists in state but not in plan)
- Security misconfigurations (open security groups, missing encryption, excess IAM
  permissions)
- Cost optimization (oversized instance types, idle resources)
- Correctness of specific resource arguments (wrong AMI ID, invalid CIDR block)
- Naming conventions for resources, variables, and outputs

These belong to `samsara:code-reviewer` (yin) for the applicable domain, not to this
reference. If you observe an out-of-scope issue, note it as a pointer to yin review
rather than scoring it here.

---

## Applicability

**Domain:** `iac`

**Excluded principles:** Two of the 9 principles are excluded for the IaC domain:
"I — Ghost Promises" and "DRY — Duplication Is a Lie Splitting". Both appear in this
file with explicit rationale. All other 7 principles apply and must be reviewed.

**Coverage transfer:** The concerns that I and DRY would catch are not lost — they are
covered by other applicable principles:
- **I → L + D**: Interface contract violations in IaC manifest as silent breach across
  module versions (L) or abstraction that swallows signals (D). See the L and D sections.
- **DRY → S + Cohesion**: Intra-environment resource duplication surfaces as multiple
  death-reasons per module (S) or elements without shared lifecycle (Cohesion). Note:
  cross-environment duplication (dev/staging/prod) is intentional in IaC and is NOT a
  DRY violation.

The structured representation below is equivalent to the prose above and is provided
for machine-readable extraction. Both say the same thing: two principles are excluded.

```yaml
domain: iac
excluded_principles:
  - "I — Ghost Promises"
  - "DRY — Duplication Is a Lie Splitting"
```

When the reviewer reaches Step 3 and checks this section, it finds two entries in
`excluded_principles`. For each of those two principles, produce UNKNOWN with rationale
pointing to this section. Do not attempt to apply them to Terraform code.

---

## How to use this reference

The 9 principles in the agent definition (`samsara:code-quality-reviewer`) supply the
review spirit — the structural judgment standards. This reference provides the
domain-specific foundation for IaC: what those principles look like when violated in
Terraform/OpenTofu configuration.

The koans in each section are illustrative, not exhaustive. If the configuration
violates a principle's spirit in a way no koan describes, it is still a violation.

When reviewing IaC:

1. For each applicable principle, first recall its **spirit** from the agent's principle
   table. The spirit defines what you are looking for.
2. Read the principle's **judgment question** from this reference. Apply it to the
   configuration under review.
3. Compare what you see to the **violation shapes (koans)**. These are domain-specific
   examples of what the violation looks like in IaC.
4. For excluded principles, produce `UNKNOWN` immediately with the rationale stated in
   their sections. Do not attempt to apply them.
5. Produce one of: `Pass`, `Concern` (with specific reference to which principle and
   which file/resource block), or `UNKNOWN` (when the principle cannot be applied to this
   configuration — too small a diff to exhibit the pattern, context missing, or
   excluded by this section).
6. `UNKNOWN` is the honest answer **when the principle cannot be applied to this
   configuration** — the diff is a single variable declaration, the domain does not
   fit, or the principle is excluded. It is NOT the answer for "I looked at the
   configuration but could not decide"; in that case, produce `Concern` with the note
   "insufficient context to verify X", so the ambiguity is visible to downstream
   reviewers. **Do not produce `Pass` by default** when the principle might apply but
   you cannot judge — `Pass` must be an affirmative judgment, not an absence of concern.

Every `Pass` must include at least one specific observation that demonstrates active
review — citing the resource block, module name, or lifecycle argument that satisfies
the principle. `Pass` without a concrete reference is indistinguishable from
rubber-stamping.

---

## S — Death Responsibility (死法責任)

### Axiom

A resource is responsible for exactly one reason to exist in the infrastructure.

### Why it matters

A Terraform resource exists not because of what it can provision, but because of what
would cost money or break downstream services if it disappeared. If a resource
vanishes from state and nothing hurts, the resource had no reason to exist. If a
module vanishes and three unrelated teams file tickets, the module was carrying
responsibilities that do not belong together — it is three infrastructure concerns
sharing one `module` call.

In IaC, responsibility is not the union of resource types a module creates. It is
**the single failure mode you are willing to fully answer for when that module is
destroyed**. A module that manages both the database and the CDN is not "full-stack
infrastructure." It is two modules with no boundary between them.

Orphaned resources — resources that exist in state, accept charges, and have no
declared dependents — are a separate failure of the same axiom: they exist without a
reason, which means no one will notice when the reason to destroy them arrives.

### Violation shapes (koans)

- **Orphaned resource**: It exists in state, Terraform plans show no changes, and
  nothing in the configuration declares a dependency on it. It costs money every
  month. Asked "what breaks if this is destroyed?", the answer is silence. It guards
  nothing; it decorates the state file.
- **Three-faced module**: When this module is destroyed, three unrelated downstream
  teams open tickets — one for networking, one for compute, one for IAM. The module
  is three responsibilities sharing one `module {}` block and one destroy action.
- **Wordless module**: Ask the module's owner: "If this module disappears, who calls
  first to complain?" They cannot answer without naming multiple unrelated services.
  Each name is a separate responsibility that leaked into the same boundary.

### Judgment questions

- If this resource or module is destroyed tomorrow, which one system feels the loss?
- Can the owner of this module state, in one sentence, the single failure they are
  responsible for when it is gone?
- If the answer names multiple unrelated concerns (networking + compute, storage +
  IAM, application + monitoring), should this be one module or several?

### Outcome cross-reference

When violated, surfaces as:
- (C1 Readability) A module carrying multiple unrelated resources cannot explain its
  purpose in one sentence
- (C2 Maintainability) Changes require reasoning about multiple unrelated resource
  lifecycles simultaneously
- (C6 Clear Structure) Module boundaries cannot justify "why here, not there" when
  asked to partition responsibilities

---

## O — The Marked Bet (賭注標記)

### Axiom

A lifecycle constraint is a bet on the future. The bet must be marked where it is
made.

### Why it matters

Every `lifecycle` block, pinned provider version, and `ignore_changes` argument is a
prediction about what will and will not change in the infrastructure's future. Where
the prediction holds, the constraint is protection: it prevents Terraform from
destroying a production database because a plan calculated a replacement, or prevents
a provider upgrade from silently changing resource behavior under caller feet.

Where the prediction fails, the constraint is a sarcophagus: it entombs the original
assumption and makes it expensive to extract. An `ignore_changes = [tags]` added
three years ago to work around a tagging system that no longer exists is now silently
masking tag drift that matters. No one can tell whether the constraint was intentional
or accidental.

A lifecycle constraint without its rationale is not infrastructure design — it is a
trap for the next engineer who runs `terraform plan` and wonders why certain changes
never appear. An unpinned provider version is the inverse bet: betting that whatever
version the registry serves today will always be compatible, without marking that as
a bet at all.

### Violation shapes (koans)

- **Unmarked provider pin**: No version constraint in `required_providers`. The
  configuration bets that the provider's next major release is backward compatible,
  silently, without documenting that assumption. When the provider releases a breaking
  change, every `terraform init` after that date is a surprise.
- **Unmarked `ignore_changes`**: `ignore_changes = [user_data]` appears with no
  comment. The original reason — perhaps a deployment system that modifies user_data
  at runtime — may no longer apply. The constraint now silently ignores meaningful
  drift. Inheritors cannot distinguish "intentional drift tolerance" from "we forgot
  this was here."
- **Implicit destroy guard**: A resource has destroy-time side effects (data loss,
  irreversible deletion, downstream breakage) but no `prevent_destroy = true` and no
  comment documenting why it is safe to destroy. The bet that "no one will accidentally
  destroy this" is made silently.
- **Sarcophagus constraint**: `lifecycle { create_before_destroy = true }` was added
  to work around a transient ordering problem. The problem was resolved two years ago.
  The constraint remains, now preventing legitimate parallel operations, because no
  one knows whether removing it is safe.

### Judgment questions

- What does this lifecycle constraint assume will not change — in the provider, in the
  deployment system, or in the team's operational behavior?
- Is that assumption written in a comment where the next engineer running `terraform
  plan` will find it?
- If this `ignore_changes` entry is removed, does drift reappear that matters? If
  the provider constraint is loosened, does the next `terraform init` fetch a
  breaking version?

### Outcome cross-reference

When violated, surfaces as:
- (C2 Maintainability) Future engineers cannot determine whether constraints are
  intentional or accidental without archaeology
- (C3 Extensibility) Provider upgrades or operational changes conflict with unmarked
  constraints, requiring invasive constraint removal with unknown blast radius

---

## L — Silent Breach (靜默違約)

### Axiom

The real violation is when a module version bump changes resource behavior and the
caller doesn't know.

### Why it matters

The conventional Liskov framing is about subtype substitution in object-oriented code.
In IaC, the substitution happens at the module boundary: a caller invokes a module
and expects consistent behavior across versions. When a module author changes a
default value — a security group rule, an encryption setting, a retention policy —
callers who do not pin the module version inherit the change silently. Their
infrastructure changes without their configuration changing.

Between "caller knows the behavior changed" and "caller must relearn the module API"
lies the dangerous third state: the module is updated, the caller's code is unchanged,
**and the caller's infrastructure silently shifted**. This is not a configuration
error caught by `terraform plan` warnings. It is infrastructure drift delivered
through a version bump, discovered by whoever is on call when the first production
anomaly surfaces.

### Violation shapes (koans)

- **Default-value silent shift**: A module version is bumped. The new version changes
  the default value of `enable_encryption` from `false` to `true` (or vice versa).
  Callers who do not override the variable inherit the change. Their configuration is
  unchanged; their infrastructure is not. The plan shows "1 to change" with no
  explanation of why.
- **Security group rule erasure**: A module update silently removes an ingress rule
  that callers depended on as a module-managed baseline. Callers did not declare the
  rule themselves because "the module handles it." After the update, traffic fails.
  The caller's code has no record of the missing rule.
- **Provider reinterpretation**: A provider upgrade changes how a resource argument
  is applied — the same HCL argument produces different infrastructure. The module
  pins the provider at a range that includes the new version. Callers inherit the
  reinterpretation silently.
- **Unpinned module source**: `source = "terraform-aws-modules/vpc/aws"` with no
  `version` constraint. Each `terraform init` may fetch a different module version.
  The caller cannot inspect what they are deploying without running `terraform init`
  first.

### Judgment questions

- If this module version is bumped, do callers need to be told? Are they in a
  position to know they need to be told?
- What default values does this module expose, and are changes to those defaults
  treated as breaking changes in the module's changelog?
- If the module is unpinned, what prevents a future `terraform init` from fetching
  a version that changes the caller's infrastructure?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Infrastructure changes without configuration changes; the diff
  between expected and actual state cannot be traced to any caller-visible change
- (C2 Maintainability) Module consumers cannot safely upgrade without auditing every
  default value change across all module versions they missed

---

## I — Ghost Promises (幽靈承諾)

### Axiom

A method you cannot name a real caller for is a ghost promise.

### Why excluded for IaC

IaC modules do not declare interfaces in the object-oriented sense. A Terraform module
exposes **outputs**, not interface contracts with behavioral commitments. An unused
output is not a ghost promise — it is dead configuration, which is a simpler problem
(remove it). There is no mechanism in Terraform for a module to make a behavioral
commitment to callers the way an interface method does in Go or TypeScript.

Where I would have caught "interface surface misleads callers about actual behavior,"
that concern transfers to **L — Silent Breach** in the IaC domain. If a module output
claims to return a fully-configured ARN but the underlying resource is conditionally
created (and sometimes nil), the caller is silently breached — this is L, not I.

### Coverage transfer

Concerns that would have been I violations in code (misleading interface surface,
outputs that claim more than they deliver, callers trusting names that lie) are
reviewed under:
- **L — Silent Breach**: for module outputs that change meaning across versions
- **D — The Soundproof Wall**: for module abstractions that swallow signals and
  return misleadingly clean outputs

Produce UNKNOWN for this principle when reviewing IaC. State the rationale:
"I — Ghost Promises is excluded for the IaC domain. IaC modules expose outputs, not
interface contracts. Concerns about misleading module surfaces are covered by L
(Silent Breach) and D (The Soundproof Wall)."

---

## D — The Soundproof Wall (隔音牆)

### Axiom

A module abstraction that makes plan warnings harder to see is protecting the rot,
not the infrastructure.

### Note on reframing

As in the code-domain reference, this principle deliberately reframes D from
dependency-direction to abstraction-visibility. In IaC, the canonical dependency
inversion concern (high-level modules depending on low-level implementation details)
surfaces under Coupling as undeclared `remote_state` dependencies. What yin-D focuses
on instead is the IaC-specific form of the soundproofing failure: the module
abstraction that translates, absorbs, or suppresses plan-time and apply-time signals
from the resources it wraps.

### Why it matters

A Terraform module buys abstraction at the cost of plan visibility. The abstraction is
the visible benefit; the signal loss is the invisible cost. When a wrapped resource
begins producing plan warnings — deprecation notices, argument drift, destroy-replace
cycles — the module will speak for it. If the module's interface does not surface
these signals to the caller, the caller will hear only "apply succeeded."

A well-designed module abstraction makes the underlying resource's plan signals
**easier** to surface, not harder. It does not translate `aws_db_instance` argument
warnings into a generic `module.db_cluster apply failed`. It does not wrap a
`prevent_destroy` lifecycle in a way that makes the guard invisible to callers who
need to know it is there.

The IaC-specific variant of single-implementation interface (a stage prop in code)
is the **single-environment wrapper module**: a module that wraps exactly one
resource configuration for exactly one environment, adds no reusability, and exists
only to give the infrastructure a "modular" silhouette. It provides the overhead of
module boundaries without the decoupling benefit.

### Violation shapes (koans)

- **Plan warning swallower**: A module wraps a resource that emits a deprecation
  warning on every plan. The module's interface returns only the output values. The
  caller sees no warning; the resource continues drifting toward the deprecated
  argument's removal date. The module is soundproofing the resource's own error
  signal.
- **Generic error translator**: The module's `apply` fails inside a nested resource.
  The error surfaces as "Error: module.network.aws_vpc.main: error applying" — the
  resource-level message is buried behind the module path. Engineers debugging the
  failure must navigate the module wrapping to find the actual error. The abstraction
  is making the failure harder to trace, not easier.
- **Invisible destroy guard**: `prevent_destroy = true` is set inside the module on a
  critical resource, but the module's README and variable interface give callers no
  indication this guard exists. A caller attempting to destroy the environment
  encounters an apply failure with no explanation at the caller level.
- **Stage prop module**: A module wraps exactly one `aws_s3_bucket` resource,
  declares no input variables, accepts no parameterization, and cannot be called
  with different arguments to produce different configurations. Its only function is
  to make the root module look structured. It adds one layer of module path to every
  error message and plan output without providing any decoupling. Detectable within
  the module definition: no `variable {}` blocks, hardcoded resource arguments,
  no `for_each` or `count` on the resource.

### Judgment questions

- Does this module make failures in its wrapped resources easier to trace, or harder?
- If a resource inside this module produces a plan warning, will the calling
  configuration's `terraform plan` output show it clearly — or will it be buried in
  module indirection?
- Where does this module translate, swallow, or rephrase signals from the resources
  it wraps? Is that translation reversible?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Plan and apply failures originate inside module indirection the
  caller cannot easily navigate
- (C6 Clear Structure) Module boundaries exist without providing the visibility
  benefit that would justify the abstraction cost

---

## Cohesion — The Right to Die Together (共同死亡的權利)

### Axiom

Cohesion is not about grouping related resources. It is about resources that share
the right to die together.

### Why it matters

A Terraform module is truly cohesive when every resource inside it shares a single
death-reason: if the module is destroyed, every resource should be destroyed with it,
no rescues. A resource that would need to be saved — moved to another module, imported
into a different root — does not belong in this module. It is a tenant, not a citizen.
It has not found its own home yet.

The mainstream reading of cohesion in IaC asks "are these resources related?" The yin
reading asks "do these resources share a lifecycle fate?" Relatedness is a weak
criterion — an S3 bucket and a Lambda function are related if they work together, but
their lifecycle owners may be different teams with different deletion authorities. Shared
fate is the real test: when the module is `terraform destroy`'d, does every resource
go willingly, or does destroying the module trigger a ticket from a team that depends
on one of its resources for an unrelated purpose?

### Violation shapes (koans)

- **Heterogeneous module**: A single module creates a VPC, a Lambda function, and a
  DynamoDB table for three different application features. Destroying the module means
  three different teams lose three different things. The module has three death-reasons;
  it should be three modules.
- **Stranded dependency**: Destroy the module. One IAM role inside it must be rescued
  — it is referenced by an external service that was not part of this module's scope.
  That IAM role never belonged here. It was grouped by "it's all infrastructure" rather
  than by shared lifecycle.
- **False relatedness**: Resources in the module share a naming prefix (`app_*`) and
  were grouped because they were created at the same time by the same engineer. They
  do not share a death-reason. Delete one concern, and the others survive fine. The
  module boundary was drawn by alphabetical convenience, not lifecycle truth.

### Judgment questions

- If this module is destroyed, does every resource inside it disappear with it? Or does
  something need to be rescued and moved elsewhere first?
- What resource would you save? Where does it actually belong, and which module owns
  its lifecycle?
- Do the resources here share one death-reason — one team, one feature, one service
  boundary — or are several unrelated lifecycle reasons tangled together inside one
  `module {}` call?

### Outcome cross-reference

When violated, surfaces as:
- (C6 Clear Structure) Module boundaries do not correspond to lifecycle responsibility
  boundaries; the module cannot explain why these resources belong together
- (C3 Extensibility) Adding a resource to the module requires reasoning about
  whether it belongs to the same lifecycle, and the boundary gives no guidance

---

## Coupling — Visibility Over Looseness (可見性優先於鬆散)

### Axiom

The danger of infrastructure coupling is not the dependency. The danger is not knowing
you depend.

### Why it matters

Explicit infrastructure dependencies are safe. A `depends_on` declaration, a
`data.terraform_remote_state` call, or a direct resource reference inside a module
announces itself: plan shows the dependency chain; apply respects it; destroy reverses
it. Responsibility is declared; the relationship is traceable.

Implicit infrastructure coupling is the trap. Two modules look independent — separate
state files, separate root modules, separate plan invocations. But one reads an SSM
Parameter that the other writes. One assumes a specific VPC CIDR that the other
allocates. When the hidden provider changes a value, the dependent module produces
wrong infrastructure without any plan-visible relationship to investigate.

In IaC, the coupling failure is especially dangerous because state files give the
illusion of isolation. A module with its own state appears independent. The implicit
coupling operates entirely outside the state model — the dependency exists in the real
infrastructure, not in any Terraform graph. `terraform plan` will not warn you. The
failure arrives during `terraform apply` or, worse, at runtime when the dependent
service connects to the wrong endpoint.

### Violation shapes (koans)

- **SSM shadow dependency**: Two modules read the same SSM parameter path
  (`/myapp/db/endpoint`). Only one writes it. The dependency between them is not
  declared in either module's `required_inputs`, not in any `depends_on`, not visible
  to `terraform graph`. When the writer changes the parameter path, the reader silently
  connects to an empty string.
- **Buried remote_state**: A "helper" module contains a `data "terraform_remote_state"`
  block that reads another environment's state. The calling root module does not know
  this; it treats the helper as a simple utility. The cross-state dependency is
  invisible at the caller level and the change surface of the remote state is unknown.
- **CIDR assumption lock-in**: A module hard-codes `10.0.0.0/16` as a security group
  source CIDR, assuming this is "the VPC CIDR." Another module allocates the VPC with
  that CIDR. The dependency exists in the infrastructure; neither module declares it.
  If the VPC CIDR changes, the security group silently stops matching.
- **Naming convention dependency**: Module A names its S3 bucket
  `${var.environment}-data-bucket`. Module B constructs the same name to access the
  bucket via `aws_s3_bucket_object`. No Terraform reference links them; only the naming
  convention. When module A changes its naming scheme, module B's access breaks with
  a permissions error, not a Terraform dependency error.

### Judgment questions

- Can you draw every dependency this module has on another module or external resource?
- Are there dependencies that are not Terraform-graph-visible — shared SSM parameters,
  assumed naming conventions, CIDR assumptions, implicit ordering requirements?
- If the other party changes silently (different CIDR, renamed SSM path, different
  module output structure), does this module's plan detect it, or does the failure
  arrive at apply or runtime?

### Outcome cross-reference

When violated, surfaces as:
- (C4 Debuggability) Apply failures and runtime errors cannot be traced to their true
  source; the dependency is invisible to Terraform's graph
- (C2 Maintainability) Refactoring either module risks silent breakage on the other,
  with no plan-visible signal

---

## DRY — Duplication Is a Lie Splitting (重複是謊言的分裂)

### Axiom

Duplicated configuration is not a line-count problem. It is two places telling the
same lie.

### Why excluded for IaC

IaC duplication across environments is frequently **intentional blast-radius
isolation**. The security group rules in `env/prod/main.tf` and `env/staging/main.tf`
may look identical, but they are not two copies of the same truth — they are two
independent configurations that happen to share a current value. When staging changes
its ingress rules for an experiment, production must not change with it. The
duplication is the point.

Collapsing cross-environment duplication into a shared module removes the blast radius
boundary. A single module change now touches all environments simultaneously. The
"DRY" refactor trades isolation for line-count reduction — and in infrastructure, that
is usually the wrong trade.

**The boundary condition where DRY does apply in IaC:** Intra-environment duplication
(the same resource block appearing twice in the same root module with identical
arguments) is a genuine DRY violation. So is duplication of module source references
with different version pins — if `dev` pins `v1.2.0` and `prod` pins `v1.2.0`, that
is a single fact stated twice, and when the correct version changes to `v1.3.0`, the
two copies will drift.

The decision to exclude DRY entirely reflects the higher risk: reviewers without IaC
domain experience may flag cross-environment duplication as harmful when it is
intentional and protective. The exclusion prevents that mistake. Intra-environment
duplication is rare enough to catch via S (Death Responsibility) and Cohesion violations
that surface it indirectly.

### Coverage transfer

The concerns DRY would have caught are covered by:
- **S — Death Responsibility**: Intra-module resource duplication (two resources with
  identical purpose, different names) surfaces as "what would you lose if one
  disappeared? nothing — they are the same."
- **Cohesion**: Modules that import the same logic for unrelated purposes betray a
  cohesion boundary failure before a duplication failure.

Produce UNKNOWN for this principle when reviewing IaC. State the rationale:
"DRY — Duplication Is a Lie Splitting is excluded for the IaC domain. Cross-environment
duplication is often intentional blast-radius isolation. Intra-environment duplication
is caught indirectly by S and Cohesion. Applying DRY to IaC risks collapsing
intentional environmental independence into shared modules."

---

## Pattern — A Named Bundle of Assumptions (被命名的假設集合)

### Axiom

Every infrastructure pattern assumes your problem is the same as the one it was
designed for.

### Why it matters

An infrastructure pattern is not a configuration template. It is a **set of
assumptions about the operational problem**, bundled under a name. Multi-AZ deployment
assumes you need failure zone redundancy at the cost of inter-zone latency and doubled
resource cost. Blue-green deployment assumes you have a load balancer, two identical
environments, and a deployment system that can switch traffic atomically. Hub-and-spoke
networking assumes you have a central transit point with controlled egress requirements.

Using a pattern module without acknowledging which of its assumptions apply to your
situation — and which do not — inherits all of the pattern's machinery without the
justification. The machinery then constrains future changes to match the pattern's
shape, even when the pattern's original problem is absent.

In IaC, the pattern trap has a specific gravity: Terraform modules from public
registries and internal platform teams arrive pre-named. "Use the company's
`terraform-vpc` module" sounds like a standards decision. It may be. But the module
encodes assumptions about VPC architecture that may not match the workload. When those
assumptions conflict with operational reality three years later, the cost of extraction
is high because the pattern's shape is entangled with the state.

### Violation shapes (koans)

- **Multi-AZ dev environment**: A development environment uses a multi-AZ module
  designed for production fault tolerance. The dev environment has one engineer, no
  SLA, and no customers. The multi-AZ machinery — two NAT gateways, multiple subnets,
  cross-zone replication — runs every day, generating cost, without any of the original
  problem (production availability) being present.
- **Production-grade encryption module on throwaway data**: A pattern module enforcing
  customer-managed KMS keys, key rotation, CloudTrail logging, and cross-region
  replication is applied to a scratch bucket that holds temporary test artifacts
  deleted after 7 days. The pattern's compliance assumptions (customer data, audit
  requirements) do not match; the complexity and key management overhead remain.
- **Naming cargo cult**: A module is named `enterprise-vpc` and used for a two-person
  startup's single environment. The name signals the pattern; the operational context
  does not match the pattern's original problem (enterprise multi-account, multi-region
  networking with compliance requirements). The machinery is inherited; the justification
  is not.
- **Stale pattern assumption**: The hub-and-spoke network pattern was adopted when the
  company had strict egress control requirements. Those requirements were lifted two
  years ago when the compliance posture changed. The transit gateway, the centralized
  egress VPC, and the spoke peering relationships remain — constraining the networking
  team's ability to add direct peering — because no one marked the original assumption
  when the pattern was adopted.

### Judgment questions

- What infrastructure pattern is being used here, and what operational problem was it
  designed for?
- Where does the original operational problem differ from the current workload's actual
  requirements?
- If the pattern's assumptions do not match here, what is being kept — the operational
  protection, the machinery, or the name? Which of those would survive removing the
  pattern?

### Outcome cross-reference

When violated, surfaces as:
- (C1 Readability) Pattern's machinery creates infrastructure complexity that engineers
  cannot map back to an operational requirement
- (C3 Extensibility) Pattern's structural constraints block infrastructure changes that
  the original problem would have permitted
- (C7 Elegant Logic) Resources and modules exist without the operational justification
  that would make their presence elegant rather than burdensome

---

## Turning principles into review output

For each IaC diff or file set under review:

1. For each of the 7 applicable principles, ask the judgment question. Compare to the
   violation shapes.
2. For the 2 excluded principles (I and DRY), produce UNKNOWN immediately with the
   rationale from their sections. Do not apply them.
3. For each applicable principle, produce one of:
   - **`Pass`** — the principle is affirmatively satisfied; note one specific
     observation as evidence, citing the resource block, module name, or lifecycle
     argument.
   - **`Concern`** — the principle is violated; cite which koan matches, and which
     file and resource block reveal it.
   - **`UNKNOWN`** — the principle does not apply to this configuration (too small a
     diff, context missing, or excluded). Explicitly state why.
4. Aggregate into an overall verdict:
   - All applicable principles `Pass` or `UNKNOWN` with reasoning → **PASS**
   - Any `Concern` at severity `Critical` → **FAIL**
   - Any `Concern` at severity `Important` → **PASS_WITH_CONCERNS**
   - Severity is judged by:
     - **Critical**: Violation would cause silent infrastructure drift, undeclared
       cross-module dependency failure, or prevent a future engineer from understanding
       what a resource is responsible for.
     - **Important**: Violation increases operational maintenance cost but does not
       cause silent failure.
     - **Suggestion**: Structural refinement that does not block review.

A review output without any specific observations — even on `Pass` — is
indistinguishable from rubber-stamping. Every verdict must be grounded in the
configuration with a resource block or module reference.

---

## Cross-reference: 9 principles → 8 outcome criteria

The 8 outcome criteria describe **what good infrastructure looks like from the
outside**. The 9 principles describe **what makes infrastructure that way from the
inside**. A violation of any applicable principle surfaces as one or more of these
outcomes becoming worse.

| Principle | Status | Primary outcomes affected |
|-----------|--------|--------------------------|
| S — Death Responsibility | Applicable | C1 Readability, C2 Maintainability, C6 Clear Structure |
| O — The Marked Bet | Applicable | C2 Maintainability, C3 Extensibility |
| L — Silent Breach | Applicable | C4 Debuggability, C2 Maintainability |
| I — Ghost Promises | **Excluded** | — (transfer to L and D) |
| D — The Soundproof Wall | Applicable | C4 Debuggability, C6 Clear Structure |
| Cohesion | Applicable | C6 Clear Structure, C3 Extensibility |
| Coupling | Applicable | C4 Debuggability, C2 Maintainability |
| DRY — Duplication Is a Lie Splitting | **Excluded** | — (transfer to S and Cohesion) |
| Pattern | Applicable | C1 Readability, C3 Extensibility, C7 Elegant Logic |

The 8 outcomes (for reference):

- **C1 Readability** — A reader understands the intent within 30 seconds
- **C2 Maintainability** — A change three months from now does not require stepping
  on landmines
- **C3 Extensibility** — A similar future requirement can be inserted without
  modifying existing infrastructure
- **C4 Debuggability** — Error signals point toward their actual source
- **C5 Reuse** — Shared infrastructure logic has exactly one authoritative location
- **C6 Clear Structure** — Every module boundary can justify "why here, not there"
- **C7 Elegant Logic** — No extra module indirection, no unused variables, no phantom
  resources
- **C8 No Redundancy** — Two places never state the same infrastructure fact

A `Concern` can cite both a principle (the yin inside) and an outcome (the visible
consequence). Doing so makes the concern actionable to both the agent and the human
who reads the review.

---

## Closing

This reference is philosophy, not policy. An IaC review that scores highly on the 7
applicable principles may still be bad infrastructure — the principles cover structural
truth-telling, not correctness, not security, not cost. They are **necessary, not
sufficient**, for good infrastructure.

The two excluded principles are not gaps. They are honest acknowledgments that the
principle framework does not apply uniformly across domains. Forcing I and DRY onto
IaC would produce verdicts that sound authoritative while being wrong about how
infrastructure actually works. The honest UNKNOWN is more useful than the confidently
wrong Concern.

An agent using this reference for review should treat each principle as a lens, not a
checklist. The difference is the difference between noticing that a module cannot
state its destroy-reason (lens) and verifying that `lifecycle {}` is present
(checklist). The first is review; the second is lint.

If this reference ever starts to feel like a checklist, it has drifted. Return it to
its axioms.
