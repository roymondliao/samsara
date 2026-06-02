"""Token-matching + step-parsing ENGINE for contract-bound-unit-tests.

DEATH-REASON OF THIS MODULE: "how a concept token is matched against a surface, and
how a numbered execution-order step list is parsed." Everything here is about the
MECHANISM of matching/parsing — it knows nothing about WHICH concepts any surface must
carry. The concept-catalog DATA (what each surface must carry) lives in the sibling
`_contract_tokens.py`, which imports `rx` and `Token` from here to construct its groups.

This split (iteration-fix-1) exists because review flagged 4 times that a change to the
matching engine and a change to the concept catalog were forced to touch the same file.
A structural death test (`test_module_split_death.py`) pins the separation: it reddens
if an engine helper leaks back into `_contract_tokens.py` or a concept group sprouts
here. Do NOT add concept-group dicts to this module.

Matching contract:
    A "token" is matched against a target text with `token_present(text, token)`:
    plain tokens are case-insensitive substring matches; tokens wrapped via `rx(...)`
    are case-insensitive regex searches. Use `rx` only when several honest wordings
    share a pattern but no single literal substring; prefer a literal substring
    otherwise, because a literal substring is the least over-fit assertion that still
    proves the concept is present.

A concept is considered "covered" by a text when AT LEAST ONE token in its tuple is
present. Tuples therefore enumerate *alternative honest phrasings* of the same concept,
not a conjunction of required strings.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Pattern, Union

Token = Union[str, Pattern[str]]

# Shared repo-root anchor. Every evaluator in this package lives at
# tests/test_contract_bound_tests/<file>.py, so the repo root is parents[2] of THIS
# module too. Exporting it here single-sources the anchor so new evaluators import it
# instead of re-deriving `Path(__file__).resolve().parents[2]` (the duplication flagged
# across task-3/task-5 reviews). A function form (`repo_root()`) was removed: it had no
# caller — the planning evaluator imports the `ROOT` constant directly — so it was a
# phantom surface commitment. Add a function form back only when a real caller needs it.
ROOT = Path(__file__).resolve().parents[2]


def rx(pattern: str) -> Pattern[str]:
    """Mark a token as a case-insensitive regex rather than a literal substring."""
    return re.compile(pattern, re.IGNORECASE)


def token_present(text: str, token: Token) -> bool:
    """True if the concept token is present in text (case-insensitive)."""
    if isinstance(token, re.Pattern):
        return token.search(text) is not None
    return token.lower() in text.lower()


def concept_present(text: str, tokens: tuple[Token, ...]) -> bool:
    """A concept is covered when AT LEAST ONE of its honest phrasings is present."""
    return any(token_present(text, t) for t in tokens)


def missing_concepts(text: str, concept_map: dict[str, tuple[Token, ...]]) -> list[str]:
    """Return the keys of concepts NOT covered by text. Empty list == full coverage."""
    return [
        name
        for name, tokens in concept_map.items()
        if not concept_present(text, tokens)
    ]


def concepts_covered_by(
    text: str, concept_map: dict[str, tuple[Token, ...]]
) -> set[str]:
    """Return the set of concept keys COVERED by text (inverse of missing_concepts).

    Shared so every decoy/polarity test phrases the same assertion identically:
    `assert not concepts_covered_by(hostile_text, groups)`. Keeping this in the
    shared module (rather than re-deriving `set(groups) - set(missing_concepts(...))`
    in each test file) means tasks 2-6 cannot silently diverge on what "covered"
    means.
    """
    return {
        name for name, tokens in concept_map.items() if concept_present(text, tokens)
    }


def pinned_heading_offenders(
    concept_map: dict[str, tuple[Token, ...]],
) -> list[tuple[str, str]]:
    """Return (concept_key, literal) pairs whose token literal contains '##'.

    A token that IS a markdown heading string ("## ...") would make a coverage
    check pass only while that specific heading survives — the exact over-fit the
    feature exists to kill. This authoritative implementation is shared by EVERY
    evaluator (task-1 reference death tests, task-2 implementer evaluator, and
    tasks 3-6) so the heading-pin guard cannot drift between files. For a regex
    token the `.pattern` source is inspected; for a literal token the string
    itself.
    """
    offenders: list[tuple[str, str]] = []
    for key, tokens in concept_map.items():
        for t in tokens:
            literal = t if isinstance(t, str) else t.pattern
            if "##" in literal:
                offenders.append((key, literal))
    return offenders


# --- Structural ordering of a numbered execution-order step list ------------
#
# CRITICAL: a concept token can prove PRESENCE, never ORDER. "Test Contract Gate
# (before unit tests)" as a step LABEL still matches if a future author moves the
# gate to AFTER the unit-test step but keeps the label text. To enforce the
# ordering INVARIANT (death test < contract gate < unit test) the position must be
# read STRUCTURALLY: parse the numbered step list, find which numbered step CONTAINS
# each concept, and compare the step indices. The parser is rewrap-robust — it
# matches the numbered step whose body carries the concept, not an exact label
# string — and it fails LOUD (returns None, callers assert) when a concept cannot be
# located, so a silently-missing step cannot pass the ordering check by default.

# A numbered step line: optional leading whitespace, a number, '.', then the body.
_NUMBERED_STEP_RX = re.compile(r"^\s*(\d+)\.\s+(.*)$")


def numbered_steps(text: str) -> list[tuple[int, str]]:
    """Return [(line_index, step_body), ...] for every numbered '`N.` ...' line.

    Only top-level numbered list items are returned (the execution-order steps).
    `line_index` is the 0-based index into `text.splitlines()` so callers can map a
    step back to a source position. The numeric label value is intentionally NOT
    used for ordering — POSITION in the list is the ordering, not the printed digit
    (so a mis-numbered list still orders by where the step physically sits).
    """
    steps: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines()):
        m = _NUMBERED_STEP_RX.match(line)
        if m:
            steps.append((i, m.group(2)))
    return steps


def step_index_of_concept(
    steps: list[tuple[int, str]], tokens: tuple[Token, ...]
) -> int | None:
    """Return the POSITIONAL index (0..len-1) of the first numbered step whose body
    matches the concept, or None if no step carries it.

    Positional (list order), NOT the printed number and NOT the source line index:
    this is exactly what makes the result an ORDER assertion. None means the concept
    is absent from the step list — callers MUST treat None as a loud failure, never
    silently compare None.
    """
    for pos, (_line, body) in enumerate(steps):
        if concept_present(body, tokens):
            return pos
    return None
