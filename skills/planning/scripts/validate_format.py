#!/usr/bin/env python3
"""Validate Planning's machine-decidable artifact reference graph.

Exit code: 0 = clean, 1 = findings, 2 = cannot validate / unknown.

New authority-graph plans declare `sources:` in index.yaml. Legacy plans without
that key retain the former seam/affects/anchors checks but do not gain invented
references retroactively.
"""

from __future__ import annotations

import re
import sys

from pathlib import Path
from typing import Any

import yaml


_SEAM_ENTRY_RE = re.compile(
    r"^\s*-\s*seam:\s*(\S+)(?P<body>.*?)(?=^\s*-\s*seam:|\Z)",
    re.MULTILINE | re.DOTALL,
)
_SOURCE_REF_RE = re.compile(
    r"^\s*-?\s*source_ref:\s*<?([A-Z]+-[A-Z0-9-]+)>?", re.MULTILINE
)
_PLANNED_LINE_RE = re.compile(r"^\s*planned:\s*(.+)$", re.MULTILINE)
_TASK_ID_RE = re.compile(r"\btask-\d+\b")
_PT_ID_RE = re.compile(r"\*\*(?:Decision|Contract) ID:\*\*\s*<?(PT-[A-Z0-9-]+)>?")
_PL_ID_RE = re.compile(r"^###\s+(PL-D\d+)\b", re.MULTILINE)


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _real_seams_section(overview_text: str) -> str | None:
    for marker in ("## Real Seams Projection", "### Real Seams"):
        start = overview_text.find(marker)
        if start == -1:
            continue
        rest = overview_text[start + len(marker) :]
        end = re.search(r"^#{1,3}\s+", rest, re.MULTILINE)
        return rest[: end.start()] if end else rest
    return None


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dependency_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            start = visiting.index(node)
            cycle = visiting[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.append(node)
        for dependency in graph.get(node, []):
            if dependency in graph:
                visit(dependency)
        visiting.pop()
        visited.add(node)

    for task_id in graph:
        visit(task_id)
    return cycles


def _authority_ids(
    feature_dir: Path, sources: dict[str, Any], findings: list[str]
) -> tuple[set[str], set[str], set[str]]:
    pre_path = feature_dir / str(sources.get("pre_thinking") or "")
    plan_path = feature_dir / str(sources.get("plan") or "")
    acceptance_path = feature_dir / str(sources.get("acceptance") or "")

    pt_ids: set[str] = set()
    pl_ids: set[str] = set()
    acceptance_ids: set[str] = set()

    if pre_path.is_file():
        pt_ids = set(_PT_ID_RE.findall(pre_path.read_text(encoding="utf-8")))
    if plan_path.is_file():
        plan_text = plan_path.read_text(encoding="utf-8")
        pl_ids = set(_PL_ID_RE.findall(plan_text))
        for ref in re.findall(r"\bPT-[A-Z0-9-]+\b", plan_text):
            if ref not in pt_ids:
                findings.append(f"planning-ref: {plan_path.name} cites unknown `{ref}`")
    if acceptance_path.is_file():
        try:
            acceptance = _read_yaml(acceptance_path)
        except yaml.YAMLError as exc:
            findings.append(
                f"acceptance-parse: {acceptance_path.name} does not parse: {exc}"
            )
            acceptance = {}
        if isinstance(acceptance, dict):
            evaluator_ref = str(acceptance.get("evaluator_ref") or "")
            if evaluator_ref and evaluator_ref not in pt_ids:
                findings.append(
                    f"acceptance-ref: evaluator_ref `{evaluator_ref}` does not resolve"
                )
            for scenario in _list(acceptance.get("scenarios")):
                if not isinstance(scenario, dict) or not scenario.get("id"):
                    findings.append("acceptance-id: scenario has no `id`")
                    continue
                scenario_id = str(scenario["id"])
                if scenario_id in acceptance_ids:
                    findings.append(f"acceptance-id: duplicate `{scenario_id}`")
                acceptance_ids.add(scenario_id)
                for ref in _list(scenario.get("source_refs")):
                    if str(ref) not in pt_ids:
                        findings.append(
                            f"acceptance-ref: {scenario_id} cites unknown `{ref}`"
                        )
    return pt_ids, pl_ids, acceptance_ids


def validate(feature_dir: Path) -> list[str]:
    findings: list[str] = []
    index_path = feature_dir / "index.yaml"
    overview_path = feature_dir / "overview.md"

    if not index_path.is_file():
        raise FileNotFoundError(f"{index_path} does not exist")
    try:
        index = _read_yaml(index_path)
    except yaml.YAMLError as exc:
        return [f"index-parse: index.yaml does not parse as YAML: {exc}"]
    if not isinstance(index, dict) or not isinstance(index.get("tasks"), list):
        return ["index-parse: index.yaml has no `tasks` list"]

    tasks = index["tasks"]
    task_ids: list[str] = []
    for position, task in enumerate(tasks):
        if not isinstance(task, dict) or not task.get("id"):
            findings.append(f"task-id: tasks[{position}] has no `id`")
            continue
        task_ids.append(str(task["id"]))
    for duplicate in sorted(
        {task_id for task_id in task_ids if task_ids.count(task_id) > 1}
    ):
        findings.append(f"task-id: duplicate task id `{duplicate}`")
    known_ids = set(task_ids)

    authority_mode = isinstance(index.get("sources"), dict)
    sources = index["sources"] if authority_mode else {}
    if authority_mode:
        overview_path = feature_dir / str(sources.get("overview") or "")
    overview_text = (
        overview_path.read_text(encoding="utf-8") if overview_path.is_file() else ""
    )
    seams_section = _real_seams_section(overview_text)
    seam_sources: dict[str, str | None] = {}
    if seams_section is not None:
        for match in _SEAM_ENTRY_RE.finditer(seams_section):
            source_match = re.search(
                r"^\s*source_ref:\s*<?([A-Z]+-[A-Z0-9-]+)>?",
                match.group("body"),
                re.MULTILINE,
            )
            seam_sources[match.group(1)] = (
                source_match.group(1) if source_match else None
            )
    declared_seams = set(seam_sources)

    pt_ids: set[str] = set()
    pl_ids: set[str] = set()
    acceptance_ids: set[str] = set()
    if authority_mode:
        for label, relative in index["sources"].items():
            if not str(relative).strip() or not (feature_dir / str(relative)).is_file():
                findings.append(f"source-file: {label} `{relative}` does not exist")
        pt_ids, pl_ids, acceptance_ids = _authority_ids(feature_dir, sources, findings)
        for ref in _SOURCE_REF_RE.findall(overview_text):
            owner = pt_ids if ref.startswith("PT-") else pl_ids
            if ref not in owner:
                findings.append(f"overview-ref: source_ref `{ref}` does not resolve")
        for seam, source_ref in seam_sources.items():
            if not source_ref:
                findings.append(f"seam-source: `{seam}` has no source_ref")
            elif source_ref not in pt_ids:
                findings.append(
                    f"seam-source: `{seam}` source_ref `{source_ref}` does not resolve"
                )

    any_seam_used = False
    dependency_graph: dict[str, list[str]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            continue
        task_id = str(task["id"])
        dependencies = [str(dep) for dep in _list(task.get("depends_on"))]
        dependency_graph[task_id] = dependencies

        task_seam = task.get("seam")
        if task_seam not in (None, "null", ""):
            any_seam_used = True
            if seams_section is None:
                findings.append(
                    f"seam-resolves: {task_id} declares seam `{task_seam}` but overview.md "
                    "has no Real Seams projection"
                )
            elif str(task_seam) not in declared_seams:
                findings.append(
                    f"seam-resolves: {task_id} seam `{task_seam}` is not declared in "
                    "overview.md Real Seams Projection (dangling seam id)"
                )

        if authority_mode:
            task_file = str(task.get("task_file") or "")
            task_path = feature_dir / task_file
            if not task_file or not task_path.is_file():
                findings.append(f"task-file: {task_id} `{task_file}` does not exist")
                task_text = ""
            else:
                task_text = task_path.read_text(encoding="utf-8")
                if f"**Task ID:** {task_id}" not in task_text:
                    findings.append(
                        f"task-file: {task_file} does not declare `{task_id}`"
                    )

            for field, known, label in (
                ("planning_refs", pl_ids, "planning-ref"),
                ("decision_refs", pt_ids, "decision-ref"),
                ("acceptance_refs", acceptance_ids, "acceptance-ref"),
            ):
                for ref in _list(task.get(field)):
                    ref_text = str(ref)
                    if ref_text not in known:
                        findings.append(
                            f"{label}: {task_id} cites unknown `{ref_text}`"
                        )
                    if task_text and ref_text not in task_text:
                        findings.append(
                            f"task-ref: {task_file} omits index reference `{ref_text}`"
                        )

        for position, entry in enumerate(_list(task.get("affects"))):
            where = f"{task_id}.affects[{position}]"
            if not isinstance(entry, dict):
                findings.append(f"affects-task: {where} is not a `task:`/`needs:` map")
                continue
            target = entry.get("task")
            if not target:
                findings.append(f"affects-task: {where} has no `task` id")
            elif str(target) not in known_ids:
                findings.append(f"affects-task: {where} points at unknown `{target}`")
            if not str(entry.get("needs") or "").strip():
                findings.append(f"affects-needs: {where} has an empty `needs`")

        for position, entry in enumerate(_list(task.get("anchors"))):
            where = f"{task_id}.anchors[{position}]"
            if not isinstance(entry, dict):
                findings.append(f"anchors-shape: {where} is not a `path:`/`why:` map")
                continue
            if not str(entry.get("path") or "").strip():
                findings.append(f"anchors-shape: {where} has no `path`")
            if not str(entry.get("why") or "").strip():
                findings.append(f"anchors-shape: {where} has no `why`")

        for dependency in dependencies:
            if dependency not in known_ids:
                findings.append(
                    f"depends-resolves: {task_id} depends_on `{dependency}` which is not a task"
                )

    for cycle in _dependency_cycles(dependency_graph):
        findings.append(f"depends-cycle: {' -> '.join(cycle)}")

    if seams_section is not None:
        for planned_value in _PLANNED_LINE_RE.findall(seams_section):
            for cited in _TASK_ID_RE.findall(planned_value):
                if cited not in known_ids:
                    findings.append(
                        f"planned-resolves: Real Seams `planned:` cites `{cited}` "
                        "which is not a task in index.yaml"
                    )

    if not any_seam_used:
        print("note: no task declares a seam; confirm no structural touch")
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
        for finding in findings:
            print(f"FINDING {finding}")
        print(f"\n{len(findings)} finding(s). Fix and re-run until clean.")
        return 1
    print(
        "planning format validation: clean (authority refs / task graph / projections)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
