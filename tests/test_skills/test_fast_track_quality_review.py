"""
Doc-contract guard for Task 6 (fast-track quality checklist -> violations-only
+ reviewed declaration): skills/fast-track/SKILL.md and
skills/fast-track/templates/fast-track.yaml must record the Step 4 quality
review as `quality_review` (`reviewed_criteria` + `violations`), not the old
`quality_checklist` (4 fixed checked+note entries with an anti-boilerplate
warning in every note).

These are DOC-PRESENCE / ARTIFACT-SHAPE tests, not behavioral tests — there is
no runtime code in this task. The instruction surfaces themselves ARE the
contract. See .samsara/systemic-scars.yaml `doc-vs-runtime-obedience`: nothing
in this repo enforces that a dispatched agent actually reviewed the criteria
it claims to have reviewed — the guard here is that the DOCUMENT requires a
`reviewed_criteria` declaration line to exist alongside any empty `violations`
list, not that the declaration is truthful at runtime (see also
`doc-instruction-no-code-enforcement`).

Death case guarded (see acceptance.yaml "Silent failure - fast-track 空違規
清單無法區分「查過」與「沒查」" + task's Death Test Requirements, DC7):
  1. 空清單雙義性未封死 — SKILL.md must state, in forbidding polarity, that an
     empty `violations` list WITHOUT a `reviewed_criteria` declaration counts
     as "not reviewed" and must not be committed. Losing this clause, or
     softening it to a permissive polarity ("... it's fine to commit anyway"),
     re-opens the exact ambiguity the task exists to close.
  2. 兩套並存 — neither SKILL.md's Output example nor
     templates/fast-track.yaml may retain the old `quality_checklist:` key
     alongside (or instead of) the new `quality_review:` key. A doc/template
     that has both is worse than having only the old one: it tells an
     implementer two contradictory output shapes.
  3. Quality symmetry 守護被刪 — the Yin-Side Constraints bullet requiring
     fast-track's Step 4 review to check BOTH the yin face and the quality
     face must survive this task's rewording. This is an existing guard this
     task must not delete as collateral damage of the quality_checklist ->
     quality_review swap.

Unit-test contract sources (see task's "Unit Test Contract"):
  - templates/fast-track.yaml quality_review field structure (documented
    artifact shape, YAML-parseable: reviewed_criteria required list,
    violations list)
  - SKILL.md Step 4 clause documenting the quality_review output shape
    (documented workflow contract)
  - SKILL.md Output section's embedded example (documented artifact shape,
    YAML-parseable, must stay structurally consistent with the template)
All concept-token assertions are polarity-bound per references/test-contract.md
rule 2 (presence-not-polarity): every directional assertion has a matching
wrong-direction decoy fixture proving the SAME predicate function reports the
decoy's claim as absent/present in the opposite direction.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
SKILL = ROOT / "skills" / "fast-track" / "SKILL.md"
TEMPLATE = ROOT / "skills" / "fast-track" / "templates" / "fast-track.yaml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Section extractors (scoped, so a whole-file search does not match unrelated
# context outside this task's two clauses of interest).
# ---------------------------------------------------------------------------


def _yin_side_section(text: str) -> str:
    start = text.find("## Yin-Side Constraints")
    assert start != -1, "fast-track SKILL.md has no '## Yin-Side Constraints' section"
    rest = text[start:]
    end = rest.find("\n## Output")
    assert end != -1, (
        "fast-track SKILL.md Yin-Side Constraints section is not bounded by '## Output'"
    )
    return rest[:end]


def _output_section(text: str) -> str:
    start = text.find("## Output")
    assert start != -1, "fast-track SKILL.md has no '## Output' section"
    return text[start:]


def _output_fenced_yaml(text: str) -> str:
    """Return the fenced ```yaml example block inside the Output section."""
    output = _output_section(text)
    start = output.find("```yaml")
    assert start != -1, (
        "fast-track SKILL.md Output section has no fenced yaml example block"
    )
    rest = output[start + len("```yaml") :]
    end = rest.find("```")
    assert end != -1, (
        "fast-track SKILL.md Output section's fenced yaml block is not closed"
    )
    return rest[:end]


def _step4_section(text: str) -> str:
    start = text.find("## Step 4:")
    assert start != -1, "fast-track SKILL.md has no '## Step 4:' section"
    rest = text[start:]
    end = rest.find("\n## Yin-Side Constraints")
    assert end != -1, (
        "fast-track SKILL.md Step 4 section is not bounded by '## Yin-Side Constraints'"
    )
    return rest[:end]


