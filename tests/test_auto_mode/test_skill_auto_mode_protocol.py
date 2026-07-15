"""
Contract-bound unit tests for Task 4 (Auto Mode Gate 去重).

Unit Test Contract sources (see task-4.md "Unit Test Contract"):
  - references/auto-mode.md's "## Stage Gate Protocol" section: documented
    artifact shape for the dispatch mechanism, append-before-continue rule,
    and the canonical meaning of proceed/revise/reject/accept_gap.
  - each SKILL.md's "## Auto Mode Gate" section: documented pointer
    structure — (1) a pointer to references/auto-mode.md Stage Gate
    Protocol, (2) this stage's workflow_prompt source, (3) this stage's
    decision-point list, (4) stage-specific inline behavior that does not
    reduce to the canonical protocol.

Every assertion below is a concept-token check: a behavior-preserving
refactor (rename the "Stage Gate Protocol" heading's surrounding prose,
reorder unrelated bullets) keeps every assertion green; the CONCEPT
disappearing (not the exact heading string) turns the matching assertion
red. Line-count assertions bound the formal pointer-length budget the task
sets (see task-4.md Key Decisions: "≤8 行" formal cap, larger stages record
their overage rationale in the scar report, not in these tests).
"""

from tests.test_auto_mode.test_protocol_helpers import (
    AUTO_MODE_REFERENCE,
    ALL_WORKFLOW_SKILLS,
    BOOTSTRAP,
    EARLY_STAGE_SKILLS,
    ITERATION_FLOW,
    LATER_STAGE_SKILLS,
    PLANNING_FLOW,
    PRE_THINKING_FLOW,
    REQUIRED_WORKFLOW_STAGES,
    read,
    section,
)


def _content_line_count(section_text: str) -> int:
    """Number of non-blank lines in a section body (heading line itself is
    not part of `section()`'s returned tail)."""
    return len([line for line in section_text.splitlines() if line.strip()])


class TestResearchExecutionModeProtocol:
    def test_research_declares_two_execution_modes(self):
        mode_section = section(
            read(EARLY_STAGE_SKILLS["research"]),
            "Step 0: Execution Mode Selection",
        )
        normalized = mode_section.lower()

        assert "`human-in-the-loop`" in mode_section
        assert "`auto`" in mode_section
        assert "default" in normalized
        assert "workflow-run" in mode_section
        assert "Execution mode:" in mode_section
        assert "Execution mode? Choose `human-in-the-loop` or `auto`." in mode_section
        assert "1-kickoff.md" in mode_section


class TestStageGateProtocolCanonicalContract:
    """Contract source: references/auto-mode.md's Stage Gate Protocol
    section is the SOLE documented home for dispatch mechanism,
    append-before-continue, and decision-value semantics."""

    def _protocol(self) -> str:
        return section(read(AUTO_MODE_REFERENCE), "Stage Gate Protocol")

    def test_protocol_names_dispatch_mechanism(self):
        protocol = self._protocol()
        assert "samsara:auto-gatekeeper" in protocol
        assert 'subagent_type: "samsara:auto-gatekeeper"' in protocol

    def test_protocol_requires_append_before_continue(self):
        protocol = self._protocol()
        assert "auto-decisions.md" in protocol
        assert "append-only" in protocol
        assert "before" in protocol

    def test_protocol_references_required_fields_instead_of_restating_them(self):
        """The protocol must point at the Decision Log Contract / Required
        Fields / Entry Template sections above it, not re-declare the field
        list — the field list has exactly one home (Required Fields)."""
        protocol = self._protocol()
        assert "Entry Shape" in protocol or "Decision Log Contract" in protocol

    def test_protocol_defines_all_four_decision_values_with_meaning(self):
        protocol = self._protocol()
        for value in ("`proceed`", "`revise`", "`reject`", "`accept_gap`"):
            assert value in protocol

    def test_protocol_notes_stages_may_narrow_a_decision_value(self):
        """Contract source: the protocol must acknowledge stage-specific
        narrowing (e.g. validate-and-ship's Step 0 forbidding accept_gap)
        stays inline in that skill, not folded into canonical text."""
        protocol = self._protocol()
        assert "narrow" in protocol.lower()


