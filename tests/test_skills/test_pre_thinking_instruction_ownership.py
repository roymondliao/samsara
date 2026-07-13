"""Ownership contracts for Pre-thinking instruction sources."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRE_THINKING = ROOT / "skills" / "pre-thinking"
SKILL = PRE_THINKING / "SKILL.md"
FLOW = PRE_THINKING / "flow.md"
ARTIFACT_TEMPLATE = PRE_THINKING / "templates" / "pre-thinking.md"
LENS_RETURN = PRE_THINKING / "templates" / "lens-report.md"
LENS_CATALOG = PRE_THINKING / "references" / "lenses.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_death__pre_thinking_sources_have_non_overlapping_owners() -> None:
    """Each file names one role; executable procedure has one canonical home."""
    skill = _normalized(SKILL)
    flow = _normalized(FLOW)
    artifact_template = _normalized(ARTIFACT_TEMPLATE)
    lens_return = _normalized(LENS_RETURN)
    lens_catalog = _normalized(LENS_CATALOG)

    assert "`flow.md` is the sole owner of executable procedure" in skill
    assert "Sole owner: executable procedure" in flow
    assert "Artifact shape only; executable procedure lives in `flow.md`." in (
        artifact_template
    )
    assert "Return shape only; dispatch procedure lives in `../flow.md` §3." in (
        lens_return
    )
    assert (
        "Catalog and lifecycle only; derivation procedure lives in `../flow.md` §3."
        in (lens_catalog)
    )


def test_death__pre_thinking_skill_is_a_compact_entrypoint() -> None:
    """The entry skill indexes the flow instead of duplicating its procedures."""
    skill = _read(SKILL)
    body = skill.split("---", 2)[-1]

    assert len(body.split()) < 500
    assert "## Step Index" in skill
    assert "If this summary conflicts with `flow.md`, `flow.md` wins." in skill


def test_death__load_bearing_procedures_exist_only_in_flow() -> None:
    """Distinctive rules must not be copied into templates or catalogs."""
    sources = {
        "skill": _normalized(SKILL),
        "flow": _normalized(FLOW),
        "artifact_template": _normalized(ARTIFACT_TEMPLATE),
        "lens_return": _normalized(LENS_RETURN),
        "lens_catalog": _normalized(LENS_CATALOG),
    }

    for phrase in (
        "No cap on lens count",
        "not a one-to-one mapping",
        "adding a lens is free",
        "fails, aborts, or is rejected",
    ):
        owners = [name for name, text in sources.items() if phrase in text]
        assert owners == ["flow"], f"{phrase!r} owners: {owners}"


def test_death__l1_handoff_is_refs_only() -> None:
    """Step 6 must point at PT-CI/PT-S entries, not restate their content."""
    template = _read(ARTIFACT_TEMPLATE)
    start = template.index("### L1")
    end = template.index("### Evaluation Contract", start)
    l1 = template[start:end]

    assert "**Decision refs:**" in l1
    assert "PT-CI" in l1 and "PT-S" in l1
    assert "**Core identity:**" not in l1
    assert "**Real seams:**" not in l1


def test_death__k3b_requires_resolvable_l1_refs() -> None:
    """Heading presence is not completion; every handoff ref must resolve."""
    recovery = _read(FLOW)[_read(FLOW).index("## 9. K3b Recovery") :]
    normalized = " ".join(recovery.split()).lower()

    assert "l1 refs" in normalized
    assert "resolve" in normalized
    assert "pt-ci" in normalized and "pt-s" in normalized


def test_death__pre_thinking_ids_have_one_immutable_human_resolver() -> None:
    """PT IDs stay machine-stable while canonical labels keep refs readable."""
    flow = _normalized(FLOW).replace("`", "")
    template = _read(ARTIFACT_TEMPLATE)

    for expansion in (
        "PT-CI (Pre-thinking Core Identity)",
        "PT-D* (Pre-thinking Design Decision)",
        "PT-S* (Pre-thinking Real Seam)",
        "PT-EVAL (Pre-thinking Evaluation Contract)",
    ):
        assert expansion in flow
    for rule in ("never renumber", "never reuse", "new ID"):
        assert rule in flow

    assert "**Canonical label:** <semantic label>" in template
    l1 = template[template.index("### L1") : template.index("### Evaluation Contract")]
    assert "PT-CI (<canonical label from Step 2>)" in l1
    assert "PT-S1 (<canonical seam name from Step 4>)" in l1
