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

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is unavailable to the uv-run Python environment.")
    print("This is an unknown outcome, not a pass.")
    sys.exit(2)


_SEAM_ENTRY_RE = re.compile(
    r"^\s*-\s*seam:\s*(\S+)(?P<body>.*?)(?=^\s*-\s*seam:|\Z)",
    re.MULTILINE | re.DOTALL,
)
_SOURCE_REF_RE = re.compile(
    r"^\s*-?\s*source_ref:\s*<?([A-Z]+-[A-Z0-9-]+)>?", re.MULTILINE
)
_PLANNED_LINE_RE = re.compile(r"^\s*planned:\s*(.+)$", re.MULTILINE)
_TASK_ID_RE = re.compile(r"\btask-\d+\b")
_WRITE_PATH_RE = re.compile(
    r"^\s*-\s*(?:Create|Modify|Test):\s*`([^`]+)`", re.MULTILINE
)
_PT_ID_RE = re.compile(r"\*\*(?:Decision|Contract) ID:\*\*\s*<?(PT-[A-Z0-9-]+)>?")
_PL_ID_RE = re.compile(r"^###\s+(PL-D\d+)\b", re.MULTILINE)
_PT_CORE_LABEL_RE = re.compile(
    r"\*\*Decision ID:\*\*\s*PT-CI\s*\n"
    r"\*\*Canonical label:\*\*\s*([^\n]+)"
)
_PT_DECISION_LABEL_RE = re.compile(
    r"^### Decision:\s*([^\n]+?)\s*$\s*"
    r"\*\*Decision ID:\*\*\s*<?(PT-D\d+)>?",
    re.MULTILINE,
)
_PT_SEAM_LABEL_RE = re.compile(
    r"^#### Seam:\s*([^\n]+?)\s*$\s*"
    r"\*\*Decision ID:\*\*\s*<?(PT-S\d+)>?",
    re.MULTILINE,
)
_PT_EVAL_LABEL_RE = re.compile(
    r"\*\*Contract ID:\*\*\s*PT-EVAL\s*\n"
    r"\*\*Canonical label:\*\*\s*([^\n]+)"
)
_PL_LABEL_RE = re.compile(r"^###\s+(PL-D\d+):\s*([^\n]+?)\s*$", re.MULTILINE)
_AUTHORITY_ID_TOKEN_RE = re.compile(r"\b(?:PT-(?:CI|EVAL|D\d+|S\d+)|PL-D\d+|AC-\d+)\b")
_COMMIT_REF_RE = re.compile(r"[0-9a-f]{7,40}")


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


def _clean_label(value: str) -> str:
    return value.strip().strip("<>").strip()


