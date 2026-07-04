"""
Doc-contract guard for Task 2 (expiry 移除): the `accept` risk-classification
format in skills/iteration/SKILL.md and skills/validate-and-ship/ship-manifest.md
(+ its template) must be signal-driven re-review (`re_review_signal` + `owner`),
not the old calendar-date `expiry_date`/`expires` field.

These are DOC-PRESENCE / ARTIFACT-SHAPE tests, not behavioral tests — there is
no runtime code in this task. The instruction surfaces themselves ARE the
contract. See .samsara/systemic-scars.yaml `doc-instruction-no-code-enforcement`:
nothing in this repo enforces that a dispatched agent actually watches for the
named signal — the guard here is that the DOCUMENT requires a signal+owner to
be named, not that the signal is monitored at runtime.

Death cases guarded (see acceptance.yaml + task's Death Test Requirements):
  1. accept 退化成無條件永久豁免 — iteration SKILL.md must keep the "accept
     requires re-review signal (+ owner)" clause, in both the Step 2 triage
     prompt and the Yin-Side Constraints section. Losing either is worse than
     the old expiry_date requirement: an accept with NO re-review condition
     at all is a permanent, unconditional exemption.
  2. 文件自相矛盾 — ship-manifest.md rule 2 must not simultaneously carry a
     direct "must have ... expiry" requirement clause alongside the new
     "must have ... signal ... owner" requirement clause. Mentioning `expires`
     in EXPLANATORY prose (why it was removed) is fine; a live REQUIREMENT
     clause for it is the contradiction this guards against.
  3. 舊資料相容 — iteration SKILL.md must explicitly tolerate historical
     `expiry_date` entries on read (no error, no required backfill), so
     existing changes/*/iteration-log.yaml files with `expiry_date` (61
     `expiry_date:` lines across 8 historical feature dirs at time of writing
     — `grep -c "expiry_date:" changes/*/iteration-log.yaml`) do not break
     future aggregation reads.

Unit-test contract sources (see task's "Unit Test Contract"):
  - ship-manifest.md rule 2 clause concept (documented artifact shape)
  - templates/ship-manifest.yaml accepted_risks field structure (documented
    artifact shape, YAML-parseable)
  - iteration SKILL.md Step 2 accept classification format (documented
    workflow contract)
All concept-token assertions are polarity-bound per references/test-contract.md
rule 2 (presence-not-polarity): every directional assertion has a matching
wrong-direction decoy fixture proving the SAME predicate function reports the
decoy's claim as absent/present in the opposite direction.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
ITERATION = ROOT / "skills" / "iteration" / "SKILL.md"
ITERATION_LOG_TEMPLATE = (
    ROOT / "skills" / "iteration" / "templates" / "iteration-log.yaml"
)
SHIP_MANIFEST_MD = ROOT / "skills" / "validate-and-ship" / "ship-manifest.md"
SHIP_MANIFEST_TEMPLATE = (
    ROOT / "skills" / "validate-and-ship" / "templates" / "ship-manifest.yaml"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Section extractors (scoped, so a whole-file search does not match unrelated
# context — Step 1 / Transition / Auto Mode Gate of iteration/SKILL.md are
# explicitly out of this task's scope and must not leak into these sections).
# ---------------------------------------------------------------------------


def _step2_section(text: str) -> str:
    start = text.find("## Step 2: Triage (Human Gate)")
    assert start != -1, (
        "iteration SKILL.md has no '## Step 2: Triage (Human Gate)' section"
    )
    rest = text[start:]
    end = rest.find("\n## Step 3")
    assert end != -1, "iteration SKILL.md Step 2 section is not bounded by '## Step 3'"
    return rest[:end]


def _yin_side_section(text: str) -> str:
    start = text.find("## Yin-Side Constraints")
    assert start != -1, "iteration SKILL.md has no '## Yin-Side Constraints' section"
    rest = text[start:]
    end = rest.find("\n## Red Flags")
    assert end != -1, (
        "iteration SKILL.md Yin-Side Constraints section is not bounded by '## Red Flags'"
    )
    return rest[:end]


def _red_flags_section(text: str) -> str:
    start = text.find("## Red Flags")
    assert start != -1, "iteration SKILL.md has no '## Red Flags' section"
    rest = text[start:]
    end = rest.find("\n## Support Files")
    assert end != -1, (
        "iteration SKILL.md Red Flags section is not bounded by '## Support Files'"
    )
    return rest[:end]


def _rule2_text(text: str) -> str:
    """Return ship-manifest.md's numbered rule 2 item body (until rule 3)."""
    start = text.find("2. **accepted_risks")
    assert start != -1, (
        "ship-manifest.md has no rule 2 starting with '2. **accepted_risks'"
    )
    rest = text[start:]
    end = rest.find("\n3. **")
    assert end != -1, "ship-manifest.md rule 2 is not bounded by rule 3"
    return rest[:end]