# ---------------------------------------------------------------------------
# Polarity-bound predicates (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function — test-contract.md
# rule 2, presence-not-polarity).
# ---------------------------------------------------------------------------

_PERMISSIVE_ZH = re.compile(r"可以|可直接|允許|沒關係|不影響")
_NEGATION_EN = re.compile(
    r"\bnot\b|\bnever\b|\bwithout\b|\bno longer\b|\bdoes not\b|\bdoesn't\b|\beither\b"
)


def forbids_ship_when_reviewed_criteria_missing(text: str) -> bool:
    """True iff the doc states, in FORBIDDING polarity and clause-bounded
    proximity, that an empty `violations` list without a `reviewed_criteria`
    declaration counts as "not reviewed" and must not be committed.

    Anchors: 缺 -> (<=15 chars) -> reviewed_criteria -> (<=30 chars) ->
    未檢查 -> (<=10 chars) -> 不得 commit. A trailing 20-char window after the
    forbidding phrase is checked for a permissive marker (catches a decoy
    that swaps '不得 commit' for a permissive tail like '但可以直接 commit').
    """
    m = re.search(r"缺[^.!?\n]{0,15}reviewed_criteria[^.!?\n]{0,30}未檢查", text)
    if not m:
        return False
    tail_start = m.end()
    forbid = re.search(r"不得\s*commit", text[tail_start : tail_start + 10])
    if not forbid:
        return False
    window = text[tail_start : min(len(text), tail_start + 20)]
    return not _PERMISSIVE_ZH.search(window)


def uses_new_quality_review_structure_only(section_lower: str) -> bool:
    """True iff `quality_review:` is present AND the retired `quality_checklist:`
    key is absent. Returns False for all three bad states this guards
    against: old-key-only (not yet migrated), both-keys-coexisting (the two
    output shapes contradict each other), and neither-key-present."""
    return (
        "quality_review:" in section_lower and "quality_checklist:" not in section_lower
    )


def yin_requires_quality_symmetry(yin_lower: str) -> bool:
    """True iff Yin-Side Constraints ties 'quality symmetry' directly (clause-
    bounded gaps) to a requirement that Step 4 review 'must check both' the
    yin face and the quality face, with no negation marker in a 40-char
    trailing window after the match."""
    m = re.search(
        r"quality symmetry[^.!?\n]{0,40}must check both[^.!?\n]{0,20}yin[^.!?\n]{0,40}quality",
        yin_lower,
    )
    if not m:
        return False
    window = yin_lower[m.end() : min(len(yin_lower), m.end() + 40)]
    return not _NEGATION_EN.search(window)


# Permanent wrong-direction / contradiction decoys (hostile fixtures baked
# into the suite so a regression that reintroduces the exact caught bug is
# detected automatically, not by one-off manual verification).

_FORBID_PERMISSIVE_DECOY = "缺 `reviewed_criteria` 的空 `violations` 清單視為未檢查，不得 commit —— 但沒關係，可以直接 commit 也行"
_FORBID_MISSING_ANCHOR_DECOY = (
    "空的 `violations` 清單代表沒有發現任何問題，可以直接 commit。"
)

_COEXIST_BOTH_KEYS_DECOY = (
    "quality_checklist:\n"
    "  - criterion: C5\n"
    "    checked: false\n"
    "quality_review:\n"
    "  reviewed_criteria: [C5]\n"
    "  violations: []\n"
)
_OLD_KEY_ONLY_DECOY = "quality_checklist:\n  - criterion: C5\n    checked: false\n"
_NEITHER_KEY_DECOY = "scar_tag: none\nscar_items: []\n"

_SYMMETRY_NEGATED_DECOY = (
    "- **quality symmetry** — fast-track's step 4 review must check both yin and "
    "quality faces, although this is no longer required in practice; either face "
    "alone is fine"
)
_SYMMETRY_DELETED_DECOY = (
    "- **every commit tagged** — `[scar:none]` or `[scar:n items]`"
)


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__skill_forbids_committing_unreviewed_empty_violations() -> None:
    """Death case 1 (空清單雙義性未封死) — DC7. If SKILL.md loses the clause
    that an empty `violations` list without `reviewed_criteria` counts as
    "not reviewed" and must not be committed, this goes RED: an empty
    violations list becomes silently ambiguous between "checked, clean" and
    "never checked".
    """
    text = read(SKILL)
    assert forbids_ship_when_reviewed_criteria_missing(text), (
        "fast-track SKILL.md no longer states, in forbidding polarity, that an "
        "empty `violations` list without a `reviewed_criteria` declaration "
        "counts as 'not reviewed' and must not be committed — DC7's "
        "space-of-ambiguity between 'reviewed and clean' and 'never reviewed' "
        "is no longer closed."
    )


