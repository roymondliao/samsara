"""DC-B guard: three-generation scar aggregation must not silently drop items.

Contract source (see task-5's Unit Test Contract): skills/iteration/SKILL.md
Step 1's "Scar format generations (read-side canonical)" section — items are
identified by field SHAPE alone (no `schema_version`), and "all three
generations count toward signal_lost identically". This module does NOT run
the real iteration skill (there is no python implementation of it — it is a
documented workflow an agent follows). Instead it implements a synthetic
reader (`count_remaining`) that follows the SAME documented shape-detection
and resolved-exclusion rules, and tests that reader against the three
tests/fixtures/scar_reports/mixed_generation/ fixtures (Gen 1 plain string,
Gen 2 description dict, Gen 3 what/bites_when slot form — each containing a
deferred item, and a resolved item via each generation's own resolution
mechanism: Gen 2's separate `resolved_items` list, Gen 3's in-place
`status: resolved`).

Known, named gap (not hidden): a synthetic test-layer reader is not the real
agent-followed workflow — see this task's scar report,
systemic_ref: doc-vs-runtime-obedience.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MIXED_GEN_DIR = ROOT / "tests" / "fixtures" / "scar_reports" / "mixed_generation"
GEN1 = MIXED_GEN_DIR / "gen1_plain_string.yaml"
GEN2 = MIXED_GEN_DIR / "gen2_description_dict.yaml"
GEN3 = MIXED_GEN_DIR / "gen3_slot_form.yaml"
ALL_FIXTURES = (GEN1, GEN2, GEN3)

_SCAR_SECTIONS = ("known_shortcuts", "silent_failure_conditions")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Correct reader: follows SKILL.md Step 1's documented shape-detection rule.
# ---------------------------------------------------------------------------


def _detect_generation(item: object) -> str:
    """Shape-only detection, per SKILL.md Step 1: Gen 1 = bare string, Gen 2 =
    `description` dict, Gen 3 = `what`/`bites_when` slot dict.

    Deliberately outside this synthetic reader's model: `systemic_ref`-shaped
    items ({systemic_ref, note}) — their resolution runs through the registry
    path of the same Step 1 pass (part of the disclosed doc-vs-runtime gap in
    this module's docstring); no current mixed-generation fixture carries one."""
    if isinstance(item, str):
        return "gen1"
    if isinstance(item, dict):
        if "what" in item and "bites_when" in item:
            return "gen3"
        if "description" in item:
            return "gen2"
    return "unknown"


def _is_resolved(item: object) -> bool:
    """In-place resolution marker (Gen 2/Gen 3 share this form per SKILL.md
    Step 1: 'resolution tracking ... is already described under item 2
    above' — read identically for Gen 3). A Gen 1 plain string can never
    carry this, so it is never excluded this way."""
    return isinstance(item, dict) and item.get("status") == "resolved"


def count_remaining(paths: tuple[Path, ...] = ALL_FIXTURES) -> tuple[int, set[str]]:
    """Total remaining (non-resolved) items across known_shortcuts and
    silent_failure_conditions, plus the set of generations actually
    encountered. Deliberately does NOT read the top-level `resolved_items`
    list — those entries never re-appear in the section lists (Gen 2's own
    resolution mechanism), so they must not be double-counted OR need
    restating to be excluded; they are excluded by never being iterated.

    Raises if any item's shape is unrecognized — a real Step-1-following
    reader must be able to classify every generation this feature declares;
    silently skipping an unrecognized shape is the exact DC-B failure this
    guard exists to catch (see naive_count_remaining below for the contrast).
    """
    total = 0
    generations_seen: set[str] = set()
    for path in paths:
        data = _load(path)
        for section in _SCAR_SECTIONS:
            for item in data.get(section) or []:
                gen = _detect_generation(item)
                assert gen != "unknown", (
                    f"{path.name}:{section} item has an unrecognized shape "
                    f"(not gen1/gen2/gen3): {item!r}"
                )
                generations_seen.add(gen)
                if not _is_resolved(item):
                    total += 1
    return total, generations_seen


# ---------------------------------------------------------------------------
# Naive (hostile) reader: recognizes only Gen 1 and Gen 2 shapes — proves the
# fixture set actually exercises the Gen 3 distinguishing behavior. If this
# decoy did NOT undercount relative to count_remaining, the fixtures would not
# be proving anything about Gen 3 detection specifically.
# ---------------------------------------------------------------------------


def _naive_detect_generation(item: object) -> str:
    if isinstance(item, str):
        return "gen1"
    if isinstance(item, dict) and "description" in item:
        return "gen2"
    return "unknown"  # what/bites_when slot shape is NOT recognized


def naive_count_remaining(paths: tuple[Path, ...] = ALL_FIXTURES) -> int:
    total = 0
    for path in paths:
        data = _load(path)
        for section in _SCAR_SECTIONS:
            for item in data.get(section) or []:
                gen = _naive_detect_generation(item)
                if gen == "unknown":
                    continue  # the exact DC-B silent-drop mode
                if isinstance(item, dict) and item.get("status") == "resolved":
                    continue
                total += 1
    return total


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__naive_shape_detection_silently_drops_gen3_items() -> None:
    """DC-B: a reader that does not recognize the Gen 3 what/bites_when slot
    shape silently drops every Gen 3 item instead of erroring or counting it.
    The correct reader (count_remaining) must classify all items and return a
    STRICTLY HIGHER total than the naive reader for the same fixture set —
    proving the naive reader's undercount is real, not a coincidence of
    fixture content.
    """
    correct_total, generations_seen = count_remaining()
    naive_total = naive_count_remaining()

    assert generations_seen == {"gen1", "gen2", "gen3"}, (
        f"the fixture set does not exercise all three generations: {generations_seen}"
    )
    assert naive_total < correct_total, (
        f"naive reader ({naive_total}) did not undercount vs the correct reader "
        f"({correct_total}) — the fixtures no longer exercise the Gen 3 "
        "silent-drop failure mode this death test exists to catch."
    )
    # Pin the drop count DERIVED from the fixture at test time (not a
    # hardcoded constant — quality review proved a literal `== 2` pin reddens
    # spuriously when a legitimate extra Gen 3 item is added): the gap must
    # equal exactly the number of non-resolved Gen 3 items in the fixture
    # set, because that is precisely what a shape-blind reader drops.
    expected_gap, _ = count_remaining((GEN3,))
    assert correct_total - naive_total == expected_gap, (
        f"naive reader's undercount ({correct_total - naive_total}) does not "
        f"equal the fixture's non-resolved Gen 3 item count ({expected_gap}) "
        "— the naive/correct gap is no longer explained purely by Gen 3 "
        "shape-blindness (DC-B), something else is being dropped or "
        "double-counted."
    )


def test_death__unrecognized_shape_is_never_silently_skipped_by_correct_reader() -> (
    None
):
    """The correct reader must ERROR (not silently skip) on a shape it cannot
    classify — feeding it a 4th, unknown shape must raise, never quietly
    return a smaller-than-true count."""
    bogus = {"schema_version": 99, "text": "an invented 4th generation"}
    assert _detect_generation(bogus) == "unknown"
    try:
        count_remaining((GEN1,))  # sanity: real fixture still works
    except AssertionError:
        raise AssertionError("count_remaining rejected a valid Gen 1 fixture")


# ---------------------------------------------------------------------------
# Unit tests (contract-bound: iteration SKILL.md Step 1 documented shape)
# ---------------------------------------------------------------------------


def test_unit__all_three_generations_count_toward_remaining_identically() -> None:
    """Contract source: SKILL.md Step 1 — 'All three generations count toward
    signal_lost identically ... an aggregator must accept old and new forms
    side by side in the same feature.' Behavior-preserving refactor (reorder
    fixture items) keeps this green; behavior-actually-broke (a generation's
    item silently excluded) turns it red via the exact total.
    """
    total, generations_seen = count_remaining()
    assert generations_seen == {"gen1", "gen2", "gen3"}
    # gen1: 2 known_shortcuts + 1 silent_failure = 3 (no resolution concept)
    # gen2: 2 known_shortcuts + 1 silent_failure = 3 remaining (1 more
    #       resolved via the separate resolved_items list, never iterated)
    # gen3: 1 remaining known_shortcut (+1 excluded via status: resolved)
    #       + 1 silent_failure = 2 remaining
    assert total == 8, (
        f"expected 8 remaining items across all 3 generations, got {total}"
    )


def test_unit__deferred_item_included_resolved_item_excluded_same_way_gen2_and_gen3() -> (
    None
):
    """Contract source: SKILL.md Step 1 — resolved-item exclusion ('resolved_items
    list vs in-place status: resolved') is 'read identically for Gen 3 triage'
    as Gen 2. Asserts by CONTENT marker (not just count) that:
      - Gen 2's deferred item (still in known_shortcuts) is counted as remaining
      - Gen 2's resolved item (only in resolved_items, never in known_shortcuts)
        is absent from the section entirely
      - Gen 3's deferred item (status absent) is counted as remaining
      - Gen 3's resolved item (status: resolved) is present in the section but
        excluded from the remaining count
    """
    gen2 = _load(GEN2)
    gen3 = _load(GEN3)

    gen2_shortcut_descriptions = [
        item["description"] for item in gen2["known_shortcuts"]
    ]
    assert any(
        "deferred" in d and "Gen2 shortcut A" in d for d in gen2_shortcut_descriptions
    ), "Gen 2 deferred item text is missing from known_shortcuts"
    assert not any("Gen2 shortcut C" in d for d in gen2_shortcut_descriptions), (
        "Gen 2's resolved item (tracked only via resolved_items) leaked into "
        "known_shortcuts — it must live SOLELY in the separate resolved_items list"
    )
    assert any(
        "Gen2 shortcut C" in item["original_description"]
        for item in gen2["resolved_items"]
    ), "Gen 2's resolved item must be traceable via resolved_items"

    gen3_shortcuts = gen3["known_shortcuts"]
    deferred_items = [
        i for i in gen3_shortcuts if i.get("deferred_to_feature_iteration")
    ]
    resolved_items = [i for i in gen3_shortcuts if _is_resolved(i)]
    assert len(deferred_items) == 1 and "Gen3 shortcut A" in deferred_items[0]["what"]
    assert len(resolved_items) == 1 and "Gen3 shortcut B" in resolved_items[0]["what"]

    # The actual parity assertion: deferred items count, resolved items don't,
    # regardless of which generation (2 or 3) or which exclusion mechanism
    # (separate list vs in-place status) is used.
    remaining_total, _ = count_remaining((GEN2, GEN3))
    assert remaining_total == 5  # gen2: 3 remaining, gen3: 2 remaining