def _format_block(text: str) -> str:
    """Return the fenced ```yaml Format block in ship-manifest.md."""
    start = text.find("```yaml")
    assert start != -1, "ship-manifest.md has no fenced yaml Format block"
    rest = text[start + len("```yaml") :]
    end = rest.find("```")
    assert end != -1, "ship-manifest.md fenced yaml Format block is not closed"
    return rest[:end]


def _accepted_risks_block(fenced_yaml: str) -> str:
    start = fenced_yaml.find("accepted_risks:")
    assert start != -1, "Format block has no 'accepted_risks:' key"
    rest = fenced_yaml[start:]
    end = rest.find("\n\n")
    return rest if end == -1 else rest[:end]


# ---------------------------------------------------------------------------
# Polarity-bound predicates (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function — test-contract.md
# rule 2, presence-not-polarity).
# ---------------------------------------------------------------------------

_NEGATION_ZH = re.compile(r"不需要|不必|無須|無需|不再要求|不用")
_NEGATION_EN = re.compile(r"\bnot\b|\bnever\b|\bwithout\b|\bno longer\b")


def _step2_accept_line(section_lower: str) -> str | None:
    m = re.search(r"\(a\)\s*accept[^\n]*", section_lower)
    return m.group(0) if m else None


def step2_accept_requires_signal(section_lower: str) -> bool:
    """True iff the '(A) Accept' triage-prompt line, on the SAME line, ties
    '必須附' (must attach/include) directly (within a 30-char clause-bounded
    gap, no DOTALL) to 're-review signal', with no negation marker in the
    matched span plus 20 trailing chars (catches a trailing negation like
    '...re-review signal 不再要求' that a leading-only check would miss).
    """
    line = _step2_accept_line(section_lower)
    if line is None:
        return False
    m = re.search(r"必須附[^\n]{0,30}?re-review signal", line)
    if not m:
        return False
    window = line[m.start() : min(len(line), m.end() + 20)]
    return not _NEGATION_ZH.search(window)


def step2_accept_requires_expiry(section_lower: str) -> bool:
    """Same shape as step2_accept_requires_signal but for an 'expir*'
    requirement — must be ABSENT in the healthy doc (see death test 2)."""
    line = _step2_accept_line(section_lower)
    if line is None:
        return False
    m = re.search(r"必須附[^\n]{0,20}?expir\w*", line)
    if not m:
        return False
    window = line[m.start() : min(len(line), m.end() + 20)]
    return not _NEGATION_ZH.search(window)


def yin_declares_accept_requires_signal(section_lower: str) -> bool:
    """True iff Yin-Side Constraints ties 'must include' directly (40-char
    clause-bounded gap) to `re_review_signal`, with no negation marker in the
    matched span plus 30 trailing chars."""
    m = re.search(r"must\s+include\b[^\n]{0,40}?re_review_signal", section_lower)
    if not m:
        return False
    window = section_lower[m.start() : min(len(section_lower), m.end() + 30)]
    return not _NEGATION_EN.search(window)


