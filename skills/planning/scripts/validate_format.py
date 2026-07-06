#!/usr/bin/env python3
"""Planning format validator — mechanical shape checks for planning artifacts.

Scope: FORMAT only (machine-decidable — a machine with no domain understanding
gets the right answer every time). This script never judges whether a seam is
the right boundary or whether an `affects` names a real structural need —
those are judgment and belong to pre-thinking and the reviewers.

Checks (each finding is line-level feedback, not a bare pass/fail):
  index-parse        index.yaml exists and parses as YAML with a tasks list
  task-id            task ids are non-empty and unique
  seam-resolves      every non-null task `seam` resolves to a seam declared in
                     overview.md Key Decisions -> Real Seams (no dangling ids)
  affects-task       every `affects.task` points to a task id that exists
  affects-needs      every `affects` entry has a non-empty `needs`
  anchors-shape      every `anchors` entry has a non-empty `path` and `why`
  depends-resolves   every `depends_on` id points to a task id that exists
  planned-resolves   every task id in a Real Seams `planned:` annotation exists
                     (an id pointing at no task = imagination annotated as
                     planned-change evidence)

Exit code: 0 = clean, 1 = findings, 2 = cannot validate (missing input /
missing dependency). Exit 2 is an explicit unknown — never treat it as pass.

Usage:
    python validate_format.py <feature-dir>
    # e.g. python validate_format.py changes/2026-07-06_my-feature/
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is not installed (pip install pyyaml).")
    print("This is an unknown outcome, not a pass.")
    sys.exit(2)

_SEAM_DECL_RE = re.compile(r"^\s*-\s*seam:\s*(\S+)", re.MULTILINE)
_PLANNED_LINE_RE = re.compile(r"^\s*planned:\s*(.+)$", re.MULTILINE)
_TASK_ID_RE = re.compile(r"\btask-\d+\b")


def _real_seams_section(overview_text: str) -> str | None:
    """Return the Real Seams section body, or None when the heading is absent."""
    marker = "### Real Seams"
    start = overview_text.find(marker)
    if start == -1:
        return None
    rest = overview_text[start + len(marker) :]
    # Section ends at the next heading of any level.
    end = re.search(r"^#{1,3} ", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def validate(feature_dir: Path) -> list[str]:
    """Return a list of finding strings (empty = clean).

    Raises FileNotFoundError when index.yaml is absent — the caller maps that
    to the cannot-validate exit, because "no artifact" is not "clean artifact".
    """
    findings: list[str] = []

    index_path = feature_dir / "index.yaml"
    overview_path = feature_dir / "overview.md"

    if not index_path.is_file():
        raise FileNotFoundError(f"{index_path} does not exist")

    try:
        index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"index-parse: index.yaml does not parse as YAML: {exc}"]

    if not isinstance(index, dict) or not isinstance(index.get("tasks"), list):
        return ["index-parse: index.yaml has no `tasks` list"]

    tasks = index["tasks"]
    task_ids: list[str] = []
    for i, task in enumerate(tasks):
        if not isinstance(task, dict) or not task.get("id"):
            findings.append(f"task-id: tasks[{i}] has no `id`")
            continue
        task_ids.append(str(task["id"]))

    duplicates = {tid for tid in task_ids if task_ids.count(tid) > 1}
    for tid in sorted(duplicates):
        findings.append(f"task-id: duplicate task id `{tid}`")
    known_ids = set(task_ids)

    # --- Seam declarations from overview.md ---
    declared_seams: set[str] = set()
    seams_section: str | None = None
    if overview_path.is_file():
        overview_text = overview_path.read_text(encoding="utf-8")
        seams_section = _real_seams_section(overview_text)
        if seams_section is not None:
            declared_seams = set(_SEAM_DECL_RE.findall(seams_section))

    # --- Per-task field checks ---
    any_seam_used = False
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        tid = str(task["id"])

        seam = task.get("seam")
        if seam not in (None, "null", ""):
            any_seam_used = True
            if seams_section is None:
                findings.append(
                    f"seam-resolves: {tid} declares seam `{seam}` but overview.md "
                    "has no `### Real Seams` section to resolve it against"
                )
            elif str(seam) not in declared_seams:
                findings.append(
                    f"seam-resolves: {tid} seam `{seam}` is not declared in "
                    "overview.md Real Seams (dangling seam id)"
                )

        for j, entry in enumerate(task.get("affects") or []):
            where = f"{tid}.affects[{j}]"
            if not isinstance(entry, dict):
                findings.append(f"affects-task: {where} is not a `task:`/`needs:` map")
                continue
            target = entry.get("task")
            if not target:
                findings.append(f"affects-task: {where} has no `task` id")
            elif str(target) not in known_ids:
                findings.append(
                    f"affects-task: {where} points at `{target}` which is not a "
                    "task in index.yaml (planned-change evidence must cite a real task)"
                )
            if not str(entry.get("needs") or "").strip():
                findings.append(
                    f"affects-needs: {where} has an empty `needs` — an affects "
                    "with no structural need is ordering noise, not a projection"
                )

        for j, entry in enumerate(task.get("anchors") or []):
            where = f"{tid}.anchors[{j}]"
            if not isinstance(entry, dict):
                findings.append(f"anchors-shape: {where} is not a `path:`/`why:` map")
                continue
            if not str(entry.get("path") or "").strip():
                findings.append(f"anchors-shape: {where} has no `path`")
            if not str(entry.get("why") or "").strip():
                findings.append(f"anchors-shape: {where} has no `why`")

        for dep in task.get("depends_on") or []:
            if str(dep) not in known_ids:
                findings.append(
                    f"depends-resolves: {tid} depends_on `{dep}` which is not a "
                    "task in index.yaml"
                )

    # --- planned: annotations in Real Seams cite real tasks ---
    if seams_section is not None:
        for planned_value in _PLANNED_LINE_RE.findall(seams_section):
            for cited in _TASK_ID_RE.findall(planned_value):
                if cited not in known_ids:
                    findings.append(
                        f"planned-resolves: Real Seams `planned:` cites `{cited}` "
                        "which is not a task in index.yaml — imagination cannot "
                        "be annotated as planned-change evidence"
                    )

    # Informational, not a finding: a feature whose tasks declare no seam at
    # all is legitimate (no structural touch) — but say so, visibly.
    if not any_seam_used:
        print(
            "note: no task declares a seam (all null/absent) — confirm the "
            "feature genuinely touches no declared seam"
        )

    return findings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    feature_dir = Path(argv[1])
    if not feature_dir.is_dir():
        print(f"CANNOT VALIDATE: {feature_dir} is not a directory")
        return 2
    try:
        findings = validate(feature_dir)
    except FileNotFoundError as exc:
        print(f"CANNOT VALIDATE: {exc}")
        return 2

    if findings:
        for line in findings:
            print(f"FINDING {line}")
        print(f"\n{len(findings)} finding(s). Fix and re-run until clean.")
        return 1

    print(
        "planning format validation: clean "
        "(index parse / seam-resolves / affects / anchors / depends / planned)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
