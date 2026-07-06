"""
Doc-contract guard for Task 1 of structural-honesty-mechanisms: the
structure-spec.yaml schema template, the planning entry guard/generation
step it introduces, and the task-format.md `structure_refs` requirement.

This is a DOC-PRESENCE / ARTIFACT-SHAPE test module — there is no runtime code
in this task. The instruction surfaces themselves (the YAML template's
comments, skills/planning/SKILL.md prose, skills/planning/task-format.md
Rules, skills/research/templates/kickoff.md) ARE the contract. Per the
systemic scar `doc-vs-runtime-obedience`: these tests can prove the rule is
WRITTEN, never that a future planning agent actually OBEYS it at runtime.

Death cases guarded here (see this feature's acceptance.yaml / overview.md):
  DC-6 "豁免永生" — an expired `poc_death_date` must force the full spec
      path; the guard text must say the exemption cannot be renewed in place.
  Degradation "domain_boundary 型證據偽裝已驗證" — every domain_boundary
      evidence entry in the template must carry `machine_verifiable: false`
      literally, never `true`.
  Degradation "poc_death_date 格式不可解析" — the guard's unknown branch must
      route through the execution-mode gate, never silently pick a path.
  DC-3 "task 檔缺 structure_refs 欄位被當純行為 task 派發" — task-format.md
      must state, in one place, that a MISSING `structure_refs` section is a
      schema violation while an EMPTY array is a confirmed non-touch — the
      two must be textually distinguished, not conflated.

Task 2 adds (implement's dispatch-time injection step):
  DC-3 (dispatch side) — skills/implement/SKILL.md's Subagent Context must
      state the SAME missing-vs-empty distinction at the point that actually
      enforces it (dispatch-time FAIL), not just describe it upstream in
      task-format.md.
  DC-2 "定向注入退化為全量注入" — skills/implement/dispatch-template.md's
      Structure Spec Fragments section must state that ONLY the entries
      `structure_refs` points to are injected (never the whole spec file),
      plus the 50% line-count directed-injection-failure signal.
  Degradation "有 spec 但漏注入 vs. 無 spec" — the `structure_spec: absent`
      notation must exist so "no spec file at all" is textually distinct
      from "spec exists but injection was skipped by mistake".

Unit-test contract sources (see task-1's "Unit Test Contract"):
  - skills/planning/templates/structure-spec.yaml field set (documented
    artifact shape): feature/spec_path/modules[].id/.boundary_rationale/
    .evidence.{type,ref,machine_verifiable,note}/patterns/dependency_rules
  - skills/planning/SKILL.md named rule sentences (Spec-Path Guard states,
    Step 2.75 ordering) — documented workflow contract
  - skills/planning/task-format.md Required Sections / Rules (documented
    artifact shape)
  - skills/research/templates/kickoff.md optional field (documented artifact
    shape)

Task 2's Unit Test Contract source (documented artifact shape):
  - skills/implement/dispatch-template.md Structure Spec Fragments section —
    injection-entry shape (id/boundary_rationale/evidence) and the
    `structure_spec: absent` notation
  - skills/implement/SKILL.md Subagent Context named check-rule sentences and
    Red Flags bullets (documented workflow contract)

All doc-text assertions use concept tokens (a stable phrase or clause-bounded
regex), not a pinned whole sentence, so an honest rewrite of surrounding
prose stays green — per references/test-contract.md's self-exemplar rule.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
TEMPLATE = ROOT / "skills" / "planning" / "templates" / "structure-spec.yaml"
PLANNING_SKILL = ROOT / "skills" / "planning" / "SKILL.md"
TASK_FORMAT = ROOT / "skills" / "planning" / "task-format.md"
KICKOFF = ROOT / "skills" / "research" / "templates" / "kickoff.md"
IMPLEMENT_SKILL = ROOT / "skills" / "implement" / "SKILL.md"
DISPATCH_TEMPLATE = ROOT / "skills" / "implement" / "dispatch-template.md"
CODE_QUALITY_REVIEWER = ROOT / "agents" / "code-quality-reviewer.md"
ITERATION_SKILL = ROOT / "skills" / "iteration" / "SKILL.md"
VALIDATE_AND_SHIP_SKILL = ROOT / "skills" / "validate-and-ship" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, start_marker: str, end_markers: list[str]) -> str:
    """Return the body starting at `start_marker` up to the first of
    `end_markers` found after it (or end of text). Raises via assert if the
    start marker is absent — callers get a clear failure message."""
    start = text.find(start_marker)
    assert start != -1, f"marker {start_marker!r} not found"
    rest = text[start + len(start_marker) :]
    end = len(rest)
    for marker in end_markers:
        idx = rest.find(marker)
        if idx != -1:
            end = min(end, idx)
    return rest[:end]


def _spec_path_guard_section(planning: str) -> str:
    return _section(planning, "### Spec-Path Guard", ["\n## Process"])


def _step_275_section(planning: str) -> str:
    return _section(planning, "## Step 2.75: Structure Spec", ["\n## Step 3: File Map"])


def _rules_section(task_format: str) -> str:
    return _section(task_format, "## Rules", [])


_NUMBERED_ITEM = re.compile(r"\n\d+\.\s")


def _numbered_rule_containing(rules: str, anchor: str) -> str:
    """Return the numbered rule item containing `anchor`, bounded by the
    next numbered item (or end of section). Anchored on a stable CONTENT
    phrase, not the ordinal ("6. "/"7. ") — a rule renumber (e.g. inserting a
    new rule earlier in the list) must not silently redirect this to the
    wrong item or go blind."""
    idx = rules.find(anchor)
    assert idx != -1, f"anchor {anchor!r} not found in Rules section"
    line_start = rules.rfind("\n", 0, idx) + 1
    m = _NUMBERED_ITEM.search(rules, idx)
    end = m.start() if m else len(rules)
    return rules[line_start:end]


def _guard_bullet(guard_section: str, anchor: str) -> str:
    """Return the single markdown bullet (`- **...**`) containing `anchor`,
    bounded to the next bullet or end of section — so a check on this bullet
    cannot be satisfied by unrelated text in a different bullet."""
    idx = guard_section.find(anchor)
    assert idx != -1, f"anchor {anchor!r} not found in guard section"
    # walk back to the start of this bullet line
    bullet_start = guard_section.rfind("\n- ", 0, idx)
    assert bullet_start != -1, f"anchor {anchor!r} is not inside a '- ' bullet"
    rest = guard_section[bullet_start + 1 :]
    next_bullet = rest.find("\n- ")
    return rest if next_bullet == -1 else rest[:next_bullet]


def _subagent_context_section(skill: str) -> str:
    return _section(skill, "### Subagent Context", ["\n### Subagent Review"])


def _red_flags_section(skill: str) -> str:
    return _section(skill, "## Red Flags", ["\n## Support Files"])


def _structure_refs_check_block(skill: str) -> str:
    """Return the Structure Refs dispatch-check paragraph inside Subagent
    Context, anchored on its fixed lead-in phrase — so a rewrite of the
    surrounding bullet list cannot silently redirect this scope to unrelated
    text elsewhere in the section."""
    context = _subagent_context_section(skill)
    return _section(context, "**Structure Refs dispatch check**", [])


def _structure_spec_fragments_section(dispatch: str) -> str:
    return _section(dispatch, "## Structure Spec Fragments", ["\n## Review Dispatch"])


def _structure_spec_mode_section(agent: str) -> str:
    return _section(agent, "## Structure Spec Mode", ["\n## Review Procedure"])


def _spec_mode_additions_section(agent: str) -> str:
    return _section(agent, "## Spec Mode Additions", ["\n---\n\n## Output Format"])


def _output_format_section(agent: str) -> str:
    return _section(agent, "## Output Format", ["\n## Constraints"])


def _iteration_step1_section(iteration: str) -> str:
    return _section(
        iteration, "## Step 1: Aggregate Remaining Scars", ["\n## Step 2: Triage"]
    )


def _structural_drift_clause(iteration: str) -> str:
    step1 = _iteration_step1_section(iteration)
    return _section(step1, "**structural_drift aggregation:**", [])


def _failure_budget_review_section(validate_ship: str) -> str:
    return _section(
        validate_ship,
        "### 1. Failure Budget Review",
        ["\n### 2. Acceptance Validation"],
    )


def _zero_dangling_audit_clause(validate_ship: str) -> str:
    section = _failure_budget_review_section(validate_ship)
    return _section(section, "**0-dangling terminal audit", [])


def _reconciliation_section(validate_ship: str) -> str:
    return _section(
        validate_ship, "### 5. Reconciliation Check", ["\n### 6. Code Review"]
    )


# ---------------------------------------------------------------------------
# Shared polarity-bound check for machine_verifiable — production assertions
# AND their hostile decoy call the SAME function (test-contract.md rule 2,
# presence-not-polarity): a domain_boundary entry with machine_verifiable
# left `true` must be reported as a violation, not silently accepted.
# ---------------------------------------------------------------------------


def _domain_boundary_violations(entries: list[dict]) -> list[dict]:
    """Return the subset of domain_boundary-typed evidence dicts whose
    `machine_verifiable` is not literally `False` (missing, true, or any
    other value all count as violations)."""
    violations = []
    for entry in entries:
        if (
            entry.get("type") == "domain_boundary"
            and entry.get("machine_verifiable") is not False
        ):
            violations.append(entry)
    return violations


def _collect_evidence(parsed: dict) -> list[dict]:
    """Flatten every `evidence` dict out of modules/patterns/dependency_rules."""
    evidence = []
    for key in ("modules", "patterns", "dependency_rules"):
        for item in parsed.get(key) or []:
            if "evidence" in item:
                evidence.append(item["evidence"])
    return evidence


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__template_domain_boundary_example_is_machine_verifiable_false() -> None:
    """Degradation guard: a domain_boundary evidence example must carry
    `machine_verifiable: false` literally. If a future edit loosens this to
    `true` (or drops the field), this must go RED — a domain boundary is
    never machine-verified, only rationale-checked."""
    parsed = yaml.safe_load(read(TEMPLATE))
    evidence = _collect_evidence(parsed)
    domain_boundary_entries = [
        e for e in evidence if e.get("type") == "domain_boundary"
    ]

    assert domain_boundary_entries, (
        "structure-spec.yaml template has no domain_boundary example entry — "
        "the death case this test guards cannot even be exercised."
    )
    violations = _domain_boundary_violations(domain_boundary_entries)
    assert not violations, (
        f"domain_boundary entries not marked machine_verifiable: false: {violations} "
        "— this is the 'domain_boundary 偽裝已驗證' degradation the schema exists to prevent."
    )


def test_death__domain_boundary_true_decoy_is_detected_as_violation() -> None:
    """Permanent regression guard: feeding the SAME violation-detection
    function a domain_boundary entry that was (wrongly) left
    `machine_verifiable: true` must report it as a violation. Guards against
    a future check that only greps for the string 'machine_verifiable: false'
    anywhere in the file (which would pass even if the domain_boundary entry
    itself says `true`, as long as `false` appears somewhere else)."""
    decoy = [{"type": "domain_boundary", "machine_verifiable": True, "note": "x"}]
    violations = _domain_boundary_violations(decoy)
    assert violations, (
        "a domain_boundary entry with machine_verifiable: true was NOT reported "
        "as a violation — the polarity check has regressed."
    )


def test_death__template_documents_three_resolution_states_and_dangling_language() -> (
    None
):
    """Degradation guard: `unknown` must never be silently folded into
    resolved/failure. The template must name all three states plus the
    'dangling' / 'parse failure' vocabulary that scopes what counts as a
    failure (a ref that does not exist) vs. an unknown (the parse basis
    itself is unreadable)."""
    resolution_block = _section(
        read(TEMPLATE), "# --- Evidence resolution:", []
    ).lower()

    for token in ("resolved", "failure", "unknown", "dangling", "parse failure"):
        assert token in resolution_block, (
            f"structure-spec.yaml template's Evidence resolution block no "
            f"longer mentions {token!r} — the three-state evidence resolution "
            "contract was silently weakened."
        )


def test_death__expired_poc_death_date_forces_spec_path_not_renewed() -> None:
    """DC-6 (豁免永生): an expired `poc_death_date` must force the full spec
    path, and the guard must say the exemption cannot be renewed in place.
    If a future edit lets an expired date keep exempt_poc alive, this goes RED."""
    guard = _spec_path_guard_section(read(PLANNING_SKILL))
    expired_bullet = _guard_bullet(guard, "過期").lower()

    assert "spec_path: default" in expired_bullet or "force" in expired_bullet, (
        "the '過期' (expired) bullet no longer forces spec_path: default — "
        "DC-6 (豁免永生) is no longer guarded."
    )
    assert "renewed in place" in guard.lower() or "續期" in guard, (
        "the Spec-Path Guard no longer states that an expired exemption cannot "
        "be renewed in place — the DC-6 anti-renewal clause was silently dropped."
    )


def test_death__unparseable_poc_death_date_routes_through_execution_mode_gate() -> None:
    """Degradation guard: an unparseable `poc_death_date` must be treated as
    `unknown` and routed through the execution-mode gate — never silently
    defaulted to either exempt_poc or the full spec path."""
    guard = _spec_path_guard_section(read(PLANNING_SKILL))
    unknown_bullet = _guard_bullet(guard, "cannot be parsed").lower()

    assert "unknown" in unknown_bullet, (
        "the unparseable-date bullet no longer labels this case 'unknown'."
    )
    assert "execution-mode gate" in unknown_bullet, (
        "the unparseable-date bullet no longer routes through the "
        "execution-mode gate — an unparseable poc_death_date could be picked "
        "silently, which is exactly the degradation this guards against."
    )


def test_death__task_format_distinguishes_missing_field_from_empty_array() -> None:
    """DC-3: task-format.md must state, in the SAME rule, that a missing
    `structure_refs` section is a schema violation (漏標) while an empty
    array is a confirmed non-touch — conflating the two lets an unlabeled
    task be dispatched as if it were confirmed structure-free."""
    rules = _rules_section(read(TASK_FORMAT))
    rule_6 = _numbered_rule_containing(rules, "Structure Refs is mandatory")

    assert "欄位缺失" in rule_6, (
        "the Structure-Refs-mandatory rule no longer names the '欄位缺失' "
        "(missing field) case explicitly."
    )
    assert "空陣列" in rule_6 or "empty array" in rule_6.lower(), (
        "the Structure-Refs-mandatory rule no longer names the '空陣列' "
        "(empty array) case explicitly."
    )
    assert "schema violation" in rule_6.lower(), (
        "the Structure-Refs-mandatory rule no longer calls a missing "
        "structure_refs section a schema violation — DC-3's dispatch-refusal "
        "guard has no textual anchor left."
    )


def test_death__template_line_count_is_within_subtraction_budget() -> None:
    """Success - 儀式淨增量在預算內 (subtraction discipline, machine-enforced):
    the template (comments included) must stay at or under 60 lines. This is
    the one number in the acceptance criteria that a doc-contract test can
    enforce exactly, rather than merely describe."""
    lines = read(TEMPLATE).splitlines()
    assert len(lines) <= 60, (
        f"structure-spec.yaml template has {len(lines)} lines, budget is 60 — "
        "the subtraction discipline (KD-5) was silently exceeded."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape / documented workflow contract)
# ---------------------------------------------------------------------------


def test_unit__template_documents_required_schema_field_set() -> None:
    """Contract source: documented artifact shape of
    skills/planning/templates/structure-spec.yaml (named in task-1's Unit
    Test Contract). Behavior-preserving refactor (reword a placeholder
    string, reorder module entries) keeps this green. Behavior-actually-broke
    (a required field dropped, or evidence losing its `type`/`note`) turns it red.
    """
    parsed = yaml.safe_load(read(TEMPLATE))

    assert "feature" in parsed
    assert parsed.get("spec_path") in ("default", "exempt_poc")
    assert isinstance(parsed.get("modules"), list) and parsed["modules"], (
        "template's default-path example must include at least one module"
    )

    required_module_fields = {"id", "boundary_rationale", "evidence"}
    required_evidence_fields = {"type", "machine_verifiable", "note"}
    for module in parsed["modules"]:
        missing = required_module_fields - module.keys()
        assert not missing, f"module {module.get('id')!r} missing fields: {missing}"
        evidence = module["evidence"]
        missing_evidence = required_evidence_fields - evidence.keys()
        assert not missing_evidence, (
            f"module {module.get('id')!r} evidence missing fields: {missing_evidence}"
        )
        assert evidence["type"] in ("git_history", "planned_task", "domain_boundary")
        if evidence["type"] != "domain_boundary":
            assert "ref" in evidence, (
                f"module {module.get('id')!r} evidence type {evidence['type']!r} "
                "must carry a `ref` (git_history/planned_task are machine-resolvable)"
            )
        else:
            assert "ref" not in evidence, (
                "domain_boundary evidence has nothing to parse — a `ref` here "
                "would falsely imply machine resolvability"
            )

    assert isinstance(parsed.get("patterns"), list) and parsed["patterns"], (
        "template must document the `patterns` shape with at least one example"
    )
    assert (
        isinstance(parsed.get("dependency_rules"), list) and parsed["dependency_rules"]
    ), "template must document the `dependency_rules` shape with at least one example"


def test_unit__skill_md_spec_path_guard_names_all_three_states() -> None:
    """Contract source: skills/planning/SKILL.md Spec-Path Guard section
    (documented workflow contract) — the three resolvable states a planning
    pass can land in."""
    guard = _spec_path_guard_section(read(PLANNING_SKILL))

    assert "spec_path: default" in guard
    assert "spec_path: exempt_poc" in guard
    assert "unknown" in guard.lower()
    # field-absent must default to `default`, not `unknown` (old features
    # predating this field must not be treated as an ambiguous case)
    absent_bullet = _guard_bullet(guard, "absent")
    assert "default" in absent_bullet.lower(), (
        "the field-absent bullet no longer defaults to spec_path: default — "
        "an old feature without poc_death_date would be wrongly treated as unknown."
    )


def test_unit__step_275_documents_exempt_poc_and_default_generation_rules() -> None:
    """Contract source: skills/planning/SKILL.md Step 2.75 body (documented
    workflow contract). Guards the ghost-promise gap: the default branch must
    name generation rules for `patterns` and `dependency_rules`, not just
    `modules` — the schema (test_unit__template_documents_required_schema_field_set)
    makes both non-optional example shapes, so the generation prose must cover
    them too, or a planning agent following only the prose would never write
    them.

    Round-2 yin finding (silent-green): the same bullet's later domain_boundary
    field-naming clause ("`boundary_rationale` for modules, `serves_change_reason`
    for patterns, `evidence.note` for dependency_rules") also contains the bare
    tokens `modules`/`patterns`/`dependency_rules`. A bare-token check on the
    whole bullet tail stays green even if the actual GENERATION clause ("for
    every pattern decision, one `patterns` entry; for every dependency-direction
    constraint, one `dependency_rules` entry") is deleted and only the
    field-naming clause survives — which is exactly the regression this test
    exists to catch. Fix: assert the specific "one `<X>` entry" generation
    phrase, which the field-naming clause does not contain, instead of the
    bare token."""
    step = _step_275_section(read(PLANNING_SKILL))

    assert "spec_path: exempt_poc" in step, (
        "Step 2.75 no longer documents the exempt_poc branch."
    )
    assert "spec_path: default" in step, (
        "Step 2.75 no longer documents the default branch."
    )
    default_branch = _section(step, "spec_path: default", [])
    assert "one `modules` entry" in default_branch, (
        "the default branch no longer states the generation rule 'one "
        "`modules` entry' — the specific generation phrase, not just the bare "
        "token (which also appears in the unrelated domain_boundary "
        "field-naming clause), must be present."
    )
    assert "one `patterns` entry" in default_branch, (
        "the default branch no longer states the generation rule 'one "
        "`patterns` entry' — ghost promise: the schema requires a `patterns` "
        "example, but the generation clause for it was silently deleted "
        "(the bare token 'patterns' can still survive in the unrelated "
        "domain_boundary field-naming clause, so a bare-token check would "
        "miss this)."
    )
    assert "one `dependency_rules` entry" in default_branch, (
        "the default branch no longer states the generation rule 'one "
        "`dependency_rules` entry' — ghost promise: the schema requires a "
        "`dependency_rules` example, but the generation clause for it was "
        "silently deleted (the bare token 'dependency_rules' can still "
        "survive in the unrelated domain_boundary field-naming clause, so a "
        "bare-token check would miss this)."
    )


def test_unit__step_2_75_sits_between_step_2_5_and_step_3() -> None:
    """Contract source: skills/planning/SKILL.md heading order (documented
    workflow contract). A structural index comparison, not a label-presence
    check — reordering the steps must redden this."""
    planning = read(PLANNING_SKILL)

    idx_2_5 = planning.find("## Step 2.5: Acceptance Criteria")
    idx_2_75 = planning.find("## Step 2.75: Structure Spec")
    idx_3 = planning.find("## Step 3: File Map Consistency Check")

    assert idx_2_5 != -1 and idx_2_75 != -1 and idx_3 != -1
    assert idx_2_5 < idx_2_75 < idx_3, (
        "Step 2.75 is not positioned strictly between Step 2.5 and Step 3."
    )


def test_unit__output_list_includes_structure_spec_yaml() -> None:
    """Contract source: skills/planning/SKILL.md Output section (documented
    artifact list)."""
    output_section = _section(read(PLANNING_SKILL), "## Output", ["\n## Transition"])
    assert "structure-spec.yaml" in output_section


def test_unit__task_format_requires_structure_refs_section() -> None:
    """Contract source: skills/planning/task-format.md Required Sections
    template block (documented artifact shape)."""
    task_format = read(TASK_FORMAT)
    required_sections = _section(task_format, "## Required Sections", ["\n## Rules"])

    assert "## Structure Refs" in required_sections
    assert "structure_refs" in required_sections


def test_unit__kickoff_template_has_optional_poc_death_date_field() -> None:
    """Contract source: skills/research/templates/kickoff.md Scope section
    (documented artifact shape) — the field must be optional and sit after
    Explicitly Out of Scope, before North Star, per task-1's File placement."""
    kickoff = read(KICKOFF)
    scope_tail = _section(kickoff, "### Explicitly Out of Scope", ["\n## North Star"])
    assert "poc_death_date" in scope_tail
    assert "optional" in scope_tail.lower()


def test_unit__auto_mode_gate_registers_two_decision_points() -> None:
    """Contract source: skills/planning/SKILL.md Auto Mode Gate section
    (documented workflow contract). The Spec-Path Guard's unknown-date branch
    dispatches the gatekeeper too (see the guard's `unknown` state), so it is
    a second decision point this gate must register — not silently folded
    into, or left out alongside, the one the section named before this task."""
    gate_section = _section(read(PLANNING_SKILL), "## Auto Mode Gate", [])
    lowered = gate_section.lower()

    assert "two" in lowered and "decision points" in lowered, (
        "Auto Mode Gate no longer states it covers two decision points."
    )
    assert "planning completion transition" in lowered, (
        "Auto Mode Gate no longer names the planning completion transition "
        "as one of its decision points."
    )
    assert "unknown-date" in lowered, (
        "Auto Mode Gate no longer names the Spec-Path Guard's unknown-date "
        "resolution as a decision point — it would dispatch the gatekeeper "
        "without ever being registered here."
    )


def test_unit__process_graph_has_structure_spec_node_between_acceptance_and_plan() -> (
    None
):
    """Contract source: skills/planning/SKILL.md Process dot graph (documented
    workflow contract). Edge-level check (not mere node presence): the graph
    must route acceptance -> structure_spec -> plan, or the diagram silently
    diverges from the Step 2.75 prose step again."""
    planning = read(PLANNING_SKILL)
    graph = _section(planning, "```dot", ["\n```"])

    assert "structure_spec" in graph, (
        "Process dot graph has no structure_spec node — diagram/prose diverge."
    )
    assert "acceptance -> structure_spec" in graph, (
        "Process dot graph does not route acceptance -> structure_spec."
    )
    assert "structure_spec -> plan" in graph, (
        "Process dot graph does not route structure_spec -> plan."
    )


def test_unit__step4_structure_refs_bullet_points_to_task_format_not_restated() -> None:
    """Contract source: skills/planning/SKILL.md Step 4 task-requirements list
    (documented workflow contract). The bullet must be a POINTER to
    task-format.md's Structure Refs / Rule 6 (which owns the required-field /
    empty-array distinction), matching the pointer convention used by the
    preceding `structure_refs`-adjacent bullet — not a restatement that could
    drift out of sync with the owning rule."""
    step4 = _section(
        read(PLANNING_SKILL), "## Step 4: Task Decomposition", ["\n## Output"]
    )
    bullet_start = step4.find("Names its `structure_refs`")
    assert bullet_start != -1, (
        "Step 4 no longer names structure_refs as a task requirement"
    )
    bullet_end = step4.find("\n- ", bullet_start)
    bullet = step4[bullet_start : bullet_end if bullet_end != -1 else len(step4)]

    assert "task-format.md" in bullet, (
        "the structure_refs bullet no longer points to task-format.md."
    )
    assert "schema violation" not in bullet.lower(), (
        "the structure_refs bullet restates the missing-field=schema-violation "
        "rule instead of pointing to task-format.md's Rule 6, which owns it."
    )


# ---------------------------------------------------------------------------
# Task 2 — Death tests: dispatch-time structure_refs check + directed
# injection rule (skills/implement/SKILL.md + dispatch-template.md)
# ---------------------------------------------------------------------------


def test_death__implement_skill_missing_structure_refs_fails_dispatch_distinct_from_empty() -> (
    None
):
    """DC-3 (dispatch side): the dispatch-time enforcer itself (not just
    task-format.md upstream) must FAIL a task whose `## Structure Refs`
    section is missing entirely, and that FAIL language must be textually
    distinguished from the empty-array case. If a future edit collapses both
    cases into one branch (e.g. both dispatch normally), this goes RED.
    Round-2 fix: scoped per-bullet (not block-wide substring checks) now that
    the check is bulleted (one state per bullet, matching Spec-Path Guard's
    format) — a block-wide check could pass even if a single bullet claimed
    BOTH verdicts."""
    block = _structure_refs_check_block(read(IMPLEMENT_SKILL))

    missing_bullet = _guard_bullet(block, "section missing entirely")
    assert "schema violation" in missing_bullet.lower(), (
        "the 'section missing entirely' bullet no longer calls it a schema violation."
    )
    assert "not dispatch" in missing_bullet.lower(), (
        "the 'section missing entirely' bullet no longer states that it "
        "blocks dispatch (FAIL)."
    )

    empty_bullet = _guard_bullet(block, "structure_refs: []")
    assert "normally" in empty_bullet.lower(), (
        "the `structure_refs: []` bullet no longer says dispatch proceeds normally."
    )
    assert "schema violation" not in empty_bullet.lower(), (
        "the `structure_refs: []` bullet now ALSO claims schema violation — "
        "missing and empty have collapsed into the same (wrong) verdict."
    )


def test_death__section_missing_check_is_unconditional_on_spec_absence() -> None:
    """yin round-3 Important #1: bullet-1 (spec absent/unreadable) states its
    priority ("checked first, independent of structure_refs's value") only
    disambiguates against bullet-3/4, the VALUE states of `structure_refs`.
    Left unqualified, a literal switch-style read could let spec absence
    short-circuit past bullet-2's schema-violation FAIL — but task-format.md
    Rule 6 requires the section-missing check to fire regardless of spec
    state (including exempt_poc, where no `modules` ever exist). If bullet-2
    loses the language stating it fires unconditionally / independent of
    spec state, this goes RED — spec-absent could then silently swallow a
    genuinely unlabeled task."""
    block = _structure_refs_check_block(read(IMPLEMENT_SKILL))
    missing_bullet = _guard_bullet(block, "section missing entirely")

    assert (
        "unconditional" in missing_bullet.lower()
        or "regardless" in missing_bullet.lower()
    ), (
        "the 'section missing entirely' bullet no longer states it fires "
        "unconditionally / regardless of spec state — bullet-1's spec-absent "
        "priority clause could be misread as short-circuiting past this FAIL."
    )
    assert "schema violation" in missing_bullet.lower(), (
        "the bullet no longer calls a missing section a schema violation."
    )


def test_death__dispatch_template_injects_only_referenced_entries_with_50_percent_signal() -> (
    None
):
    """DC-2 (定向注入退化為全量注入): the Structure Spec Fragments section
    must state that ONLY the entries `structure_refs` points to are injected
    — never the whole spec file — and must name the 50% directed-injection
    -failure signal. If a future edit drops the "only"/"never the whole"
    language, or drops the 50% signal, this goes RED."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))

    assert "only" in section.lower(), (
        "Structure Spec Fragments no longer states that ONLY the matching "
        "entries are injected."
    )
    assert "never the whole spec file" in section.lower(), (
        "Structure Spec Fragments no longer states that the whole spec file "
        "must never be injected — directed injection could degrade to "
        "full-file injection silently."
    )
    assert "50%" in section, (
        "Structure Spec Fragments no longer names the 50% directed-"
        "injection-failure signal (DC-2 measurement evidence)."
    )
    assert "known_shortcut" in section, (
        "the 50% signal no longer says where it must be recorded (the "
        "task's scar report known_shortcuts) — a fired signal with nowhere "
        "to land is not measurement evidence, it is a dropped alarm."
    )


def test_death__dispatch_template_has_structure_spec_absent_notation() -> None:
    """Degradation guard: `structure_spec: absent` must exist as a literal
    notation so "no spec file for this feature at all" (exempt_poc / old
    feature) is textually distinguishable from "spec exists but injection
    was skipped by mistake". If this literal disappears, a real absence and
    a silent injection-skip both look like nothing was written."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))

    assert "structure_spec: absent" in section, (
        "Structure Spec Fragments no longer documents the literal "
        "`structure_spec: absent` notation."
    )
    absent_clause = _section(section, "structure_spec: absent", [])
    assert "does not exist" in absent_clause.lower(), (
        "the `structure_spec: absent` clause no longer ties the notation to "
        "the spec file not existing for this feature."
    )
    assert (
        "never pasted in" in absent_clause.lower()
        or "never injected" in absent_clause.lower()
    ), (
        "the `structure_spec: absent` clause no longer distinguishes itself "
        "from a non-empty structure_refs whose entries were never injected "
        "by mistake — the two silent-gap shapes collapse into one."
    )


def test_death__implement_skill_red_flags_has_missing_refs_and_full_injection_flags() -> (
    None
):
    """Both new Red Flags bullets required by task-2 must exist: dispatching
    a task with a missing `## Structure Refs` section, and injecting the
    whole spec file instead of only the referenced entries. If either bullet
    is silently dropped, the corresponding degradation has no red-flag
    anchor left for a future agent to check itself against."""
    red_flags = _red_flags_section(read(IMPLEMENT_SKILL))

    missing_bullet = _guard_bullet(red_flags, "Structure Refs")
    assert "schema violation" in missing_bullet.lower(), (
        "no Red Flags bullet calls dispatching a task with a missing "
        "Structure Refs section a schema violation."
    )

    injection_bullet = _guard_bullet(red_flags, "structure-spec.yaml")
    assert "50%" in injection_bullet, (
        "no Red Flags bullet ties injecting the whole structure-spec.yaml "
        "to the 50% signal — the full-injection red flag has no measurable "
        "anchor left."
    )


# ---------------------------------------------------------------------------
# Task 2 — Unit tests (contract-bound, documented artifact shape)
# ---------------------------------------------------------------------------


def test_unit__structure_spec_fragments_documents_injection_entry_fields() -> None:
    """Contract source: skills/implement/dispatch-template.md Structure Spec
    Fragments section (documented artifact shape) — what an injected entry
    is made of. Behavior-preserving refactor (reword the surrounding
    sentence) keeps this green; dropping a required field from the pasted
    entry (e.g. no longer pasting `evidence`) turns it red."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))

    assert "boundary_rationale" in section, (
        "Structure Spec Fragments no longer names `boundary_rationale` as "
        "part of what gets pasted into a dispatch."
    )
    assert "evidence" in section, (
        "Structure Spec Fragments no longer names `evidence` as part of "
        "what gets pasted into a dispatch."
    )
    assert "implementer" in section.lower() and "reviewer" in section.lower(), (
        "Structure Spec Fragments no longer names BOTH the implementer "
        "dispatch and the reviewer dispatches as injection targets — task-2's "
        "rule requires fragments in all three (implementer + two reviewers)."
    )


def test_unit__structure_spec_fragments_states_priority_and_unreadable_distinction() -> (
    None
):
    """Contract source: skills/implement/dispatch-template.md Structure Spec
    Fragments section (documented artifact shape). Round-2 quality-reviewer
    Suggestion: the absent branch must state (a) its priority relative to
    the structure_refs states — spec existence/readability is checked FIRST,
    independent of structure_refs's value — and (b) that a spec file that
    exists but cannot be read is NEVER the same as absent: it must be
    written as `structure_spec: unreadable` and treated as FAIL, never
    silently downgraded to a legitimate absence."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))

    priority_para = _section(
        section,
        "Check `changes/<feature>/structure-spec.yaml`'s existence/readability FIRST",
        ["\n\nWhen it exists"],
    )
    assert "independent" in priority_para.lower(), (
        "the priority paragraph no longer states spec existence/readability "
        "is checked independent of structure_refs's value — a bare "
        "block-wide token check on 'first'/'independent' could stay green "
        "even if this specific sentence were deleted and the words survived "
        "elsewhere in the section by coincidence."
    )
    assert "structure_spec: unreadable" in section, (
        "Structure Spec Fragments no longer documents the "
        "`structure_spec: unreadable` notation."
    )
    unreadable_clause = _section(section, "Unreadable", [])
    assert "fail" in unreadable_clause.lower(), (
        "the unreadable clause no longer says dispatch is treated as FAIL — "
        "an unreadable spec could be silently downgraded to absent again."
    )


def test_unit__structure_spec_fragments_defines_single_50_percent_basis() -> None:
    """Contract source: skills/implement/dispatch-template.md Structure Spec
    Fragments section (documented artifact shape) — the 50% signal must have
    exactly ONE stated computation basis (line count), per this task's
    Expected Scar Item ("50% 注入量的計算方式若未精確定義，agent 各自解讀").
    A behavior-preserving reword keeps this green; adding a second competing
    basis (e.g. also mentioning character count) without picking one turns
    this red."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))

    assert "line" in section.lower(), (
        "the 50% signal no longer names a line-count basis."
    )
    assert "character" not in section.lower(), (
        "a second competing basis (character count) appears alongside the "
        "line-count basis — the signal must have exactly one definition."
    )


def test_unit__structure_spec_fragments_section_within_subtraction_budget() -> None:
    """Success - 儀式淨增量在預算內 (KD-5 subtraction discipline, machine
    -enforced): task-2's Files note caps this new section at <= 20 lines,
    mirroring task-1's line-budget test for structure-spec.yaml."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))
    lines = section.splitlines()
    assert len(lines) <= 20, (
        f"Structure Spec Fragments section has {len(lines)} lines, budget "
        "is 20 — the subtraction discipline (KD-5) was silently exceeded."
    )


def test_unit__implement_skill_structure_refs_check_names_all_dispatch_states_and_mode_c() -> (
    None
):
    """Contract source: skills/implement/SKILL.md Subagent Context named
    check-rule sentence (documented workflow contract) — the check must
    cover all four dispatch states named in task-2's rule (spec-absent-or-
    unreadable / missing / empty / non-empty) AND state it applies
    identically in inline mode C, per this task's Expected Scar Item on the
    mode-C silent gap.

    Round-2 DRY fix: the spec-absent/unreadable bullet must POINT to
    dispatch-template.md (single owner of that notation) rather than
    restate `structure_spec: absent` literally in SKILL.md — asserting the
    literal notation is ABSENT from SKILL.md's block guards against the DRY
    regression coming back."""
    block = _structure_refs_check_block(read(IMPLEMENT_SKILL))

    absent_bullet = _guard_bullet(block, "absent or unreadable")
    assert "dispatch-template.md" in absent_bullet, (
        "the spec-absent/unreadable bullet no longer points to "
        "dispatch-template.md, which owns the absent/unreadable notation."
    )
    assert "structure_spec: absent" not in block, (
        "SKILL.md restates the `structure_spec: absent` notation instead of "
        "pointing to dispatch-template.md — a second, driftable source of "
        "truth for the same notation (DRY regression)."
    )
    assert "mode c" in block.lower(), (
        "the dispatch check no longer states it applies in inline mode C — "
        "this is exactly the mode-C silent gap task-2's Expected Scar Item warned about."
    )


def test_unit__yin_side_constraints_points_to_structure_refs_check_not_restated() -> (
    None
):
    """Contract source: skills/implement/SKILL.md Yin-Side Constraints bullet
    list (documented workflow contract). The other two inline-mode (mode C)
    carve-outs already live here, collected together; a reader who only scans
    this list (not Subagent Context) must still discover the Structure Refs
    check applies inline. Per this codebase's established pointer-not-
    restatement convention (task-1's step4-bullet test), the bullet must
    POINT to Subagent Context, not restate the schema-violation rule (which
    would create a second source of truth for the same rule)."""
    skill = read(IMPLEMENT_SKILL)
    yin_side = _section(skill, "## Yin-Side Constraints", ["\n## Red Flags"])
    bullet = _guard_bullet(yin_side, "Structure Refs dispatch check applies inline too")

    assert "mode c" in bullet.lower(), (
        "the Yin-Side Constraints pointer bullet no longer names mode C."
    )
    assert "subagent context" in bullet.lower(), (
        "the pointer bullet no longer points to Subagent Context."
    )
    assert "schema violation" not in bullet.lower(), (
        "the pointer bullet restates the schema-violation rule instead of "
        "pointing to Subagent Context, which owns it — this would create a "
        "second, driftable source of truth for the same rule."
    )


# ---------------------------------------------------------------------------
# Task 3 — Death tests: code-quality-reviewer dual-mode (spec/principles/
# UNKNOWN) + drift_items output schema (agents/code-quality-reviewer.md)
# ---------------------------------------------------------------------------


def test_death__unreadable_spec_forces_unknown_never_downgrades_to_principles_mode() -> (
    None
):
    """DC-4: a structure-spec.yaml that exists but is unreadable/unparseable
    must force UNKNOWN (blocking) — never a silent downgrade to reviewing
    under the 9 principles alone as if the spec commitment didn't exist. If
    a future edit adds a permissive escape hatch ("fall back to principles
    mode" or any of its common phrasings), this must go RED. The forbidden
    phrases are checked against the WHOLE agent file (not just this section)
    because a degradation escape hatch could be added anywhere, e.g. bolted
    onto Constraints instead of this section."""
    agent_text = read(CODE_QUALITY_REVIEWER)
    section = _structure_spec_mode_section(agent_text)
    unknown_bullet = _guard_bullet(section, "UNKNOWN (blocking)")

    assert "unreadable" in unknown_bullet.lower(), (
        "the UNKNOWN (blocking) bullet no longer names the unreadable-spec case."
    )
    assert "unknown" in unknown_bullet.lower()

    lowered_whole_file = agent_text.lower()
    forbidden_phrases = (
        "fall back to principles mode",
        "falls back to principles mode",
        "falling back to principles mode",
        "downgrade to principles mode",
        "downgrades to principles mode",
        "revert to principles mode",
        "retreat to principles mode",
    )
    for phrase in forbidden_phrases:
        assert phrase not in lowered_whole_file, (
            f"agent file contains the degradation escape-hatch phrase {phrase!r} — "
            "DC-4's silent-downgrade-to-principles-mode path has reappeared."
        )


def test_death__drift_items_names_three_categories_and_missing_neq_empty_array() -> (
    None
):
    """DC-5: drift_items must name exactly the three category tokens, and the
    agent definition must state that a MISSING drift_items field is not the
    same as an explicit empty array — the missing case must be read
    downstream as a parse failure, never as zero drift. If any of these
    tokens/statements are silently dropped, this goes RED."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))

    for category in ("undeclared_boundary", "violated_boundary", "abandoned_commitment"):
        assert category in section, (
            f"Spec Mode Additions no longer names the drift_items category {category!r}."
        )

    assert "drift_items: []" in section, (
        "Spec Mode Additions no longer shows the explicit empty-array form "
        "`drift_items: []` as the 'checked, none found' state."
    )
    lowered = section.lower()
    assert "not equivalent to an empty array" in lowered, (
        "the MISSING-field clause no longer states it is not equivalent to "
        "an empty array — DC-5's field-missing-vs-empty distinction is gone."
    )
    assert "parse failure" in lowered and "zero drift" in lowered, (
        "the MISSING-field clause no longer states downstream reads a "
        "missing field as a parse failure rather than zero drift."
    )
    normalized = " ".join(section.split()).lower()
    assert "canonical owner" in normalized, (
        "round-2 quality review low-cost item #6: the drift_items category "
        "names no longer carry an explicit ownership marker (this agent "
        "definition as canonical owner) — an aggregator (task-4) could "
        "restate the names instead of pointing back here."
    )


def test_death__evidence_ref_resolution_dangling_is_a_finding() -> None:
    """DC-1 (reviewer-side first defense line): the agent definition must
    state its own responsibility to resolve each evidence ref (git_history /
    planned_task / domain_boundary) and that any `failure`/`unknown`
    resolution is a finding, never silent. If this sentence is dropped, this
    goes RED — cargo-cult evidence would pass review unchallenged.

    Round-3 fix: anchor moved off "are **findings**" (round-2 wording) onto
    "is a **finding**, never silent" — the intro-scoped singular form that
    replaced it when the sentence moved ahead of the bullet list to avoid
    nesting under one bullet (round-3 Important #1/#3 fix) — same contract,
    current wording."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))

    for evidence_type in ("git_history", "planned_task", "domain_boundary"):
        assert evidence_type in section, (
            f"Spec Mode Additions no longer names evidence type {evidence_type!r}."
        )
    assert "index.yaml" in section, (
        "Spec Mode Additions no longer states resolving planned_task refs "
        "against index.yaml."
    )
    assert "dangling" in section.lower(), (
        "Spec Mode Additions no longer names the dangling-ref shape at all."
    )

    findings_clause = _section(section, "is a **finding**", [])
    lowered = findings_clause.lower()
    assert "never silent" in lowered, (
        "the failure/unknown-resolutions clause no longer states these are "
        "never silent — the DC-1 first-defense-line language was weakened."
    )
    assert "cargo-cult evidence" in lowered, (
        "the failure/unknown-resolutions clause no longer names cargo-cult "
        "evidence as what this defends against."
    )


def test_death__verdict_must_declare_mode_used() -> None:
    """The verdict must always declare which of the three modes (spec /
    principles / UNKNOWN) was used for that review. If this requirement
    sentence is dropped, a review could silently apply spec-mode-shaped
    leniency (or omit spec-mode scrutiny) without anyone downstream being
    able to tell which mode actually ran."""
    section = _structure_spec_mode_section(read(CODE_QUALITY_REVIEWER))
    lowered = section.lower()

    assert "mode: spec / principles / unknown" in lowered, (
        "Structure Spec Mode no longer names the exact mode-declaration "
        "token `Mode: spec / principles / UNKNOWN`."
    )
    assert "must state which mode was used" in lowered, (
        "Structure Spec Mode no longer requires every verdict to state "
        "which mode was used."
    )
    assert "malformed" in lowered, (
        "Structure Spec Mode no longer treats an undeclared mode as "
        "malformed output — this was the enforcement teeth of the rule."
    )


def test_death__all_unknown_output_templates_carry_mode_placeholder() -> None:
    """Round-2 quality review Important #1: the UNKNOWN(blocking) branch
    points readers at 'the compressed UNKNOWN output', and the mode
    -declaration rule says omitting Mode is malformed — but if the actual
    UNKNOWN-shaped templates in this file have no Mode field, that
    combination is unsatisfiable BY CONSTRUCTION on every path that returns
    UNKNOWN. Guards all UNKNOWN-shaped output blocks (Reference File
    Protocol, Step 0 Case 1, Step 0 Case 2, and the general compressed
    format) each carry the Mode placeholder line — not just the rule that
    demands it."""
    text = read(CODE_QUALITY_REVIEWER)
    unknown_block_starts = [
        m.start() for m in re.finditer(r"## Code Quality Review — UNKNOWN", text)
    ]
    assert len(unknown_block_starts) >= 4, (
        "expected at least 4 UNKNOWN-shaped output blocks (Reference File "
        "Protocol, Step 0 Case 1, Step 0 Case 2, compressed format) in "
        "agents/code-quality-reviewer.md — count dropped below what this "
        "test's premise assumes; re-audit which blocks exist before trusting "
        "this test's coverage."
    )
    for start in unknown_block_starts:
        # Round-3 low-cost #5 (yin non-blocking): slice to the block's own
        # closing code-fence (each UNKNOWN template is a ```-delimited
        # example) instead of a fixed byte offset — a structural boundary
        # that survives the block growing or shrinking, rather than an
        # arbitrary character count that could silently stop covering the
        # real end of a block if it grew past it.
        fence_end = text.find("```", start)
        assert fence_end != -1, (
            f"UNKNOWN-shaped block at offset {start} has no closing code "
            "fence — this test's structural-boundary assumption no longer holds."
        )
        block = text[start:fence_end]
        assert "Mode: [spec / principles / UNKNOWN]" in block, (
            f"the UNKNOWN-shaped output block starting at offset {start} has "
            "no `Mode: [spec / principles / UNKNOWN]` placeholder line — a "
            "verdict following this exact template cannot satisfy the "
            "mode-declaration rule, reproducing the round-2 self-contradiction."
        )


def test_death__spec_entries_output_field_exists_for_per_entry_verdicts() -> None:
    """Round-2 yin review: Spec Mode Additions requires producing a
    Pass/Concern row per injected spec entry id, but Output Format had no
    field to hold it — that core deliverable could silently not appear in a
    real review output, and downstream could not distinguish 'checked, all
    Pass' from 'never ran'. Guards the Spec Entries field's presence."""
    section = _output_format_section(read(CODE_QUALITY_REVIEWER))
    assert "### Spec Entries" in section, (
        "Output Format has no home for the per-entry Pass/Concern verdicts "
        "Spec Mode Additions requires producing."
    )
    spec_entries_block = _section(section, "### Spec Entries", ["\n###"])
    lowered = spec_entries_block.lower()
    assert "pass/concern" in lowered, (
        "the Spec Entries field no longer shows the Pass/Concern verdict "
        "shape per entry."
    )


# ---------------------------------------------------------------------------
# Task 3 — Unit tests (contract-bound, documented artifact shape)
# ---------------------------------------------------------------------------


def test_unit__structure_spec_mode_documents_three_states_with_dispatch_notations() -> (
    None
):
    """Contract source: agents/code-quality-reviewer.md Structure Spec Mode
    section (documented workflow contract) — the three mode names, tied to
    the exact dispatch notations task-2 established
    (`structure_spec: absent` / `structure_spec: unreadable`). Behavior
    -preserving reword keeps this green; dropping a mode or its dispatch
    trigger turns it red."""
    section = _structure_spec_mode_section(read(CODE_QUALITY_REVIEWER))

    assert "**Spec mode**" in section
    assert "**Principles mode**" in section
    assert "**UNKNOWN (blocking)**" in section
    assert "structure_spec: absent" in section, (
        "Principles mode is no longer tied to the `structure_spec: absent` "
        "dispatch notation task-2 established."
    )
    assert "structure_spec: unreadable" in section, (
        "UNKNOWN (blocking) is no longer tied to the `structure_spec: "
        "unreadable` dispatch notation task-2 established."
    )


def test_unit__spec_mode_additions_documents_boundary_rationale_check_and_evidence_types() -> (
    None
):
    """Contract source: agents/code-quality-reviewer.md Spec Mode Additions
    section (documented artifact shape) — per-entry judgment against
    boundary_rationale/serves_change_reason, plus the three evidence-type
    resolution rules (each type's specific check)."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))

    assert "boundary_rationale" in section and "serves_change_reason" in section
    git_history_clause = _guard_bullet(section, "`git_history`")
    assert "exists in the repo" in git_history_clause.lower()

    domain_boundary_clause = _guard_bullet(section, "`domain_boundary`")
    assert "machine_verifiable: false" in domain_boundary_clause, (
        "the domain_boundary resolution rule no longer checks for the "
        "`machine_verifiable: false` flag — task-1's per-instance degradation "
        "(machine_verifiable left true) would go unreviewed."
    )
    assert "non-empty" in domain_boundary_clause.lower()


def test_death__domain_boundary_judgment_is_binary_not_three_state() -> None:
    """Round-3 quality review Important #1: the pointer to structure-
    spec.yaml's template only defines resolved/failure/unknown for ref
    -bearing types (git_history/planned_task) — that template comment never
    covers `domain_boundary`, which has no ref to resolve. Without an
    explicit scoping statement, the agent definition would be pointing at an
    owner that does not own the content being pointed to, and per-entry
    `unknown` for domain_boundary would be undefined (a real gap: what does
    'unknown' even mean for a type with no external resolution target?).
    Guards that domain_boundary's judgment is explicitly declared to be
    owned HERE and binary (pass/failure only — no per-entry unknown), not
    silently inheriting the ref-bearing three-state vocabulary."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))
    domain_boundary_clause = _guard_bullet(section, "`domain_boundary`")
    lowered = domain_boundary_clause.lower()

    assert "owned here" in lowered, (
        "the domain_boundary bullet no longer declares its judgment is "
        "owned by this agent definition, not the ref-bearing template."
    )
    assert "binary" in lowered and "not three-state" in lowered, (
        "the domain_boundary bullet no longer declares its judgment is "
        "binary (pass/failure), not the three-state resolved/failure/unknown "
        "vocabulary that only applies to ref-bearing evidence types."
    )


def test_unit__planned_task_derivation_names_multi_feature_diff_ambiguity() -> None:
    """Round-3 quality review low-cost #4 (Suggestion): the primary feature
    -derivation step (from a `changes/<feature>/...` Changed Files/diff
    path) must itself name the case where the diff spans more than one
    distinct feature path — that is ambiguous too, same `unknown` outcome as
    the Glob/Grep fallback's ambiguous-match case, not a silent pick of
    whichever path happens to be found first."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))
    planned_task_clause = _guard_bullet(section, "`planned_task`")
    lowered = planned_task_clause.lower()

    assert "ambiguous" in lowered, (
        "the planned_task derivation no longer names the multi-feature-diff "
        "ambiguity case at all."
    )
    assert ">1" in planned_task_clause or "more than one" in lowered, (
        "the planned_task derivation no longer states the diff-spans-"
        "multiple-features condition that triggers the ambiguous outcome."
    )


def test_unit__spec_mode_additions_points_to_template_for_evidence_vocabulary() -> None:
    """Round-2 quality review Important #2 (DRY): the resolved/failure/unknown
    three-state vocabulary is owned by structure-spec.yaml's template
    (task-1); this agent definition must POINT to it rather than restate the
    states in different wording (parallel-evolution risk). Guards the
    pointer's presence — a future edit that drops the pointer and reverts to
    a from-scratch restatement should go RED."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))
    assert "skills/planning/templates/structure-spec.yaml" in section, (
        "Spec Mode Additions no longer points to structure-spec.yaml's "
        "template as the owner of the resolved/failure/unknown vocabulary."
    )
    normalized = " ".join(section.split()).lower()
    assert "evidence resolution" in normalized, (
        "Spec Mode Additions no longer names the template's Evidence "
        "resolution comment as the specific pointer target."
    )
    assert "git_history/planned_task" in normalized or (
        "for git_history" in normalized and "planned_task" in normalized
    ), (
        "round-3 Important #1 (DRY pointer scope): the pointer to the "
        "template's vocabulary must be explicitly scoped to git_history/"
        "planned_task — it does not own domain_boundary's ref-less judgment."
    )


def test_unit__principles_mode_covers_no_structure_spec_notation_at_all() -> None:
    """Round-2 quality review low-cost item #4: the three-state mode
    selection must also cover a dispatch that carries NO structure_spec
    notation whatsoever (backward compatibility for non-spec-path callers),
    routed to principles mode. Round-3 Coupling fix corrected the
    attribution: `skills/implement/SKILL.md`'s Structure Refs dispatch check
    is the actual guarantor a spec-path dispatch never omits the notation
    silently — dispatch-template.md owns only the notation's format, not the
    guarantee, and the bullet must say so explicitly (not just credit
    dispatch-template.md).

    Round-3 yin Critical fix: the old assertion (`"dispatch-template.md" in
    principles_bullet`) was polarity-blind — it is satisfied by the CORRECT
    text's negation ("...not dispatch-template.md") but would stay equally
    green if a future edit reverted to the round-2 WRONG attribution
    ("dispatch-template.md's four-state guard guarantees this"), since both
    strings contain the same bare substring. Now double-locked: assert
    SKILL.md is affirmatively named as the guarantor, AND assert the
    dispatch-template.md disclaim phrase specifically (not just presence of
    the bare token) — reverting the attribution must redden at least one."""
    section = _structure_spec_mode_section(read(CODE_QUALITY_REVIEWER))
    principles_bullet = _guard_bullet(section, "**Principles mode**")
    normalized = " ".join(principles_bullet.split()).lower()

    assert "no structure_spec notation at all" in normalized, (
        "Principles mode no longer covers the case where the dispatch "
        "carries no structure_spec notation whatsoever."
    )
    assert "skills/implement/skill.md" in normalized and "guarantee" in normalized, (
        "Principles mode's backward-compat bullet no longer affirmatively "
        "names skills/implement/SKILL.md's Structure Refs dispatch check as "
        "the actual guarantor this is never silently missing."
    )
    assert "not dispatch-template.md" in normalized, (
        "Principles mode's backward-compat bullet no longer disclaims "
        "dispatch-template.md as the guarantor — without this exact "
        "disclaim, reverting to the round-2 wrong attribution "
        "('dispatch-template.md's four-state guard guarantees this') would "
        "still satisfy a bare 'dispatch-template.md' substring check."
    )


def test_unit__output_format_declares_mode_and_drift_items_schema_fields() -> None:
    """Contract source: agents/code-quality-reviewer.md Output Format section
    (documented artifact shape) — the `Mode` line and the `drift_items`
    example's required fields (category/ref/description). A behavior
    -preserving reword keeps this green; dropping a required field from the
    documented drift_items shape turns it red."""
    section = _output_format_section(read(CODE_QUALITY_REVIEWER))

    assert "Mode: [spec / principles / UNKNOWN]" in section, (
        "Output Format no longer shows the Mode declaration line in the "
        "sample verdict output."
    )
    drift_block = _section(section, "drift_items:", ["\n###"])
    assert "category:" in drift_block
    assert "ref:" in drift_block
    assert "description:" in drift_block
    for category in ("undeclared_boundary", "violated_boundary", "abandoned_commitment"):
        assert category in drift_block


def test_unit__spec_mode_additions_within_subtraction_budget() -> None:
    """Success - 儀式淨增量在預算內 (KD-5 subtraction discipline, machine
    -enforced): task-3's Files note caps the overall agent-definition net
    diff at <= 60 lines. The Spec Mode Additions section alone (the largest
    single addition) is capped at <= 30 lines so no single block silently
    consumes the whole budget."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))
    lines = section.splitlines()
    assert len(lines) <= 30, (
        f"Spec Mode Additions section has {len(lines)} lines, budget is 30 — "
        "the subtraction discipline (KD-5) was silently exceeded."
    )


# ---------------------------------------------------------------------------
# Task 4 — Death tests: iteration structural_drift aggregation +
# validate-and-ship reconciliation structural dimension / 0-dangling
# terminal audit (skills/iteration/SKILL.md + skills/validate-and-ship/SKILL.md)
# ---------------------------------------------------------------------------


def test_death__structural_drift_and_signal_lost_are_parallel_not_mixed() -> None:
    """KD-4: `structural_drift` and `signal_lost` are two independent
    signals — mixing them lets structural drift silently inflate or dilute
    the scar-based signal_lost number (or vice versa). If a future edit
    folds structural_drift into the signal_lost formula, or drops the
    parallel-not-mixed statement, this must go RED."""
    clause = _structural_drift_clause(read(ITERATION_SKILL))

    assert "structural_drift" in clause and "signal_lost" in clause, (
        "the structural_drift aggregation clause no longer names both "
        "signals."
    )
    assert "並列不混計" in clause, (
        "the structural_drift aggregation clause no longer states "
        "'並列不混計' (parallel, never mixed) — KD-4's division of labor "
        "between structural_drift and signal_lost has no textual anchor left."
    )
    assert "never fold" in clause.lower(), (
        "the clause no longer explicitly forbids folding structural_drift "
        "into the signal_lost formula."
    )


def test_death__drift_items_missing_field_is_parse_failure_not_zero_drift() -> None:
    """DC-5 (consumption side): a task whose spec-mode review returned no
    `drift_items` field at all must be aggregated as a parse failure, never
    silently read as zero drift. Closes task-3's deferred scar item (missing
    vs. explicit empty array has no code enforcement; this is the
    iteration-aggregation prose closing it). If this clause is weakened to
    drop the parse-failure treatment, this must go RED."""
    clause = _structural_drift_clause(read(ITERATION_SKILL))
    lowered = clause.lower()

    assert "drift_items" in clause, (
        "the structural_drift aggregation clause no longer names "
        "`drift_items` as its source field."
    )
    assert "欄位缺失" in clause, (
        "the clause no longer names the missing-field ('欄位缺失') case "
        "explicitly."
    )
    assert "parse failure" in lowered, (
        "a task with no `drift_items` field is no longer treated as a "
        "parse failure — DC-5's consumption-side guard is gone."
    )
    assert "distinct from" in lowered and "drift_items: []" in clause, (
        "the clause no longer distinguishes a missing `drift_items` field "
        "from an explicit `drift_items: []` — the two silent-zero-drift "
        "shapes could collapse into one again."
    )


def test_death__zero_dangling_audit_names_three_states_and_dangling_is_blocking() -> (
    None
):
    """DC-1 (terminal defense line): validate-and-ship's terminal audit must
    name all three evidence-resolution states (resolved / failure / unknown)
    and state that a dangling (`failure`) ref is a BLOCKING finding — never
    silently passed. If any of these are dropped, cargo-cult evidence could
    reach ship with nothing catching it at the terminal gate."""
    clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    lowered = clause.lower()
    # Normalize whitespace: the prose soft-wraps at arbitrary columns, so a
    # two-word phrase can legitimately straddle a line break in the source
    # file without any change in meaning (test-contract.md's
    # behavior-preserving-reword rule — a rewrap must not redden this).
    normalized = " ".join(lowered.split())

    for token in ("resolved", "failure", "unknown"):
        assert token in lowered, (
            f"the 0-dangling terminal audit clause no longer names the "
            f"{token!r} resolution state."
        )
    assert "dangling" in lowered, (
        "the clause no longer names the dangling-ref shape."
    )
    assert "blocking finding" in normalized, (
        "the clause no longer states a dangling ref is a blocking finding — "
        "DC-1's terminal defense line has no enforcement language left."
    )
    assert "never silently pass" in normalized, (
        "the clause no longer forbids silently passing a dangling ref."
    )


def test_death__structure_spec_absent_exempt_distinguishes_skip_from_finding() -> None:
    """Degradation guard: `structure_spec: absent/exempt` must cover BOTH
    legitimate no-audit cases (exempt_poc, and a pre-spec-path feature with
    no structure-spec.yaml AND no task referencing structure_refs) — and the
    clause must state that a missing spec some task's `structure_refs` DOES
    reference is a FINDING, not folded into the same skip. Without this
    three-way split, a genuinely missing spec (anomaly) would look
    identical, on disk, to a legitimate exemption or an old feature."""
    clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    lowered = clause.lower()

    assert "structure_spec: absent/exempt" in clause, (
        "the clause no longer records the `structure_spec: absent/exempt` "
        "notation."
    )
    assert "exempt_poc" in lowered, (
        "the clause no longer names exempt_poc as one of the legitimate "
        "skip cases."
    )
    assert "skip this audit" in lowered, (
        "the clause no longer states the legitimate cases skip the audit."
    )
    assert "is a **finding**, not a skip" in clause, (
        "the clause no longer distinguishes a missing-but-referenced spec "
        "as a finding rather than a skip — the anomaly case has silently "
        "merged into the legitimate-exemption case."
    )


def test_death__structural_dimension_field_must_exist_missing_neq_empty() -> None:
    """DC-5 (reconciliation side): review round-2 yin finding — the
    Structural dimension bullet must state its output field MUST exist, and
    that an explicit empty result ('compared, no drift found') is textually
    distinct from a MISSING field ('the comparison never ran, reconciliation
    is incomplete'). Without this, the exact DC-5 disease this feature has
    already been turned back for three times (missing read as zero) would
    reappear at the terminal reconciliation step itself. If this distinction
    is dropped, this must go RED."""
    section = _reconciliation_section(read(VALIDATE_AND_SHIP_SKILL))
    lowered = section.lower()
    # Normalize whitespace: the prose soft-wraps at arbitrary columns, so a
    # multi-word phrase can legitimately straddle a line break in the source
    # file without any change in meaning (test-contract.md's
    # behavior-preserving-reword rule — a rewrap must not redden this).
    # Matches the established convention at :1385 for the same reason.
    normalized = " ".join(lowered.split())

    assert "must exist" in normalized, (
        "the Structural dimension bullet no longer states its output field "
        "MUST exist."
    )
    assert "structural_drift_final: []" in section, (
        "the bullet no longer shows the explicit-empty form "
        "`structural_drift_final: []` as the 'compared, no drift found' state."
    )
    assert "missing" in normalized and "never ran" in normalized, (
        "the bullet no longer states a MISSING field means the comparison "
        "never ran."
    )
    assert "reconciliation is incomplete" in normalized, (
        "the bullet no longer states a missing field makes reconciliation "
        "incomplete (not clean) — DC-5's missing-vs-empty distinction has "
        "no consequence attached to it at the reconciliation step."
    )


# ---------------------------------------------------------------------------
# Task 4 — Unit tests (contract-bound, documented artifact shape)
# ---------------------------------------------------------------------------


def test_unit__structural_drift_points_to_canonical_owner_not_restated() -> None:
    """Contract source: skills/iteration/SKILL.md Step 1 structural_drift
    aggregation clause (documented workflow contract). Per this feature's
    established pointer-not-restatement convention (three prior tasks were
    turned back for restating/faking a pointer): the clause must point to
    `agents/code-quality-reviewer.md` Spec Mode Additions as the canonical
    owner of the three drift_items category names, and must NOT restate
    those category names itself — a behavior-preserving reword of the
    surrounding sentence keeps this green; copying the category names in
    here (creating a second, driftable source of truth) turns it red."""
    clause = _structural_drift_clause(read(ITERATION_SKILL))

    assert "agents/code-quality-reviewer.md" in clause, (
        "the clause no longer points to agents/code-quality-reviewer.md as "
        "the drift_items source."
    )
    assert "canonical" in clause.lower(), (
        "the clause no longer names code-quality-reviewer.md as the "
        "canonical owner."
    )
    for category in ("undeclared_boundary", "violated_boundary", "abandoned_commitment"):
        assert category not in clause, (
            f"the clause restates the drift_items category {category!r} "
            "instead of pointing to its canonical owner — a second, "
            "driftable source of truth for the same names."
        )


def test_unit__zero_dangling_audit_points_to_structure_spec_template_not_restated() -> (
    None
):
    """Contract source: skills/validate-and-ship/SKILL.md Failure Budget
    Review's 0-dangling audit clause (documented workflow contract). The
    resolved/failure/unknown vocabulary's full definitions are owned by
    `skills/planning/templates/structure-spec.yaml`'s Evidence resolution
    comment — the clause must point there (same pattern
    agents/code-quality-reviewer.md already uses for git_history/
    planned_task) rather than re-deriving its own definitions."""
    clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))

    assert "skills/planning/templates/structure-spec.yaml" in clause, (
        "the clause no longer points to structure-spec.yaml's template as "
        "the owner of the resolved/failure/unknown vocabulary."
    )
    assert "evidence resolution" in clause.lower(), (
        "the clause no longer names the template's Evidence resolution "
        "comment as the specific pointer target."
    )
    assert "not restated here" in clause.lower(), (
        "the clause no longer marks itself as deferring to the template "
        "instead of restating the vocabulary's definitions."
    )


def test_unit__zero_dangling_audit_is_full_scan_not_sampling() -> None:
    """Contract source: skills/validate-and-ship/SKILL.md 0-dangling audit
    clause (documented workflow contract) — Expected Scar Item: the audit is
    named a terminal 'audit' but must be a FULL scan of every evidence ref,
    not a sample, since entry counts are small. Guards against a future
    reword silently narrowing 'every ref' to a sampled subset."""
    clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    lowered = clause.lower()

    assert "every evidence ref" in lowered, (
        "the clause no longer states EVERY evidence ref is resolved."
    )
    assert "not sampled" in lowered, (
        "the clause no longer explicitly rules out sampling — a 'terminal "
        "audit' that only samples entries would silently reintroduce the "
        "cargo-cult-evidence gap at the one place meant to close it."
    )


def test_unit__reconciliation_step5_names_structural_dimension_bullet() -> None:
    """Contract source: skills/validate-and-ship/SKILL.md Step 5
    Reconciliation Check bullet list (documented workflow contract) — the
    structural dimension bullet must exist, be scoped to `spec_path:
    default`, and must explicitly distinguish itself from iteration's
    per-task `structural_drift` tally (a one-time terminal comparison, not a
    duplicate of the per-task aggregation)."""
    section = _reconciliation_section(read(VALIDATE_AND_SHIP_SKILL))
    lowered = section.lower()

    assert "structural dimension" in lowered, (
        "Step 5 no longer names a Structural dimension bullet."
    )
    assert "spec_path: default" in section, (
        "the Structural dimension bullet no longer scopes itself to "
        "`spec_path: default`."
    )
    assert "structural_drift" in section and "not a duplicate of it" in lowered, (
        "the Structural dimension bullet no longer distinguishes itself "
        "from iteration's per-task `structural_drift` tally — a reader "
        "could mistake this for a second place computing the same count."
    )


def test_unit__zero_dangling_audit_and_structural_dimension_cross_reference() -> (
    None
):
    """Contract source: skills/validate-and-ship/SKILL.md Step 1 and Step 5
    (documented workflow contract). Review round-2 quality finding: the two
    structural checks in this file (Step 1's referential-integrity audit and
    Step 5's spec-vs-shipped compliance check) must name each other, so a
    reader of either one alone still learns the other exists and what it
    covers instead of assuming the check in front of them is the only one."""
    audit_clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    recon_section = _reconciliation_section(read(VALIDATE_AND_SHIP_SKILL))

    audit_normalized = " ".join(audit_clause.lower().split())
    recon_normalized = " ".join(recon_section.lower().split())

    assert "step 5's structural dimension" in audit_normalized, (
        "the 0-dangling audit clause no longer references Step 5's "
        "Structural dimension by name."
    )
    assert "not step 1's referential-integrity audit" in recon_normalized, (
        "the Structural dimension bullet no longer references Step 1's "
        "referential-integrity audit by name."
    )


def test_unit__structure_spec_absent_exempt_token_scope_documented() -> None:
    """Contract source: skills/validate-and-ship/SKILL.md 0-dangling audit
    clause (documented workflow contract). Review round-2 quality finding:
    `structure_spec: absent/exempt` reuses dispatch-template.md's per-task
    `structure_spec: absent` token, but at a different scope (feature-level
    audit-skip record vs. a per-task dispatch note). The clause must state
    this relationship explicitly, or a reader could assume the two notations
    are governed by the same rule."""
    clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    normalized = " ".join(clause.lower().split())

    assert "dispatch-template.md" in clause, (
        "the clause no longer names dispatch-template.md as the origin of "
        "the reused `structure_spec: absent` token."
    )
    assert "per-task" in normalized and "feature-level audit skip" in normalized, (
        "the clause no longer states the scope difference (per-task dispatch "
        "note vs. feature-level audit skip) between the two token usages."
    )


def test_unit__structural_drift_clause_sits_after_signal_lost_before_step2() -> None:
    """Contract source: skills/iteration/SKILL.md Step 1 heading order
    (documented workflow contract). Structural index comparison, not mere
    label presence — the structural_drift clause must sit after the
    signal_lost formula and before Step 2 (Triage), so it is aggregated in
    the same pass, not scattered elsewhere in the file."""
    iteration = read(ITERATION_SKILL)

    idx_signal_lost = iteration.find("signal_lost = count(known_shortcuts)")
    idx_drift = iteration.find("**structural_drift aggregation:**")
    idx_step2 = iteration.find("## Step 2: Triage")

    assert idx_signal_lost != -1 and idx_drift != -1 and idx_step2 != -1
    assert idx_signal_lost < idx_drift < idx_step2, (
        "the structural_drift aggregation clause is not positioned between "
        "the signal_lost formula and Step 2: Triage."
    )


def test_unit__task4_net_addition_within_subtraction_budget() -> None:
    """Success - 儀式淨增量在預算內 (KD-5 subtraction discipline, machine
    -enforced): task-4's Files note caps the combined net addition across
    both SKILL.md files at <= 40 lines. Checked per-clause (not via git
    diff, which would depend on an external repo state this test does not
    control) so the budget is enforced regardless of what else changed in
    either file around it."""
    iteration_clause = _structural_drift_clause(read(ITERATION_SKILL))
    audit_clause = _zero_dangling_audit_clause(read(VALIDATE_AND_SHIP_SKILL))
    section = _reconciliation_section(read(VALIDATE_AND_SHIP_SKILL))
    recon_bullet_start = section.lower().find("- **structural dimension**")
    assert recon_bullet_start != -1
    recon_bullet_end = section.find("\n### 6", recon_bullet_start)
    recon_bullet = section[
        recon_bullet_start : recon_bullet_end if recon_bullet_end != -1 else len(section)
    ]

    total_lines = (
        len(iteration_clause.splitlines())
        + len(audit_clause.splitlines())
        + len(recon_bullet.splitlines())
    )
    assert total_lines <= 40, (
        f"combined new clauses total {total_lines} lines, budget is 40 — "
        "the subtraction discipline (KD-5) was silently exceeded."
    )


# ---------------------------------------------------------------------------
# Fix-1 (Level-2 iteration) — Dispatch-record durability: dispatcher-side
# review-record convention + reviewer Feature field
# (skills/implement/dispatch-template.md)
#
# Closes four source scar items: task-2 silent_failure #2 (echo-only
# durability, indistinguishable from "no injection happened"), task-3's
# verified:false assumption (no Feature field named in reviewer dispatch —
# planned_task ref resolution falls straight to the repo-wide Glob+Grep
# fallback), task-4's verified:false assumption (no persisted location named
# for drift_items), and task-6 silent_failure #1 (echo proves claimed
# receipt only, never content correctness).
# ---------------------------------------------------------------------------


def _yin_reviewer_block(dispatch: str) -> str:
    return _section(dispatch, "### Yin reviewer", ["\n### Code Quality reviewer"])


def _code_quality_reviewer_block(dispatch: str) -> str:
    # Tightened end marker (round-1 coordinator fix): the old marker
    # ("\n## Review Record Durability") swallowed the two trailing Review
    # Dispatch paragraphs ("Both reviewers must report back...", "After both
    # reviews pass..."), which are not part of the Code Quality reviewer
    # PROMPT BLOCK the helper's name promises. Bounding on the next prose
    # line keeps the span to exactly the dispatch code fence.
    return _section(
        dispatch, "### Code Quality reviewer", ["\nBoth reviewers must report back"]
    )


def _review_record_durability_section(dispatch: str) -> str:
    # No end marker: this is intentionally the LAST section in the file. If
    # a future edit appends further sections after it without updating this
    # helper, the span silently grows to swallow that new content too.
    return _section(dispatch, "## Review Record Durability", [])


def test_death__dispatch_template_has_review_record_durability_section() -> None:
    """Closes task-2 silent_failure #2 / task-6 silent_failure #1: the
    dispatcher-side review-record convention must exist as a named section,
    requiring VERBATIM (not summarized) excerpts of the verdict's key
    sections into `changes/<feature>/review-record.md`, including the
    mode declaration and `drift_items` (this is drift_items' named
    persistence location, closing task-4's assumption). If this section
    disappears, or the verbatim requirement is dropped, this goes RED — the
    convention proven by precedent
    (changes/2026-07-05_issue-002-validate-live-surface/review-record.md)
    would have no durable textual anchor left in the dispatch template."""
    section = _review_record_durability_section(read(DISPATCH_TEMPLATE))
    lowered = section.lower()

    assert "review-record.md" in lowered, (
        "Review Record Durability no longer names "
        "changes/<feature>/review-record.md as the landing artifact."
    )
    assert "verbatim" in lowered, (
        "Review Record Durability no longer requires VERBATIM excerpts — "
        "a summarized excerpt could silently drop or reword content the "
        "convention exists to preserve exactly."
    )
    assert "mode declaration" in lowered, (
        "Review Record Durability no longer names the mode declaration as "
        "one of the required verbatim excerpts."
    )
    assert "drift_items" in section, (
        "Review Record Durability no longer names `drift_items` as part of "
        "what must be excerpted — closing task-4's assumption (no persisted "
        "location named for drift_items) would reopen."
    )
    assert "issue-003" in lowered, (
        "Review Record Durability no longer cross-references ISSUE-003 "
        "(issue.md) — the honest marker disclosing that this convention has "
        "no aggregation-time consumer yet was dropped; a future editor would "
        "have to hunt the scar report to learn the bet."
    )


def test_death__review_record_absent_entry_is_never_recorded_not_nothing_to_record() -> (
    None
):
    """DC-5 pole: an absent review-record entry for a task that ran spec
    mode must be read as "never recorded" (a finding at aggregation time),
    never as "nothing to record" — the same missing-vs-empty discipline this
    feature enforces for drift_items/structural_drift elsewhere must also
    apply to the review-record artifact itself, or the durability convention
    would create a NEW place where "never recorded" is indistinguishable
    from "recorded empty". If this discipline sentence is dropped, this goes
    RED."""
    section = _review_record_durability_section(read(DISPATCH_TEMPLATE))
    lowered = section.lower()

    assert "never recorded" in lowered, (
        "Review Record Durability no longer states that an absent entry "
        "means 'never recorded'."
    )
    assert "nothing to record" in lowered, (
        "Review Record Durability no longer explicitly rules out reading an "
        "absent entry as 'nothing to record' — DC-5's missing-vs-empty "
        "distinction has no textual anchor left for this artifact."
    )
    assert "finding" in lowered, (
        "Review Record Durability no longer states an absent entry is a "
        "finding at aggregation time."
    )


def test_unit__both_reviewer_dispatch_blocks_have_feature_field() -> None:
    """Contract source: skills/implement/dispatch-template.md Yin reviewer
    and Code Quality reviewer prompt blocks (documented artifact shape).
    Closes task-3's verified:false assumption: dispatch-template.md named no
    feature field, so a task whose Changed Files are all outside
    changes/<feature>/ fell straight to the repo-wide Glob+Grep fallback for
    planned_task ref resolution.

    Round-1 (coordinator) fix: yin and quality use the Feature field for
    DIFFERENT purposes — quality resolves `planned_task` refs against
    index.yaml (agents/code-quality-reviewer.md owns that concept); yin has
    NO planned_task/index.yaml concept (agents/code-reviewer.md: zero
    matches) and only uses the path to locate feature artifacts (scar
    reports, review-record.md) for cross-checks. Both blocks must carry
    `## Feature` + `changes/<feature>/`; only quality's block may claim the
    planned_task/index.yaml CLAIM SENTENCE — yin repeating that same claim
    would be a ghost promise.

    Polarity note: yin's differentiated wording explicitly DISCLAIMS
    planned_task/index.yaml ("not for planned_task/index.yaml resolution"),
    so a bare-token 'planned_task'/'index.yaml' absence check on yin_block
    would be polarity-blind (the negation sentence itself contains both
    tokens) — this asserts on the CLAIM SENTENCE presence/absence instead,
    plus the disclaim sentence's presence in yin, matching this file's
    established presence-not-polarity convention."""
    text = read(DISPATCH_TEMPLATE)
    yin_block = _yin_reviewer_block(text)
    quality_block = _code_quality_reviewer_block(text)
    yin_normalized = " ".join(yin_block.split()).lower()
    quality_normalized = " ".join(quality_block.split()).lower()
    claim_sentence = "resolve planned_task evidence refs against this feature's index.yaml"

    for block, label in ((yin_block, "yin"), (quality_block, "code quality")):
        assert "## Feature" in block, (
            f"the {label} reviewer dispatch block has no `## Feature` field."
        )
        assert "changes/<feature>/" in block, (
            f"the {label} reviewer dispatch block's Feature field does not "
            "name the changes/<feature>/ directory."
        )

    assert claim_sentence in quality_normalized, (
        "the code quality reviewer dispatch block's Feature field no longer "
        "tells the quality reviewer to resolve planned_task refs against "
        "this feature's index.yaml."
    )
    assert claim_sentence not in yin_normalized, (
        "the yin reviewer dispatch block claims the SAME planned_task/"
        "index.yaml resolution sentence as quality — agents/code-reviewer.md "
        "has no such concept; this is the ghost promise the differentiation "
        "fix was supposed to remove."
    )
    assert "not for planned_task/index.yaml resolution" in yin_normalized, (
        "the yin reviewer dispatch block no longer explicitly disclaims "
        "planned_task/index.yaml resolution — without this sentence, a "
        "future bare-token check for 'planned_task'/'index.yaml' cannot "
        "reliably distinguish yin's block from quality's, since both "
        "contain the tokens (quality via the claim, yin via the negation)."
    )


def test_death__code_quality_reviewer_names_feature_field_as_first_planned_task_source() -> (
    None
):
    """Closes the quality reviewer's own round-1 Coupling finding: fix-1
    injects a `## Feature` field into the dispatch (change B), but this
    agent definition's planned_task Evidence Resolution procedure never
    named it as an input source — it derived the feature exclusively from a
    `changes/<feature>/...` path in Changed Files/diff, falling straight to
    the repo-wide Glob otherwise. A dispatch whose Changed Files are all
    outside changes/<feature>/ (fix-1 itself is an example) would still hit
    the Glob branch even though the dispatch carried a Feature field.

    Guards the ORDER (not just presence) via index positions: the dispatch's
    `## Feature` field must be checked FIRST, path-derivation SECOND, Glob
    +Grep fallback LAST. If a future edit drops the Feature-field source, or
    reorders it behind the other two, this goes RED."""
    section = _spec_mode_additions_section(read(CODE_QUALITY_REVIEWER))
    clause = _guard_bullet(section, "`planned_task`")

    idx_feature = clause.find("## Feature")
    idx_path = clause.find("changes/<feature>/")
    idx_glob = clause.find("Glob")

    assert idx_feature != -1, (
        "the planned_task resolution bullet no longer names the dispatch's "
        "`## Feature` field as an input source at all."
    )
    assert idx_path != -1 and idx_glob != -1, (
        "the planned_task resolution bullet lost the path-derivation or "
        "Glob+Grep fallback source — this test's premise no longer holds."
    )
    assert idx_feature < idx_path < idx_glob, (
        "the planned_task resolution bullet's source order regressed — the "
        "dispatch's `## Feature` field must be checked FIRST, path-"
        "derivation SECOND, Glob+Grep fallback LAST."
    )


def test_unit__structure_spec_fragments_durability_points_to_review_record_not_echo_only() -> (
    None
):
    """Contract source: skills/implement/dispatch-template.md Structure Spec
    Fragments section's Durability paragraph (documented artifact shape).
    Change C: the paragraph previously said the implementer echo is the
    only durable artifact "Until a dedicated dispatch log exists" — that
    stale claim must be gone, replaced by a pointer to the Review Record
    Durability section as the SINGLE OWNER of the full durability statement.

    Round-1 (coordinator) DRY fix: this paragraph must not restate the full
    content (echo cross-check, claimed-receipt caveat) that Review Record
    Durability already owns — the contract is "points to review-record.md,
    no stale echo-only claim", not duplication of that section's content.
    Deliberately does NOT assert echo/claimed-receipt wording here (that
    content, and its own test coverage, belongs solely to the Review Record
    Durability section — see test_death__dispatch_template_has_review_record_durability_section)."""
    section = _structure_spec_fragments_section(read(DISPATCH_TEMPLATE))
    durability = _section(section, "Durability:", [])
    lowered = durability.lower()

    assert "review-record.md" in lowered, (
        "the Structure Spec Fragments Durability paragraph no longer points "
        "to changes/<feature>/review-record.md as the dispatcher-side "
        "durable artifact."
    )
    assert "review record durability" in lowered, (
        "the Durability paragraph no longer points readers to the Review "
        "Record Durability section by name."
    )
    assert "until a dedicated dispatch log exists" not in lowered, (
        "the Durability paragraph still claims the implementer echo is the "
        "only durable artifact 'until a dedicated dispatch log exists' — "
        "this is the stale echo-only claim the Review Record Durability "
        "section replaces."
    )


# ---------------------------------------------------------------------------
# Fix-2 (Level-2 iteration) — Coordinator-side measured-numbers rule
# (skills/implement/dispatch-template.md ## Rules)
#
# Source scar: task-6 wrote "spec full text 30 lines" into a dispatch prompt
# without measuring (actual 25, `wc -l`) — the wrong number was inherited by
# a reviewer verdict and only caught in review (durable evidence:
# changes/2026-07-05_issue-002-validate-live-surface/review-record.md:10).
# The coordinator has the same measurement obligation as the implementer
# (agents/implementer.md Mandatory Behavior #5); this closes the gap on the
# dispatch-composition side.
# ---------------------------------------------------------------------------


def _dispatch_template_rules_section(dispatch: str) -> str:
    return _section(dispatch, "## Rules", ["\n## Anti-Patterns"])


def test_unit__dispatch_template_rules_require_measuring_numbers_before_writing() -> (
    None
):
    """Contract source: skills/implement/dispatch-template.md ## Rules
    section (documented artifact shape). The Rules list must contain a 6th
    rule requiring quantitative values placed into a dispatch prompt (spec
    line counts, entry counts, test counts) to be measured before being
    written, not estimated — reviewers inherit dispatch numbers into
    verdicts, and an unmeasured estimate can silently become a wrong verdict
    (the "30 vs 25" precedent this fix closes). If the 6th rule is dropped,
    or the measure-before-writing anchor phrase is diluted to a vague
    reminder with no failure-mode link, this goes RED.

    Behavior-preserving-refactor check: renumbering the rules (including
    inserting a new rule that shifts this one's ordinal) or rewording the
    other rules leaves this test green, since it anchors only on the
    measured-numbers rule's own content within the Rules section — never on
    its list position. Behavior-actually-broke check: deleting the rule (or
    its 'measure' anchor) reddens it — this is not a tautological
    presence-of-the-word-Rules check."""
    section = _dispatch_template_rules_section(read(DISPATCH_TEMPLATE))
    lowered = section.lower()

    assert "measure" in lowered, (
        "the Rules section no longer mentions measuring — the "
        "coordinator-side obligation to measure quantitative values before "
        "writing them into a dispatch prompt has no textual anchor left."
    )
    assert "reviewers inherit" in lowered, (
        "the Rules section's measured-numbers rule no longer names WHY it "
        "matters (reviewers inherit dispatch numbers into verdicts) — "
        "without this link, a future editor could soften the rule into a "
        "vague style preference disconnected from the '30 vs 25' precedent."
    )
    assert "never an estimate" in lowered, (
        "the Rules section's measured-numbers rule no longer explicitly "
        "rules out writing an estimate into a dispatch prompt — without "
        "this, 'measure' alone could be read as 'measure when convenient', "
        "not as a hard requirement replacing estimation."
    )
