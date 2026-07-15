from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTO_MODE_REFERENCE = ROOT / "references" / "auto-mode.md"
AUTO_GATEKEEPER = ROOT / "agents" / "auto-gatekeeper.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestAutoModeReferenceContract:
    def test_reference_names_decisions_and_machine_actions(self):
        text = read(AUTO_MODE_REFERENCE)

        for action in ("proceed", "revise", "reject", "accept_gap"):
            assert action in text

        for action_type in ("continue", "revise_and_rerun", "stop"):
            assert action_type in text

    def test_reference_contains_copyable_decision_entry_template(self):
        text = read(AUTO_MODE_REFERENCE)

        assert "## decision-001" in text
        for field in (
            "schema_version:",
            "decision_id:",
            "gate_id:",
            "workflow_prompt:",
            "answer:",
            "decision:",
            "reason:",
            "evidence_refs:",
            "next_action:",
            "gap:",
            "supersedes:",
        ):
            assert field in text

    def test_reference_treats_generic_approval_as_invalid(self):
        text = read(AUTO_MODE_REFERENCE)

        assert "generic approval" in text
        assert "invalid" in text
        assert "question-specific" in text


class TestAutoGatekeeperAgentContract:
    def test_gatekeeper_has_source_frontmatter(self):
        text = read(AUTO_GATEKEEPER)

        assert text.startswith("---\n")
        assert "name: auto-gatekeeper" in text
        assert "description:" in text

    def test_gatekeeper_defines_principle_level_authority(self):
        text = " ".join(read(AUTO_GATEKEEPER).split())

        required_phrases = (
            "project prior knowledge",
            "principle-level reasoning",
            "problem insight",
            "system architecture judgment",
        )
        for phrase in required_phrases:
            assert phrase in text

    def test_gatekeeper_requires_append_before_continuing(self):
        text = " ".join(read(AUTO_GATEKEEPER).split())

        assert "before continuing" in text
        assert "append-only" in text
        assert "auto-decisions.md" in text
        assert "workflow_prompt" in text
        assert "answer" in text
        assert "validate_auto_decisions.py" in text

    def test_reference_unknown_blocks_transition(self):
        text = " ".join(read(AUTO_MODE_REFERENCE).split())

        assert "cannot determine whether the gate can pass" in text
        assert "must not transition" in text
        assert "as if the gate" in text

    def test_gatekeeper_rejects_unresolved_security_unknowns(self):
        text = read(AUTO_GATEKEEPER)

        assert "security/privacy" in text
        assert "high-uncertainty `reject`" in text
