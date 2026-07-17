#!/usr/bin/env python3
"""Validate Debugging diagnosis artifacts.

FORMAT only: this script checks YAML shape, enums, phase linkage, and declared
route consistency. It never judges whether the diagnosis, route, or free-text
content is adequate.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is unavailable.")
    sys.exit(2)


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


def _nonempty(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty string")


def _required(
    mapping: dict[str, Any], keys: Iterable[str], path: str, errors: list[str]
) -> None:
    for key in keys:
        if key not in mapping:
            errors.append(f"{path}.{key}: missing")


def _load(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"{label}: missing {path.name}")
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{label}: YAML parse error: {exc}")
        return {}
    return _mapping(data, label, errors)


def validate_debugging(directory: Path) -> list[str]:
    """Return mechanical findings for one bugfix diagnosis directory."""
    errors: list[str] = []
    report = _load(directory / "bug-report.yaml", "bug-report", errors)
    cause = _load(directory / "root-cause.yaml", "root-cause", errors)
    if (directory / "fix-summary.yaml").exists():
        errors.append(
            "fix-summary.yaml: retired artifact; repair owner records the fix"
        )
    if not report or not cause:
        return errors

    _required(
        report,
        {"schema_version", "bug", "failure", "impact", "containment", "unknowns"},
        "bug-report",
        errors,
    )
    if report.get("schema_version") != 1:
        errors.append("bug-report.schema_version: expected 1")
    bug = _mapping(report.get("bug"), "bug-report.bug", errors)
    _required(
        bug,
        {"title", "reported_by", "observable_result", "evidence_refs"},
        "bug-report.bug",
        errors,
    )
    for key in ("title", "reported_by", "observable_result"):
        _nonempty(bug.get(key), f"bug-report.bug.{key}", errors)
    _list(bug.get("evidence_refs"), "bug-report.bug.evidence_refs", errors)

    failure = _mapping(report.get("failure"), "bug-report.failure", errors)
    _required(failure, {"level", "rationale"}, "bug-report.failure", errors)
    if failure.get("level") not in {1, 2, 3, 4}:
        errors.append("bug-report.failure.level: expected 1, 2, 3, or 4")
    _nonempty(failure.get("rationale"), "bug-report.failure.rationale", errors)

    impact = _mapping(report.get("impact"), "bug-report.impact", errors)
    _required(
        impact,
        {"scope", "duration", "detection_delay", "evidence_refs"},
        "bug-report.impact",
        errors,
    )
    _list(impact.get("evidence_refs"), "bug-report.impact.evidence_refs", errors)

    containment = _mapping(report.get("containment"), "bug-report.containment", errors)
    _required(
        containment,
        {"required", "action", "authorization"},
        "bug-report.containment",
        errors,
    )
    if containment.get("required") not in {"yes", "no", "unknown"}:
        errors.append("bug-report.containment.required: invalid enum")
    if containment.get("authorization") not in {
        "not_requested",
        "requested",
        "approved",
        "applied",
    }:
        errors.append("bug-report.containment.authorization: invalid enum")
    _list(report.get("unknowns"), "bug-report.unknowns", errors)

    _required(
        cause,
        {
            "schema_version",
            "bug_report_ref",
            "root_cause",
            "reproduction",
            "rot_path",
            "death_test",
            "repair",
        },
        "root-cause",
        errors,
    )
    if cause.get("schema_version") != 1:
        errors.append("root-cause.schema_version: expected 1")
    if cause.get("bug_report_ref") != "bug-report.yaml":
        errors.append("root-cause.bug_report_ref: expected bug-report.yaml")

    diagnosis = _mapping(cause.get("root_cause"), "root-cause.root_cause", errors)
    _required(
        diagnosis,
        {"status", "hypothesis", "evidence_refs", "refuting_evidence", "why_hidden"},
        "root-cause.root_cause",
        errors,
    )
    if diagnosis.get("status") not in {"hypothesized", "confirmed", "unknown"}:
        errors.append("root-cause.root_cause.status: invalid enum")
    _list(
        diagnosis.get("evidence_refs"),
        "root-cause.root_cause.evidence_refs",
        errors,
    )
    _list(
        diagnosis.get("refuting_evidence"),
        "root-cause.root_cause.refuting_evidence",
        errors,
    )

    reproduction = _mapping(
        cause.get("reproduction"), "root-cause.reproduction", errors
    )
    _required(
        reproduction,
        {"status", "evidence_ref"},
        "root-cause.reproduction",
        errors,
    )
    if reproduction.get("status") not in {
        "reproduced",
        "not_reproduced",
        "unknown",
    }:
        errors.append("root-cause.reproduction.status: invalid enum")
    _list(cause.get("rot_path"), "root-cause.rot_path", errors)

    death_test = _mapping(cause.get("death_test"), "root-cause.death_test", errors)
    _required(
        death_test,
        {"status", "evidence_ref", "specification"},
        "root-cause.death_test",
        errors,
    )
    if death_test.get("status") not in {"failing", "specified", "unavailable"}:
        errors.append("root-cause.death_test.status: invalid enum")

    repair = _mapping(cause.get("repair"), "root-cause.repair", errors)
    _required(
        repair,
        {"authorized", "scope", "route", "rationale"},
        "root-cause.repair",
        errors,
    )
    if not isinstance(repair.get("authorized"), bool):
        errors.append("root-cause.repair.authorized: expected boolean")
    if repair.get("scope") not in {"bounded", "structural", "wide", "unknown"}:
        errors.append("root-cause.repair.scope: invalid enum")
    if repair.get("route") not in {"diagnosis_only", "fast_track", "research"}:
        errors.append("root-cause.repair.route: invalid enum")
    _nonempty(repair.get("rationale"), "root-cause.repair.rationale", errors)

    route = repair.get("route")
    if route == "diagnosis_only" and repair.get("authorized") is not False:
        errors.append("root-cause.repair: diagnosis_only requires authorized=false")
    if route in {"fast_track", "research"} and repair.get("authorized") is not True:
        errors.append(f"root-cause.repair: {route} requires authorized=true")
    if route == "fast_track":
        if diagnosis.get("status") != "confirmed":
            errors.append("root-cause.repair: fast_track requires confirmed root cause")
        if repair.get("scope") != "bounded":
            errors.append("root-cause.repair: fast_track requires bounded scope")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    errors = validate_debugging(args.directory)
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    print("VALID: debugging format")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
