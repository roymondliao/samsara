"""Death contracts for Validate & Ship's terminal evidence authority."""

from pathlib import Path

import re
import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "skills" / "validate-and-ship" / "SKILL.md"
ITERATION_FLOW = ROOT / "skills" / "iteration" / "flow.md"
MANIFEST_GUIDE = ROOT / "skills" / "validate-and-ship" / "ship-manifest.md"
MANIFEST_TEMPLATE = (
    ROOT / "skills" / "validate-and-ship" / "templates" / "ship-manifest.yaml"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    rest = text[start:]
    end = rest.find("\n## ", len(heading))
    return rest if end == -1 else rest[:end]


def test_death__validate_never_fixes_code_inline() -> None:
    text = _read(VALIDATE).lower()
    normalized = " ".join(text.split())

    assert "inline fix" not in text
    assert "return to `samsara:iteration`" in text
    assert "implement owns code and test changes" in normalized
    assert "rerun step 0 against the full diff" in normalized


def test_death__iteration_owns_validation_finding_reentry() -> None:
    flow = _read(ITERATION_FLOW).lower()
    section = _section(flow, "## validation re-entry")

    assert "validation finding" in section
    assert "scar" in section
    assert "samsara:implement" in section
    assert "ready_for_validation" in section


def test_death__every_validation_result_has_a_non_success_route() -> None:
    text = _read(VALIDATE).lower()

    for step in (
        "security and privacy",
        "remaining exposure",
        "acceptance",
        "primary evaluator",
        "e2e",
        "reconciliation",
        "review evidence",
    ):
        assert step in text
    assert "fail returns to the owning layer" in text
    assert "unknown blocks delivery" in text
    assert "only `ready_for_delivery`" in text


def test_death__process_graph_is_english_derived_topology() -> None:
    text = _read(VALIDATE)
    graph = _section(text, "## Derived Process Overview")

    assert "canonical" in graph.lower()
    assert "```dot" in graph
    assert not re.search(r"[\u3400-\u9fff]", graph)
    assert 'label="fail or unknown"' in graph
    assert "iteration" in graph.lower()


def test_death__remaining_exposure_uses_lifecycle_not_item_count_risk() -> None:
    text = _read(VALIDATE).lower()
    guide = _read(MANIFEST_GUIDE).lower()

    assert "remaining exposure check" in text
    assert "failure budget review" not in text
    assert "`open`, `blocked`, and unresolved legacy items block delivery" in text
    assert "silent_failure_surface" not in guide
    assert "low | medium | high" not in guide


def test_death__acceptance_includes_unknown_outcome() -> None:
    text = _read(VALIDATE).lower()

    assert "`unknown_outcome`" in text
    assert "every scenario declared in `acceptance.yaml`" in text


def test_death__review_consumes_both_durable_reviewer_results() -> None:
    text = _read(VALIDATE).lower()
    review = _section(text, "### 6. review evidence check")

    assert "review-record.md" in review
    assert "yin" in review and "quality" in review
    assert "invoke the `code-reviewer` agent" not in review
    assert "missing" in review and "unknown" in review


def test_death__mandatory_failures_cannot_be_accepted_at_final_gate() -> None:
    gate = _section(_read(VALIDATE).lower(), "## auto mode gate")

    for blocker in (
        "security",
        "primary evaluator",
        "format",
        "open",
        "blocked",
        "missing reviewer",
    ):
        assert blocker in gate
    assert "`accept_gap` cannot override" in gate


def test_death__delivery_is_recorded_and_prepared_not_executed() -> None:
    transition = _section(_read(VALIDATE).lower(), "## transition")
    normalized = " ".join(transition.split())

    assert "record" in transition and "prepare" in transition
    assert "do not merge" in normalized
    assert "do not create the pr" in normalized
    assert "do not discard" in normalized


def test_unit__ship_manifest_template_is_the_only_shape_authority() -> None:
    guide = _read(MANIFEST_GUIDE).lower()
    manifest = yaml.safe_load(_read(MANIFEST_TEMPLATE))

    assert "```yaml" not in guide
    assert "templates/ship-manifest.yaml" in guide
    assert "sole shape authority" in guide
    assert {
        "feature",
        "delivered_capability",
        "snapshot",
        "validation_status",
        "validation",
        "operational_controls",
        "delivery",
    } <= manifest.keys()


def test_death__manifest_does_not_force_invented_operational_claims() -> None:
    manifest = yaml.safe_load(_read(MANIFEST_TEMPLATE))
    serialized = _read(MANIFEST_TEMPLATE).lower()

    assert "known_failure_modes" not in manifest
    assert "silent_failure_surface" not in manifest
    assert "monitoring_hooks" not in manifest
    assert "kill_switch" not in manifest
    assert manifest["validation"]["remaining_exposure"]["accepted_refs"] == []
    assert manifest["validation"]["remaining_exposure"]["deferred_refs"] == []
    assert "available | absent | not_applicable | unknown" in serialized