def yin_tolerates_legacy_expiry(section_lower: str) -> bool:
    """True iff Yin-Side Constraints states legacy `expiry_date` is tolerated
    on read (no error, no required backfill) — a conjunction of FOUR distinct
    positive phrases, so a decoy would have to independently satisfy all four
    to false-positive (silent-green guard: weakest-token-in-an-OR floor is
    avoided by requiring the conjunction, not any single alternative)."""
    return (
        "expiry_date" in section_lower
        and re.search(r"tolerat\w*", section_lower) is not None
        and ("without error" in section_lower or "no error" in section_lower)
        and (
            "without requiring backfill" in section_lower
            or "no backfill" in section_lower
            or ("not require" in section_lower and "backfill" in section_lower)
        )
    )


def rule2_requires_expiry(rule2_lower: str) -> bool:
    """True iff ship-manifest.md rule 2 has a direct 'must have ... expir*'
    requirement clause, proximity-bound to 20 chars so an unrelated 'expir*'
    mention later in the rationale prose (explaining WHY expiry was removed)
    cannot false-positive. This is the exact old-rule-2 shape
    ('accepted_risks must have expiry dates.')."""
    return bool(re.search(r"must\s+have\b[^.!?\n]{0,20}expir\w*", rule2_lower))


def rule2_requires_signal_and_owner(rule2_lower: str) -> bool:
    """True iff rule 2 ties 'must have' to both 're-review signal' and 'owner'
    within the same clause (60/40-char gaps, clause-bounded — stops at
    sentence punctuation, never DOTALL)."""
    return bool(
        re.search(
            r"must\s+have\b[^.!?\n]{0,60}re[-_ ]review[-_ ]signal[^.!?\n]{0,40}\bowner\b",
            rule2_lower,
        )
    )


# Permanent wrong-direction / contradiction decoys (hostile fixtures baked
# into the suite so a regression that reintroduces the exact caught bug is
# detected automatically, not by one-off manual verification).

_STEP2_SIGNAL_NEGATED_DECOY = (
    "  (a) accept — 已知風險，接受（必須附 rationale；re-review signal 不再要求）"
)
_STEP2_CONTRADICTION_DECOY = (
    "  (a) accept — 已知風險，接受（必須附 expiry date + re-review signal + rationale）"
)

_YIN_SIGNAL_NEGATED_DECOY = (
    "accept classifications must include a rationale; a `re_review_signal` is not "
    "required for legacy items."
)

_YIN_EXPIRY_REJECT_DECOY = (
    "legacy `expiry_date` fields must be rejected: reading an old iteration-log.yaml entry "
    "with `expiry_date` raises an error and requires backfill to `re_review_signal`/`owner` "
    "before it is considered valid."
)

_RULE2_CONTRADICTION_DECOY = (
    "2. **accepted_risks must have expiry dates.** risk acceptance is not permanent. "
    "every accepted risk has a date by which it must be re-evaluated. accepted risks "
    "must have a re-review signal and an owner."
)

_RULE2_SIGNAL_NEGATED_DECOY = (
    "2. **accepted_risks do not need a re_review_signal or owner.** just note the risk "
    "and move on."
)


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__iteration_step2_accept_requires_rereview_signal_not_expiry() -> None:
    """Death case 1 (accept 退化成無條件永久豁免), Step 2 triage-prompt half.

    If the '(A) Accept' line loses its 're-review signal' requirement, or an
    'expiry' requirement is reintroduced, this goes RED.
    """
    step2 = _step2_section(read(ITERATION)).lower()

    assert step2_accept_requires_signal(step2), (
        "iteration SKILL.md Step 2 triage prompt's '(A) Accept' line no longer "
        "requires a re-review signal — accept would degenerate into an "
        "unconditional permanent exemption, worse than the old expiry_date "
        "requirement it replaces."
    )
    assert not step2_accept_requires_expiry(step2), (
        "iteration SKILL.md Step 2 triage prompt's '(A) Accept' line still "
        "requires an 'expiry date' — the expiry requirement was supposed to be "
        "removed, not merely supplemented."
    )


