"""Doc-contract tests for the 1.0.0 global thinking channel (design notes 1-3, 5, 6).

The channel exists to fix the implementer-isolation blind spot: a task-local
slice architecturally forces junior output (structural-honesty task-4 and
ISSUE-001 are the recorded failures). These tests guard the WRITTEN contract —
that the channel's pieces stay present, single-sourced, and correctly wired —
not runtime obedience (doc-presence != runtime obedience; deferred to dogfood).

Guarded contracts:
  C1 pre-thinking owns seam decisions; planning projects cited seams into the
     derived Overview and STOPs back on a missing seam.
  C2 index.yaml template carries the L1/L2 fields (seam / affects / anchors)
     and distinguishes affects (structural, reverse) from depends_on (ordering).
  C3 dispatch copies L1/L2 from planning products, never composes them, and an
     old plan surfaces as an explicit `global_channel: absent`.
  C4 scar schema carries dual-face structural_decisions with the evidence-at-
     decision-time rule and the granularity floor.
  C5 the three agents consume/review the channel (implementer anchors +
     evidence-anchored patterns; quality reviewer reasoning payload +
     arbitration; yin reviewer seam placement dimension).
  C6 research hands pre-thinking a named problem essence + boundary scope.

The tests assert behavioral tokens, not exact prose.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _section(text: str, marker: str) -> str:
    """Return the section starting at `marker` until the next '## ' heading."""
    start = text.find(marker)
    assert start != -1, f"section marker not found: {marker!r}"
    rest = text[start + len(marker) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


# ---------------------------------------------------------------------------
# C1 — planning: seam authority + derived projection + STOP gate
# ---------------------------------------------------------------------------


def test_planning_has_codebase_craft_products_step() -> None:
    planning = read("skills/planning/flow.md")
    section = _section(planning, "## 4. Task Decomposition and Reference Graph")
    lowered = section.lower()
    assert "seam" in lowered
    assert "affects" in lowered
    assert "anchors" in lowered
    assert "planned-change" in lowered, "evidence strengthening tier missing"


def test_planning_missing_seam_stops_back_to_pre_thinking() -> None:
    """A seam pre-thinking did not identify is a design-decision gap: planning
    must STOP and return, never invent the seam locally (ISSUE-001 shape)."""
    section = _section(
        read("skills/planning/flow.md"),
        "## 4. Task Decomposition and Reference Graph",
    )
    assert "STOP" in section
    assert "samsara:pre-thinking" in section
    lowered = section.lower()
    assert "do not invent" in lowered or "not invent a new seam" in lowered


def test_planning_affects_is_not_depends_on() -> None:
    section = _section(
        read("skills/planning/flow.md"),
        "## 4. Task Decomposition and Reference Graph",
    )
    lowered = section.lower()
    # both relations named, with the structural-vs-ordering distinction
    assert "depends_on" in lowered
    assert "ordering" in lowered
    assert "structural" in lowered
    assert "noise" in lowered, "the ordering-restated-as-needs noise rule is gone"


def test_planning_volume_discipline_is_consumption_not_line_count() -> None:
    """A hard line-count gate trains gaming the number (KD-5 lesson) — the
    written discipline must be consumption-driven and soft."""
    section = _section(
        read("skills/planning/flow.md"),
        "## 4. Task Decomposition and Reference Graph",
    )
    lowered = section.lower()
    assert "consumption" in lowered
    assert "over-projection" in lowered
    assert "forced_by" in section, "consumption must be traced via forced_by citations"


def test_planning_format_validation_section_wired() -> None:
    planning = read("skills/planning/flow.md")
    section = _section(planning, "## 6. Format Validation")
    assert "validate_format.py" in section
    lowered = section.lower()
    assert "judgment" in lowered, "format/judgment split must be stated at the gate"
    assert "visible missing" in lowered, "silent skip must convert to visible missing"


def test_planning_validator_script_exists() -> None:
    assert (ROOT / "skills/planning/scripts/validate_format.py").is_file()


def test_implement_validator_script_exists() -> None:
    assert (ROOT / "skills/implement/scripts/validate_format.py").is_file()


# ---------------------------------------------------------------------------
# C2 — templates: index.yaml fields + overview single source
# ---------------------------------------------------------------------------


def test_index_template_carries_channel_fields() -> None:
    index = read("skills/planning/templates/index.yaml")
    assert "seam:" in index
    assert "affects:" in index
    assert "anchors:" in index
    assert "depends_on:" in index


def test_index_template_upstream_contract_is_live_interface_anchor() -> None:
    """F3 decision: upstream contracts travel as anchors to LIVE interface
    files of depended-on tasks, never as a prose summary that drifts."""
    index = read("skills/planning/templates/index.yaml").lower()
    assert "interface" in index
    assert "live" in index
    assert "whitelist" in index, "anchors must be marked starting-set-not-whitelist"


def test_overview_template_projects_cited_real_seams() -> None:
    overview = read("skills/planning/templates/overview.md")
    assert "## Real Seams Projection" in overview
    lowered = overview.lower()
    assert "derived implementation projection" in lowered
    assert "source_ref" in overview
    assert "single source of seam declarations" not in lowered
    assert "core identity" in lowered
    assert "pre-thinking" in lowered, "seam content must be cited from pre-thinking"
    assert "evidence" in lowered, "seam declarations must carry an evidence tier"


# ---------------------------------------------------------------------------
# C3 — dispatch: copy never compose, absence visible
# ---------------------------------------------------------------------------


def test_dispatch_has_four_layer_channel_section() -> None:
    dispatch = read("skills/implement/dispatch-template.md")
    section = _section(dispatch, "## Global Thinking Channel")
    for token in ("L1", "L2", "L3", "L4"):
        assert token in section, f"channel layer {token} missing"
    lowered = section.lower()
    assert "push" in lowered and "pull" in lowered


def test_dispatch_copies_l1_l2_never_composes() -> None:
    dispatch = read("skills/implement/dispatch-template.md")
    section = _section(dispatch, "## Global Thinking Channel")
    lowered = section.lower()
    assert "never" in lowered and ("compose" in lowered or "invent" in lowered), (
        "the copy-never-compose rule is the piece that replaces the hand-curation "
        "blind spot; without it dispatch reverts to improvised projections"
    )
    assert "global_channel: absent" in dispatch, (
        "plans predating the channel must surface as an explicit absence marker, "
        "never a silent omission"
    )


def test_dispatch_prompt_carries_l1_l2_sections() -> None:
    dispatch = read("skills/implement/dispatch-template.md")
    assert "## Global Position (L1)" in dispatch
    assert "## Context Projection (L2)" in dispatch


def test_implement_skill_arbitration_path_present() -> None:
    """F6: a reviewer block must stay arguable — third-party arbitration
    (human / auto-gatekeeper), never reviewer-auto-wins or self-exemption."""
    skill = read("skills/implement/SKILL.md")
    assert "samsara:auto-gatekeeper" in skill
    lowered = skill.lower()
    assert "arbitrat" in lowered  # arbitration / arbitrates / arbiter (stem)
    assert "auto-wins" in lowered or "auto wins" in lowered
    assert "self-exempt" in lowered


def test_implement_skill_runs_scar_validator_before_commit() -> None:
    skill = read("skills/implement/SKILL.md")
    section = _section(skill, "### After all tasks complete")
    assert "validate_format.py" in section
    idx_validate = section.find("validate_format.py")
    idx_commit = section.lower().rfind("commit all changes")
    assert idx_validate != -1 and idx_commit != -1 and idx_validate < idx_commit, (
        "the scar-report format validator must run BEFORE the commit step"
    )


# ---------------------------------------------------------------------------
# C4 — scar schema: dual-face structural decisions
# ---------------------------------------------------------------------------


def test_scar_schema_structural_decisions_dual_face() -> None:
    schema = read("skills/implement/templates/scar-schema.yaml")
    assert "structural_decisions:" in schema
    for field in (
        "decision:",
        "serves_seam:",
        "forced_by:",
        "refused:",
        "risk_if_wrong:",
    ):
        assert field in schema, f"dual-face field missing from schema: {field}"


def test_scar_schema_forced_by_evidence_at_decision_time() -> None:
    """Rule 17: forced_by cites only evidence that existed at decision time —
    the anti-post-hoc-rationalization defense."""
    schema = read("skills/implement/templates/scar-schema.yaml").lower()
    assert "existed at decision time" in schema
    assert "post-hoc" in schema


def test_scar_schema_granularity_floor() -> None:
    """Rule 15: only structural bets earn an entry; function splitting and
    naming sit below the floor. Empty list valid, missing key distinct."""
    schema = read("skills/implement/templates/scar-schema.yaml").lower()
    assert "granularity floor" in schema
    assert "structural bet" in schema
    assert "structural_decisions: []" in schema, (
        "the empty-list-vs-missing-key distinction must be spelled out"
    )


# ---------------------------------------------------------------------------
# C5 — agents consume/review the channel
# ---------------------------------------------------------------------------


def test_implementer_consumes_channel_with_evidence_anchored_patterns() -> None:
    agent = read("agents/implementer.md")
    section = _section(agent, "## Global Thinking Channel")
    lowered = section.lower()
    assert "affects" in lowered
    assert "anchors" in lowered
    assert "imagination" in lowered, (
        "the staff/junior line — planned change legitimate, imagination "
        "prohibited — must be written where patterns are chosen"
    )
    # the license boundary: affects marks the joint, never builds the future now
    assert "never authorizes" in lowered or "not authorize" in lowered


def test_implementer_anchors_feed_read_before_write_order_intact() -> None:
    """Anchors upgrade the existing read-neighbors discipline; the ordering
    contract (read before death tests) must survive the upgrade."""
    agent = read("agents/implementer.md")
    start = agent.lower().find("## execution order")
    assert start != -1
    section = agent.lower()[start:]
    end = section.find("\n## ", 1)
    section = section if end == -1 else section[:end]
    read_idx = section.find("read before you write")
    anchor_idx = section.find("anchor")
    death_idx = section.find("write death tests")
    assert anchor_idx != -1, "L2 anchors not wired into the read-before-write step"
    assert -1 < read_idx < death_idx, "read-before-write must still precede death tests"


def test_implementer_scar_section_requires_dual_face_entries() -> None:
    agent = read("agents/implementer.md")
    section = _section(agent, "## Scar Report")
    lowered = section.lower()
    assert "structural_decisions" in section
    assert "yang" in lowered and "yin" in lowered
    assert (
        "existed when you decided" in lowered or "existed at decision time" in lowered
    )


def test_quality_reviewer_structural_decision_lane() -> None:
    agent = read("agents/code-quality-reviewer.md")
    section = _section(agent, "## Structural Decision Review")
    lowered = section.lower()
    assert "forced_by" in section
    assert "relevance" in lowered, (
        "mechanical resolution belongs to validators; the reviewer's lane is "
        "whether a resolvable citation genuinely forces the decision"
    )
    assert "speculative" in lowered
    assert "payload is the reasoning" in lowered
    assert "review-record" in lowered, "reasoning must be durable, not conversational"


def test_quality_reviewer_block_is_argument_not_gate() -> None:
    agent = read("agents/code-quality-reviewer.md").lower()
    assert "auto-gatekeeper" in agent
    assert "not auto-win" in agent or "do not auto-win" in agent


def test_yin_reviewer_seam_placement_dimension() -> None:
    agent = read("agents/code-reviewer.md")
    lowered = agent.lower()
    assert "seam placement" in lowered
    # format/judgment split: resolution is the validator's, truth is yin's
    assert "format" in lowered and "judgment" in lowered
    assert "global_channel: absent" in agent, (
        "old plans must be classifiable as out-of-scope, not silently passed"
    )


# ---------------------------------------------------------------------------
# C6 — research hands pre-thinking a named essence + boundary scope
# ---------------------------------------------------------------------------


def test_research_problem_essence_is_named_product() -> None:
    skill = read("skills/research/SKILL.md")
    assert "Problem Essence" in skill
    assert "named handoff to pre-thinking" in skill
    kickoff = read("skills/research/templates/kickoff.md")
    assert "## Problem Essence" in kickoff
    assert "## Boundary Scope" in kickoff


def test_research_boundary_scope_three_lists() -> None:
    kickoff = read("skills/research/templates/kickoff.md")
    for token in ("What must be solved", "Areas involved", "Not solved now"):
        assert token in kickoff, f"boundary-scope list missing: {token}"