def test_death__template_and_output_example_do_not_coexist_with_old_checklist() -> None:
    """Death case 2 (兩套並存) — both templates/fast-track.yaml and SKILL.md's
    Output fenced example must use ONLY the new `quality_review:` structure.
    If either still carries the retired `quality_checklist:` key (alone, or
    alongside the new key), this goes RED.
    """
    template_text = read(TEMPLATE).lower()
    assert uses_new_quality_review_structure_only(template_text), (
        "templates/fast-track.yaml does not use the new `quality_review:` "
        "structure exclusively — it is missing `quality_review:`, still has "
        "the retired `quality_checklist:` key, or has both (two contradictory "
        "output shapes)."
    )

    output_fenced = _output_fenced_yaml(read(SKILL)).lower()
    assert uses_new_quality_review_structure_only(output_fenced), (
        "fast-track SKILL.md's Output example does not use the new "
        "`quality_review:` structure exclusively — it is missing "
        "`quality_review:`, still has the retired `quality_checklist:` key, "
        "or has both."
    )


def test_death__yin_side_quality_symmetry_guard_survives() -> None:
    """Death case 3 (Quality symmetry 守護被刪) — the pre-existing guard
    requiring Step 4 review to check BOTH yin and quality faces must survive
    this task's rewording. If deleted or negated, this goes RED (a
    subtraction task accidentally cutting a guard it was told not to cut).
    """
    yin = _yin_side_section(read(SKILL)).lower()
    assert yin_requires_quality_symmetry(yin), (
        "fast-track SKILL.md Yin-Side Constraints no longer requires Step 4 "
        "review to check BOTH the yin face and the quality face — this "
        "pre-existing guard must survive the quality_checklist -> "
        "quality_review rewording, not be deleted as collateral damage."
    )


# ---------------------------------------------------------------------------
# Decoy-detection regression guards (permanent hostile fixtures — prove the
# SAME predicate used above correctly rejects the wrong-direction / reintro-
# duced-contradiction case, per test-contract.md rule 2).
# ---------------------------------------------------------------------------


def test_death__forbid_permissive_polarity_decoy_is_detected_as_missing() -> None:
    assert (
        forbids_ship_when_reviewed_criteria_missing(_FORBID_PERMISSIVE_DECOY) is False
    ), (
        "The '不得 commit —— 但沒關係，可以直接 commit 也行' decoy (forbidding "
        "phrase immediately undercut by a permissive tail) was reported as a "
        "valid forbidding clause — the trailing-permissive-window check has "
        "regressed."
    )


def test_death__forbid_missing_anchor_decoy_is_detected_as_missing() -> None:
    assert (
        forbids_ship_when_reviewed_criteria_missing(_FORBID_MISSING_ANCHOR_DECOY)
        is False
    ), (
        "The '空的 violations 清單代表沒有發現任何問題，可以直接 commit' decoy "
        "(no '缺 reviewed_criteria ... 未檢查' anchor at all, and permissive) "
        "was reported as a valid forbidding clause — the anchor-presence "
        "check has regressed."
    )


def test_death__coexist_both_keys_decoy_is_detected_as_bad() -> None:
    assert uses_new_quality_review_structure_only(_COEXIST_BOTH_KEYS_DECOY) is False, (
        "The both-keys-coexisting decoy (`quality_checklist:` and "
        "`quality_review:` both present) was reported as using the new "
        "structure exclusively — the coexistence guard has regressed."
    )


def test_death__old_key_only_decoy_is_detected_as_bad() -> None:
    assert uses_new_quality_review_structure_only(_OLD_KEY_ONLY_DECOY) is False, (
        "The old-key-only decoy (`quality_checklist:` present, no "
        "`quality_review:`) was reported as using the new structure — the "
        "presence-of-new-key requirement has regressed."
    )


def test_death__neither_key_decoy_is_detected_as_bad() -> None:
    assert uses_new_quality_review_structure_only(_NEITHER_KEY_DECOY) is False, (
        "The neither-key-present decoy was reported as using the new "
        "structure — the predicate must require `quality_review:` to be "
        "actually present, not merely absence of the old key."
    )