def test_death__iteration_yin_side_accept_requires_rereview_signal() -> None:
    """Death case 1 (accept 退化成無條件永久豁免), Yin-Side Constraints half.

    If the Yin-Side Constraints bullet requiring re_review_signal is deleted
    or negated, this goes RED.
    """
    yin = _yin_side_section(read(ITERATION)).lower()

    assert yin_declares_accept_requires_signal(yin), (
        "iteration SKILL.md Yin-Side Constraints no longer requires accept "
        "classifications to include a `re_review_signal` — the yin-side guard "
        "against permanent unconditional risk acceptance was silently removed."
    )


def test_death__iteration_red_flags_still_bans_signal_less_accept() -> None:
    """Death case 1, Red Flags half — 'Never: Accept items without expiry
    dates' must be updated to the signal+owner requirement, not just deleted.
    """
    red_flags = _red_flags_section(read(ITERATION)).lower()

    assert "re-review signal" in red_flags or "re_review_signal" in red_flags, (
        "iteration SKILL.md Red Flags no longer names re-review signal as a "
        "required accept field — the 'Never: accept without X' guard rail is gone."
    )
    assert "owner" in red_flags, (
        "iteration SKILL.md Red Flags no longer names 'owner' as a required "
        "accept field."
    )


def test_death__iteration_yin_side_tolerates_legacy_expiry_date_on_read() -> None:
    """Death case 3 (舊資料相容) — historical iteration-log.yaml `expiry_date`
    entries (10 accept entries across 5 historical features, confirmed by
    grep) must be tolerated on read. If this clause is deleted, a future
    aggregation pass over old logs could silently error or (worse) demand
    backfill that was never promised to users of the old format.
    """
    yin = _yin_side_section(read(ITERATION)).lower()

    assert yin_tolerates_legacy_expiry(yin), (
        "iteration SKILL.md Yin-Side Constraints no longer states that legacy "
        "`expiry_date` entries are tolerated on read (no error, no required "
        "backfill) — reading a historical iteration-log.yaml could now break, "
        "or silently demand backfill that documentation never asked authors "
        "of those old logs to provide."
    )


def test_death__ship_manifest_rule2_no_contradictory_expiry_requirement() -> None:
    """Death case 2 (文件自相矛盾) — ship-manifest.md rule 2 must require
    re_review_signal + owner and must NOT simultaneously carry a live 'must
    have ... expiry' requirement clause. If both requirements coexist, an
    author reading rule 2 gets two contradictory instructions.
    """
    rule2 = _rule2_text(read(SHIP_MANIFEST_MD)).lower()

    assert rule2_requires_signal_and_owner(rule2), (
        "ship-manifest.md rule 2 no longer requires both `re_review_signal` "
        "and `owner` in the same 'must have' clause."
    )
    assert not rule2_requires_expiry(rule2), (
        "ship-manifest.md rule 2 still carries a live 'must have ... expiry' "
        "requirement clause alongside the new signal requirement — this is "
        "the exact self-contradiction (expiry AND signal both required) the "
        "task exists to remove. Mentioning `expires` in explanatory prose "
        "about WHY it was removed is fine; a requirement clause is not."
    )


# ---------------------------------------------------------------------------
# Decoy-detection regression guards (permanent hostile fixtures — prove the
# SAME predicate used above correctly rejects the wrong-direction / reintro-
# duced-contradiction case, per test-contract.md rule 2).
# ---------------------------------------------------------------------------


