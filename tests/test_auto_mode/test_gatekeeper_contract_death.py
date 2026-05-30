from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTO_MODE_REFERENCE = ROOT / "references" / "auto-mode.md"
AUTO_GATEKEEPER = ROOT / "agents" / "auto-gatekeeper.md"

REQUIRED_DECISION_FIELDS = (
    "decision_id",
    "stage",
    "prompt_type",
    "workflow_prompt",
    "gatekeeper_answer",
    "decision",
    "rationale",
    "principles_used",
    "architecture_considerations",
    "evidence_checked",
    "uncertainty",
    "consequences",
    "timestamp",
)


class TestAutoModeDecisionProtocolDeath:
    def test_reference_protocol_exists_before_gatekeeper_can_be_used(self):
        assert AUTO_MODE_REFERENCE.exists(), (
            "SILENT FAILURE [AUTO-DECISION-1]: auto mode has no reusable "
            "decision protocol. Gatekeepers could produce plausible approvals "
            "without an auditable append-only contract."
        )

    def test_reference_protocol_requires_append_only_decision_log(self):
        text = AUTO_MODE_REFERENCE.read_text(encoding="utf-8")

        required_terms = (
            "append-only",
            "auto-decisions.md",
            "must not edit",
            "superseded decision",
        )
        for term in required_terms:
            assert term in text, (
                "SILENT FAILURE [AUTO-DECISION-2]: auto decision records can be "
                f"rewritten or summarized because the protocol does not require {term!r}."
            )

    def test_reference_protocol_requires_auditable_decision_fields(self):
        text = AUTO_MODE_REFERENCE.read_text(encoding="utf-8")

        missing = [field for field in REQUIRED_DECISION_FIELDS if field not in text]
        assert not missing, (
            "SILENT FAILURE [AUTO-DECISION-3]: auto decision records are missing "
            f"required audit fields: {missing}. A generic approval could look complete."
        )

    def test_reference_protocol_forces_question_specific_answers(self):
        text = AUTO_MODE_REFERENCE.read_text(encoding="utf-8")

        assert "original workflow prompt" in text
        assert "question-specific" in text
        assert "generic approval" in text


class TestAutoGatekeeperContractDeath:
    def test_gatekeeper_agent_exists(self):
        assert AUTO_GATEKEEPER.exists(), (
            "SILENT FAILURE [AUTO-GATEKEEPER-1]: workflow skills can dispatch "
            "samsara:auto-gatekeeper but no source agent exists for conversion."
        )

    def test_gatekeeper_cannot_request_human_input_after_auto_starts(self):
        text = AUTO_GATEKEEPER.read_text(encoding="utf-8")

        prohibited_phrases = (
            "request_user_input",
            "AskUserQuestion",
            "ask the user for help",
            "fall back to human",
            "fallback to human",
        )
        found = [phrase for phrase in prohibited_phrases if phrase in text]
        assert not found, (
            "SILENT FAILURE [AUTO-GATEKEEPER-2]: auto mode can secretly become "
            f"human-in-the-loop through these instructions: {found}"
        )

    def test_gatekeeper_must_write_auto_decisions_before_continuing(self):
        text = AUTO_GATEKEEPER.read_text(encoding="utf-8")

        assert "auto-decisions.md" in text
        assert "before continuing" in text
        assert "workflow_prompt" in text
        assert "gatekeeper_answer" in text

    def test_gatekeeper_records_revise_without_mutating_artifacts(self):
        text = AUTO_GATEKEEPER.read_text(encoding="utf-8")

        assert "owning workflow or main agent must change" in text
        assert "Do not implement tasks." in text
