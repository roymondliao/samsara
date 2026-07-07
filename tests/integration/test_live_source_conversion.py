"""Death test — the LIVE repo source must convert cleanly for every platform.

Fixture blind spot (found 2026-07-07): every other integration test converts
the frozen fixture at tests/fixtures/source/, so live skills/agents content is
never exercised by the suite. A real conversion of the live repo left 94
`samsara:X` (colon-form) references in the codex output — names that do not
exist on the target platform — while `samsara-cli validate` reported PASS.

This test is the CI consumer ISSUE-002 asked for: it converts the actual repo
and asserts, independently of TargetValidator, that no colon-form namespace
residue survives in the instruction surface the target platform will execute.
"""

import re
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine

REPO_ROOT = Path(__file__).parent.parent.parent

# Colon-form namespace residue. The target platforms name everything
# `samsara-X`; any surviving `samsara:X` is a dead reference on that platform.
_RESIDUE = re.compile(r"samsara:[\w-]+")

# Instruction-surface extensions the target platform actually executes.
# YAML companions (templates/, schemas) legitimately carry source-form names.
_SCAN_SUFFIXES = {".md", ".txt", ".toml"}


@pytest.mark.parametrize("platform", ["codex", "gemini-cli"])
def test_death__live_repo_converts_with_no_namespace_residue(
    tmp_path: Path, platform: str
) -> None:
    output_dir = tmp_path / platform
    engine = ConversionEngine(platform)
    # Raises on target-validation failure — that alone is a death signal here.
    engine.run(source_dir=REPO_ROOT, output_dir=output_dir)

    residue: list[str] = []
    for file_path in output_dir.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in _SCAN_SUFFIXES:
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        match = _RESIDUE.search(text)
        if match:
            residue.append(f"{file_path.relative_to(output_dir)}: {match.group()}")

    assert residue == [], (
        f"{len(residue)} file(s) in the {platform} output still carry colon-form "
        "`samsara:X` references that do not resolve on the target platform "
        "(dead references for the executing agent). First offenders:\n"
        + "\n".join(residue[:10])
    )