def test_death__step2_signal_negated_decoy_is_detected_as_missing() -> None:
    assert step2_accept_requires_signal(_STEP2_SIGNAL_NEGATED_DECOY) is False, (
        "The '必須附 rationale；re-review signal 不再要求' decoy (signal "
        "requirement negated later in the same line) was reported as a valid "
        "signal requirement — the polarity/trailing-negation check has regressed."
    )


def test_death__step2_contradiction_decoy_is_detected_as_expiry_required() -> None:
    assert step2_accept_requires_expiry(_STEP2_CONTRADICTION_DECOY) is True, (
        "The '必須附 expiry date + re-review signal + rationale' contradiction "
        "decoy was NOT detected as requiring expiry — the contradiction-guard "
        "predicate has regressed and would silently let this ship."
    )
    assert step2_accept_requires_signal(_STEP2_CONTRADICTION_DECOY) is True, (
        "sanity: the contradiction decoy should ALSO satisfy the signal "
        "requirement (both requirements coexist — that IS the contradiction)."
    )


def test_death__yin_signal_negated_decoy_is_detected_as_missing() -> None:
    assert (
        yin_declares_accept_requires_signal(_YIN_SIGNAL_NEGATED_DECOY.lower()) is False
    ), (
        "The 'must include a rationale; a re_review_signal is not required for "
        "legacy items' decoy was reported as a valid signal requirement — the "
        "trailing-negation window check has regressed."
    )


def test_death__yin_expiry_reject_decoy_is_detected_as_not_tolerant() -> None:
    assert yin_tolerates_legacy_expiry(_YIN_EXPIRY_REJECT_DECOY.lower()) is False, (
        "The 'legacy expiry_date fields must be rejected ... raises an error "
        "and requires backfill' decoy was reported as tolerant — the "
        "conjunction-of-four-phrases guard has regressed."
    )


def test_death__rule2_contradiction_decoy_is_detected() -> None:
    assert rule2_requires_expiry(_RULE2_CONTRADICTION_DECOY) is True, (
        "The rule-2 contradiction decoy (old 'must have expiry dates' sentence "
        "plus a new 'must have signal and owner' sentence, both present) was "
        "NOT detected as requiring expiry — the contradiction guard has regressed."
    )
    assert rule2_requires_signal_and_owner(_RULE2_CONTRADICTION_DECOY) is True, (
        "sanity: the contradiction decoy should ALSO satisfy the signal+owner "
        "requirement — that dual-presence IS the contradiction."
    )


def test_death__rule2_signal_negated_decoy_is_detected_as_missing() -> None:
    assert rule2_requires_signal_and_owner(_RULE2_SIGNAL_NEGATED_DECOY) is False, (
        "The 'accepted_risks do not need a re_review_signal or owner' decoy "
        "was reported as a valid signal+owner requirement — the "
        "'must have' anchor check has regressed."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape)
# ---------------------------------------------------------------------------


def test_unit__ship_manifest_template_accepted_risks_has_signal_and_owner_fields() -> (
    None
):
    """Contract source: templates/ship-manifest.yaml accepted_risks field
    structure (documented artifact shape, YAML-parseable).

    Behavior-preserving refactor (reword the placeholder text, reorder other
    top-level keys) keeps this green. Behavior-actually-broke (the field is
    dropped, or `expires`/`expiry` reappears) turns it red.
    """
    parsed = yaml.safe_load(read(SHIP_MANIFEST_TEMPLATE))
    assert isinstance(parsed, dict) and "accepted_risks" in parsed, (
        "templates/ship-manifest.yaml must have a top-level 'accepted_risks' key"
    )
    risks = parsed["accepted_risks"]
    assert isinstance(risks, list) and len(risks) >= 1, (
        "templates/ship-manifest.yaml 'accepted_risks' must be a non-empty list "
        "(the template entry itself)"
    )
    entry = risks[0]
    assert "re_review_signal" in entry, (
        "templates/ship-manifest.yaml accepted_risks entry is missing "
        "'re_review_signal'"
    )
    assert "owner" in entry, (
        "templates/ship-manifest.yaml accepted_risks entry is missing 'owner'"
    )
    assert (
        "expires" not in entry and "expiry" not in entry and "expiry_date" not in entry
    ), (
        "templates/ship-manifest.yaml accepted_risks entry still has an "
        "expiry-shaped field — the expiry field was supposed to be removed, "
        "not left alongside the new signal fields"
    )
    assert entry["re_review_signal"].strip(), (
        "re_review_signal placeholder must not be empty"
    )
    assert entry["owner"].strip(), "owner placeholder must not be empty"


