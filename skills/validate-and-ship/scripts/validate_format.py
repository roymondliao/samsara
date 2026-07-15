#!/usr/bin/env python3
"""Validate the machine-decidable Ship Manifest evidence graph.

Scope is FORMAT only: YAML shape, enums, commit/ref resolution, step coverage,
and ready-state consistency. Risk quality, evidence relevance, and operational
control adequacy remain judgment.

Exit code: 0 = clean, 1 = findings, 2 = cannot validate / unknown.

Usage:
    python validate_format.py <feature-dir> [--repo-root <path>]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment-dependent
    print("CANNOT VALIDATE: PyYAML is unavailable to the uv-run environment.")
    print("This is an unknown outcome, not a pass.")
    sys.exit(2)


_AUTHORITY_RE = re.compile(r"^(?:PT-(?:CI|EVAL|D\d+|S\d+)|PL-D\d+|AC-\d+)$")
_SCAR_REF_RE = re.compile(r"^(scar-reports/[^#]+)#(SC-[1-9]\d*)$")
_MARKDOWN_REF_RE = re.compile(r"^([^#]+)#(.+)$")
_PLACEHOLDER_RE = re.compile(r"<[^>]+>")
_FINDING_ID_RE = re.compile(r"^VF-[1-9]\d*$")

_TOP_STATUSES = {"in_progress", "ready_for_delivery", "blocked"}
_SECURITY_STATUSES = {"pass", "accepted_risk", "fail", "unknown"}
_EXPOSURE_STATUSES = {"pass", "blocked", "unknown"}
_RESULT_STATUSES = {"pass", "fail", "unknown"}
_E2E_STATUSES = {"pass", "fail", "not_applicable", "unknown"}
_CONTROL_STATUSES = {"available", "absent", "not_applicable", "unknown"}
_DELIVERY_ACTIONS = {"pending", "merge", "create_pr", "keep_branch", "discard"}
_SELECTORS = {None, "human", "auto-gatekeeper"}
_FINDING_STEPS = {
    "security_privacy",
    "remaining_exposure",
    "acceptance",
    "primary_evaluator",
    "e2e",
    "reconciliation",
    "review_evidence",
}
_FINDING_RESULTS = {"fail", "unknown"}
_FINDING_OWNERS = {"iteration", "implement", "planning", "pre-thinking"}
_FINDING_SEVERITIES = {None, "critical", "high", "medium", "low"}


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _map(value: Any, where: str, findings: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        findings.append(f"shape: `{where}` must be a mapping")
        return {}
    return value


def _require(
    mapping: dict[str, Any], fields: set[str], where: str, findings: list[str]
) -> None:
    for field in sorted(fields - set(mapping)):
        findings.append(f"shape: `{where}` is missing `{field}`")


def _enum(value: Any, allowed: set[Any], where: str, findings: list[str]) -> None:
    if value not in allowed:
        rendered = ", ".join(str(item) for item in sorted(allowed, key=str))
        findings.append(f"enum: `{where}` must be one of: {rendered}")


def _string_list(value: Any, where: str, findings: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        findings.append(f"shape: `{where}` must be a list of strings")
        return []
    return value


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_PLACEHOLDER_RE.search(value))
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    return False


def _commit_exists(repo_root: Path, commit: Any) -> bool:
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _authority_ids(feature_dir: Path) -> set[str]:
    ids: set[str] = set()
    for name in ("pre-thinking.md", "2-plan.md"):
        path = feature_dir / name
        if path.is_file():
            ids.update(
                re.findall(
                    r"\b(?:PT-(?:CI|EVAL|D\d+|S\d+)|PL-D\d+)\b",
                    path.read_text(encoding="utf-8"),
                )
            )
    acceptance = feature_dir / "acceptance.yaml"
    if acceptance.is_file():
        try:
            data = _read_yaml(acceptance)
        except yaml.YAMLError:
            return ids
        if isinstance(data, dict) and isinstance(data.get("scenarios"), list):
            ids.update(
                str(item.get("id"))
                for item in data["scenarios"]
                if isinstance(item, dict) and item.get("id")
            )
    return ids


def _scar_ids(path: Path) -> set[str] | None:
    if not path.is_file():
        return None
    try:
        data = _read_yaml(path)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    ids: set[str] = set()
    for section in ("known_shortcuts", "silent_failure_conditions", "assumptions_made"):
        items = data.get(section)
        if not isinstance(items, list):
            continue
        ids.update(
            str(item.get("scar_id"))
            for item in items
            if isinstance(item, dict) and item.get("scar_id")
        )
    return ids


def _check_scar_refs(
    feature_dir: Path, refs: list[str], where: str, findings: list[str]
) -> None:
    for ref in refs:
        match = _SCAR_REF_RE.fullmatch(ref)
        if match is None:
            findings.append(f"scar-ref: `{where}` has invalid ref `{ref}`")
            continue
        path = feature_dir / match.group(1)
        ids = _scar_ids(path)
        if ids is None or match.group(2) not in ids:
            findings.append(f"scar-ref: `{where}` cannot resolve `{ref}`")


def _check_markdown_refs(
    feature_dir: Path, refs: list[str], where: str, findings: list[str]
) -> None:
    for ref in refs:
        match = _MARKDOWN_REF_RE.fullmatch(ref)
        if match is None:
            findings.append(f"evidence-ref: `{where}` must use `file#anchor`: `{ref}`")
            continue
        path = feature_dir / match.group(1)
        if (
            not path.is_file()
            or match.group(2).lower() not in path.read_text(encoding="utf-8").lower()
        ):
            findings.append(f"evidence-ref: `{where}` cannot resolve `{ref}`")


def _check_security(
    section: dict[str, Any], selected_by: Any, findings: list[str]
) -> None:
    _require(
        section,
        {"status", "scope_ref", "evidence_refs", "accepted_risks"},
        "validation.security_privacy",
        findings,
    )
    status = section.get("status")
    _enum(status, _SECURITY_STATUSES, "validation.security_privacy.status", findings)
    _string_list(
        section.get("evidence_refs"),
        "validation.security_privacy.evidence_refs",
        findings,
    )
    risks = section.get("accepted_risks")
    if not isinstance(risks, list):
        findings.append(
            "shape: `validation.security_privacy.accepted_risks` must be a list"
        )
        risks = []
    required = {"finding_ref", "rationale", "re_review_signal", "owner"}
    for index, risk in enumerate(risks):
        where = f"validation.security_privacy.accepted_risks[{index}]"
        if not isinstance(risk, dict):
            findings.append(f"shape: `{where}` must be a mapping")
            continue
        _require(risk, required, where, findings)
        for field in required:
            if not str(risk.get(field) or "").strip():
                findings.append(f"accepted-risk: `{where}.{field}` must be non-empty")
    if status == "accepted_risk" and not risks:
        findings.append(
            "accepted-risk: status accepted_risk requires at least one risk"
        )
    if status == "pass" and risks:
        findings.append("accepted-risk: pass cannot carry accepted security risks")
    if selected_by == "auto-gatekeeper" and risks:
        findings.append(
            "accepted-risk: auto-gatekeeper cannot accept security/privacy risk"
        )


def _check_control(name: str, value: Any, findings: list[str]) -> None:
    control = _map(value, f"operational_controls.{name}", findings)
    _require(
        control,
        {"status", "mechanism", "evidence_refs"},
        f"operational_controls.{name}",
        findings,
    )
    status = control.get("status")
    _enum(status, _CONTROL_STATUSES, f"operational_controls.{name}.status", findings)
    refs = _string_list(
        control.get("evidence_refs"),
        f"operational_controls.{name}.evidence_refs",
        findings,
    )
    mechanism = control.get("mechanism")
    if status == "available" and (not str(mechanism or "").strip() or not refs):
        findings.append(
            f"operational-control: {name} available requires non-empty mechanism and evidence_refs"
        )


def _check_validation_findings(
    value: Any, known_ids: set[str], findings: list[str]
) -> list[dict[str, Any]]:
    where = "validation.findings"
    if not isinstance(value, list):
        findings.append(f"shape: `{where}` must be a list")
        return []

    required = {
        "id",
        "step",
        "result",
        "owner",
        "observable_result",
        "evidence_refs",
        "severity",
        "path",
        "location",
        "source_ref",
    }
    parsed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for index, raw_finding in enumerate(value):
        item_where = f"{where}[{index}]"
        item = _map(raw_finding, item_where, findings)
        _require(item, required, item_where, findings)
        parsed.append(item)

        finding_id = item.get("id")
        if (
            not isinstance(finding_id, str)
            or _FINDING_ID_RE.fullmatch(finding_id) is None
        ):
            findings.append(f"finding-id: `{item_where}.id` must match `VF-N`")
        elif finding_id in seen_ids:
            findings.append(f"finding-id: duplicate `{finding_id}`")
        else:
            seen_ids.add(finding_id)

        _enum(item.get("step"), _FINDING_STEPS, f"{item_where}.step", findings)
        _enum(item.get("result"), _FINDING_RESULTS, f"{item_where}.result", findings)
        _enum(item.get("owner"), _FINDING_OWNERS, f"{item_where}.owner", findings)
        _enum(
            item.get("severity"),
            _FINDING_SEVERITIES,
            f"{item_where}.severity",
            findings,
        )

        if not str(item.get("observable_result") or "").strip():
            findings.append(
                f"finding: `{item_where}.observable_result` must be non-empty"
            )
        evidence_refs = _string_list(
            item.get("evidence_refs"), f"{item_where}.evidence_refs", findings
        )
        if not evidence_refs or any(not ref.strip() for ref in evidence_refs):
            findings.append(
                f"finding: `{item_where}.evidence_refs` must contain durable evidence"
            )

        path = item.get("path")
        location = item.get("location")
        source_ref = item.get("source_ref")
        has_path_locator = bool(str(path or "").strip()) and bool(
            str(location or "").strip()
        )
        has_source_locator = bool(str(source_ref or "").strip())
        if not has_path_locator and not has_source_locator:
            findings.append(
                f"finding-locator: `{item_where}` requires path and location or source_ref"
            )
        if has_source_locator and (
            not isinstance(source_ref, str)
            or _AUTHORITY_RE.fullmatch(source_ref) is None
            or source_ref not in known_ids
        ):
            findings.append(
                f"finding-locator: `{item_where}.source_ref` cannot resolve `{source_ref}`"
            )

    return parsed


def validate(feature_dir: Path, repo_root: Path) -> tuple[list[str], str | None]:
    manifest_path = feature_dir / "ship-manifest.yaml"
    if not manifest_path.is_file():
        return [], f"missing `{manifest_path}`"
    try:
        raw = _read_yaml(manifest_path)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [], f"cannot parse `{manifest_path}`: {exc}"
    if not isinstance(raw, dict):
        return ["shape: manifest root must be a mapping"], None

    findings: list[str] = []
    _require(
        raw,
        {
            "feature",
            "delivered_capability",
            "snapshot",
            "validation_status",
            "validation",
            "operational_controls",
            "delivery",
        },
        "manifest",
        findings,
    )
    if _contains_placeholder(raw):
        findings.append("placeholder: manifest still contains `<...>` template text")

    capability = _map(raw.get("delivered_capability"), "delivered_capability", findings)
    _require(capability, {"summary", "source_refs"}, "delivered_capability", findings)
    if not str(capability.get("summary") or "").strip():
        findings.append("shape: `delivered_capability.summary` must be non-empty")
    source_refs = _string_list(
        capability.get("source_refs"), "delivered_capability.source_refs", findings
    )
    known_ids = _authority_ids(feature_dir)
    for ref in source_refs:
        if _AUTHORITY_RE.fullmatch(ref) is None or ref not in known_ids:
            findings.append(f"authority-ref: cannot resolve `{ref}`")

    snapshot = _map(raw.get("snapshot"), "snapshot", findings)
    _require(snapshot, {"base_commit", "candidate_commit"}, "snapshot", findings)
    base = snapshot.get("base_commit")
    candidate = snapshot.get("candidate_commit")
    for field, value in (("base_commit", base), ("candidate_commit", candidate)):
        if not _commit_exists(repo_root, value):
            findings.append(
                f"commit-ref: `snapshot.{field}` does not resolve: `{value}`"
            )

    index_path = feature_dir / "index.yaml"
    if not index_path.is_file():
        findings.append("snapshot: `index.yaml` is missing")
    else:
        try:
            index = _read_yaml(index_path)
        except yaml.YAMLError:
            index = None
        checkpoint = index.get("iteration_entry") if isinstance(index, dict) else None
        if not isinstance(checkpoint, dict):
            findings.append("snapshot: `index.yaml.iteration_entry` must be a mapping")
        elif checkpoint.get("last_commit") != candidate:
            findings.append(
                "snapshot: candidate_commit must equal the last_commit field "
                "under iteration_entry in index.yaml"
            )

    top_status = raw.get("validation_status")
    _enum(top_status, _TOP_STATUSES, "validation_status", findings)
    validation = _map(raw.get("validation"), "validation", findings)
    step_names = {
        "security_privacy",
        "remaining_exposure",
        "acceptance",
        "primary_evaluator",
        "e2e",
        "reconciliation",
        "review_evidence",
    }
    _require(validation, step_names | {"findings"}, "validation", findings)
    validation_findings = _check_validation_findings(
        validation.get("findings"), known_ids, findings
    )

    delivery = _map(raw.get("delivery"), "delivery", findings)
    _require(
        delivery,
        {"action", "selected_by", "decision_ref", "preparation"},
        "delivery",
        findings,
    )
    action = delivery.get("action")
    selected_by = delivery.get("selected_by")
    _enum(action, _DELIVERY_ACTIONS, "delivery.action", findings)
    _enum(selected_by, _SELECTORS, "delivery.selected_by", findings)
    _string_list(delivery.get("preparation"), "delivery.preparation", findings)
    if selected_by == "auto-gatekeeper":
        decision_ref = delivery.get("decision_ref")
        if not isinstance(decision_ref, str) or not decision_ref.strip():
            findings.append("delivery: auto-gatekeeper requires non-empty decision_ref")
        else:
            _check_markdown_refs(
                feature_dir, [decision_ref], "delivery.decision_ref", findings
            )

    security = _map(
        validation.get("security_privacy"), "validation.security_privacy", findings
    )
    _check_security(security, selected_by, findings)
    if security.get("scope_ref") != f"{base}...{candidate}":
        findings.append(
            "snapshot: security_privacy.scope_ref must equal base_commit...candidate_commit"
        )

    exposure = _map(
        validation.get("remaining_exposure"), "validation.remaining_exposure", findings
    )
    exposure_fields = {
        "status",
        "accepted_refs",
        "deferred_refs",
        "open_refs",
        "blocked_refs",
    }
    _require(exposure, exposure_fields, "validation.remaining_exposure", findings)
    _enum(
        exposure.get("status"),
        _EXPOSURE_STATUSES,
        "validation.remaining_exposure.status",
        findings,
    )
    for field in exposure_fields - {"status"}:
        refs = _string_list(
            exposure.get(field), f"validation.remaining_exposure.{field}", findings
        )
        _check_scar_refs(
            feature_dir, refs, f"validation.remaining_exposure.{field}", findings
        )

    acceptance = _map(validation.get("acceptance"), "validation.acceptance", findings)
    _require(
        acceptance, {"status", "scenario_results"}, "validation.acceptance", findings
    )
    _enum(
        acceptance.get("status"),
        _RESULT_STATUSES,
        "validation.acceptance.status",
        findings,
    )
    results = acceptance.get("scenario_results")
    if not isinstance(results, list):
        findings.append(
            "shape: `validation.acceptance.scenario_results` must be a list"
        )
        results = []
    result_ids: list[str] = []
    for index, result in enumerate(results):
        where = f"validation.acceptance.scenario_results[{index}]"
        item = _map(result, where, findings)
        _require(item, {"scenario_ref", "status", "evidence_refs"}, where, findings)
        scenario_ref = str(item.get("scenario_ref") or "")
        result_ids.append(scenario_ref)
        if scenario_ref not in known_ids or not scenario_ref.startswith("AC-"):
            findings.append(f"acceptance-ref: cannot resolve `{scenario_ref}`")
        _enum(item.get("status"), _RESULT_STATUSES, f"{where}.status", findings)
        _string_list(item.get("evidence_refs"), f"{where}.evidence_refs", findings)
    declared_ac = {item for item in known_ids if item.startswith("AC-")}
    if set(result_ids) != declared_ac or len(result_ids) != len(set(result_ids)):
        findings.append(
            "acceptance-coverage: scenario_results must cover each declared AC-* exactly once"
        )

    evaluator = _map(
        validation.get("primary_evaluator"), "validation.primary_evaluator", findings
    )
    _require(
        evaluator,
        {"evaluator_ref", "status", "evidence_refs"},
        "validation.primary_evaluator",
        findings,
    )
    if evaluator.get("evaluator_ref") != "PT-EVAL" or "PT-EVAL" not in known_ids:
        findings.append("evaluator-ref: `PT-EVAL` does not resolve")
    _enum(
        evaluator.get("status"),
        _RESULT_STATUSES,
        "validation.primary_evaluator.status",
        findings,
    )
    _string_list(
        evaluator.get("evidence_refs"),
        "validation.primary_evaluator.evidence_refs",
        findings,
    )

    e2e = _map(validation.get("e2e"), "validation.e2e", findings)
    _require(e2e, {"status", "evidence_refs"}, "validation.e2e", findings)
    _enum(e2e.get("status"), _E2E_STATUSES, "validation.e2e.status", findings)
    _string_list(e2e.get("evidence_refs"), "validation.e2e.evidence_refs", findings)

    reconciliation = _map(
        validation.get("reconciliation"), "validation.reconciliation", findings
    )
    _require(reconciliation, {"status", "drift"}, "validation.reconciliation", findings)
    _enum(
        reconciliation.get("status"),
        _RESULT_STATUSES,
        "validation.reconciliation.status",
        findings,
    )
    if not isinstance(reconciliation.get("drift"), list):
        findings.append("shape: `validation.reconciliation.drift` must be a list")

    review = _map(
        validation.get("review_evidence"), "validation.review_evidence", findings
    )
    _require(
        review, {"status", "evidence_refs"}, "validation.review_evidence", findings
    )
    _enum(
        review.get("status"),
        _RESULT_STATUSES,
        "validation.review_evidence.status",
        findings,
    )
    review_refs = _string_list(
        review.get("evidence_refs"),
        "validation.review_evidence.evidence_refs",
        findings,
    )
    _check_markdown_refs(
        feature_dir, review_refs, "validation.review_evidence.evidence_refs", findings
    )

    controls = _map(raw.get("operational_controls"), "operational_controls", findings)
    _require(
        controls,
        {"monitoring", "rollback_or_disable"},
        "operational_controls",
        findings,
    )
    _check_control("monitoring", controls.get("monitoring"), findings)
    _check_control("rollback_or_disable", controls.get("rollback_or_disable"), findings)

    if top_status == "blocked" and not validation_findings:
        findings.append(
            "blocked-handoff: `validation.findings` must name why validation stopped"
        )

    if top_status == "ready_for_delivery":
        required_pass = {
            "security_privacy": {"pass", "accepted_risk"},
            "remaining_exposure": {"pass"},
            "acceptance": {"pass"},
            "primary_evaluator": {"pass"},
            "e2e": {"pass", "not_applicable"},
            "reconciliation": {"pass"},
            "review_evidence": {"pass"},
        }
        for step, allowed in required_pass.items():
            section = validation.get(step)
            status = section.get("status") if isinstance(section, dict) else None
            if status not in allowed:
                findings.append(
                    f"ready-for-delivery: `{step}` has non-passing status `{status}`"
                )
        for field in ("open_refs", "blocked_refs"):
            if isinstance(exposure.get(field), list) and exposure[field]:
                findings.append(f"ready-for-delivery: `{field}` must be empty")
        if validation_findings:
            findings.append("ready-for-delivery: `validation.findings` must be empty")
        if action == "pending" or selected_by is None:
            findings.append(
                "ready-for-delivery: delivery action and selected_by must be final"
            )

    return findings, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feature_dir", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    findings, cannot_validate = validate(
        args.feature_dir.resolve(), args.repo_root.resolve()
    )
    if cannot_validate:
        print(f"CANNOT VALIDATE: {cannot_validate}")
        print("This is an unknown outcome, not a pass.")
        return 2
    if findings:
        for finding in findings:
            print(f"FINDING: {finding}")
        return 1
    print("FORMAT OK: ship-manifest.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