def _duplicates(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def _pre_thinking_labels(text: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    core = _PT_CORE_LABEL_RE.search(text)
    if core:
        labels["PT-CI"] = _clean_label(core.group(1))
    for label, decision_id in _PT_DECISION_LABEL_RE.findall(text):
        labels[decision_id] = _clean_label(label)
    for label, seam_id in _PT_SEAM_LABEL_RE.findall(text):
        labels[seam_id] = _clean_label(label)
    evaluator = _PT_EVAL_LABEL_RE.search(text)
    if evaluator:
        labels["PT-EVAL"] = _clean_label(evaluator.group(1))
    return labels


def _validate_human_ref_labels(
    text: str, path_name: str, canonical: dict[str, str], findings: list[str]
) -> None:
    """Check readable refs without treating authority-definition headings as refs."""
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _AUTHORITY_ID_TOKEN_RE.finditer(line):
            authority_id = match.group(0)
            expected = canonical.get(authority_id)
            if expected is None:
                continue
            if re.match(rf"^###\s+{re.escape(authority_id)}\s*:", line):
                continue
            suffix = line[match.end() :]
            rendered = re.match(r"`?\s+\(([^)\n]+)\)", suffix)
            if rendered is None:
                findings.append(
                    f"ref-label-missing: {path_name}:{line_number} `{authority_id}` "
                    f"must include `({expected})`"
                )
                continue
            actual = rendered.group(1).strip()
            if actual != expected:
                findings.append(
                    f"ref-label-drift: {path_name}:{line_number} `{authority_id}` "
                    f"uses `{actual}`; canonical label is `{expected}`"
                )


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


def _validate_iteration_entry(value: Any, findings: list[str]) -> None:
    """Validate the durable Iteration checkpoint's mechanical shape only."""
    if value is None:
        return
    if not isinstance(value, dict):
        findings.append("iteration-entry: value must be null or a map")
        return

    required = {
        "status",
        "route",
        "round",
        "evaluator",
        "signal_lost",
        "stagnation_count",
        "reason",
        "last_commit",
        "reversible",
    }
    for field in sorted(required - set(value)):
        findings.append(f"iteration-entry: missing `{field}`")

    if value.get("status") not in {
        "in_progress",
        "ready_for_validation",
        "blocked",
    }:
        findings.append(
            "iteration-entry: `status` must be in_progress, "
            "ready_for_validation, or blocked"
        )
    if value.get("route") not in {"skip_rounds", "fix_rounds", "unknown"}:
        findings.append(
            "iteration-entry: `route` must be skip_rounds, fix_rounds, or unknown"
        )
    if value.get("evaluator") not in {"pass", "fail", "unknown"}:
        findings.append("iteration-entry: `evaluator` must be pass, fail, or unknown")
    for field in ("round", "signal_lost", "stagnation_count"):
        number = value.get(field)
        if type(number) is not int or number < 0:
            findings.append(
                f"iteration-entry: `{field}` must be a non-negative integer"
            )
    if not str(value.get("reason") or "").strip():
        findings.append("iteration-entry: `reason` must be non-empty")
    if value.get("reversible") is not True:
        findings.append("iteration-entry: `reversible` must be true")

    last_commit = value.get("last_commit")
    if last_commit is not None and _COMMIT_REF_RE.fullmatch(str(last_commit)) is None:
        findings.append(
            "iteration-entry: `last_commit` must be null or a 7-40 character git SHA"
        )
    if value.get("status") == "ready_for_validation" and last_commit is None:
        findings.append(
            "iteration-entry: ready_for_validation requires a non-null `last_commit`"
        )
    if value.get("route") == "skip_rounds" and value.get("evaluator") != "pass":
        findings.append("iteration-entry: skip_rounds requires evaluator `pass`")
    if value.get("status") == "ready_for_validation" and (
        value.get("evaluator") != "pass" or value.get("route") == "unknown"
    ):
        findings.append(
            "iteration-entry: ready_for_validation requires evaluator `pass` "
            "and a non-unknown route"
        )


def _authority_ids(
    feature_dir: Path, sources: dict[str, Any], findings: list[str]
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    pre_path = feature_dir / str(sources.get("pre_thinking") or "")
    plan_path = feature_dir / str(sources.get("plan") or "")
    acceptance_path = feature_dir / str(sources.get("acceptance") or "")

    pt_labels: dict[str, str] = {}
    pl_labels: dict[str, str] = {}
    acceptance_labels: dict[str, str] = {}
    pt_ids: set[str] = set()
    acceptance_ids: set[str] = set()

    if pre_path.is_file():
        pre_text = pre_path.read_text(encoding="utf-8")
        pt_id_entries = _PT_ID_RE.findall(pre_text)
        pt_ids = set(pt_id_entries)
        for authority_id in sorted(_duplicates(pt_id_entries)):
            findings.append(
                f"authority-id: {pre_path.name} has duplicate `{authority_id}`"
            )
        pt_labels = _pre_thinking_labels(pre_text)
        for authority_id in sorted(pt_ids - set(pt_labels)):
            findings.append(
                f"authority-label: {pre_path.name} `{authority_id}` has no "
                "canonical label"
            )
        if pt_labels.get("PT-EVAL") not in (None, "evaluation-contract"):
            findings.append(
                f"authority-label: {pre_path.name} `PT-EVAL` must use fixed "
                "label `evaluation-contract`"
            )
    if plan_path.is_file():
        plan_text = plan_path.read_text(encoding="utf-8")
        pl_id_entries = _PL_ID_RE.findall(plan_text)
        pl_ids = set(pl_id_entries)
        for authority_id in sorted(_duplicates(pl_id_entries)):
            findings.append(
                f"authority-id: {plan_path.name} has duplicate `{authority_id}`"
            )
        pl_labels = {
            decision_id: _clean_label(label)
            for decision_id, label in _PL_LABEL_RE.findall(plan_text)
        }
        for authority_id in sorted(pl_ids - set(pl_labels)):
            findings.append(
                f"authority-label: {plan_path.name} `{authority_id}` has no "
                "canonical label"
            )
        for ref in re.findall(r"\bPT-[A-Z0-9-]+\b", plan_text):
            if ref not in pt_labels:
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
                if re.fullmatch(r"AC-\d+", scenario_id) is None:
                    findings.append(
                        f"acceptance-id: `{scenario_id}` must match fixed `AC-<number>` "
                        "format"
                    )
                if scenario_id in acceptance_ids:
                    findings.append(f"acceptance-id: duplicate `{scenario_id}`")
                acceptance_ids.add(scenario_id)
                scenario_label = str(scenario.get("label") or "").strip()
                if not scenario_label:
                    findings.append(
                        f"acceptance-label: {scenario_id} has no canonical `label`"
                    )
                else:
                    acceptance_labels[scenario_id] = scenario_label
                for ref in _list(scenario.get("source_refs")):
                    if str(ref) not in pt_labels:
                        findings.append(
                            f"acceptance-ref: {scenario_id} cites unknown `{ref}`"
                        )
    if plan_path.is_file():
        _validate_human_ref_labels(
            plan_text,
            plan_path.name,
            pt_labels | pl_labels | acceptance_labels,
            findings,
        )
    return pt_labels, pl_labels, acceptance_labels


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

    if "iteration_entry" in index:
        _validate_iteration_entry(index.get("iteration_entry"), findings)

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

    pt_labels: dict[str, str] = {}
    pl_labels: dict[str, str] = {}
    acceptance_labels: dict[str, str] = {}
    if authority_mode:
        for label, relative in index["sources"].items():
            if not str(relative).strip() or not (feature_dir / str(relative)).is_file():
                findings.append(f"source-file: {label} `{relative}` does not exist")
        pt_labels, pl_labels, acceptance_labels = _authority_ids(
            feature_dir, sources, findings
        )
        pt_ids = set(pt_labels)
        pl_ids = set(pl_labels)
        acceptance_ids = set(acceptance_labels)
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
                if "## Files" not in task_text or not _WRITE_PATH_RE.findall(task_text):
                    findings.append(
                        f"task-write-scope: {task_file} has no declared "
                        "Create/Modify/Test path"
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
            if task_text:
                _validate_human_ref_labels(
                    task_text,
                    task_file,
                    pt_labels | pl_labels | acceptance_labels,
                    findings,
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