def test_death__symmetry_negated_decoy_is_detected_as_missing() -> None:
    assert yin_requires_quality_symmetry(_SYMMETRY_NEGATED_DECOY) is False, (
        "The 'must check both ... although this is no longer required ... "
        "either face alone is fine' decoy was reported as a valid symmetry "
        "requirement — the trailing-negation window check has regressed."
    )


def test_death__symmetry_deleted_decoy_is_detected_as_missing() -> None:
    assert yin_requires_quality_symmetry(_SYMMETRY_DELETED_DECOY) is False, (
        "A Yin-Side Constraints section with the quality symmetry bullet "
        "entirely deleted was reported as still requiring symmetry — the "
        "match-presence check has regressed."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape)
# ---------------------------------------------------------------------------


def test_unit__template_quality_review_has_reviewed_criteria_and_violations_shape() -> (
    None
):
    """Contract source: templates/fast-track.yaml quality_review field
    structure (documented artifact shape, YAML-parseable).

    Behavior-preserving refactor (reword the inline comments, reorder other
    top-level keys) keeps this green. Behavior-actually-broke (reviewed_criteria
    dropped, violations dropped, or the retired quality_checklist key
    reappears) turns it red.
    """
    parsed = yaml.safe_load(read(TEMPLATE))
    assert isinstance(parsed, dict) and "quality_review" in parsed, (
        "templates/fast-track.yaml must have a top-level 'quality_review' key"
    )
    quality_review = parsed["quality_review"]
    assert isinstance(quality_review, dict), (
        "templates/fast-track.yaml 'quality_review' must be a mapping"
    )

    assert "reviewed_criteria" in quality_review, (
        "templates/fast-track.yaml quality_review is missing 'reviewed_criteria'"
    )
    reviewed = quality_review["reviewed_criteria"]
    assert isinstance(reviewed, list) and len(reviewed) >= 1, (
        "templates/fast-track.yaml quality_review.reviewed_criteria must be a non-empty list"
    )

    assert "violations" in quality_review, (
        "templates/fast-track.yaml quality_review is missing 'violations'"
    )
    assert isinstance(quality_review["violations"], list), (
        "templates/fast-track.yaml quality_review.violations must be a list"
    )

    assert "quality_checklist" not in parsed, (
        "templates/fast-track.yaml still has a top-level 'quality_checklist' key — "
        "the retired 4-fixed-entry checked+note structure was supposed to be "
        "replaced, not left alongside the new quality_review structure"
    )


def test_unit__output_example_quality_review_matches_template_shape() -> None:
    """Contract source: SKILL.md Output section's embedded example
    (documented artifact shape, YAML-parseable) — must stay structurally
    consistent with templates/fast-track.yaml's quality_review shape.
    """
    parsed = yaml.safe_load(_output_fenced_yaml(read(SKILL)))
    assert isinstance(parsed, dict) and "quality_review" in parsed, (
        "fast-track SKILL.md Output example must have a top-level 'quality_review' key"
    )
    quality_review = parsed["quality_review"]
    assert "reviewed_criteria" in quality_review and isinstance(
        quality_review["reviewed_criteria"], list
    ), (
        "fast-track SKILL.md Output example's quality_review is missing a "
        "list-shaped 'reviewed_criteria'"
    )
    assert "violations" in quality_review and isinstance(
        quality_review["violations"], list
    ), (
        "fast-track SKILL.md Output example's quality_review is missing a "
        "list-shaped 'violations'"
    )
    assert "quality_checklist" not in parsed, (
        "fast-track SKILL.md Output example still has a top-level "
        "'quality_checklist' key alongside quality_review"
    )


def test_unit__step4_documents_quality_review_output_field_names() -> None:
    """Contract source: SKILL.md Step 4 clause documenting the quality_review
    output shape (documented workflow contract) — an implementer following
    Step 4 prose alone (without opening the template) must be told the field
    names to write.
    """
    step4 = _step4_section(read(SKILL))
    assert "quality_review" in step4, (
        "fast-track SKILL.md Step 4 no longer names the `quality_review` output field"
    )
    assert "reviewed_criteria" in step4, (
        "fast-track SKILL.md Step 4 no longer names the `reviewed_criteria` output field"
    )
    assert "violations" in step4, (
        "fast-track SKILL.md Step 4 no longer names the `violations` output field"
    )
