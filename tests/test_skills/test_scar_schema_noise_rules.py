"""
Doc-contract guard for the scar-report-subtraction feature, spanning three
tasks' additions: task-1 (Scar 產出瘦身 — schema noise rules, the
systemic-scar registry, the implementer report-format dedup, and the
generational backward-compat rebind onto iteration SKILL.md Step 1), task-2
(scar-schema.yaml's new slot/budget form and its anti-dup guard against
regrowing compat-rule text), and task-4 (the numbered-Rule-N to named-anchor
citation sweep and its dangling-citation death test).

These are DOC-PRESENCE / ARTIFACT-SHAPE tests, not behavioral tests — there is
no runtime code in this task. The instruction surfaces themselves (scar-schema
comments, the registry YAML, agents/implementer.md, skills/iteration/SKILL.md)
ARE the contract. A later trim of any of these files can silently delete a
rule with no other signal; these tests make that deletion go RED.

Death cases guarded (see acceptance.yaml):
  DC3 "舊格式 scar 聚合靜默歸零" — the backward-compat rules (plain string,
      missing deferred flag, old resolved_items list) must survive, AND the
      new rules (systemic_ref, status: resolved) must say explicitly that they
      are additive, not a replacement.
  DC4 "systemic_ref 懸空" — a scar report referencing an id NOT in
      .samsara/systemic-scars.yaml must be documented as a parse failure
      (named file + id, never silently skipped), and a MISSING registry file
      must be documented as "mark unknown, pass through the gate" — never a
      silent drop.

Unit-test contract sources (see task's "Unit Test Contract"):
  - scar-schema.yaml Rules block (documented artifact shape)
  - .samsara/systemic-scars.yaml field structure (id/description/
    first_recorded/applies_when) — documented artifact shape
  - agents/implementer.md Report Format section (documented artifact shape)
  - skills/iteration/SKILL.md Step 1 aggregation section (documented workflow
    contract)
All unit tests use concept-token assertions per references/test-contract.md's
self-exemplar rule: they assert the concept (a stable identifier like
`systemic_ref`, or a tolerant regex for `status: resolved`), not a pinned
whole sentence — an honest rewrite of surrounding prose keeps them green.
"""

import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
SCAR_SCHEMA = ROOT / "skills" / "implement" / "templates" / "scar-schema.yaml"
ITERATION = ROOT / "skills" / "iteration" / "flow.md"
IMPLEMENTER = ROOT / "agents" / "implementer.md"
CODE_REVIEWER = ROOT / "agents" / "code-reviewer.md"
SCAR_REPORT_MD = ROOT / "skills" / "implement" / "scar-report.md"
REGISTRY = ROOT / ".samsara" / "systemic-scars.yaml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rules_section(text: str) -> str:
    """Return the scar-schema.yaml '# --- Rules ---' block body.

    Scoped extraction matters: the Schema and Verbatim Example blocks above/
    below also use words like 'resolved_items', so a whole-file search would
    match the wrong context.
    """
    start = text.find("# --- Rules ---")
    assert start != -1, "scar-schema.yaml has no '# --- Rules ---' section"
    rest = text[start:]
    end = rest.find("# --- Verbatim Example")
    assert end != -1, (
        "scar-schema.yaml has no '# --- Verbatim Example' marker to bound the Rules section"
    )
    return rest[:end]


def _iteration_step1_section(text: str) -> str:
    """Return iteration SKILL.md '## Step 1: Aggregate Remaining Scars' body."""
    start = text.find("## Step 1: Aggregate Remaining Scars")
    assert start != -1, (
        "iteration SKILL.md has no '## Step 1: Aggregate Remaining Scars' section"
    )
    rest = text[start:]
    end = rest.find("\n## Step 2")
    assert end != -1, "iteration SKILL.md Step 1 section is not bounded by '## Step 2'"
    return rest[:end]