def test_unit__ship_manifest_md_format_block_documents_signal_and_owner() -> None:
    """Contract source: ship-manifest.md '## Format' fenced yaml block
    (documented artifact shape) — the accepted_risks example.
    """
    fenced = _format_block(read(SHIP_MANIFEST_MD))
    accepted = _accepted_risks_block(fenced)
    assert "re_review_signal" in accepted, (
        "ship-manifest.md Format block's accepted_risks example is missing "
        "'re_review_signal'"
    )
    assert "owner" in accepted, (
        "ship-manifest.md Format block's accepted_risks example is missing 'owner'"
    )
    assert "expires" not in accepted.lower() and "expiry" not in accepted.lower(), (
        "ship-manifest.md Format block's accepted_risks example still shows an "
        "expiry-shaped field alongside the new signal fields"
    )


def test_unit__iteration_step2_accept_format_names_signal_owner_and_rationale() -> None:
    """Contract source: iteration SKILL.md Step 2 accept classification format
    (documented workflow contract) — the '(A) Accept' triage line must name
    all three required pieces of information for an accept decision.
    """
    step2 = _step2_section(read(ITERATION)).lower()
    line = _step2_accept_line(step2)
    assert line is not None, "iteration SKILL.md Step 2 has no '(A) Accept' triage line"

    assert "re-review signal" in line, (
        "'(A) Accept' line does not name 're-review signal'"
    )
    assert "rationale" in line, "'(A) Accept' line no longer requires 'rationale'"
    # "誰負責" (who is responsible) is the Chinese phrase naming the owner
    # requirement inline in the triage-prompt format string.
    assert "誰負責" in line or "owner" in line, (
        "'(A) Accept' line no longer names who is responsible for the signal "
        "(neither '誰負責' nor 'owner' present)"
    )


def test_unit__iteration_log_template_accept_schema_uses_signal_not_expiry() -> None:
    """Contract source: iteration-log.yaml template Rules block + inline
    schema comment (documented artifact shape) — this template is the
    new-write side (Additional Context: "模板是新寫入端，要用新格式"), so it
    must show the new field names, not the retired expiry_date.
    """
    text = read(ITERATION_LOG_TEMPLATE).lower()
    assert "re_review_signal" in text, (
        "iteration-log.yaml template no longer mentions 're_review_signal'"
    )
    assert "owner" in text, (
        "iteration-log.yaml template no longer mentions 'owner' for accept entries"
    )

    # The accept schema comment line (list of {description, ...}) must not
    # retain expiry_date as part of the NEW schema shape.
    schema_comment = re.search(r"accept:\s*\[\]\s*#\s*list of \{[^}]*\}", text)
    assert schema_comment is not None, (
        "iteration-log.yaml template's 'accept: []  # list of {...}' schema "
        "comment is missing or reworded beyond recognition"
    )
    assert "expiry_date" not in schema_comment.group(0), (
        "iteration-log.yaml template's accept schema comment still lists "
        "'expiry_date' as part of the NEW write-side shape"
    )
    assert "re_review_signal" in schema_comment.group(0), (
        "iteration-log.yaml template's accept schema comment does not list "
        "'re_review_signal' as part of the accept entry shape"
    )