class TestWorkflowSkillPointerStructure:
    """Contract source: each SKILL.md's Auto Mode Gate section pointer
    structure — (1) points at canonical, (2) names workflow_prompt source,
    (3) names decision points covered."""

    def test_every_stage_points_at_canonical_stage_gate_protocol(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            assert "references/auto-mode.md" in auto_section, stage
            assert "Stage Gate Protocol" in auto_section, stage

    def test_every_stage_names_its_workflow_prompt_source(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            assert "workflow_prompt" in auto_section, stage

    def test_every_stage_names_its_decision_points(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            assert "Decision points" in auto_section, stage

    def test_execution_mode_trigger_is_canonical_not_restated_per_skill(self):
        """The `Execution mode: auto` trigger condition lives ONCE in the
        canonical Dispatch clause (see TestStageGateProtocolCanonicalContract);
        repeating it in every skill's pointer section is exactly the kind of
        boilerplate this task removes, so it is intentionally NOT asserted
        per-skill here."""
        protocol = section(read(AUTO_MODE_REFERENCE), "Stage Gate Protocol")
        assert "Execution mode: auto" in protocol


class TestStageSpecificInlineBehaviorPreserved:
    """Contract source: documented artifact shape for the 3 stages with
    genuine stage-specific gate behavior that must not be absorbed by
    the dedup (task-4.md Key Decisions)."""

    def test_implement_names_execution_strategy_and_completion_prompts(self):
        auto_section = section(read(LATER_STAGE_SKILLS["implement"]), "Auto Mode Gate")
        assert "implementation strategy selection" in auto_section
        assert "implementation.strategy" in auto_section
        assert "Subagent parallel" in auto_section
        assert "Inline sequential" in auto_section

    def test_iteration_names_all_decision_points_it_covers(self):
        auto_section = section(read(LATER_STAGE_SKILLS["iteration"]), "Auto Mode Gate")
        for term in (
            "triage",
            "blocked-fix handling",
            "round continuation",
            "safety valve",
        ):
            assert term in auto_section

    def test_validate_and_ship_keeps_step0_overrides_and_double_trace_check(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )
        for term in (
            "empty diff",
            "base branch",
            "no built-in security review capability",
            "unknown result",
            "accepted risk",
            "prior gate entries",
            "after the Gatekeeper appends the final validation decision",
        ):
            assert term in auto_section


class TestPointerLineBudget:
    """Contract source: line-count budget named in task-4.md Key Decisions
    ("≤8 行" formal cap, larger stages allowed with recorded rationale).
    Asserts the pointer SHRANK to a bounded size, not an exact count — a
    regression back toward full per-skill boilerplate duplication (the
    dedup's own death case) must overflow the budget and go red."""

    # Budgets = post-dedup actual + 1 line of slack (re-tightened after the
    # review round removed the pseudo-specific `reject` residue from 5 skills).
    # Raising a budget requires naming the NEW stage-specific behavior that
    # justifies it — headroom is not free space to grow prose back into.
    _BUDGETS = {
        "research": 12,
        "planning": 12,
        "pre-thinking": 16,
        "implement": 18,
        "iteration": 19,
        "validate-and-ship": 49,
    }

    def test_each_stage_auto_gate_section_stays_within_its_line_budget(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            line_count = _content_line_count(auto_section)
            budget = self._BUDGETS[stage]
            assert line_count <= budget, (
                f"{stage}'s Auto Mode Gate section has {line_count} content "
                f"lines, over its {budget}-line budget — this smells like "
                "duplicated boilerplate growing back instead of a pointer."
            )


class TestPrimaryEvaluatorProtocol:
    def test_workflow_decision_points_declare_human_and_auto_paths(self):
        decision_sections = {
            "research transition": (EARLY_STAGE_SKILLS["research"], "Transition"),
            "pre-thinking gap questions": (
                PRE_THINKING_FLOW,
                "Execution Mode Routing",
            ),
            "pre-thinking evaluation contract": (
                PRE_THINKING_FLOW,
                "Execution Mode Routing",
            ),
            "pre-thinking commitment": (
                PRE_THINKING_FLOW,
                "Execution Mode Routing",
            ),
            "planning transition": (PLANNING_FLOW, "7. Transition"),
            "implement execution strategy": (
                LATER_STAGE_SKILLS["implement"],
                "Execution Strategy Selection",
            ),
            "iteration entry triage": (
                ITERATION_FLOW,
                "Entry Triage",
            ),
            "iteration triage": (
                ITERATION_FLOW,
                "Step 2: Triage (Execution-Mode Gate)",
            ),
            "iteration fix handling": (
                ITERATION_FLOW,
                "Step 3: Fix (Per-Fix Commit)",
            ),
            "iteration round gate": (
                ITERATION_FLOW,
                "Step 4: Round Check + Safety Valve",
            ),
            "security step0 gate": (
                LATER_STAGE_SKILLS["validate-and-ship"],
                "Step 0: Security & Privacy Gate（STOP）",
            ),
            "validation transition": (
                LATER_STAGE_SKILLS["validate-and-ship"],
                "Transition",
            ),
        }

        for label, (path, heading) in decision_sections.items():
            decision_section = " ".join(section(read(path), heading).split())
            assert "`Execution mode: human-in-the-loop`" in decision_section, label
            assert "`Execution mode: auto`" in decision_section, label
            assert "do not ask the user" in decision_section, label
            assert "samsara:auto-gatekeeper" in decision_section, label

    def test_primary_evaluator_stage_set_is_complete(self):
        assert set(ALL_WORKFLOW_SKILLS) == REQUIRED_WORKFLOW_STAGES

    def test_primary_evaluator_stages_all_point_at_canonical_protocol(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            assert "references/auto-mode.md" in auto_section, stage
            assert "Stage Gate Protocol" in auto_section, stage

    def test_source_skills_do_not_use_converted_gatekeeper_name(self):
        checked_paths = [BOOTSTRAP, *ALL_WORKFLOW_SKILLS.values()]
        for path in checked_paths:
            assert "samsara-auto-gatekeeper" not in read(path), path
