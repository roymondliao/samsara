#!/usr/bin/env python3
"""Validate and publish one Codebase Map candidate.

FORMAT only: this companion checks Git snapshot identity, YAML shape, stable
IDs, referential integrity, evidence paths, and ignored output paths. It never
judges whether responsibilities, capabilities, flows, or risks are correct.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is unavailable.")
    sys.exit(2)


ROOT_FIELDS = {
    "schema_version",
    "project",
    "source",
    "generated_at",
    "generated_by",
    "scan_scope",
    "summary",
    "modules",
    "global_nodes",
    "cross_module_relationships",
    "business_flows",
    "infrastructure",
}
MODULE_FIELDS = {
    "schema_version",
    "id",
    "interfaces",
    "nodes",
    "internal_relationships",
    "rot_risks",
    "hidden_coupling",
    "assumptions",
}
NODE_FIELDS = {
    "id",
    "kind",
    "path",
    "responsibility",
    "provides",
    "evidence_refs",
}
RELATIONSHIP_FIELDS = {"from", "to", "type", "evidence_refs"}
MODULE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
LINE_REF_RE = re.compile(r"^(.+):([1-9][0-9]*)$")
NODE_KINDS = {"file", "function", "class", "interface", "command", "config", "schema"}
RELATIONSHIP_TYPES = {
    "contains",
    "imports",
    "calls",
    "implements",
    "configures",
    "reads",
    "writes",
    "emits",
    "consumes",
}
ISO_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _mapping(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected mapping")
        return {}
    return value


def _list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected list")
        return []
    return value


def _string(value: Any, path: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")
        return ""
    return value


def _string_list(value: Any, path: str, errors: list[str]) -> list[str]:
    values = _list(value, path, errors)
    return [
        _string(item, f"{path}[{index}]", errors)
        for index, item in enumerate(values)
    ]


def _required(
    mapping: dict[str, Any], keys: Iterable[str], path: str, errors: list[str]
) -> None:
    for key in keys:
        if key not in mapping:
            errors.append(f"{path}.{key}: missing")


def _exact_fields(
    mapping: dict[str, Any], fields: set[str], path: str, errors: list[str]
) -> None:
    _required(mapping, fields, path, errors)
    for key in sorted(set(mapping) - fields):
        errors.append(f"{path}.{key}: unexpected field")


def _git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _git_value(
    project: Path, args: tuple[str, ...], label: str, errors: list[str]
) -> str:
    result = _git(project, *args)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        errors.append(f"{label}: {detail}")
        return ""
    return result.stdout.strip()


def _repo_path(value: Any, path: str, errors: list[str]) -> str:
    text = _string(value, path, errors)
    if not text:
        return ""
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or ".." in candidate.parts:
        errors.append(f"{path}: expected normalized repository-relative path")
        return ""
    return text


def _evidence_path(ref: str) -> tuple[str, int | None]:
    if "#" in ref:
        return ref.split("#", 1)[0], None
    line_match = LINE_REF_RE.match(ref)
    if line_match:
        return line_match.group(1), int(line_match.group(2))
    return ref, None


def _evidence_refs(
    value: Any,
    path: str,
    snapshot_root: Path,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> None:
    refs = _list(value, path, errors)
    if not refs and not allow_empty:
        errors.append(f"{path}: expected at least one evidence reference")
    for index, raw_ref in enumerate(refs):
        ref_path = f"{path}[{index}]"
        ref = _string(raw_ref, ref_path, errors)
        if not ref:
            continue
        raw_file, line = _evidence_path(ref)
        file_path = _repo_path(raw_file, ref_path, errors)
        if not file_path:
            continue
        resolved = snapshot_root / file_path
        if not resolved.is_file():
            errors.append(f"{ref_path}: evidence path does not exist in snapshot")
            continue
        if line is not None:
            try:
                line_count = len(resolved.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeError):
                errors.append(f"{ref_path}: line evidence is not readable text")
                continue
            if line > line_count:
                errors.append(
                    f"{ref_path}: line {line} exceeds snapshot file length {line_count}"
                )


def _death_impact(
    value: Any,
    path: str,
    snapshot_root: Path,
    errors: list[str],
) -> None:
    impact = _mapping(value, path, errors)
    _exact_fields(impact, {"severity", "effect", "evidence_refs"}, path, errors)
    severity = impact.get("severity")
    if severity not in {"high", "medium", "low", "unknown"}:
        errors.append(f"{path}.severity: invalid enum")
    effect = _string(impact.get("effect"), f"{path}.effect", errors)
    refs = impact.get("evidence_refs")
    _evidence_refs(
        refs,
        f"{path}.evidence_refs",
        snapshot_root,
        errors,
        allow_empty=severity == "unknown",
    )
    if severity != "unknown" and effect == "unknown":
        errors.append(f"{path}.effect: known severity requires a concrete effect")


def _validate_node(
    raw: Any,
    path: str,
    snapshot_root: Path,
    node_ids: set[str],
    errors: list[str],
) -> None:
    node = _mapping(raw, path, errors)
    _exact_fields(node, NODE_FIELDS, path, errors)
    node_id = _string(node.get("id"), f"{path}.id", errors)
    if node_id:
        if node_id in node_ids:
            errors.append(f"{path}.id: duplicate node id {node_id!r}")
        node_ids.add(node_id)
    node_path = _repo_path(node.get("path"), f"{path}.path", errors)
    if node_path and not (snapshot_root / node_path).exists():
        errors.append(f"{path}.path: does not exist in snapshot")
    if node.get("kind") not in NODE_KINDS:
        errors.append(f"{path}.kind: invalid enum")
    _string(node.get("responsibility"), f"{path}.responsibility", errors)
    _string_list(node.get("provides"), f"{path}.provides", errors)
    _evidence_refs(
        node.get("evidence_refs"),
        f"{path}.evidence_refs",
        snapshot_root,
        errors,
    )


def _collect_relationship(
    raw: Any,
    path: str,
    snapshot_root: Path,
    pending: list[tuple[str, str, str]],
    allowed_types: set[str],
    errors: list[str],
) -> None:
    relationship = _mapping(raw, path, errors)
    _exact_fields(relationship, RELATIONSHIP_FIELDS, path, errors)
    source = _string(relationship.get("from"), f"{path}.from", errors)
    target = _string(relationship.get("to"), f"{path}.to", errors)
    if relationship.get("type") not in allowed_types:
        errors.append(f"{path}.type: invalid enum")
    if source and target:
        pending.append((path, source, target))
    _evidence_refs(
        relationship.get("evidence_refs"),
        f"{path}.evidence_refs",
        snapshot_root,
        errors,
    )


def _validate_snapshot_identity(
    project_root: Path,
    snapshot_root: Path,
    expected_commit: str,
    errors: list[str],
) -> None:
    project_head = _git_value(
        project_root, ("rev-parse", "HEAD"), "project HEAD", errors
    )
    snapshot_head = _git_value(
        snapshot_root, ("rev-parse", "HEAD"), "snapshot HEAD", errors
    )
    if project_head and project_head != expected_commit:
        errors.append(
            "project HEAD: changed during generation "
            f"(expected {expected_commit}, found {project_head})"
        )
    if snapshot_head and snapshot_head != expected_commit:
        errors.append(
            f"snapshot HEAD: expected {expected_commit}, found {snapshot_head}"
        )
    branch = _git(snapshot_root, "symbolic-ref", "-q", "HEAD")
    if branch.returncode == 0:
        errors.append("snapshot HEAD: expected a detached worktree")
    snapshot_status = _git(snapshot_root, "status", "--porcelain")
    if snapshot_status.returncode != 0:
        errors.append("snapshot worktree: Git status cannot be verified")
    elif snapshot_status.stdout.strip():
        errors.append("snapshot worktree: expected no tracked or untracked changes")
    exists = _git(project_root, "cat-file", "-e", f"{expected_commit}^{{commit}}")
    if exists.returncode != 0:
        errors.append(f"source.commit: Git cannot resolve {expected_commit!r}")


def _validate_ignored(
    snapshot_root: Path, expected_commit: str, errors: list[str]
) -> None:
    for relative in (
        ".samsara/codebase-map.yaml",
        f".samsara/codebase-map/{expected_commit}/modules/__probe__.yaml",
    ):
        result = _git(snapshot_root, "check-ignore", "-q", "--no-index", relative)
        if result.returncode != 0:
            errors.append(f"{relative}: output path must be ignored by Git")


def _validate_scope(
    value: Any, snapshot_root: Path, errors: list[str]
) -> set[str]:
    scope = _mapping(value, "codebase-map.scan_scope", errors)
    _exact_fields(
        scope,
        {"roots", "exclusions", "coverage_gaps"},
        "codebase-map.scan_scope",
        errors,
    )
    roots = _list(scope.get("roots"), "codebase-map.scan_scope.roots", errors)
    for index, root in enumerate(roots):
        root_path = _repo_path(
            root, f"codebase-map.scan_scope.roots[{index}]", errors
        )
        if root_path and not (snapshot_root / root_path).exists():
            errors.append(
                f"codebase-map.scan_scope.roots[{index}]: does not exist in snapshot"
            )

    exclusions = _list(
        scope.get("exclusions"), "codebase-map.scan_scope.exclusions", errors
    )
    for index, raw_exclusion in enumerate(exclusions):
        path = f"codebase-map.scan_scope.exclusions[{index}]"
        exclusion = _mapping(raw_exclusion, path, errors)
        _exact_fields(exclusion, {"path", "reason"}, path, errors)
        _repo_path(exclusion.get("path"), f"{path}.path", errors)
        _string(exclusion.get("reason"), f"{path}.reason", errors)

    coverage_paths: set[str] = set()
    gaps = _list(
        scope.get("coverage_gaps"), "codebase-map.scan_scope.coverage_gaps", errors
    )
    for index, raw_gap in enumerate(gaps):
        path = f"codebase-map.scan_scope.coverage_gaps[{index}]"
        gap = _mapping(raw_gap, path, errors)
        _exact_fields(gap, {"path", "referenced_by", "reason"}, path, errors)
        gap_path = _repo_path(gap.get("path"), f"{path}.path", errors)
        if gap_path:
            coverage_paths.add(gap_path)
        _string(gap.get("referenced_by"), f"{path}.referenced_by", errors)
        _string(gap.get("reason"), f"{path}.reason", errors)
    return coverage_paths


def _validate_module(
    module_file: Path,
    expected_id: str,
    snapshot_root: Path,
    node_ids: set[str],
    pending_relationships: list[tuple[str, str, str]],
    errors: list[str],
) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(module_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"{module_file}: cannot parse YAML: {exc}")
        return {}
    module = _mapping(parsed, f"module[{expected_id}]", errors)
    _exact_fields(module, MODULE_FIELDS, f"module[{expected_id}]", errors)
    if module.get("schema_version") != 2:
        errors.append(f"module[{expected_id}].schema_version: expected 2")
    module_id = _string(module.get("id"), f"module[{expected_id}].id", errors)
    if module_id != expected_id:
        errors.append(
            f"module[{expected_id}].id: expected {expected_id!r}, found {module_id!r}"
        )
    for index, raw_node in enumerate(
        _list(module.get("nodes"), f"module[{expected_id}].nodes", errors)
    ):
        _validate_node(
            raw_node,
            f"module[{expected_id}].nodes[{index}]",
            snapshot_root,
            node_ids,
            errors,
        )
    for index, raw_relationship in enumerate(
        _list(
            module.get("internal_relationships"),
            f"module[{expected_id}].internal_relationships",
            errors,
        )
    ):
        _collect_relationship(
            raw_relationship,
            f"module[{expected_id}].internal_relationships[{index}]",
            snapshot_root,
            pending_relationships,
            RELATIONSHIP_TYPES,
            errors,
        )
    return module


def validate_candidate(
    candidate: Path,
    project_root: Path,
    snapshot_root: Path,
    expected_commit: str,
) -> tuple[list[str], dict[str, Any]]:
    """Return mechanical findings and the parsed root manifest."""
    errors: list[str] = []
    root_file = candidate / "codebase-map.yaml"
    modules_dir = candidate / "modules"
    if not root_file.is_file():
        return [f"{root_file}: missing"], {}
    if not modules_dir.is_dir():
        return [f"{modules_dir}: missing"], {}

    _validate_snapshot_identity(
        project_root, snapshot_root, expected_commit, errors
    )
    _validate_ignored(snapshot_root, expected_commit, errors)

    try:
        parsed = yaml.safe_load(root_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{root_file}: cannot parse YAML: {exc}"], {}
    root = _mapping(parsed, "codebase-map", errors)
    _exact_fields(root, ROOT_FIELDS, "codebase-map", errors)
    if root.get("schema_version") != 2:
        errors.append("codebase-map.schema_version: expected 2")
    _string(root.get("project"), "codebase-map.project", errors)
    generated_at = _string(
        root.get("generated_at"), "codebase-map.generated_at", errors
    )
    if generated_at and not ISO_TIMESTAMP_RE.fullmatch(generated_at):
        errors.append(
            "codebase-map.generated_at: expected ISO-8601 timestamp with timezone"
        )
    if root.get("generated_by") != "samsara:codebase-map":
        errors.append("codebase-map.generated_by: expected samsara:codebase-map")

    source = _mapping(root.get("source"), "codebase-map.source", errors)
    _exact_fields(source, {"commit"}, "codebase-map.source", errors)
    source_commit = _string(
        source.get("commit"), "codebase-map.source.commit", errors
    )
    if source_commit and source_commit != expected_commit:
        errors.append(
            "codebase-map.source.commit: "
            f"expected {expected_commit}, found {source_commit}"
        )

    coverage_paths = _validate_scope(root.get("scan_scope"), snapshot_root, errors)
    summary = _mapping(root.get("summary"), "codebase-map.summary", errors)
    _exact_fields(
        summary,
        {"purpose", "capabilities", "silent_failure_surface", "rot_hotspots"},
        "codebase-map.summary",
        errors,
    )
    _string(summary.get("purpose"), "codebase-map.summary.purpose", errors)
    _string_list(
        summary.get("capabilities"), "codebase-map.summary.capabilities", errors
    )
    if summary.get("silent_failure_surface") not in {
        "low",
        "medium",
        "high",
        "unknown",
    }:
        errors.append("codebase-map.summary.silent_failure_surface: invalid enum")
    hotspots = _list(
        summary.get("rot_hotspots"),
        "codebase-map.summary.rot_hotspots",
        errors,
    )
    for index, raw_hotspot in enumerate(hotspots):
        path = f"codebase-map.summary.rot_hotspots[{index}]"
        hotspot = _mapping(raw_hotspot, path, errors)
        _exact_fields(
            hotspot,
            {"module_id", "description", "evidence_refs"},
            path,
            errors,
        )
        _string(hotspot.get("module_id"), f"{path}.module_id", errors)
        _string(hotspot.get("description"), f"{path}.description", errors)
        _evidence_refs(
            hotspot.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )

    node_ids: set[str] = set()
    pending_relationships: list[tuple[str, str, str]] = []
    module_ids: set[str] = set()
    module_data: dict[str, dict[str, Any]] = {}
    module_entries = _list(root.get("modules"), "codebase-map.modules", errors)
    for index, raw_entry in enumerate(module_entries):
        path = f"codebase-map.modules[{index}]"
        entry = _mapping(raw_entry, path, errors)
        _exact_fields(
            entry,
            {
                "id",
                "name",
                "path",
                "responsibility",
                "provides",
                "death_impact",
                "detail_ref",
            },
            path,
            errors,
        )
        module_id = _string(entry.get("id"), f"{path}.id", errors)
        if module_id:
            if not MODULE_ID_RE.fullmatch(module_id):
                errors.append(f"{path}.id: invalid stable module id")
            if module_id in module_ids:
                errors.append(f"{path}.id: duplicate module id {module_id!r}")
            module_ids.add(module_id)
        _string(entry.get("name"), f"{path}.name", errors)
        module_path = _repo_path(entry.get("path"), f"{path}.path", errors)
        if module_path and not (snapshot_root / module_path).exists():
            errors.append(f"{path}.path: does not exist in snapshot")
        _string(entry.get("responsibility"), f"{path}.responsibility", errors)
        _string_list(entry.get("provides"), f"{path}.provides", errors)
        _death_impact(
            entry.get("death_impact"),
            f"{path}.death_impact",
            snapshot_root,
            errors,
        )
        detail_ref = _string(entry.get("detail_ref"), f"{path}.detail_ref", errors)
        expected_ref = (
            f".samsara/codebase-map/{expected_commit}/modules/{module_id}.yaml"
        )
        if module_id and detail_ref != expected_ref:
            errors.append(
                f"{path}.detail_ref: expected {expected_ref!r}, found {detail_ref!r}"
            )
        if module_id:
            module_file = modules_dir / f"{module_id}.yaml"
            if not module_file.is_file():
                errors.append(f"{path}.detail_ref: candidate module file is missing")
            else:
                module_data[module_id] = _validate_module(
                    module_file,
                    module_id,
                    snapshot_root,
                    node_ids,
                    pending_relationships,
                    errors,
                )

    expected_files = {f"{module_id}.yaml" for module_id in module_ids}
    module_entries_on_disk = list(modules_dir.iterdir())
    actual_files = {
        path.name
        for path in module_entries_on_disk
        if path.is_file() and path.suffix == ".yaml"
    }
    for extra in sorted(actual_files - expected_files):
        errors.append(f"candidate.modules.{extra}: unreferenced module file")
    for path in module_entries_on_disk:
        if path.is_symlink() or not path.is_file() or path.suffix != ".yaml":
            errors.append(
                f"candidate.modules.{path.name}: expected a regular YAML module file"
            )

    for index, raw_hotspot in enumerate(hotspots):
        hotspot = _mapping(
            raw_hotspot,
            f"codebase-map.summary.rot_hotspots[{index}]",
            errors,
        )
        module_id = hotspot.get("module_id")
        if isinstance(module_id, str) and module_id not in module_ids:
            errors.append(
                "codebase-map.summary.rot_hotspots"
                f"[{index}].module_id: unknown module id {module_id!r}"
            )

    for index, raw_node in enumerate(
        _list(root.get("global_nodes"), "codebase-map.global_nodes", errors)
    ):
        _validate_node(
            raw_node,
            f"codebase-map.global_nodes[{index}]",
            snapshot_root,
            node_ids,
            errors,
        )
    for index, raw_relationship in enumerate(
        _list(
            root.get("cross_module_relationships"),
            "codebase-map.cross_module_relationships",
            errors,
        )
    ):
        _collect_relationship(
            raw_relationship,
            f"codebase-map.cross_module_relationships[{index}]",
            snapshot_root,
            pending_relationships,
            RELATIONSHIP_TYPES - {"contains"},
            errors,
        )

    for path, source_id, target_id in pending_relationships:
        if source_id not in node_ids:
            errors.append(f"{path}.from: dangling node id {source_id!r}")
        if target_id not in node_ids:
            errors.append(f"{path}.to: dangling node id {target_id!r}")

    for module_id, module in module_data.items():
        finding_ids: set[str] = set()
        interfaces = _list(
            module.get("interfaces"), f"module[{module_id}].interfaces", errors
        )
        for index, raw_interface in enumerate(interfaces):
            path = f"module[{module_id}].interfaces[{index}]"
            interface = _mapping(raw_interface, path, errors)
            _exact_fields(interface, {"name", "node", "evidence_refs"}, path, errors)
            _string(interface.get("name"), f"{path}.name", errors)
            node_id = _string(interface.get("node"), f"{path}.node", errors)
            if node_id and node_id not in node_ids:
                errors.append(f"{path}.node: dangling node id {node_id!r}")
            _evidence_refs(
                interface.get("evidence_refs"),
                f"{path}.evidence_refs",
                snapshot_root,
                errors,
            )

        couplings = _list(
            module.get("hidden_coupling"),
            f"module[{module_id}].hidden_coupling",
            errors,
        )
        for index, raw_coupling in enumerate(couplings):
            path = f"module[{module_id}].hidden_coupling[{index}]"
            coupling = _mapping(raw_coupling, path, errors)
            _exact_fields(
                coupling,
                {
                    "id",
                    "type",
                    "with_node",
                    "risk",
                    "confidence",
                    "evidence_refs",
                },
                path,
                errors,
            )
            coupling_id = _string(coupling.get("id"), f"{path}.id", errors)
            if coupling_id:
                if coupling_id in finding_ids:
                    errors.append(f"{path}.id: duplicate module-local finding id")
                finding_ids.add(coupling_id)
            _string(coupling.get("type"), f"{path}.type", errors)
            target = _string(
                coupling.get("with_node"), f"{path}.with_node", errors
            )
            if target and target not in node_ids and target not in coverage_paths:
                errors.append(
                    f"{path}.with_node: expected node id or coverage-gap path"
                )
            _string(coupling.get("risk"), f"{path}.risk", errors)
            if coupling.get("confidence") not in {"high", "medium", "low"}:
                errors.append(f"{path}.confidence: invalid enum")
            _evidence_refs(
                coupling.get("evidence_refs"),
                f"{path}.evidence_refs",
                snapshot_root,
                errors,
            )

        for index, raw_risk in enumerate(
            _list(
                module.get("rot_risks"),
                f"module[{module_id}].rot_risks",
                errors,
            )
        ):
            path = f"module[{module_id}].rot_risks[{index}]"
            risk = _mapping(raw_risk, path, errors)
            _exact_fields(
                risk,
                {
                    "id",
                    "failure_level",
                    "description",
                    "confidence",
                    "evidence_refs",
                },
                path,
                errors,
            )
            risk_id = _string(risk.get("id"), f"{path}.id", errors)
            if risk_id:
                if risk_id in finding_ids:
                    errors.append(f"{path}.id: duplicate module-local finding id")
                finding_ids.add(risk_id)
            if risk.get("failure_level") not in {1, 2, 3, 4}:
                errors.append(f"{path}.failure_level: invalid enum")
            _string(risk.get("description"), f"{path}.description", errors)
            if risk.get("confidence") not in {"high", "medium", "low"}:
                errors.append(f"{path}.confidence: invalid enum")
            _evidence_refs(
                risk.get("evidence_refs"),
                f"{path}.evidence_refs",
                snapshot_root,
                errors,
            )

        for index, raw_assumption in enumerate(
            _list(
                module.get("assumptions"),
                f"module[{module_id}].assumptions",
                errors,
            )
        ):
            path = f"module[{module_id}].assumptions[{index}]"
            assumption = _mapping(raw_assumption, path, errors)
            _exact_fields(
                assumption,
                {"statement", "status", "evidence_refs"},
                path,
                errors,
            )
            _string(assumption.get("statement"), f"{path}.statement", errors)
            if assumption.get("status") not in {"verified", "unverified"}:
                errors.append(f"{path}.status: invalid enum")
            _evidence_refs(
                assumption.get("evidence_refs"),
                f"{path}.evidence_refs",
                snapshot_root,
                errors,
            )

    flows = _list(root.get("business_flows"), "codebase-map.business_flows", errors)
    for flow_index, raw_flow in enumerate(flows):
        path = f"codebase-map.business_flows[{flow_index}]"
        flow = _mapping(raw_flow, path, errors)
        _exact_fields(
            flow, {"name", "purpose", "evidence_refs", "steps"}, path, errors
        )
        _string(flow.get("name"), f"{path}.name", errors)
        _string(flow.get("purpose"), f"{path}.purpose", errors)
        _evidence_refs(
            flow.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )
        for step_index, raw_step in enumerate(
            _list(flow.get("steps"), f"{path}.steps", errors)
        ):
            step_path = f"{path}.steps[{step_index}]"
            step = _mapping(raw_step, step_path, errors)
            _exact_fields(
                step, {"node", "action", "evidence_refs"}, step_path, errors
            )
            node_id = _string(step.get("node"), f"{step_path}.node", errors)
            if node_id and node_id not in node_ids:
                errors.append(f"{step_path}.node: dangling node id {node_id!r}")
            _string(step.get("action"), f"{step_path}.action", errors)
            _evidence_refs(
                step.get("evidence_refs"),
                f"{step_path}.evidence_refs",
                snapshot_root,
                errors,
            )

    infrastructure = _mapping(
        root.get("infrastructure"), "codebase-map.infrastructure", errors
    )
    _exact_fields(
        infrastructure,
        {"build", "config_sources", "data_flow"},
        "codebase-map.infrastructure",
        errors,
    )
    build = _mapping(
        infrastructure.get("build"), "codebase-map.infrastructure.build", errors
    )
    _exact_fields(
        build,
        {"tool", "test_command", "build_command", "ci_config"},
        "codebase-map.infrastructure.build",
        errors,
    )
    _string(build.get("tool"), "codebase-map.infrastructure.build.tool", errors)
    _string(
        build.get("test_command"),
        "codebase-map.infrastructure.build.test_command",
        errors,
    )
    _string(
        build.get("build_command"),
        "codebase-map.infrastructure.build.build_command",
        errors,
    )
    ci_config = _string(
        build.get("ci_config"),
        "codebase-map.infrastructure.build.ci_config",
        errors,
    )
    if ci_config and ci_config != "unknown":
        ci_path = _repo_path(
            ci_config,
            "codebase-map.infrastructure.build.ci_config",
            errors,
        )
        if ci_path and not (snapshot_root / ci_path).is_file():
            errors.append(
                "codebase-map.infrastructure.build.ci_config: "
                "does not exist in snapshot"
            )

    for index, raw_source in enumerate(
        _list(
            infrastructure.get("config_sources"),
            "codebase-map.infrastructure.config_sources",
            errors,
        )
    ):
        path = f"codebase-map.infrastructure.config_sources[{index}]"
        source_item = _mapping(raw_source, path, errors)
        _exact_fields(
            source_item,
            {"type", "path", "scope", "evidence_refs"},
            path,
            errors,
        )
        if source_item.get("type") not in {
            "env",
            "yaml",
            "json",
            "toml",
            "secrets",
            "code",
        }:
            errors.append(f"{path}.type: invalid enum")
        _string(source_item.get("path"), f"{path}.path", errors)
        if source_item.get("scope") not in {
            "runtime",
            "build-time",
            "both",
            "unknown",
        }:
            errors.append(f"{path}.scope: invalid enum")
        _evidence_refs(
            source_item.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )

    data_flow = _mapping(
        infrastructure.get("data_flow"),
        "codebase-map.infrastructure.data_flow",
        errors,
    )
    _exact_fields(
        data_flow,
        {"entry_points", "storage", "external_services"},
        "codebase-map.infrastructure.data_flow",
        errors,
    )
    for index, raw_entry in enumerate(
        _list(
            data_flow.get("entry_points"),
            "codebase-map.infrastructure.data_flow.entry_points",
            errors,
        )
    ):
        path = f"codebase-map.infrastructure.data_flow.entry_points[{index}]"
        entry = _mapping(raw_entry, path, errors)
        _exact_fields(
            entry, {"node", "description", "evidence_refs"}, path, errors
        )
        node_id = _string(entry.get("node"), f"{path}.node", errors)
        if node_id and node_id not in node_ids:
            errors.append(f"{path}.node: dangling node id {node_id!r}")
        _string(entry.get("description"), f"{path}.description", errors)
        _evidence_refs(
            entry.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )

    for index, raw_storage in enumerate(
        _list(
            data_flow.get("storage"),
            "codebase-map.infrastructure.data_flow.storage",
            errors,
        )
    ):
        path = f"codebase-map.infrastructure.data_flow.storage[{index}]"
        storage = _mapping(raw_storage, path, errors)
        _exact_fields(
            storage,
            {"type", "technology", "purpose", "evidence_refs"},
            path,
            errors,
        )
        if storage.get("type") not in {
            "database",
            "cache",
            "file-system",
            "external",
        }:
            errors.append(f"{path}.type: invalid enum")
        _string(storage.get("technology"), f"{path}.technology", errors)
        _string(storage.get("purpose"), f"{path}.purpose", errors)
        _evidence_refs(
            storage.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )

    for index, raw_service in enumerate(
        _list(
            data_flow.get("external_services"),
            "codebase-map.infrastructure.data_flow.external_services",
            errors,
        )
    ):
        path = f"codebase-map.infrastructure.data_flow.external_services[{index}]"
        service = _mapping(raw_service, path, errors)
        _exact_fields(
            service,
            {"name", "purpose", "connection", "evidence_refs"},
            path,
            errors,
        )
        _string(service.get("name"), f"{path}.name", errors)
        _string(service.get("purpose"), f"{path}.purpose", errors)
        _string(service.get("connection"), f"{path}.connection", errors)
        _evidence_refs(
            service.get("evidence_refs"),
            f"{path}.evidence_refs",
            snapshot_root,
            errors,
        )

    return errors, root


def _publish_candidate(
    candidate: Path,
    project_root: Path,
    expected_commit: str,
    previous_commit: str | None,
) -> None:
    samsara_dir = project_root / ".samsara"
    generations_dir = samsara_dir / "codebase-map"
    final_generation = generations_dir / expected_commit
    samsara_dir.mkdir(parents=True, exist_ok=True)
    generations_dir.mkdir(parents=True, exist_ok=True)

    if final_generation.exists():
        raise RuntimeError(
            f"generation already exists: {final_generation}; remove the ignored "
            "generation or use the current root manifest"
        )

    temporary_generation = Path(
        tempfile.mkdtemp(prefix=f".{expected_commit}.", dir=generations_dir)
    )
    try:
        shutil.copytree(
            candidate / "modules",
            temporary_generation / "modules",
            dirs_exist_ok=True,
        )
        os.replace(temporary_generation, final_generation)
    except Exception:
        shutil.rmtree(temporary_generation, ignore_errors=True)
        raise

    root_temp = samsara_dir / f".codebase-map.{expected_commit}.tmp"
    try:
        root_data = yaml.safe_load(
            (candidate / "codebase-map.yaml").read_text(encoding="utf-8")
        )
        root_temp.write_text(
            yaml.safe_dump(root_data, sort_keys=False),
            encoding="utf-8",
        )
        os.replace(root_temp, samsara_dir / "codebase-map.yaml")
    except Exception:
        root_temp.unlink(missing_ok=True)
        shutil.rmtree(final_generation, ignore_errors=True)
        raise

    keep = {expected_commit}
    if previous_commit:
        keep.add(previous_commit)
    for path in generations_dir.iterdir():
        if path.is_dir() and not path.name.startswith(".") and path.name not in keep:
            shutil.rmtree(path, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    project_root = args.project_root.resolve()
    snapshot_root = args.snapshot_root.resolve()
    errors, root = validate_candidate(
        candidate,
        project_root,
        snapshot_root,
        args.expected_commit,
    )
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    if not args.publish:
        print("VALID: codebase map format")
        return 0

    previous_commit: str | None = None
    live_root = project_root / ".samsara" / "codebase-map.yaml"
    if live_root.is_file():
        try:
            live = yaml.safe_load(live_root.read_text(encoding="utf-8"))
            value = (
                live.get("source", {}).get("commit")
                if isinstance(live, dict)
                else None
            )
            previous_commit = value if isinstance(value, str) else None
        except (OSError, UnicodeError, yaml.YAMLError):
            previous_commit = None

    try:
        _publish_candidate(
            candidate,
            project_root,
            args.expected_commit,
            previous_commit,
        )
    except (OSError, RuntimeError, shutil.Error) as exc:
        print(f"CANNOT PUBLISH: {exc}")
        return 2

    published = root.get("source", {}).get("commit")
    print(f"PUBLISHED: codebase map for {published}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
