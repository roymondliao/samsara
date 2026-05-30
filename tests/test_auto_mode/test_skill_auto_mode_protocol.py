from tests.test_auto_mode.test_protocol_helpers import (
    BOOTSTRAP,
    ALL_WORKFLOW_SKILLS,
    EARLY_STAGE_SKILLS,
    LATER_STAGE_SKILLS,
    REQUIRED_WORKFLOW_STAGES,
    read,
    section,
)


class TestBootstrapExecutionModeProtocol:
    def test_bootstrap_declares_two_execution_modes(self):
        mode_section = section(read(BOOTSTRAP), "Execution Mode Selection")

        assert "`human-in-the-loop`" in mode_section
        assert "`auto`" in mode_section
        assert "Default" in mode_section
        assert "session-level" in mode_section
        assert "Execution mode:" in mode_section
        assert "Execution mode? Choose `human-in-the-loop` or `auto`." in mode_section
        assert 'subagent_type: "samsara:auto-gatekeeper"' in mode_section


class TestEarlyWorkflowAutoGateProtocol:
    def test_each_early_stage_has_gatekeeper_decision_contract(self):
        for path in EARLY_STAGE_SKILLS.values():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "samsara:auto-gatekeeper" in auto_section
            assert 'subagent_type: "samsara:auto-gatekeeper"' in auto_section
            assert "changes/<feature>/auto-decisions.md" in auto_section
            assert "workflow_prompt" in auto_section
            assert "gatekeeper_answer" in auto_section

    def test_each_early_stage_follows_recorded_decision(self):
        for path in EARLY_STAGE_SKILLS.values():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "`proceed`" in auto_section
            assert "`revise`" in auto_section
            assert "`reject`" in auto_section
            assert "`accept_gap`" in auto_section
            assert "follow the recorded decision" in auto_section


class TestLaterWorkflowAutoGateProtocol:
    def test_each_later_stage_has_gatekeeper_decision_contract(self):
        for path in LATER_STAGE_SKILLS.values():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "samsara:auto-gatekeeper" in auto_section
            assert 'subagent_type: "samsara:auto-gatekeeper"' in auto_section
            assert "changes/<feature>/auto-decisions.md" in auto_section
            assert "workflow_prompt" in auto_section
            assert "gatekeeper_answer" in auto_section

    def test_each_workflow_stage_reads_explicit_execution_mode(self):
        for path in ALL_WORKFLOW_SKILLS.values():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "Execution mode: auto" in auto_section

    def test_security_and_validation_have_stage_specific_guards(self):
        security_section = section(
            read(LATER_STAGE_SKILLS["security-privacy-review"]), "Auto Mode Gate"
        )
        validation_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "high-uncertainty `reject`" in security_section
        assert "must not transition to validate-and-ship" in security_section
        assert "auto-decisions.md" in validation_section
        assert "must fail validation" in validation_section
        assert "after appending the final validation decision" in validation_section


class TestPrimaryEvaluatorProtocol:
    def test_workflow_decision_points_declare_human_and_auto_paths(self):
        decision_sections = {
            "research transition": (EARLY_STAGE_SKILLS["research"], "Transition"),
            "pre-thinking gap questions": (
                EARLY_STAGE_SKILLS["pre-thinking"],
                "Step B — Question Groups",
            ),
            "pre-thinking evaluation contract": (
                EARLY_STAGE_SKILLS["pre-thinking"],
                "Evaluation Contract",
            ),
            "pre-thinking commitment": (
                EARLY_STAGE_SKILLS["pre-thinking"],
                "Step C — Commitment",
            ),
            "planning transition": (EARLY_STAGE_SKILLS["planning"], "Transition"),
            "implement execution mode": (
                LATER_STAGE_SKILLS["implement"],
                "Execution Mode Selection",
            ),
            "implement transition": (LATER_STAGE_SKILLS["implement"], "Transition"),
            "iteration triage": (
                LATER_STAGE_SKILLS["iteration"],
                "Step 2: Triage (Human Gate)",
            ),
            "iteration fix handling": (
                LATER_STAGE_SKILLS["iteration"],
                "Step 3: Fix (Per-Fix Commit)",
            ),
            "iteration round gate": (
                LATER_STAGE_SKILLS["iteration"],
                "Step 4: Round Check + Safety Valve",
            ),
            "security entry": (
                LATER_STAGE_SKILLS["security-privacy-review"],
                "Entry: Compute Diff",
            ),
            "security capability": (
                LATER_STAGE_SKILLS["security-privacy-review"],
                "Step 1: Security & Privacy Review",
            ),
            "security result handling": (
                LATER_STAGE_SKILLS["security-privacy-review"],
                "Step 2: Result Handling",
            ),
            "security fix loop": (
                LATER_STAGE_SKILLS["security-privacy-review"],
                "Step 3: Fix Loop",
            ),
            "security transition": (
                LATER_STAGE_SKILLS["security-privacy-review"],
                "Transition",
            ),
            "validation transition": (
                LATER_STAGE_SKILLS["validate-and-ship"],
                "Transition",
            ),
        }

        for label, (path, heading) in decision_sections.items():
            decision_section = section(read(path), heading)
            assert "`Execution mode: human-in-the-loop`" in decision_section, label
            assert "`Execution mode: auto`" in decision_section, label
            assert "do not ask the user" in decision_section, label
            assert "samsara:auto-gatekeeper" in decision_section, label

    def test_primary_evaluator_stage_set_is_complete(self):
        assert set(ALL_WORKFLOW_SKILLS) == REQUIRED_WORKFLOW_STAGES

    def test_primary_evaluator_requires_auto_decisions_for_all_stages(self):
        for stage, path in ALL_WORKFLOW_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")
            assert "auto-decisions.md" in auto_section, stage
            assert "samsara:auto-gatekeeper" in auto_section, stage
            assert 'subagent_type: "samsara:auto-gatekeeper"' in auto_section, stage

    def test_source_skills_do_not_use_converted_gatekeeper_name(self):
        checked_paths = [BOOTSTRAP, *ALL_WORKFLOW_SKILLS.values()]
        for path in checked_paths:
            assert "samsara-auto-gatekeeper" not in read(path), path
