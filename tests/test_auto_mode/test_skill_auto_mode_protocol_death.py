from tests.test_auto_mode.test_protocol_helpers import (
    BOOTSTRAP,
    EARLY_STAGE_SKILLS,
    REQUIRED_WORKFLOW_STAGES,
    LATER_STAGE_SKILLS,
    read,
    section,
)


class TestBootstrapExecutionModeDeath:
    def test_bootstrap_requires_session_mode_selection_before_research(self):
        text = read(BOOTSTRAP)
        mode_section = section(text, "Execution Mode Selection")

        required = (
            "before invoking `samsara:research`",
            "`human-in-the-loop`",
            "`auto`",
            "default",
            "Execution mode:",
            "ask the user to choose",
            "Execution mode? Choose `human-in-the-loop` or `auto`.",
        )
        for term in required:
            assert term in mode_section, (
                "SILENT FAILURE [AUTO-MODE-1]: bootstrap can enter research "
                f"without an explicit execution mode contract. Missing {term!r}."
            )

    def test_bootstrap_marks_persistent_config_out_of_scope(self):
        text = read(BOOTSTRAP)
        mode_section = section(text, "Execution Mode Selection")

        assert "persistent config" in mode_section
        assert "out of scope" in mode_section


class TestEarlyWorkflowAutoGateDeath:
    def test_early_stage_auto_gates_dispatch_gatekeeper(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "samsara:auto-gatekeeper" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-2]: "
                f"{stage} can transition in auto mode without the gatekeeper."
            )
            assert 'subagent_type: "samsara:auto-gatekeeper"' in auto_section, (
                "SILENT FAILURE [AUTO-MODE-2B]: "
                f"{stage} names the gatekeeper without an explicit source subagent dispatch target."
            )
            assert "auto-decisions.md" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-3]: "
                f"{stage} can transition without an audit record."
            )

    def test_early_stage_auto_gates_require_append_only_prompt_answer_log(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            required = (
                "append-only",
                "workflow_prompt",
                "gatekeeper_answer",
                "prompt_type",
                "before continuing",
            )
            missing = [term for term in required if term not in auto_section]
            assert not missing, (
                "SILENT FAILURE [AUTO-MODE-4]: "
                f"{stage} auto gate omits required decision-log terms: {missing}."
            )

    def test_early_stage_auto_gates_do_not_pause_for_human_confirmation(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            prohibited = (
                "AskUserQuestion",
                "request_user_input",
                "human confirmation",
                "user confirmation",
            )
            found = [term for term in prohibited if term in auto_section]
            assert not found, (
                "SILENT FAILURE [AUTO-MODE-5]: "
                f"{stage} auto gate can still pause for human input: {found}."
            )


class TestLaterWorkflowAutoGateDeath:
    def test_later_stage_auto_gates_dispatch_gatekeeper(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "samsara:auto-gatekeeper" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-6]: "
                f"{stage} can transition in auto mode without the gatekeeper."
            )
            assert 'subagent_type: "samsara:auto-gatekeeper"' in auto_section, (
                "SILENT FAILURE [AUTO-MODE-6B]: "
                f"{stage} names the gatekeeper without an explicit source subagent dispatch target."
            )
            assert "auto-decisions.md" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-7]: "
                f"{stage} can transition without an audit record."
            )

    def test_later_stage_auto_gates_preserve_original_prompt(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "workflow_prompt" in auto_section
            assert "gatekeeper_answer" in auto_section
            assert "append-only" in auto_section
            assert "before continuing" in auto_section

    def test_later_stage_auto_gates_do_not_pause_for_human_confirmation(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            prohibited = (
                "AskUserQuestion",
                "request_user_input",
                "human confirmation",
                "user confirmation",
                "human accept",
                "human accepted",
            )
            found = [term for term in prohibited if term in auto_section]
            assert not found, (
                "SILENT FAILURE [AUTO-MODE-8]: "
                f"{stage} auto gate can still pause for human input: {found}."
            )

    def test_security_unknown_records_high_uncertainty_reject(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["security-privacy-review"]), "Auto Mode Gate"
        )

        assert "high-uncertainty `reject`" in auto_section
        assert "unknown" in auto_section
        assert "must not transition to validate-and-ship" in auto_section

    def test_validate_and_ship_checks_auto_decisions_before_completion(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "auto-decisions.md" in auto_section
        assert "completion" in auto_section
        assert "must fail validation" in auto_section

    def test_implement_auto_gate_covers_execution_mode_selection(self):
        auto_section = section(read(LATER_STAGE_SKILLS["implement"]), "Auto Mode Gate")

        assert "implementation execution-mode selection" in auto_section
        assert "Subagent parallel" in auto_section
        assert "Inline sequential" in auto_section

    def test_iteration_auto_gate_covers_internal_decision_points(self):
        auto_section = section(read(LATER_STAGE_SKILLS["iteration"]), "Auto Mode Gate")

        for term in (
            "triage",
            "blocked-fix handling",
            "round continuation",
            "safety valve",
        ):
            assert term in auto_section

    def test_security_auto_gate_overrides_internal_human_fallbacks(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["security-privacy-review"]), "Auto Mode Gate"
        )

        for term in (
            "empty diff",
            "base branch",
            "no built-in security review capability",
            "unknown result",
            "accepted risk",
        ):
            assert term in auto_section

    def test_validation_auto_gate_checks_trace_after_final_append(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "prior gate entries" in auto_section
        assert "after appending the final validation decision" in auto_section


class TestPrimaryEvaluatorCoverageDeath:
    def test_auto_mode_evaluator_covers_every_required_workflow_stage(self):
        covered = set(EARLY_STAGE_SKILLS) | set(LATER_STAGE_SKILLS)

        assert covered == REQUIRED_WORKFLOW_STAGES, (
            "SILENT FAILURE [AUTO-EVALUATOR-1]: primary evaluator stage list drifted. "
            f"Missing: {sorted(REQUIRED_WORKFLOW_STAGES - covered)}; "
            f"Extra: {sorted(covered - REQUIRED_WORKFLOW_STAGES)}"
        )
