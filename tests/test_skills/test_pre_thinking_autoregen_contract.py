"""
Doc-contract guard and artifact-contract tests for Task 3:
pre-thinking auto-regen + codebase-map fail-honest contract.

Death tests (DC-N numbers are FILE-LOCAL to this contract suite; the hook test
suite tests/test_hooks/test_check_codebase_map.py uses its own independent DC-N
namespace — DC-4/DC-5 here are unrelated to DC-4/DC-5 there):
  DC-4 (regen failure silent reuse): codebase-map/SKILL.md write/regen section
  MUST contain an explicit "do not advance last_updated on failure/abort" clause
  AND a "mark stale + reason" instruction. Absence means a failed regen silently
  leaves last_updated advanced, poisoning the freshness signal for the next session.

  DC-5 (failed-autoregen deadlock / dishonest-completion): both pre-thinking/SKILL.md
  and pre-thinking/flow.md MUST contain an explicit escape clause for when
  auto-initiated regen fails, aborts, or is Phase-4-rejected. Without it, flow.md's
  "do not proceed until regen completes" has no exit — the agent may deadlock,
  loop, or dishonestly claim completion; the exact rot the fail-honest contract
  exists to prevent.

Unit tests (doc-artifact contract):
  Contract source: the SKILL/flow documented-artifact contract — the presence of
  the prescribed behavioral instructions in each skill doc file.
  Assertions are anchored to proximity context (not whole-file substring) so a
  misplaced token in an unrelated section does not produce a false green.
"""

import re
from pathlib import Path

# parents[2] bet: this file lives at tests/test_skills/<name>.py, so
# parents[0]=test_skills/, parents[1]=tests/, parents[2]=repo root.
# If the test layout changes (e.g., a new nesting level), this path breaks.
ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Module-level compiled patterns (hoisted to avoid per-test recompilation)
# ---------------------------------------------------------------------------

# DC-4 / fail-honest: "do not advance|bump last_updated" (backtick-tolerant)
_NO_BUMP_RE = re.compile(
    r"(do not|not) (advance|bump) `?last_updated`?",
    re.IGNORECASE,
)

# DC-4 / fail-honest: "mark ... stale" instruction
_MARK_STALE_RE = re.compile(r"mark.{0,30}stale", re.IGNORECASE)

# DC-5 / escape clause: failure condition → proceed → documentation
# Matches the escape paragraph: "fails/aborts/rejected ... proceed ... information gap / marked stale"
_ESCAPE_CLAUSE_RE = re.compile(
    r"(fails|aborts|rejected).{0,600}"
    r"proceed.{0,300}"
    r"(information.{0,3}gap|marked.{0,3}stale)",
    re.IGNORECASE | re.DOTALL,
)


