"""Death tests — samsara: namespace residue in converted output (DC: dead reference).

The corruption signature: converted output for codex/gemini-cli still contains
`samsara:X` (colon form) — a name that does not exist on the target platform
(the target name is `samsara-X`). A weaker model following the converted skill
hits a dead reference at dispatch time, and the old TargetValidator reported
PASS because it only enumerated two known patterns (invoke `samsara:X`,
subagent_type:) instead of scanning for the residue signature itself.

These tests pin the strict-namespace lane:
- strict_namespace=True: ANY `samsara:X` in scannable output is an error.
- default (False): behavior unchanged — repo-root validation (ISSUE-002
  live-surface mode) must not explode on legitimate source-form names.
"""

from pathlib import Path

from samsara_cli.validators.target import TargetValidator


def _make_minimal_output(tmp_path: Path, skill_body: str) -> Path:
    """Build a minimal codex-shaped converted-output tree with one skill file."""
    output = tmp_path / "output"
    skill_dir = output / ".agents" / "skills" / "samsara-planning"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(skill_body, encoding="utf-8")
    (output / ".codex" / "agents").mkdir(parents=True)
    return output


class TestNamespaceResidueStrictLane:
    def test_death__dispatch_variant_residue_is_error_under_strict(
        self, tmp_path: Path
    ) -> None:
        """`dispatch `samsara:auto-gatekeeper`` is not matched by the two legacy
        patterns — without the strict namespace scan it ships silently."""
        output = _make_minimal_output(
            tmp_path,
            "In auto mode, dispatch `samsara:auto-gatekeeper` and record it.\n",
        )
        errors = TargetValidator().validate(
            output_dir=output, platform="codex", strict_namespace=True
        )
        assert any("samsara:auto-gatekeeper" in e for e in errors), (
            "strict_namespace=True must flag `samsara:X` residue that the legacy "
            f"patterns miss. Got errors: {errors}"
        )

    def test_death__dot_graph_residue_is_error_under_strict(
        self, tmp_path: Path
    ) -> None:
        """Dot-graph labels use `invoke samsara:X` without backticks — the legacy
        invoke pattern (backtick-anchored) never fires on them."""
        output = _make_minimal_output(
            tmp_path,
            'digraph g { next [label="invoke samsara:implement"]; }\n',
        )
        errors = TargetValidator().validate(
            output_dir=output, platform="codex", strict_namespace=True
        )
        assert any("samsara:implement" in e for e in errors)

    def test_hyphen_form_is_not_flagged(self, tmp_path: Path) -> None:
        """Decoy: the correct target-form name `samsara-X` must pass strict —
        otherwise the check reddens on every valid conversion."""
        output = _make_minimal_output(
            tmp_path,
            "Use the `$samsara-pre-thinking` skill, then samsara-planning.\n",
        )
        errors = TargetValidator().validate(
            output_dir=output, platform="codex", strict_namespace=True
        )
        assert errors == []

    def test_default_lane_unchanged(self, tmp_path: Path) -> None:
        """Backward compat: without strict_namespace, bare `samsara:X` residue is
        NOT an error (repo-root / ISSUE-002 live-surface mode must not explode
        on legitimate source-form names)."""
        output = _make_minimal_output(
            tmp_path,
            "In auto mode, dispatch `samsara:auto-gatekeeper` and record it.\n",
        )
        errors = TargetValidator().validate(output_dir=output, platform="codex")
        assert errors == []
