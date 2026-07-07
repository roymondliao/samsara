"""Doc-contract tests for the review-record durability convention.

Origin: the structural-honesty feature's Level-2 iteration (fix 9ee97e9)
established that reviewer verdicts are excerpted VERBATIM into a durable
`changes/<feature>/review-record.md`, and that both reviewer dispatch blocks
carry a `## Feature` field. The 1.0.0 design explicitly inherits this
convention (design note 5 §7: review-side evidence visibility lands in
review-record.md; note 6 §3.1: the reviewer's reasoning is the payload and
must be durable). The gate machinery that first shipped alongside it
(spec mode, drift_items) was removed in the 1.0.0 reclassification cleanup —
these tests guard the surviving convention in its 1.0.0 shape.

The tests assert behavioral tokens, not exact prose.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCH_TEMPLATE = ROOT / "skills" / "implement" / "dispatch-template.md"


def _section(text: str, marker: str, end_markers: list[str]) -> str:
    start = text.find(marker)
    assert start != -1, f"section marker not found: {marker!r}"
    rest = text[start + len(marker) :]
    for end_marker in end_markers:
        end = rest.find(end_marker)
        if end != -1:
            return rest[:end]
    return rest


def _review_record_durability_section(dispatch: str) -> str:
    # Intentionally the LAST section in the file — no end marker.
    return _section(dispatch, "## Review Record Durability", [])


def test_death__dispatch_template_has_review_record_durability_section() -> None:
    """The dispatcher-side review-record convention must exist as a named
    section requiring VERBATIM (not summarized) excerpts into
    `changes/<feature>/review-record.md` — including the reviewer's
    structural-judgment REASONING (1.0.0: the payload is the reasoning, not
    only the verdict line) and any arbitration of a disputed Critical."""
    section = _review_record_durability_section(
        DISPATCH_TEMPLATE.read_text(encoding="utf-8")
    )
    lowered = section.lower()

    assert "review-record.md" in lowered, (
        "Review Record Durability no longer names "
        "changes/<feature>/review-record.md as the landing artifact."
    )
    assert "verbatim" in lowered, (
        "Review Record Durability no longer requires VERBATIM excerpts — a "
        "summarized excerpt could silently drop or reword content the "
        "convention exists to preserve exactly."
    )
    assert "reasoning" in lowered, (
        "Review Record Durability no longer names the reviewer's reasoning "
        "as part of what must be excerpted — 1.0.0's evidence-visibility "
        "landing for the review side would lose its durable home."
    )
    assert "arbitrat" in lowered, (
        "Review Record Durability no longer records arbitration of disputed "
        "Criticals — the F6 arbitration path would leave no durable trace."
    )


def test_death__review_record_absent_entry_is_never_recorded_not_nothing_to_record() -> (
    None
):
    """DC-5 pole: an absent review-record entry for a reviewed task must be
    read as "never recorded" (a finding at aggregation time), never as
    "nothing to record" — otherwise the durability convention creates a NEW
    place where "never recorded" is indistinguishable from "recorded empty"."""
    section = _review_record_durability_section(
        DISPATCH_TEMPLATE.read_text(encoding="utf-8")
    )
    lowered = section.lower()

    assert "never recorded" in lowered
    assert "nothing to record" in lowered
    assert "finding" in lowered


def test_unit__both_reviewer_dispatch_blocks_have_feature_field() -> None:
    """Contract source: the Yin reviewer and Code Quality reviewer prompt
    blocks (documented artifact shape). Both must carry `## Feature` naming
    changes/<feature>/ — without it, a task whose changed files are all
    outside changes/<feature>/ leaves reviewers unable to locate feature
    artifacts (yin: scar reports / review-record cross-checks; quality:
    resolving forced_by / seam / affects citations against index.yaml and
    overview.md)."""
    text = DISPATCH_TEMPLATE.read_text(encoding="utf-8")
    yin_block = _section(text, "### Yin reviewer", ["\n### Code Quality reviewer"])
    quality_block = _section(
        text, "### Code Quality reviewer", ["\nBoth reviewers must report back"]
    )

    for block, label in ((yin_block, "yin"), (quality_block, "code quality")):
        assert "## Feature" in block, (
            f"the {label} reviewer dispatch block has no `## Feature` field."
        )
        assert "changes/<feature>/" in block, (
            f"the {label} reviewer dispatch block's Feature field does not "
            "name the changes/<feature>/ directory."
        )

    # quality's Feature field carries the 1.0.0 resolution purpose
    quality_normalized = " ".join(quality_block.split()).lower()
    assert "forced_by" in quality_normalized, (
        "the quality reviewer's Feature field no longer names forced_by/"
        "seam/affects citation resolution as its purpose."
    )