def _execution_order_section(text_lower: str) -> str:
    """Return implementer.md '## Execution Order' body (until the next '## ')."""
    start = text_lower.find("## execution order")
    assert start != -1, "implementer.md has no '## Execution Order' section"
    rest = text_lower[start + len("## execution order") :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _step0_section(text: str) -> str:
    """Return implementer.md '## STEP 0' body (until the next '## ')."""
    start = text.find("## STEP 0")
    assert start != -1, "implementer.md has no '## STEP 0' section"
    rest = text[start:]
    end = rest.find("\n## ")
    assert end != -1, (
        "implementer.md STEP 0 section is not bounded by a following '## ' heading"
    )
    return rest[:end]


def _report_format_section(text: str) -> str:
    """Return implementer.md '## Report Format' body (to end of file)."""
    start = text.find("## Report Format")
    assert start != -1, "implementer.md has no '## Report Format' section"
    return text[start:]


# ---------------------------------------------------------------------------
# Shared polarity-bound checks (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function — see
# references/test-contract.md rule 2, presence-not-polarity: a token that
# matches a concept's keyword but not its direction must be rejected, and the
# proof is a hostile decoy baked into the test file, not a one-off manual
# temp-swap that leaves no trace for the next reader).
# ---------------------------------------------------------------------------

_NEGATION_NEAR = re.compile(r"\bnot\b|\bnever\b|\bno longer\b")


def _report_format_declares_single_carrier(section_lower: str) -> bool:
    """True iff `section_lower` makes an UNDAMAGED 'single/sole/only carrier'
    claim: the qualifier must sit directly next to 'carrier' (adjacency, not
    scattered co-occurrence — rejects 'only new findings' + an unrelated
    'carrier' word elsewhere), AND the 40 characters immediately preceding the
    phrase must carry no negation marker (rejects 'is NOT the single carrier').
    """
    for m in re.finditer(r"(single|sole|only)\s+carrier", section_lower):
        preceding = section_lower[max(0, m.start() - 40) : m.start()]
        if not _NEGATION_NEAR.search(preceding):
            return True
    return False


_CLAUSE = r"[^.!?\n]"  # clause-bounded gap: stop at sentence punctuation or
# newline, never DOTALL-cross into an unrelated clause (test-contract.md rule
# 5, boundary bleed).

_PLAIN_STRING_EXCLUSION_ANCHOR = re.compile(r"not\s+the\s+old\s+plain[- ]string")
_LEGACY_INVALID_ACTUAL_CLAIM = re.compile(
    rf"legacy-invalid{_CLAUSE}{{0,60}}(count|normally|never\s+treat{_CLAUSE}{{0,20}}parse\s*failure)"
)


def _step1_declares_plain_string_exclusion(sentence_lower: str) -> bool:
    """True iff `sentence_lower` makes an UNDAMAGED legacy-invalid-exclusion
    claim: (a) the negative anchor 'not the old plain-string' appears
    verbatim (rejects an unrelated 'does NOT conform' satisfying a loose
    'not' trigger from far away in the sentence), AND
    (b) 'legacy-invalid' is directly followed, within the same clause (no
        crossing a sentence boundary), by an actual claim ('count'/
        'normally'/'never treat ... parse failure') — rejects a decoy that
        cites the anchor to (wrongly) justify treating plain-string AS a
        parse failure.

    Historical note (task-4, scar-schema numeric-rule sweep): this anchor was
    named `Rule 8` before scar-schema.yaml's rule numbering was retired in
    favor of named anchors; `legacy-invalid` is its current name.
    """
    return bool(
        _PLAIN_STRING_EXCLUSION_ANCHOR.search(sentence_lower)
        and _LEGACY_INVALID_ACTUAL_CLAIM.search(sentence_lower)
    )


# Permanent wrong-direction decoys (yin round-3/round-4 hostile fixtures).
# Feeding these to the SAME functions the production assertions call must
# report the concept MISSING — this is the regression guard against a future
# assertion silently regaining the exact presence-not-polarity gap that was
# caught by mutation testing.

_CARRIER_POLARITY_DECOY = (
    "the scar report yaml is not the single carrier of scar detail — "
    "restate items fully in prose wherever helpful"
).lower()

_PLAIN_STRING_REINTRODUCTION_DECOY = (
    "**parse failure handling:** if a scar report does not conform to "
    "`scar-schema.yaml` (e.g., markdown format instead of yaml — treat old "
    "plain-string format as a parse failure per rule 8) or contains a "
    "dangling `systemic_ref`, list the file explicitly:"
).lower()

# Isolates the renamed _LEGACY_INVALID_ACTUAL_CLAIM branch specifically: the
# decoy above never reaches that branch (it fails the OTHER half of the `and`
# — _PLAIN_STRING_EXCLUSION_ANCHOR — first, so its False result is ambiguous
# about which half caught it). This decoy satisfies the anchor half (contains
# "not the old plain-string" verbatim) but names the legacy-invalid anchor
# WITHOUT the actual claim (count/normally/never-treat-parse-failure) in the
# same clause — must still report False, and must do so because the claim
# regex specifically rejected it.
_LEGACY_INVALID_ANCHOR_WITHOUT_CLAIM_DECOY = (
    "this is not the old plain-string format — the legacy-invalid anchor "
    "governs backward compatibility for future writers."
).lower()


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__dangling_systemic_ref_is_documented_as_parse_failure() -> None:
    """DC4 (systemic_ref 懸空) — split write/read binding (D3 canonical-home
    migration, task-1).

    The `systemic_ref` item-FORM marker stays anchored to scar-schema.yaml —
    that is write-side guidance (task-2 territory, untouched this task). The
    "a dangling id is a parse failure, never silently skip" declaration is
    READ-side (aggregation-time) behavior and is now bound to iteration
    SKILL.md Step 1 — the read-side canonical home. If either half is
    silently deleted, this test goes RED.
    """
    schema_rules = _rules_section(read(SCAR_SCHEMA)).lower()
    assert "systemic_ref" in schema_rules, (
        "scar-schema.yaml Rules section no longer documents the systemic_ref "
        "item form — a future scar writer has no way to know this form exists."
    )

    step1 = _iteration_step1_section(read(ITERATION)).lower()
    assert "parse failure" in step1, (
        "iteration SKILL.md Step 1 no longer says a dangling systemic_ref "
        "is a parse failure — the DC4 death case guard was silently removed."
    )
    assert "dangling" in step1, (
        "iteration SKILL.md Step 1 no longer names the dangling-reference "
        "case explicitly."
    )
    assert "never silently skip" in step1 or "not silently skip" in step1, (
        "iteration SKILL.md Step 1 no longer prohibits silently skipping "
        "a dangling systemic_ref."
    )


def test_death__iteration_registry_missing_marks_unknown_not_silent_drop() -> None:
    """DC4 (systemic_ref 懸空), doc half in iteration SKILL.md Step 1.

    If the missing-registry handling ("mark unknown, pass through the gate,
    never silently disappear") is removed from Step 1, this must go RED.
    """
    step1 = _iteration_step1_section(read(ITERATION)).lower()

    assert "systemic_ref" in step1, (
        "iteration SKILL.md Step 1 no longer mentions systemic_ref resolution "
        "at all — aggregation would not know these items exist."
    )
    assert "unknown" in step1, (
        "iteration SKILL.md Step 1 no longer documents marking systemic_ref "
        "items 'unknown' when the registry is missing."
    )
    assert "missing" in step1 or "unreadable" in step1, (
        "iteration SKILL.md Step 1 no longer names the missing/unreadable "
        "registry-file case."
    )
    assert (
        "silently disappear" in step1
        or "silently drop" in step1
        or "not dropped" in step1
    ), (
        "iteration SKILL.md Step 1 no longer prohibits silently dropping "
        "systemic_ref items when the registry file is absent — this is the "
        "exact DC4 silent-failure mode the death case guards against."
    )
    assert "dangling" in step1 and "parse failure" in step1, (
        "iteration SKILL.md Step 1 no longer documents that a dangling "
        "systemic_ref (registry present, id absent) is a parse failure."
    )


def test_death__iteration_step1_documents_all_three_scar_format_generations() -> None:
    """D6 (世代識別用欄位形狀推斷，無 schema_version).

    Guards the read-side generation-identification contract: plain string
    (Gen 1), `description` dict (Gen 2), and `what`/`bites_when` slots (Gen 3,
    introduced by this feature's task-2) must all remain identifiable by
    field shape alone. If any one generation's identifying language is
    deleted, a future aggregator has no textual instruction telling it that
    generation exists — the exact DC-B silent-drop mode (an entire generation
    of items quietly falls out of aggregation).
    """
    step1 = _iteration_step1_section(read(ITERATION)).lower()

    assert "plain string" in step1, (
        "iteration SKILL.md Step 1 no longer identifies the Gen 1 plain-string "
        "scar item shape — an aggregator has no way to recognize this generation."
    )
    assert "description dict" in step1, (
        "iteration SKILL.md Step 1 no longer identifies the Gen 2 `description` "
        "dict scar item shape."
    )
    assert re.search(r"what\s*/\s*bites_when", step1), (
        "iteration SKILL.md Step 1 no longer identifies the Gen 3 `what`/"
        "`bites_when` slot scar item shape (adjacency-bound check — a bare "
        "'what' or 'bites_when' anywhere in the section is NOT sufficient, "
        "since 'what' is an ordinary English word that would silently keep "
        "this test green even if the Gen 3 line were deleted and replaced "
        "with unrelated prose) — the newest format would be unrecognized by "
        "a future aggregator (DC-B)."
    )


def test_death__iteration_step1_all_generations_count_toward_signal_lost() -> None:
    """DC-B textual guard: the commitment that ALL THREE generations count
    toward signal_lost identically must survive. If deleted, a future
    aggregator could silently treat one generation (e.g. the newest, Gen 3)
    as worth less — or as not countable at all — understating signal_lost
    with no other signal catching it.
    """
    step1 = _iteration_step1_section(read(ITERATION)).lower()

    assert "all three generations" in step1, (
        "iteration SKILL.md Step 1 no longer states that all three scar "
        "format generations are covered — the aggregation-parity commitment "
        "was silently dropped."
    )
    assert "signal_lost" in step1, (
        "iteration SKILL.md Step 1 no longer mentions signal_lost near the "
        "generation-parity commitment."
    )
    assert "identically" in step1 or "equally" in step1 or "the same" in step1, (
        "iteration SKILL.md Step 1 no longer states that all three "
        "generations count toward signal_lost the SAME way — a future "
        "aggregator could silently weight one generation differently."
    )


def test_death__backward_compat_rules_survive_and_extend_to_new_forms() -> None:
    """DC3 (舊格式 scar 聚合靜默歸零) — read-side canonical home (D3): the
    generational backward-compat reading contract now lives in iteration
    SKILL.md Step 1. scar-schema.yaml's old Rules 7/8/11/14 numbering was
    fully retired by task-2 in favor of named anchors (task-4 swept the
    dangling numeric citations that survived that rewrite) — this test
    asserts the READ-side text, which is the copy an aggregator actually
    follows, and no longer pins the old numbers themselves.

    Guards THREE things simultaneously so a partial regression is caught:
      1. the pre-existing rule-7 marker (missing deferred flag / resolved_items)
      2. the pre-existing rule-8 marker (plain-string format, now `legacy-invalid`)
      3. the NEW extension marker saying the newer forms are additive, not a
         replacement, for scar reports already on disk (formerly rule 14,
         now the `legacy-invalid` backward-compat extension)
    If ANY of the three is deleted, this test goes RED.
    """
    step1 = _iteration_step1_section(read(ITERATION)).lower()

    # (1) pre-existing rule 7
    assert "missing deferred flag = false" in step1, (
        "rule 7 backward-compat marker (missing deferred flag = false) is gone "
        "from iteration SKILL.md Step 1 — older scar reports without the flag "
        "would no longer be documented as valid."
    )
    assert "missing resolved_items = no self-iteration" in step1, (
        "rule 7 backward-compat marker for missing resolved_items is gone."
    )

    # (2) pre-existing rule 8
    assert "plain string format backward compatibility" in step1, (
        "rule 8 plain-string backward-compat header is gone from iteration "
        "SKILL.md Step 1."
    )
    assert "do not reject or silently skip plain string format items" in step1, (
        "rule 8's explicit 'do not silently skip plain string items' clause is "
        "gone — this is the exact DC3 silent-zeroing failure mode."
    )

    # (3) NEW extension tying old rules to the new forms introduced by this task
    assert (
        "the legacy-generation reading guarantees continue to apply unchanged" in step1
    ), (
        "the backward-compat extension marker (formerly rule 14, now the "
        "legacy-invalid anchor) is gone — without it there is no documented "
        "guarantee that systemic_ref / status:resolved additions do not "
        "implicitly deprecate the old formats."
    )
    assert "additive" in step1, (
        "the extension marker (rule 14) no longer states that the new forms "
        "are additive, not a replacement, for pre-existing scar reports."
    )


def test_death__iteration_parse_failure_example_does_not_contradict_legacy_invalid() -> (
    None
):
    """Regression guard for a real bug caught by yin review during this task.

    Historical note (task-4, scar-schema numeric-rule sweep): this test was
    named `..._does_not_contradict_rule_8` before scar-schema.yaml's rule
    numbering was retired in favor of named anchors; `legacy-invalid` is the
    anchor's current name, and the name below reflects that.

    skills/iteration/SKILL.md's 'Parse failure handling' sentence once listed
    'old plain-string format' as an example of a non-conforming scar report to
    treat as a parse failure — directly contradicting scar-schema.yaml's
    legacy-invalid anchor (plain string known_shortcuts/silent_failure_conditions
    is a VALID format that must be counted normally, never excluded as a parse
    failure). Had this shipped, an agent following the literal instruction
    would silently drop valid old-format items from signal_lost — the exact
    DC3 failure mode this task exists to prevent.

    This assertion is UNCONDITIONAL — it does not gate on first finding a
    trigger keyword (e.g. "if 'plain-string' in sentence: check for a counter-
    note"). A keyword-gated check is silently defeated by a rewording that
    drops the trigger word while reintroducing the same contradiction under
    different wording (e.g. "legacy string format") — the gate would simply
    never fire, and the assertion would vacuously pass. Instead, the exclusion
    anchor is asserted present ALWAYS; if it is missing (for any reason,
    including a rewording that removed it or moved it out of this sentence),
    this test goes RED — loud, not skipped.

    Round-4 mutation testing (yin) proved the FIRST fix of this test still had
    a presence-not-polarity + boundary-bleed gap: a wide `.{0,100}` DOTALL
    window let an unrelated "does NOT conform" satisfy the "not" trigger, and
    let a decoy citing "per Rule 8" to (wrongly) justify treating plain-string
    AS a parse failure still match. See _step1_declares_plain_string_exclusion
    (shared with test_death__plain_string_reintroduction_decoy_is_detected)
    for the clause-bounded, claim-anchored replacement.
    """
    step1 = _iteration_step1_section(read(ITERATION))
    marker = "Parse failure handling:"
    idx = step1.find(marker)
    assert idx != -1, "Step 1 no longer has a 'Parse failure handling:' sentence"
    sentence_end = step1.find("\n\n", idx)
    assert sentence_end != -1, (
        "Step 1's 'Parse failure handling' sentence is not bounded by a blank "
        "line — cannot isolate it to check the Rule 8 exclusion anchor."
    )
    sentence = step1[idx:sentence_end].lower()

    assert _step1_declares_plain_string_exclusion(sentence), (
        "Step 1's Parse failure handling sentence no longer carries the explicit "
        "'NOT the old plain-string ... Rule 8 requires counting normally' exclusion "
        "claim (unconditional, clause-bounded check — not gated behind a trigger "
        "keyword, not fooled by an unrelated 'not' or a decoy citing Rule 8 to "
        "justify the opposite claim). This recreates the DC3 contradiction that "
        "was caught and fixed once already: plain-string format wrongly treated "
        "as a parse failure, contradicting Rule 8."
    )


def test_death__plain_string_reintroduction_decoy_is_detected() -> None:
    """Permanent regression guard for the yin round-4 hostile mutation.

    yin proved by mutation testing that citing "per Rule 8" to justify
    treating plain-string AS a parse failure ("(treat old plain-string format
    as a parse failure per Rule 8)") satisfied the round-3 regex (an unrelated
    "does NOT conform" trigger + a 100-char DOTALL window reaching "rule 8")
    and stayed GREEN — silently missing the reintroduced DC3 bug. Feeding that
    exact decoy to the SAME function the production death test calls
    (_step1_declares_plain_string_exclusion) must report the claim MISSING.
    This bakes the hostile fixture into the suite permanently, replacing the
    one-off manual temp-swap verification from rounds 2-3 (test-contract.md
    rule 2: presence-not-polarity).
    """
    assert (
        _step1_declares_plain_string_exclusion(_PLAIN_STRING_REINTRODUCTION_DECOY)
        is False
    ), (
        "The plain-string reintroduction decoy (Rule 8 cited to justify treating "
        "plain-string AS a parse failure) was reported as a valid exclusion claim "
        "— the polarity/boundary-bleed check has regressed."
    )


def test_death__legacy_invalid_anchor_without_claim_decoy_is_detected() -> None:
    """Task-4 tripwire for the renamed `_LEGACY_INVALID_ACTUAL_CLAIM` branch.

    The pre-existing reintroduction decoy above never exercises this branch:
    it fails `_PLAIN_STRING_EXCLUSION_ANCHOR` first, so its False result
    proves nothing about the claim regex specifically. This decoy satisfies
    the anchor half (contains "not the old plain-string" verbatim) but names
    `legacy-invalid` WITHOUT the actual claim in the same clause — if a
    future edit widens `_LEGACY_INVALID_ACTUAL_CLAIM` to match on the bare
    anchor name alone (dropping the count/normally/never-treat-parse-failure
    requirement), this decoy starts reporting a valid exclusion claim and
    this test goes RED.
    """
    assert (
        _step1_declares_plain_string_exclusion(
            _LEGACY_INVALID_ANCHOR_WITHOUT_CLAIM_DECOY
        )
        is False
    ), (
        "The legacy-invalid-anchor-without-claim decoy (anchor named, but no "
        "count/normally/never-treat-parse-failure claim attached) was reported "
        "as a valid exclusion claim — _LEGACY_INVALID_ACTUAL_CLAIM has "
        "regressed to matching on the bare anchor name."
    )


def test_death__implementer_step0_four_questions_present() -> None:
    """Guards STEP 0's four-question structure against over-deletion.

    Checks structurally (a numbered list of >= 4 items inside STEP 0), not by
    pinning exact question wording, so an honest rewrite of a question stays
    green — but deleting questions down to <4 goes RED.
    """
    step0 = _step0_section(read(IMPLEMENTER))
    numbered_items = re.findall(r"^\d+\.\s", step0, flags=re.MULTILINE)
    assert len(numbered_items) >= 4, (
        f"implementer.md STEP 0 section has only {len(numbered_items)} numbered "
        "questions; the four-question prerequisite gate was over-deleted."
    )
    assert "needs_context" in step0.lower(), (
        "implementer.md STEP 0 no longer instructs reporting NEEDS_CONTEXT when "
        "question 3 cannot be answered with specifics."
    )


def test_death__implementer_death_test_before_unit_test_ordering_present() -> None:
    """Guards the death-test-before-unit-test ordering inside Execution Order.

    If a future edit reorders these steps (or drops one), this goes RED.
    """
    section = _execution_order_section(read(IMPLEMENTER).lower())
    death_idx = section.find("write death tests")
    unit_idx = section.find("write contract-bound unit tests")
    assert death_idx != -1, "'write death tests' step missing from Execution Order"
    assert unit_idx != -1, (
        "'write contract-bound unit tests' step missing from Execution Order"
    )
    assert death_idx < unit_idx, (
        f"death-test step (index {death_idx}) must precede the unit-test step "
        f"(index {unit_idx}) in Execution Order — death-test-first ordering was "
        "silently reversed or removed."
    )


def test_death__systemic_scars_registry_is_not_gitignored() -> None:
    """
    Guards the .gitignore carve-out for the registry file (discovered mid-task:
    the whole `.samsara/` directory was blanket-ignored as "kept locally, not
    shipped" — a bare `.samsara` directory-ignore cannot be undone by a
    negation pattern, so the fix rewrote it to `.samsara/*` plus an explicit
    `!.samsara/systemic-scars.yaml` exception).

    If a future edit reverts to a bare `.samsara` ignore, or drops the
    negation line, the registry silently stops being trackable: every fresh
    clone ships with a missing registry and every systemic_ref item silently
    degrades to the "registry missing -> unknown" path, with no error and no
    other test catching it.

    Returncode contract for `git check-ignore`:
      0  — path IS ignored (bad: the registry would not be committed)
      1  — path is NOT ignored (good)
      128 — fatal error, e.g. not inside a git repo (fail loudly)
    """
    result = subprocess.run(
        ["git", "check-ignore", str(REGISTRY)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1), (
        f"git check-ignore exited with returncode {result.returncode} for {REGISTRY} "
        f"— unexpected git error. stderr: {result.stderr!r}. This guard is now blind."
    )
    assert result.returncode == 1, (
        f"{REGISTRY} is git-ignored (matched: {result.stdout.strip()!r}). "
        "The registry cannot be committed or shipped, silently degrading every "
        "systemic_ref resolution to the 'registry missing' path on a fresh clone. "
        "Check .gitignore for a bare '.samsara' directory-ignore (negation cannot "
        "undo it) or a missing '!.samsara/systemic-scars.yaml' exception line."
    )


def test_death__implementer_scar_report_necessity_present() -> None:
    """Guards the 'no scar report = completion_unverified' constraint.

    This is the load-bearing sentence that makes scar reports mandatory, not
    optional. If it is deleted, this goes RED.
    """
    text = read(IMPLEMENTER).lower()
    assert "completion_unverified" in text, (
        "implementer.md no longer states that a task without a scar report is "
        "'completion_unverified' — the mandatory-scar-report constraint was "
        "silently removed."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape)
# ---------------------------------------------------------------------------


def test_unit__systemic_scars_registry_has_required_field_shape() -> None:
    """Contract source: documented artifact shape of .samsara/systemic-scars.yaml.

    Behavior-preserving refactor (reorder entries, reword `applies_when`
    prose) keeps this green. Behavior-actually-broke (an entry missing a
    required field, or a malformed id) turns it red.
    """
    parsed = yaml.safe_load(read(REGISTRY))
    assert isinstance(parsed, dict) and "entries" in parsed, (
        "systemic-scars.yaml must have a top-level 'entries' list"
    )
    entries = parsed["entries"]
    assert isinstance(entries, list) and len(entries) >= 1, (
        "systemic-scars.yaml 'entries' must be a non-empty list"
    )

    required_fields = {"id", "description", "first_recorded", "applies_when"}
    kebab_case = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    date_shape = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    ids_seen = []
    for entry in entries:
        missing = required_fields - entry.keys()
        assert not missing, f"entry {entry.get('id')!r} is missing fields: {missing}"
        assert kebab_case.match(entry["id"]), f"id {entry['id']!r} is not kebab-case"
        assert date_shape.match(str(entry["first_recorded"])), (
            f"first_recorded {entry['first_recorded']!r} is not an ISO date (YYYY-MM-DD)"
        )
        assert entry["description"].strip(), (
            f"entry {entry['id']!r} has an empty description"
        )
        assert entry["applies_when"].strip(), (
            f"entry {entry['id']!r} has an empty applies_when"
        )
        ids_seen.append(entry["id"])

    # Task-specified prefilled ids must exist — this is the artifact's required content,
    # not an implementation detail (referenced by the task's own dogfood scar report).
    assert "doc-vs-runtime-obedience" in ids_seen, (
        "registry is missing the required 'doc-vs-runtime-obedience' entry"
    )
    assert "doc-instruction-no-code-enforcement" in ids_seen, (
        "registry is missing the required 'doc-instruction-no-code-enforcement' entry"
    )
    assert len(ids_seen) == len(set(ids_seen)), "systemic-scars.yaml has duplicate ids"


def test_unit__scar_schema_documents_verified_true_single_line_and_status_resolved() -> (
    None
):
    """Contract source: scar-schema.yaml Rules block (documented artifact shape).

    Concept-token assertions, not pinned sentences:
      - the verified:true compression rule names 'note' as an evidence
        pointer (file:line / test name), not free narrative
      - the status:resolved in-place form replaces resolved_items re-copy
    """
    rules = _rules_section(read(SCAR_SCHEMA)).lower()

    assert "single line" in rules, (
        "no rule documents compressing verified:true assumptions to a single line"
    )
    assert "file:line" in rules or "test name" in rules, (
        "no rule names a concrete evidence-pointer form (file:line / test name) "
        "for verified:true assumption notes"
    )
    assert re.search(r"status:\s*resolved", rules), (
        "no rule documents the in-place `status: resolved` marker form"
    )
    assert "resolution" in rules, (
        "no rule documents the one-line `resolution` field accompanying status: resolved"
    )
    assert "review-round" in rules or "round-by-round" in rules, (
        "no rule prohibits the review-round-diary narrative anti-pattern"
    )
    assert "write filter" in rules or (
        "future reader" in rules and "change their action" in rules
    ), (
        "no rule documents the write-filter question for gating what gets "
        "written into a scar report"
    )


def test_death__scar_schema_requires_direct_single_fact_bullets() -> None:
    """A length-bounded bullet can still hide a paragraph-sized argument.

    The write contract must shape wording as well as YAML structure: one
    actionable fact per bullet, result first, with verification history kept
    out of the item text.
    """
    rules = _rules_section(read(SCAR_SCHEMA)).lower()

    assert "direct-bullets" in rules, (
        "scar-schema.yaml has no named direct-bullets writing contract"
    )
    assert re.search(r"one (?:actionable )?fact", rules) and "bullet" in rules, (
        "the direct-bullets contract no longer requires one fact per bullet"
    )
    assert "result first" in rules or "point first" in rules, (
        "the direct-bullets contract no longer requires the key point first"
    )
    assert "verification" in rules and (
        "pointer" in rules or "go-elsewhere" in rules
    ), (
        "the direct-bullets contract no longer routes verification detail out "
        "of scar item prose"
    )


def test_death__scar_schema_active_document_is_a_minimal_honest_default() -> None:
    """The injected YAML must not nudge writers to populate optional scars."""
    schema = yaml.safe_load(read(SCAR_SCHEMA))

    assert schema == {
        "task_id": "task-N",
        "completion_status": "done",
        "known_shortcuts": [],
        "silent_failure_conditions": [],
        "assumptions_made": [],
        "debt_registered": False,
        "debt_location": None,
        "structural_decisions": [],
    }, (
        "the active scar-schema document must be the minimal valid report; "
        "optional examples belong in comments so writers do not fill them by default"
    )


def test_death__scar_schema_omits_task_history_from_injected_writer_contract() -> None:
    """Implementation history consumes attention but gives writers no action."""
    schema = read(SCAR_SCHEMA).lower()
    for historical_phrase in (
        "three generations",
        "task-3 onward",
        "left 不動 by this task",
    ):
        assert historical_phrase not in schema, (
            f"writer contract still contains task-local history: {historical_phrase!r}"
        )


def test_death__live_agents_use_current_scar_item_and_resolution_forms() -> None:
    """Concrete stale agent instructions override the injected schema."""
    implementer = read(IMPLEMENTER).lower()
    reviewer = read(CODE_REVIEWER).lower()
    integrity = reviewer[reviewer.index("### 6. scar report integrity") :]
    integrity = integrity.split("\n### 7.", maxsplit=1)[0]

    assert "optional `resolved_items`" not in implementer, (
        "implementer still advertises retired resolved_items as a current write form"
    )
    assert "{description, deferred_to_feature_iteration}" not in integrity, (
        "code reviewer still requires the retired description item shape"
    )
    for slot in ("what", "bites_when", "where"):
        assert slot in integrity, (
            f"code reviewer does not require the current {slot!r} scar slot"
        )
    assert "status: resolved" in integrity and "resolution" in integrity, (
        "code reviewer does not validate the current in-place resolution form"
    )
    assert "resolved_items" not in integrity, (
        "code reviewer still reviews the retired resolved_items carrier"
    )


def test_unit__implementer_report_format_avoids_duplicate_scar_carriers() -> None:
    """Contract source: agents/implementer.md Report Format section (artifact shape).

    Behavior-preserving refactor (reword a bullet) stays green as long as the
    concept survives. Behavior-actually-broke (Report Format goes back to
    demanding full scar content restated in prose) turns it red.

    Round-4 mutation testing (yin) proved the round-3 adjacency-only regex
    still had a presence-not-polarity gap: reversing the sentence to "is NOT
    the single carrier ... restate items fully in prose" still matched,
    because the regex checked adjacency but not the polarity of the clause it
    sits in. See _report_format_declares_single_carrier (shared with
    test_death__carrier_polarity_decoy_is_detected) for the negation-bound
    replacement.
    """
    section = _report_format_section(read(IMPLEMENTER)).lower()

    assert _report_format_declares_single_carrier(section), (
        "Report Format no longer states the scar YAML is the single/sole "
        "carrier of scar detail — the qualifier word must sit directly next "
        "to 'carrier' (adjacent phrase, not merely co-occurring anywhere in "
        "the section), AND the phrase must not be negated ('is NOT the single "
        "carrier') within the 40 characters preceding it."
    )
    assert "do not re-describe" in section or "do not re-paste" in section, (
        "Report Format no longer prohibits re-describing scar content in prose"
    )
    assert "counts only" in section or (
        "numbers" in section and "not restated item text" in section
    ), "Report Format no longer restricts the self-iteration summary to counts"
    assert (
        "only new findings" in section
        or "new findings only" in section
        or "not already captured" in section
    ), (
        "Report Format no longer restricts self-review findings to items not "
        "already captured in the scar report"
    )


def test_death__carrier_polarity_decoy_is_detected_as_missing() -> None:
    """Permanent regression guard for the yin round-4 hostile mutation.

    yin proved by mutation testing that reversing the claim's polarity ("the
    scar report yaml is NOT the single carrier of scar detail — restate items
    fully in prose wherever helpful") still matched the round-3
    adjacency-only regex and stayed GREEN — silently missing the concept's
    negation. Feeding that exact decoy to the SAME function the production
    unit test calls (_report_format_declares_single_carrier) must report the
    claim MISSING. This bakes the hostile fixture into the suite permanently,
    replacing the one-off manual temp-swap verification from earlier rounds
    (test-contract.md rule 2: presence-not-polarity).
    """
    assert _report_format_declares_single_carrier(_CARRIER_POLARITY_DECOY) is False, (
        "The carrier-polarity decoy (single carrier claim negated) was reported "
        "as a valid single-carrier claim — the polarity check has regressed."
    )


def test_unit__iteration_step1_documents_all_three_systemic_ref_resolution_paths() -> (
    None
):
    """Contract source: skills/iteration/SKILL.md Step 1 section (documented
    workflow contract) — the three resolution branches for systemic_ref.
    """
    step1 = _iteration_step1_section(read(ITERATION)).lower()

    assert ".samsara/systemic-scars.yaml" in step1, (
        "Step 1 no longer names the registry file path to resolve systemic_ref against"
    )
    assert "present" in step1, (
        "Step 1 no longer documents the 'id found in registry' path"
    )
    assert "dangling" in step1, "Step 1 no longer documents the dangling-id path"
    assert "unknown" in step1, (
        "Step 1 no longer documents the missing-registry -> unknown path"
    )


def test_unit__scar_report_md_documents_write_filter_and_review_diary_antipattern() -> (
    None
):
    """Contract source: skills/implement/scar-report.md (documented format guide)."""
    text = read(SCAR_REPORT_MD).lower()
    assert "write filter" in text, "scar-report.md does not document the write filter"
    assert "narrative" in text and (
        "review diary" in text or "review-round" in text or "round-by-round" in text
    ), (
        "scar-report.md does not document the review-diary narrative anti-pattern "
        "(both 'narrative' and a review-diary/review-round marker must be present — "
        "'narrative' alone is a green-by-construction word that proves nothing about "
        "the anti-pattern)"
    )


# ---------------------------------------------------------------------------
# Iteration-fix 1 (feature workflow-subtraction-optimization, Level 2):
# when Level 2 iteration is default-skipped, Validate & Ship's Remaining
# Exposure Check is the final place a dangling systemic_ref can be
# caught before ship. This guard pins that clause.
# ---------------------------------------------------------------------------

VALIDATE_AND_SHIP = ROOT / "skills" / "validate-and-ship" / "SKILL.md"


def _remaining_exposure_section(text: str) -> str:
    start = text.find("### 1. Remaining Exposure Check")
    assert start != -1, (
        "validate-and-ship SKILL.md has no Remaining Exposure Check heading"
    )
    rest = text[start:]
    end = rest.find("\n### ")
    return rest if end == -1 else rest[:end]


def test_death__validate_and_ship_remaining_exposure_resolves_systemic_refs() -> None:
    """DEATH: if Remaining Exposure loses its systemic_ref resolution
    clause, a feature that default-skips Level 2 iteration ships with dangling
    systemic_refs and nothing ever resolves them (task-1 scar, deferred item)."""
    section = _remaining_exposure_section(read(VALIDATE_AND_SHIP)).lower()
    assert "systemic_ref" in section, (
        "SILENT FAILURE: Remaining Exposure Check no longer mentions systemic_ref "
        "resolution — the iteration-skip path ships dangling refs unchecked."
    )
    # Polarity: a dangling or unreadable ref is unknown, never an implicit pass.
    m = re.search(r"dangling[^.!?\n]{0,60}unknown", section)
    assert m, (
        "SILENT FAILURE: the clause no longer binds 'dangling' to 'unknown' "
        "within one clause — presence without that polarity lets a "
        "reworded clause drop the actual guarantee."
    )


# ---------------------------------------------------------------------------
# Task-2 (feature scar-report-subtraction): scar-schema.yaml rewritten to a
# one-page WRITE contract. Compat reading rules (Gen 1/2/3 backward
# compatibility) now live SOLELY in iteration SKILL.md Step 1 (task-1's new
# canonical home) — schema must never regrow them (DC-C single-source
# drift). Schema must instead declare the new what/bites_when/where/
# accepted_because slot form and its budget numbers, so a future trim cannot
# silently narrow the write contract with no other signal catching it.
# ---------------------------------------------------------------------------

_FORBIDDEN_COMPAT_TOKENS = (
    "plain string format backward compatibility",
    "missing deferred flag = false",
    "missing resolved_items = no self-iteration",
    "do not reject or silently skip plain string format items",
    "rules 7 and 8 continue to apply unchanged",
    "remain valid and must still be read as resolved",
)


def test_death__schema_does_not_regrow_compat_rule_tokens() -> None:
    """DC-C (單一源漂移): if any of these exact backward-compat reading
    tokens is pasted back into scar-schema.yaml, the write-side and
    read-side (iteration SKILL.md Step 1) copies would drift independently
    again with nothing else catching it. This must go RED the moment any
    ONE token reappears verbatim in scar-schema.yaml.
    """
    schema = read(SCAR_SCHEMA).lower()
    for token in _FORBIDDEN_COMPAT_TOKENS:
        assert token not in schema, (
            f"scar-schema.yaml re-introduced compat-rule token {token!r} — "
            "the canonical home for scar-format backward-compat reading "
            "rules is iteration SKILL.md Step 1 (task-1); scar-schema.yaml "
            "(the write contract) must not restate it (DC-C single-source "
            "drift, anti-dup death test)."
        )


def test_death__schema_declares_new_slot_form_and_budget_numbers() -> None:
    """Guards against a future trim silently narrowing the write contract:
    the current-generation item slot fields, and the length-budget numbers
    a scar report must be written within, must both remain declared in
    scar-schema.yaml. If either disappears, a writer (or task-3's validator,
    which reads these same numbers) has no textual source for the contract.

    Anchoring notes (yin mutation-testing round, both fixed after a real
    catch):
      - Slot tokens are anchored to line-start/list-item position
        (`^\\s*-?\\s*<slot>:`), NOT a bare substring. A bare `"where:" in
        schema` is silent-green: deleting every actual `where:` slot line
        still passes, because the prose word "elsewhere" (inside the
        `go-elsewhere:` anchor heading) contains "where:" as a substring.
        Line-start anchoring rejects that mid-word match.
      - Budget numbers are matched with a bounded regex tolerant of both the
        `≤` glyph and an ASCII `<=` fallback, with a trailing `\\b` word
        boundary — `≤6` alone would falsely stay green if the number were
        silently widened to `≤60` (substring match), and pinning only the
        `≤` glyph would falsely go red on an honest `≤`→`<=` rewording that
        preserves the exact same figure.
    """
    schema = read(SCAR_SCHEMA).lower()

    slot_patterns = {
        "scar_id:": r"^\s*(?:#\s*)?-?\s*scar_id:",
        "what:": r"^\s*(?:#\s*)?-?\s*what:",
        "bites_when:": r"^\s*(?:#\s*)?-?\s*bites_when:",
        "where:": r"^\s*(?:#\s*)?-?\s*where:",
        "status:": r"^\s*(?:#\s*)?-?\s*status:",
        "iteration:": r"^\s*(?:#\s*)?-?\s*iteration:",
    }
    for slot, pattern in slot_patterns.items():
        assert re.search(pattern, schema, re.MULTILINE), (
            f"scar-schema.yaml no longer declares the {slot!r} slot field at "
            "line-start/list-item position — the current-generation item "
            "form was silently narrowed (a substring match on prose "
            "elsewhere, e.g. 'go-elsewhere:', must NOT satisfy this)."
        )

    budget_patterns = {
        "≤200": r"(?:≤|<=)\s*200\b",
        "≤120": r"(?:≤|<=)\s*120\b",
        "≤14": r"(?:≤|<=)\s*14\b",
        "≤10": r"(?:≤|<=)\s*10\b",
        "≤90": r"(?:≤|<=)\s*90\b",
    }
    for label, pattern in budget_patterns.items():
        assert re.search(pattern, schema), (
            f"scar-schema.yaml no longer states the {label!r} budget figure "
            "(checked tolerant of the ≤/<= glyph, bounded to the exact "
            "number by a word boundary) — a future validator (task-3) and a "
            "future writer would have no shared textual source for this "
            "number."
        )


# ---------------------------------------------------------------------------
# Task-4 (feature scar-report-subtraction): task-2 retired scar-schema.yaml's
# Rule 1-17 numbering in favor of named anchors. Every cross-file citation
# that still says "Rule N" now points at nothing a grep can resolve — DC-D
# (a dangling numbered-rule citation surviving the sweep, silently, with the
# surrounding doc "looking consistent"). This section sweeps all such
# citations in the live instruction surfaces and guards the sweep against
# regression.
# ---------------------------------------------------------------------------

_LIVE_SURFACE_DIRS = ("skills", "agents", ".samsara")
_LIVE_SURFACE_EXCLUDED_PARTS = {"changes", "docs", "bugfix", "dist"}
_LIVE_SURFACE_SUFFIXES = {".md", ".py", ".yaml", ".yml"}

# Single source of truth for the named scar-schema anchors. Referenced by both
# the death test's docstring/assert message and the unit test below it, so
# the list is written out exactly once.
_NAMED_ANCHORS = (
    "write-filter",
    "direct-bullets",
    "verified-pointer",
    "no-review-diary",
    "granularity-floor",
    "dual-face",
    "forced-by-evidence",
    "systemic-ref",
    "resolved-in-place",
    "validation-finding-ref",
    "legacy-invalid",
    "go-elsewhere",
)

# Case-insensitive numbered-rule citation: "Rule 13", "schema Rule 9",
# "rules 7 and 8", "rules: 7,8,9" (colon-separated enumeration — the shape
# actually found in .samsara/modules/skill-implement.yaml during the task-4
# sweep; a bare `rules?\s+[0-9]` pattern misses this list shape because a
# colon sits between the word and the first digit). Excludes the unrelated
# "Mother Rule N" numbering (agents/code-reviewer.md's own permanent
# code-quality rule set, a different intentionally-numbered system this task
# does not touch) via a negative lookbehind.
_DANGLING_RULE_CITATION = re.compile(
    r"(?<!mother )(schema )?rules?\s*:?\s*[0-9]", re.IGNORECASE
)


def _iter_live_surface_files():
    for dirname in _LIVE_SURFACE_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in _LIVE_SURFACE_SUFFIXES:
                continue
            if _LIVE_SURFACE_EXCLUDED_PARTS & set(path.relative_to(ROOT).parts):
                continue
            yield path


def test_death__no_dangling_numbered_rule_citation_in_live_surfaces() -> None:
    """DC-D (數字規則引用全量 sweep, task-4): scar-schema.yaml's Rule 1-17
    numbering was retired by task-2 in favor of the 10 named anchors in
    `_NAMED_ANCHORS` above. Any surviving numeric rule citation ("Rule 13",
    "schema Rule 9", "rules 7 and 8") in a live instruction surface
    (skills/, agents/, .samsara/) now points at nothing a future reader can
    resolve by grep — a silent dangling reference. This must go RED the
    moment ANY such citation exists anywhere in these three directories,
    and stay RED for every citation found, not just the first (a sweep that
    silently stops after the first hit is itself a DC-D failure mode).

    Excludes: changes/, docs/, bugfix/, dist/ (history and generated
    snapshots — dist/ in particular still carries the pre-sweep, numbered
    schema until a future regeneration task runs; see task-4 scar report,
    known_shortcuts). Also excludes the unrelated "Mother Rule N" numbering
    (agents/code-reviewer.md's own permanent code-quality rule set) via a
    negative lookbehind — a different rule system, not a scar-schema
    citation, and out of this task's scope.
    """
    hits = []
    for path in _iter_live_surface_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _DANGLING_RULE_CITATION.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert not hits, (
        "Dangling numbered scar-schema rule citation(s) found in live "
        "instruction surfaces (skills/, agents/, .samsara/) — rewrite each "
        "to the correct named anchor ("
        + ", ".join(_NAMED_ANCHORS)
        + "):\n"
        + "\n".join(hits)
    )


def test_unit__rewritten_citations_name_the_correct_anchor() -> None:
    """Contract source: documented artifact shape of the live instruction
    surfaces task-4 rewired from numbered scar-schema.yaml Rule references to
    named anchors. The absence-only death test above cannot distinguish "the
    citation was correctly renamed" from "the citation (and its meaning) was
    silently deleted" — both leave zero digits behind. This unit test asserts
    the POSITIVE contract: the correct anchor name must be present at each
    rewired citation point.

    Behavior-preserving refactor (reword the surrounding sentence, keep the
    anchor name) keeps this green. Behavior-actually-broke (the citation is
    deleted outright, or renamed to the WRONG anchor) turns it red.
    """
    implementer = read(IMPLEMENTER)
    assert "resolved-in-place" in implementer, (
        "agents/implementer.md no longer names the resolved-in-place anchor "
        "at its status:resolved citation points."
    )
    assert "write-filter" in implementer, (
        "agents/implementer.md Report Format no longer names the write-filter anchor."
    )
    for anchor in ("granularity-floor", "dual-face", "forced-by-evidence"):
        assert anchor in implementer, (
            f"agents/implementer.md Structural Decisions section no longer "
            f"names the {anchor!r} anchor."
        )

    skill_implement = read(ROOT / "skills" / "implement" / "SKILL.md")
    assert "resolved-in-place" in skill_implement, (
        "skills/implement/SKILL.md Execution Order no longer names the "
        "resolved-in-place anchor."
    )
    assert "legacy-invalid" in skill_implement, (
        "skills/implement/SKILL.md Execution Order no longer names the "
        "legacy-invalid anchor."
    )

    step1 = _iteration_step1_section(read(ITERATION)).lower()
    for anchor in ("systemic-ref", "resolved-in-place", "legacy-invalid"):
        assert anchor in step1, (
            f"iteration SKILL.md Step 1 no longer names the {anchor!r} anchor "
            "at its rewired citation point."
        )

    registry = read(REGISTRY)
    assert "systemic-ref" in registry, (
        ".samsara/systemic-scars.yaml header comments no longer name the "
        "systemic-ref anchor at their scar-schema.yaml citation points."
    )

    validate_format = read(
        ROOT / "skills" / "implement" / "scripts" / "validate_format.py"
    )
    for anchor in ("granularity-floor", "legacy-invalid", "forced-by-evidence"):
        assert anchor in validate_format, (
            f"validate_format.py no longer names the {anchor!r} anchor in its "
            "docstrings/finding messages."
        )

    # scar-report.md's citations were task-2's edits, not task-4's — but the
    # positive contract covers every live citation surface regardless of
    # which task wrote it (a future trim here is just as silent a break).
    scar_report_md = read(SCAR_REPORT_MD)
    for anchor in ("write-filter", "direct-bullets", "no-review-diary"):
        assert anchor in scar_report_md, (
            f"skills/implement/scar-report.md no longer names the {anchor!r} "
            "anchor at its scar-schema.yaml citation point."
        )
