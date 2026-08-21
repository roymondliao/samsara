"""Death tests for Research-owned Auto mode initialization."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"
RESEARCH = ROOT / "skills" / "research" / "SKILL.md"
KICKOFF = ROOT / "skills" / "research" / "templates" / "kickoff.md"
REFERENCE = ROOT / "references" / "auto-mode.md"
GATEKEEPER = ROOT / "agents" / "auto-gatekeeper.md"
VALIDATE = ROOT / "skills" / "validate-and-ship" / "SKILL.md"
PRE_THINKING = ROOT / "skills" / "pre-thinking" / "SKILL.md"
PLANNING = ROOT / "skills" / "planning" / "SKILL.md"
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
ITERATION = ROOT / "skills" / "iteration" / "SKILL.md"
GATEKEEPER_VALIDATOR = (
    ROOT / "agents" / "auto-gatekeeper" / "scripts" / "validate_auto_decisions.py"
)
RESEARCH_VALIDATOR = (
    ROOT / "skills" / "research" / "scripts" / "validate_auto_decisions.py"
)
BOOTSTRAP_VALIDATOR = (
    ROOT / "skills" / "samsara-bootstrap" / "scripts" / "validate_auto_decisions.py"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_bootstrap_routes_feature_work_without_selecting_execution_mode() -> None:
    bootstrap = read(BOOTSTRAP)

    assert "## Execution Mode Selection" not in bootstrap
    assert "Select execution mode first" not in bootstrap
    assert "select execution mode first" not in bootstrap
    assert "invoke `samsara:research`" in bootstrap.lower()


def test_research_step_zero_owns_workflow_run_execution_mode() -> None:
    research = read(RESEARCH)
    normalized = " ".join(research.split())

    assert "## Step 0: Execution Mode Selection" in research
    assert "workflow-run execution mode" in normalized
    assert "Execution mode? Choose `human-in-the-loop` or `auto`." in research
    assert "If the user does not choose" in normalized
    assert "must never silently become `auto`" in normalized
    assert "1-kickoff.md" in normalized


def test_kickoff_persists_the_research_selected_execution_mode() -> None:
    kickoff = read(KICKOFF)

    assert "## Execution Mode" in kickoff
    assert "human-in-the-loop | auto" in kickoff
    assert "Research" in kickoff


def test_later_stages_consume_the_mode_from_kickoff() -> None:
    for path in (PRE_THINKING, PLANNING, IMPLEMENT, ITERATION, VALIDATE):
        text = read(path)
        assert "1-kickoff.md" in text, path

    reference = read(REFERENCE)
    assert "reads `Execution mode:` from Research's `1-kickoff.md`" in reference
    assert "never infers mode from another feature" in reference


def test_auto_decision_validator_is_owned_by_the_gatekeeper_agent() -> None:
    assert GATEKEEPER_VALIDATOR.is_file()
    assert not RESEARCH_VALIDATOR.exists()
    assert not BOOTSTRAP_VALIDATOR.exists()

    for path in (REFERENCE, GATEKEEPER):
        text = read(path)
        assert "installed-auto-gatekeeper-companion-directory" in text
        assert "installed-research-skill-directory" not in text
        assert "installed-samsara-bootstrap-skill-directory" not in text

    validate = read(VALIDATE)
    assert "installed-research-skill-directory" not in validate
    assert "validate_auto_decisions.py" not in validate
    assert "installed-validate-and-ship-skill-directory" in validate


def test_gatekeeper_uses_one_atomic_validate_and_append_command() -> None:
    gatekeeper = read(GATEKEEPER)

    assert "--append-candidate" in gatekeeper
    assert "Run the validator again" not in gatekeeper