def _read_skill(relative_path: str) -> str:
    return (ROOT / "skills" / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death_dc4__fail_honest_clause_guards_last_updated() -> None:
    """
    DC-4: regen-failure silent-reuse guard.

    codebase-map/SKILL.md must contain:
      1. An explicit prohibition on advancing last_updated when regen fails
         or is aborted ("do not advance last_updated" or "do not bump
         last_updated").
      2. A "mark stale + reason" instruction so the failure is surfaced rather
         than silently swallowed.

    Without (1): a partial or aborted regen silently preserves an advanced
    timestamp that pre-thinking trusts as fresh next session — the exact
    DC-4 failure mode.
    Without (2): the failure disappears with no audit trail.

    This test MUST be red before the skill doc is edited and green after.
    The anti-over-fit rule does NOT apply here — this is a death test, and the
    exact failure mode (the token "do not advance/bump last_updated") IS its
    contract.
    """
    content = _read_skill("codebase-map/SKILL.md")

    # Behavioral token 1: explicit prohibition on advancing last_updated on failure.
    assert _NO_BUMP_RE.search(content) is not None, (
        "DC-4 FAIL: codebase-map/SKILL.md is missing the fail-honest clause. "
        "The write step must explicitly state 'do not advance last_updated' (or "
        "'do not bump last_updated') when regen fails or is aborted. "
        "Without this guard, a partial regen silently poisons the freshness signal."
    )

    # Behavioral token 2: mark-stale instruction.
    assert _MARK_STALE_RE.search(content) is not None, (
        "DC-4 FAIL: codebase-map/SKILL.md is missing the 'mark stale' instruction. "
        "A failed/aborted regen must mark the map stale (not silently continue). "
        "Add a clause: 'mark the map stale with a recorded reason'."
    )

    # Behavioral token 3: reason must accompany the stale mark.
    has_reason = bool(
        re.search(
            r"stale.{0,120}reason|reason.{0,120}stale",
            content,
            re.IGNORECASE | re.DOTALL,
        )
    )
    assert has_reason, (
        "DC-4 FAIL: codebase-map/SKILL.md marks stale but does not require recording "
        "a reason. The mark-stale instruction must require WHY the regen failed, so "
        "the next session can surface it instead of silently treating the map as fresh."
    )


def test_death_dc5__escape_clause_for_failed_autoregen() -> None:
    """
    DC-5: failed-auto-initiated-regen deadlock / dishonest-completion guard.

    Both pre-thinking/SKILL.md (Atomic Context Boundary) AND pre-thinking/flow.md
    (step 3 atomic context procedure) must contain an explicit escape clause for
    when auto-initiated regen fails, aborts, or is rejected at Phase 4.

    Without it:
      - flow.md's "do not proceed until regen completes" has no exit for a failed regen
      - The agent may deadlock indefinitely, loop, or dishonestly claim completion
      - This is the exact rot the Fail-Honest Contract exists to prevent

    Required behavioral tokens (in close proximity, both files):
      - failure condition: "fails" OR "aborts" OR "rejected"
      - action: "proceed"
      - documentation: "information gap" OR "marked stale"

    This test MUST be red (tokens absent) before the doc edit and green after.
    The anti-over-fit rule does NOT apply — this is a death test, and the
    failure mode tokens ARE the contract.
    """
    for skill_path in ("pre-thinking/SKILL.md", "pre-thinking/flow.md"):
        content = _read_skill(skill_path)
        assert _ESCAPE_CLAUSE_RE.search(content) is not None, (
            f"DC-5 FAIL: {skill_path} is missing the escape clause for failed "
            "auto-initiated regen. When auto-initiated regen fails, aborts, or is "
            "Phase-4-rejected, the agent must NOT block indefinitely or fake completion. "
            "Add: 'If regen fails, aborts, or is rejected → proceed with map marked "
            "stale, record an information gap, continue planning on that basis.'"
        )


# ---------------------------------------------------------------------------
# Unit tests (doc-artifact contract)
# ---------------------------------------------------------------------------


def test_unit__pre_thinking_skill_has_auto_initiate_on_over_threshold() -> None:
    """
    Contract source: skills/pre-thinking/SKILL.md documented-artifact contract.

    The Atomic Context Boundary section must contain an imperative auto-initiate
    instruction that fires when churn exceeds staleness_churn_threshold.

    Assertion is anchored: "auto-initiate" must appear in proximity to "churn",
    "threshold", or "staleness_churn_threshold" so a misplaced token in an
    unrelated section does not produce a false green.

    Advisory wording ("consider regenerating", "may regenerate") silently degrades
    the trigger to optional — the required wording is imperative "auto-initiate".
    The token itself IS the contract (per scar item: "wording must be imperative").

    Contract-gate:
      - Behavior-preserving refactor that preserves proximity of "auto-initiate"
        near "churn"/"threshold": assertion stays green.
      - Clause deleted, moved to unrelated section, or replaced with advisory
        wording: assertion goes red.
    """
    content = _read_skill("pre-thinking/SKILL.md")

    # Proximity-anchored: auto-initiate must appear near churn/threshold context
    _AUTO_INITIATE_ANCHORED = re.compile(
        r"auto-initiate.{0,400}(churn|threshold|staleness_churn_threshold)"
        r"|"
        r"(churn|threshold|staleness_churn_threshold).{0,400}auto-initiate",
        re.IGNORECASE | re.DOTALL,
    )
    assert _AUTO_INITIATE_ANCHORED.search(content) is not None, (
        "pre-thinking/SKILL.md is missing the imperative 'auto-initiate' instruction "
        "near the churn/threshold condition in the Atomic Context Boundary section. "
        "Advisory wording ('consider', 'may') or a misplaced token in an unrelated "
        "section will not satisfy this guard — the instruction must be co-located with "
        "the threshold condition."
    )


def test_unit__pre_thinking_flow_auto_initiate_retains_phase4_review() -> None:
    """
    Contract source: skills/pre-thinking/flow.md documented-artifact contract.

    Section 1 atomic context procedure step 3 must:
      (a) Contain an imperative 'auto-initiate' instruction in proximity to the
          churn/threshold condition (context-anchored, not whole-file).
      (b) Explicitly retain Phase 4 human review or "human review" in HITL mode,
          anchored near the auto-initiate instruction.

    KD2: auto-initiate WITHOUT losing Phase 4 review — both must be present
    in the same context (not just anywhere in the file).

    Contract-gate:
      - Prose rewording that preserves both tokens in proximity: assertions stay green.
      - Either token deleted or moved out of context: corresponding assertion goes red.
    """
    content = _read_skill("pre-thinking/flow.md")

    # (a) auto-initiate near churn/threshold context
    _AUTO_INITIATE_NEAR_THRESHOLD = re.compile(
        r"auto-initiate.{0,300}(churn|threshold|staleness_churn_threshold)"
        r"|"
        r"(churn|threshold|staleness_churn_threshold).{0,300}auto-initiate",
        re.IGNORECASE | re.DOTALL,
    )
    assert _AUTO_INITIATE_NEAR_THRESHOLD.search(content) is not None, (
        "pre-thinking/flow.md section 1 atomic context procedure step 3 is missing "
        "the imperative 'auto-initiate' instruction near the threshold/churn condition. "
        "A token in an unrelated section does not satisfy this guard."
    )

    # (b) Phase 4 / human review retained near the auto-initiate instruction
    _PHASE4_NEAR_AUTO = re.compile(
        r"auto-initiate.{0,400}(phase.?4|human.?review)"
        r"|"
        r"(phase.?4|human.?review).{0,400}auto-initiate",
        re.IGNORECASE | re.DOTALL,
    )
    assert _PHASE4_NEAR_AUTO.search(content) is not None, (
        "pre-thinking/flow.md is missing 'Phase 4' or 'human review' near the "
        "'auto-initiate' instruction. KD2 requires Phase 4 review to be explicitly "
        "retained in HITL mode when auto-initiation triggers regeneration — a token "
        "elsewhere in the file does not satisfy this guard."
    )


def test_unit__codebase_map_skill_documents_auto_initiated_trigger() -> None:
    """
    Contract source: skills/codebase-map/SKILL.md documented-artifact contract.

    The SKILL must document that samsara:pre-thinking can auto-initiate it (not
    only user-invoked). The token is anchored: "auto-initiat" must appear in
    proximity to "staleness_churn_threshold" so a misplaced mention in an
    unrelated section does not produce a false green.

    Contract-gate:
      - Triggers section present with both tokens in proximity: assertion stays green.
      - Trigger section deleted or the tokens separated: assertion goes red.
    """
    content = _read_skill("codebase-map/SKILL.md")

    _AUTO_NEAR_THRESHOLD = re.compile(
        r"auto-initiat.{0,400}staleness_churn_threshold"
        r"|"
        r"staleness_churn_threshold.{0,400}auto-initiat",
        re.IGNORECASE | re.DOTALL,
    )
    assert _AUTO_NEAR_THRESHOLD.search(content) is not None, (
        "codebase-map/SKILL.md does not document the auto-initiated trigger in "
        "proximity to staleness_churn_threshold. A Triggers section must co-locate "
        "both: the auto-initiation trigger and the field that controls the threshold."
    )


def test_unit__codebase_map_skill_documents_staleness_churn_threshold() -> None:
    """
    Contract source: skills/codebase-map/SKILL.md documented-artifact contract.

    The SKILL must reference staleness_churn_threshold so the auto-initiation
    threshold is self-documenting. Without this, the field controlling the trigger
    is invisible to anyone reading the skill doc.

    Contract-gate:
      - Field name present (even in a comment or note): assertion stays green.
      - Field name absent: assertion goes red.
    """
    content = _read_skill("codebase-map/SKILL.md")

    assert "staleness_churn_threshold" in content, (
        "codebase-map/SKILL.md does not mention staleness_churn_threshold. "
        "The field controlling auto-initiation must be documented in the skill "
        "that is triggered by it, so the threshold is self-documenting."
    )


def test_unit__codebase_map_skill_documents_fail_honest_contract() -> None:
    """
    Contract source: skills/codebase-map/SKILL.md documented-artifact contract.

    Positive artifact assertion: the SKILL must contain the fail-honest write
    contract clauses:
      - last_updated must not be advanced on failed/aborted regen
      - The map must be marked stale with a recorded reason

    This is a presence test confirming the fail-honest contract is documented
    as a positive artifact. DC-4 guards the same clauses as a death test
    (fails loudly when absent); both serve their distinct roles.

    Contract-gate:
      - Both clauses present: assertions stay green.
      - Either clause deleted: corresponding assertion goes red.
    """
    content = _read_skill("codebase-map/SKILL.md")

    assert _NO_BUMP_RE.search(content) is not None, (
        "codebase-map/SKILL.md is missing the 'do not advance/bump last_updated' "
        "clause. The fail-honest write contract must be explicit in the skill doc."
    )
    assert _MARK_STALE_RE.search(content) is not None, (
        "codebase-map/SKILL.md is missing the 'mark stale' instruction in the "
        "fail-honest write contract section."
    )
