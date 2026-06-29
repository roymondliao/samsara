"""
Tests for codebase-map schema integrity.

Death tests:
  - DC (dead-field resurrection): staleness_threshold_days has no live consumer in
    hooks/, skills/, samsara_cli/ after removal from the template.
  - One-threshold-key contract: all top-level keys containing "threshold" in the
    parsed template equal exactly {"staleness_churn_threshold"}. Catches both the
    dead-field still present and a future rogue threshold field being added.

Unit tests:
  - Contract source: the rendered template artifact shape — the documented YAML schema
    (a public artifact contract). Asserts parsed dict has staleness_churn_threshold
    with an int value.
"""

from pathlib import Path
import subprocess
import yaml


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "skills" / "codebase-map" / "templates" / "codebase-map.yaml"

# Live source directories asserted to be the COMPLETE set of dirs where a
# consumer of staleness_threshold_days could live.  docs/ and changes/ are
# excluded — they may mention the field historically.
#
# INCLUSION BET: if a new top-level consumer directory is added to this repo
# (e.g. plugins/, extensions/), it MUST be added here, or the dead-field
# resurrection guard will silently miss it.  The returncode-2 check below
# catches a listed dir that has gone missing, but NOT a new dir that was
# never listed.
LIVE_SOURCE_DIRS = [
    ROOT / "hooks",
    ROOT / "skills",
    ROOT / "samsara_cli",
]


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__dead_field_has_no_live_consumer() -> None:
    """
    DC — dead-field resurrection guard.

    After removing staleness_threshold_days from the template, no file in
    hooks/, skills/, or samsara_cli/ should reference it.  A match here means
    a live consumer would silently lose its configured threshold.

    Returncode contract for `grep -rl`:
      0  — matches found (bad: a consumer still exists)
      1  — no matches found (good: field is dead)
      2+ — grep error, e.g. directory missing or permission denied (fail loudly —
           guarding nothing is worse than a red test)
    """
    matches: list[str] = []
    for directory in LIVE_SOURCE_DIRS:
        result = subprocess.run(
            ["grep", "-rl", "staleness_threshold_days", str(directory)],
            capture_output=True,
            text=True,
        )
        assert result.returncode in (0, 1), (
            f"grep exited with returncode {result.returncode} while scanning "
            f"{directory} — directory missing or permission denied. "
            f"stderr: {result.stderr!r}. "
            "This guard is now blind; fix the directory or update LIVE_SOURCE_DIRS."
        )
        if result.stdout.strip():
            matches.extend(result.stdout.strip().splitlines())

    assert matches == [], (
        "staleness_threshold_days is still referenced in live source — removing it "
        f"would break a silent consumer. Files: {matches}"
    )


def test_death__template_threshold_keys_are_exactly_the_live_contract() -> None:
    """
    One-threshold-key contract guard.

    All top-level keys in the parsed template that contain the substring
    "threshold" must equal exactly {"staleness_churn_threshold"}.

    This catches three failure modes simultaneously:
      - staleness_threshold_days still present (two sources of truth)
      - staleness_churn_threshold missing (hook contract broken)
      - a future rogue threshold-like key added without review

    This test MUST fail (red) before the template is edited and pass (green)
    after.
    """
    parsed = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
    threshold_keys = {k for k in parsed if "threshold" in k}

    expected = {"staleness_churn_threshold"}
    assert threshold_keys == expected, (
        f"Template top-level threshold keys {threshold_keys!r} != "
        f"expected {expected!r}. "
        "Either the hook contract field is missing, the dead field is still present, "
        "or an unreviewed threshold field was added."
    )


# ---------------------------------------------------------------------------
# Unit tests (artifact shape contract)
# ---------------------------------------------------------------------------


def test_death__stale_reason_is_documented_but_not_a_default_key() -> None:
    """
    Cross-task contract consistency guard.

    The SKILL.md Fail-Honest Write Contract instructs: on a failed/aborted regen,
    write a `stale_reason` field to .samsara/codebase-map.yaml.  Without template
    documentation, an agent following that contract writes a schema-undocumented
    (ghost) field, and a later successful full regen could silently drop it.

    Two poles guarded simultaneously:
      - DOCUMENTED pole: `stale_reason` must appear somewhere in the template TEXT
        (as a comment / optional field marker), confirming the schema acknowledges it.
      - NOT-FABRICATED pole: the parsed YAML dict must NOT contain `stale_reason`
        as a populated key — it must be absent on a fresh/successful map.

    This test is RED before the template edit (no `stale_reason` in text) and
    GREEN after the commented-optional field is added.
    """
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    parsed = yaml.safe_load(template_text)

    # Pole 1: the field is documented (appears in the file text, even if commented)
    assert "stale_reason" in template_text, (
        "stale_reason is not documented in the template.  "
        "SKILL.md Fail-Honest Write Contract requires agents to write this field "
        "on a failed regen, but the template schema does not acknowledge it — "
        "making every agent-written stale_reason a ghost field invisible to schema "
        "consumers.  Add a commented-optional stale_reason to the template."
    )

    # Pole 2: the field is NOT a mandatory/default-present key in the parsed YAML
    assert "stale_reason" not in parsed, (
        "stale_reason is a populated key in the parsed template dict.  "
        "Every generated map would carry a stale_reason it never had — a fabricated "
        "failure marker on maps that succeeded.  stale_reason must be absent from "
        "the parsed YAML (commented-only or optional) — written ONLY on actual regen failure."
    )


def test_unit__template_staleness_churn_threshold_is_int() -> None:
    """
    Contract source: the documented YAML schema (public artifact contract).

    The rendered template must expose staleness_churn_threshold as an integer.
    The bash hook (later task) will read this field and treat it as a numeric
    count of changed files.  A non-integer value would silently produce wrong
    comparison behavior in bash arithmetic.
    """
    parsed = yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))
    value = parsed.get("staleness_churn_threshold")
    assert isinstance(value, int), (
        f"staleness_churn_threshold must be an int for bash arithmetic compatibility; "
        f"got {type(value).__name__!r} = {value!r}"
    )
