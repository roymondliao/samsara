"""Reviewer and dispatch invariants for the test contract gate."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CODE_REVIEWER = ROOT / "agents" / "code-reviewer.md"
CODE_QUALITY_REVIEWER = ROOT / "agents" / "code-quality-reviewer.md"
DISPATCH_TEMPLATE = ROOT / "skills" / "implement" / "dispatch-template.md"
IMPLEMENT_SKILL = ROOT / "skills" / "implement" / "SKILL.md"


def read_code_reviewer() -> str:
    return CODE_REVIEWER.read_text(encoding="utf-8")


def read_code_quality_reviewer() -> str:
    return CODE_QUALITY_REVIEWER.read_text(encoding="utf-8")


def read_dispatch_template() -> str:
    return DISPATCH_TEMPLATE.read_text(encoding="utf-8")


def read_implement_skill() -> str:
    return IMPLEMENT_SKILL.read_text(encoding="utf-8")


def section(text: str, start_prefix: str, end_prefixes: tuple[str, ...]) -> str:
    lines = text.splitlines()
    start = next(
        (
            i
            for i, line in enumerate(lines)
            if line.strip().lower().startswith(start_prefix)
        ),
        None,
    )
    assert start is not None, f"section not found: {start_prefix}"
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if any(lines[i].startswith(prefix) for prefix in end_prefixes)
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def h3_headings(text: str) -> list[tuple[int, str]]:
    return [
        (i, line) for i, line in enumerate(text.splitlines()) if line.startswith("### ")
    ]


def first_heading_index(headings: list[tuple[int, str]], pattern: str) -> int | None:
    rx = re.compile(pattern, re.IGNORECASE)
    return next((i for i, heading in headings if rx.search(heading)), None)


def test_code_reviewer_reviews_tests_before_correctness():
    review_order = section(read_code_reviewer(), "## review order", ("## ",))
    headings = h3_headings(review_order)
    test_index = first_heading_index(headings, r"\btest")
    correctness_index = first_heading_index(headings, r"\bcorrectness\b")

    assert test_index is not None, "Review Order must include a test review step"
    assert correctness_index is not None, (
        "Review Order must include a correctness review step"
    )
    assert test_index < correctness_index, (
        "tests must be reviewed before implementation correctness"
    )


def test_dispatch_template_asks_both_reviewers_for_test_quality_review():
    text = read_dispatch_template()
    for heading in ("### yin reviewer", "### code quality reviewer"):
        block = section(text, heading, ("### ", "## "))
        lower = block.lower()
        assert "test-quality review" in lower or "test quality review" in lower, (
            f"{heading} dispatch block must ask for test-quality review"
        )
        assert re.search(r"\b(brittle|tautolog|silent-green|contract)\b", lower), (
            f"{heading} dispatch block must name the test-quality risk being reviewed"
        )


def test_code_quality_reviewer_refers_test_contract_verdicts_to_yin():
    text = read_code_quality_reviewer().lower()
    assert re.search(r"structural\s+evidence", text)
    assert "do not issue the final test-contract verdict" in text
    assert "refer any brittle" in text
    assert "samsara:code-reviewer" in text


def test_quality_dispatch_refers_brittle_verdict_to_yin_reviewer():
    block = section(
        read_dispatch_template(), "### code quality reviewer", ("### ", "## ")
    ).lower()
    assert "structural evidence" in block
    assert "refer any brittle" in block
    assert "fix-the-test verdict" in block


def test_reviewer_unknown_blocks_implementation_progress():
    combined = (read_dispatch_template() + "\n" + read_implement_skill()).lower()

    assert "unknown" in combined
    assert re.search(r"unknown[^.\n]*(block|fail|stop|do not proceed)", combined), (
        "reviewer UNKNOWN must be explicitly blocking, not allowed to fall through"
    )
    assert re.search(r"missing reference|unreadable reference|reference", combined), (
        "UNKNOWN blocking rule must name reference availability as a gate condition"
    )
