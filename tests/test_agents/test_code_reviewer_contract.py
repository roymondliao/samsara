"""
Doc-contract guard for the Step 0 domain router's instruction-surface route.

This is a DOC-PRESENCE + SCOPING test, not a behavioral test: an agent's
instruction file is its contract. The Step 0 domain router in
agents/code-reviewer.md lists five known domains (code/iac/container/
pipeline/orchestration) and returns UNKNOWN otherwise. Skill/agent/reference
markdown (skills/*.md incl. templates, agents/*.md, references/*.md) had NO
explicit route — reviews of instruction-surface diffs (the majority of this
repo's own changes) depended entirely on dispatch anchor wording and reviewer
precedent.

This gap surfaced three times during feature structural-honesty-mechanisms:
task-3 (two reviewers wrote domain-routing caveats) and task-4, where a yin
dispatch hit a HARD UNKNOWN and cost a full re-dispatch round (durable
evidence: changes/2026-07-04_structural-honesty-mechanisms/index.yaml task-4
review field). This fix promotes the de-facto precedent — instruction-surface
markdown reviews under the `code` domain — into an explicit routing rule.

Both tests are scoped to the "## Step 0: Determine Domain Before Review"
section only (not the whole file), so a future edit that moves the route out
of the loaded Step 0 router — e.g. into a reference doc not read on every
dispatch — goes RED instead of silently passing a whole-file substring check.

Anchors are content phrases only, never ordinal/list-position markers (a
"\\n6." style assertion was rejected in fix-2's review as structural
coupling that breaks the moment someone reorders or reformats the list).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tests/test_agents/ -> repo root
CODE_REVIEWER = ROOT / "agents" / "code-reviewer.md"

_STEP0_HEADER = "## step 0: determine domain before review"


def _step0_section(text_lower: str) -> str:
    """Return the '## Step 0: Determine Domain Before Review' section body,
    mirroring test_implementer_contract.py's `_execution_order_section`
    scoping rationale.

    End marker is the literal next real section header ('## Reference File
    Protocol'), NOT a generic '\\n## ' search: Step 0's body embeds example
    markdown headings inside fenced code blocks ('## Code Review — UNKNOWN'),
    so a generic search would silently truncate the span mid-section (a
    coupling defect found by fix-3's quality review). The assert makes a
    rename of the next section fail loudly instead of silently widening the
    span to end-of-file."""
    start = text_lower.find(_STEP0_HEADER)
    assert start != -1, (
        "code-reviewer.md has no '## Step 0: Determine Domain Before Review' section"
    )
    rest = text_lower[start + len(_STEP0_HEADER) :]
    end = rest.find("\n## reference file protocol")
    assert end != -1, (
        "code-reviewer.md no longer has a '## Reference File Protocol' "
        "section after Step 0 — update _step0_section's end marker to the "
        "real next section header."
    )
    return rest[:end]


def test_death__instruction_surface_markdown_routes_to_code_domain() -> None:
    """Step 0 must explicitly route skill/agent/reference definition markdown
    to the `code` domain. Without this route, a reviewer dispatched against
    an instruction-surface diff (skills/*.md, agents/*.md, references/*.md)
    has no router entry to follow and must fall back to dispatch-anchor
    wording or reviewer precedent — exactly the gap that cost task-4 a full
    re-dispatch round. If this route silently disappears (e.g. trimmed for
    budget reasons), this test goes RED."""
    section = _step0_section(CODE_REVIEWER.read_text(encoding="utf-8").lower())
    assert "instruction-surface markdown" in section, (
        "Step 0 no longer names 'instruction-surface markdown' as a routing "
        "concept — the explicit route this fix installed has been removed or "
        "reworded past recognition."
    )
    assert "skill definitions" in section and "agent definitions" in section, (
        "Step 0's instruction-surface route no longer names both skill "
        "definitions and agent definitions as covered file kinds — a partial "
        "route (e.g. agents only) silently narrows what task-4's incident "
        "showed needs coverage."
    )
    assert "routes to the `code` domain" in section, (
        "Step 0 no longer states that instruction-surface markdown routes to "
        "the `code` domain — without this explicit target, a reviewer still "
        "cannot resolve which reference file to load for these diffs."
    )


def test_death__instruction_surface_route_is_scoped_not_a_catch_all() -> None:
    """Polarity guard: the instruction-surface route must be explicitly
    scoped so it cannot silently widen into a catch-all for every .md file.
    Non-instruction-surface markdown (arbitrary prose docs with no contract)
    must still fall to UNKNOWN. If the scoping sentence disappears, a future
    reader could reasonably (and wrongly) conclude ANY markdown file now
    routes to `code`, defeating the UNKNOWN outcome for genuinely
    undetermined files — this test goes RED if that boundary is dropped."""
    section = _step0_section(CODE_REVIEWER.read_text(encoding="utf-8").lower())
    assert "instruction-surface markdown" in section, (
        "instruction-surface route missing entirely — scoping cannot be "
        "verified without the route it scopes."
    )
    assert "still fall to unknown" in section, (
        "Step 0's instruction-surface route no longer states that markdown "
        "outside the instruction surface still falls to UNKNOWN — without "
        "this boundary sentence the route reads as an unscoped catch-all for "
        "every .md file in the repo, which is explicitly prohibited."
    )
