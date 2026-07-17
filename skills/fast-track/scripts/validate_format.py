#!/usr/bin/env python3
"""Validate Fast-track artifact shape.

FORMAT only: this script checks YAML shape, enums, lifecycle consistency, and
placeholders. It never judges whether risk is truly low or review evidence is
persuasive.
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


_TOP_LEVEL = {
    "type",
    "status",
    "description",
    "source_refs",
    "entry",
    "acceptance",
    "death_evidence",
    "verification",
    "review",
    "files_changed",
    "escalation",
}
_RETIRED = {"scar_tag", "scar_items", "quality_review", "quality_checklist"}


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


def _find_placeholders(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, str) and "<" in value and ">" in value:
        errors.append(f"{path}: unresolved placeholder")
    elif isinstance(value, dict):
        for key, child in value.items():
            _find_placeholders(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _find_placeholders(child, f"{path}[{index}]", errors)


def validate_fast_track(path: Path) -> list[str]:
    """Return mechanical findings for one fast-track record."""
    errors: list[str] = []
    if path.is_dir():
        path = path / "fast-track.yaml"
    if not path.is_file():
        return [f"{path}: missing"]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: YAML parse error: {exc}"]
    root = _mapping(data, "fast-track", errors)
    if not root:
        return errors

    _required(root, _TOP_LEVEL, "fast-track", errors)
    for key in sorted(set(root) & _RETIRED):
        errors.append(f"fast-track.{key}: retired field")
    for key in sorted(set(root) - _TOP_LEVEL - _RETIRED):
        errors.append(f"fast-track.{key}: unexpected field")

    if root.get("type") != "fast_track":
        errors.append("fast-track.type: expected fast_track")
    if root.get("status") not in {"completed", "escalated"}:
        errors.append("fast-track.status: expected completed or escalated")
    _nonempty(root.get("description"), "fast-track.description", errors)
    _list(root.get("source_refs"), "fast-track.source_refs", errors)
    _list(root.get("acceptance"), "fast-track.acceptance", errors)
    _list(root.get("verification"), "fast-track.verification", errors)
    _list(root.get("files_changed"), "fast-track.files_changed", errors)

    entry = _mapping(root.get("entry"), "fast-track.entry", errors)
    _required(
        entry,
        {
            "authority",
            "risk_evidence",
            "affected_surfaces",
            "structural_impact",
            "unknowns",
        },
        "fast-track.entry",
        errors,
    )
    _nonempty(entry.get("authority"), "fast-track.entry.authority", errors)
    _list(entry.get("risk_evidence"), "fast-track.entry.risk_evidence", errors)
    _list(entry.get("affected_surfaces"), "fast-track.entry.affected_surfaces", errors)
    _list(entry.get("unknowns"), "fast-track.entry.unknowns", errors)
    if entry.get("structural_impact") not in {"none", "present", "unknown"}:
        errors.append(
            "fast-track.entry.structural_impact: expected none, present, or unknown"
        )

    death = _mapping(root.get("death_evidence"), "fast-track.death_evidence", errors)
    _required(death, {"clause", "pre_change"}, "fast-track.death_evidence", errors)
    _nonempty(death.get("clause"), "fast-track.death_evidence.clause", errors)
    pre_change = _mapping(
        death.get("pre_change"), "fast-track.death_evidence.pre_change", errors
    )
    _required(
        pre_change,
        {"command", "result"},
        "fast-track.death_evidence.pre_change",
        errors,
    )
    _nonempty(
        pre_change.get("command"),
        "fast-track.death_evidence.pre_change.command",
        errors,
    )
    _nonempty(
        pre_change.get("result"),
        "fast-track.death_evidence.pre_change.result",
        errors,
    )

    review = _mapping(root.get("review"), "fast-track.review", errors)
    _required(
        review,
        {"domains", "reference_refs", "evidence_refs", "findings", "unknowns"},
        "fast-track.review",
        errors,
    )
    for key in ("domains", "reference_refs", "evidence_refs", "findings", "unknowns"):
        _list(review.get(key), f"fast-track.review.{key}", errors)

    escalation = _mapping(root.get("escalation"), "fast-track.escalation", errors)
    _required(escalation, {"route", "reason"}, "fast-track.escalation", errors)
    route = escalation.get("route")
    reason = escalation.get("reason")
    if root.get("status") == "completed" and (route is not None or reason is not None):
        errors.append(
            "fast-track.escalation: completed record must use null route/reason"
        )
    if root.get("status") == "escalated":
        if route != "research":
            errors.append(
                "fast-track.escalation.route: escalated record must use research"
            )
        _nonempty(reason, "fast-track.escalation.reason", errors)

    _find_placeholders(root, "fast-track", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate_fast_track(args.path)
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    print("VALID: fast-track format")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
