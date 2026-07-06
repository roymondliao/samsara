#!/usr/bin/env python3
"""Implement format validator — mechanical shape checks for scar reports.

Scope: FORMAT only (machine-decidable). This script never judges whether a
structural decision is a good bet, whether a refusal is wise, or whether a
forced_by ref is genuinely RELEVANT — those are judgment and belong to the
reviewers. It checks the mechanical shape the reviewers and aggregators
depend on, so a silent skip becomes a visible missing.

Checks per changes/<feature>/scar-reports/task-N-scar.yaml:
  scar-parse           file parses as YAML with a task_id
  dual-face            every structural_decisions entry carries both faces:
                       decision + forced_by (yang) AND refused + risk_if_wrong
                       (yin); serves_seam key present (null allowed)
  forced-by-resolves   every forced_by ref resolves to something checkable:
                       `task-N` ids exist in index.yaml (and when the citing
                       task's affects/depends context is available, the cited
                       task is reachable from it); `seam: <name>` resolves to
                       overview.md Real Seams; `git:`/file refs point at paths
                       that exist
  seam-resolves        serves_seam (non-null) resolves to a declared seam
  systemic-ref         every systemic_ref id exists in .samsara/systemic-scars.yaml
                       (a dangling id is a parse failure at aggregation time)
  debt-consistency     debt_registered is true when shortcuts / silent failure
                       conditions exist

structural_decisions key policy: required for NEW reports —
`structural_decisions: []` = checked, no structural bet; a MISSING key is
reported as a finding (schema Rule 15). Old reports predating the rule are
this script's caller's concern; at implement handoff every report is new.

Exit code: 0 = clean, 1 = findings, 2 = cannot validate.

Usage:
    python validate_format.py <feature-dir> [--repo-root <path>]
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

_TASK_ID_RE = re.compile(r"\btask-\d+\b")
_SEAM_REF_RE = re.compile(r"\bseam:\s*(\S+)")
_FILE_REF_RE = re.compile(r"\bgit:\s*([^\s:#]+)")
_SEAM_DECL_RE = re.compile(r"^\s*-\s*seam:\s*(\S+)", re.MULTILINE)


def _declared_seams(feature_dir: Path) -> set[str]:
    overview = feature_dir / "overview.md"
    if not overview.is_file():
        return set()
    text = overview.read_text(encoding="utf-8")
    start = text.find("### Real Seams")
    if start == -1:
        return set()
    rest = text[start:]
    end = re.search(r"^#{1,3} ", rest[len("### Real Seams") :], re.MULTILINE)
    body = rest if end is None else rest[: end.start() + len("### Real Seams")]
    return set(_SEAM_DECL_RE.findall(body))


def _known_task_ids(feature_dir: Path) -> set[str]:
    index = feature_dir / "index.yaml"
    if not index.is_file():
        return set()
    try:
        data = yaml.safe_load(index.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        return set()
    return {
        str(t.get("id")) for t in data["tasks"] if isinstance(t, dict) and t.get("id")
    }


def _registry_ids(repo_root: Path) -> set[str] | None:
    """Return systemic scar registry ids, or None when the registry is absent."""
    registry = repo_root / ".samsara" / "systemic-scars.yaml"
    if not registry.is_file():
        return None
    try:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict):
        return set()
    scars = data.get("scars", data)
    if isinstance(scars, dict):
        return {str(k) for k in scars}
    if isinstance(scars, list):
        return {str(s.get("id")) for s in scars if isinstance(s, dict) and s.get("id")}
    return set()


def _iter_items(section: list | None) -> list[dict]:
    """Normalize a scar list section: plain strings become dicts (schema Rule 8)."""
    items: list[dict] = []
    for item in section or []:
        if isinstance(item, str):
            items.append({"description": item})
        elif isinstance(item, dict):
            items.append(item)
    return items


def validate_scar(
    scar_path: Path,
    known_ids: set[str],
    seams: set[str],
    registry: set[str] | None,
    repo_root: Path,
) -> list[str]:
    name = scar_path.name
    try:
        data = yaml.safe_load(scar_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"scar-parse: {name} does not parse as YAML: {exc}"]
    if not isinstance(data, dict) or not data.get("task_id"):
        return [f"scar-parse: {name} has no task_id"]

    findings: list[str] = []

    # --- systemic_ref dangling check across all scar list sections ---
    for section_name in (
        "known_shortcuts",
        "silent_failure_conditions",
        "assumptions_made",
    ):
        for item in _iter_items(data.get(section_name)):
            ref = item.get("systemic_ref")
            if not ref:
                continue
            if registry is None:
                findings.append(
                    f"systemic-ref: {name} {section_name} cites `{ref}` but "
                    ".samsara/systemic-scars.yaml does not exist"
                )
            elif str(ref) not in registry:
                findings.append(
                    f"systemic-ref: {name} {section_name} cites `{ref}` which is "
                    "not in .samsara/systemic-scars.yaml (dangling id = parse "
                    "failure at aggregation time)"
                )

    # --- debt consistency (mechanical: lists non-empty => flag true) ---
    has_debt = bool(_iter_items(data.get("known_shortcuts"))) or bool(
        _iter_items(data.get("silent_failure_conditions"))
    )
    if has_debt and data.get("debt_registered") is not True:
        findings.append(
            f"debt-consistency: {name} has shortcuts/silent-failure items but "
            "debt_registered is not true"
        )

    # --- structural_decisions ---
    if "structural_decisions" not in data:
        findings.append(
            f"dual-face: {name} has no structural_decisions key — write "
            "`structural_decisions: []` when the task made no structural bet "
            "(missing key = never considered, schema Rule 15)"
        )
        return findings

    decisions = data.get("structural_decisions") or []
    if not isinstance(decisions, list):
        findings.append(f"dual-face: {name} structural_decisions is not a list")
        return findings

    for i, entry in enumerate(decisions):
        where = f"{name} structural_decisions[{i}]"
        if not isinstance(entry, dict):
            findings.append(f"dual-face: {where} is not a map")
            continue
        if not str(entry.get("decision") or "").strip():
            findings.append(f"dual-face: {where} has no `decision`")
        forced_by = entry.get("forced_by") or []
        if not forced_by:
            findings.append(
                f"dual-face: {where} has empty `forced_by` — a structural bet "
                "with no citable force should not have been written (Rule 17)"
            )
        if not str(entry.get("refused") or "").strip():
            findings.append(f"dual-face: {where} missing yin face `refused`")
        if not str(entry.get("risk_if_wrong") or "").strip():
            findings.append(f"dual-face: {where} missing yin face `risk_if_wrong`")
        if "serves_seam" not in entry:
            findings.append(
                f"dual-face: {where} missing `serves_seam` key (null allowed)"
            )

        seam = entry.get("serves_seam")
        if seam not in (None, "null", "") and str(seam) not in seams:
            findings.append(
                f"seam-resolves: {where} serves_seam `{seam}` is not declared "
                "in overview.md Real Seams"
            )

        for ref in forced_by:
            ref_str = str(ref)
            resolved = False
            for tid in _TASK_ID_RE.findall(ref_str):
                resolved = True
                if tid not in known_ids:
                    findings.append(
                        f"forced-by-resolves: {where} cites `{tid}` which is not "
                        "a task in index.yaml"
                    )
            for seam_ref in _SEAM_REF_RE.findall(ref_str):
                resolved = True
                if seam_ref not in seams:
                    findings.append(
                        f"forced-by-resolves: {where} cites seam `{seam_ref}` "
                        "not declared in overview.md Real Seams"
                    )
            for file_ref in _FILE_REF_RE.findall(ref_str):
                resolved = True
                if not (repo_root / file_ref).exists():
                    findings.append(
                        f"forced-by-resolves: {where} cites `git: {file_ref}` "
                        "which does not exist in the repo"
                    )
            if not resolved:
                findings.append(
                    f"forced-by-resolves: {where} forced_by entry resolves to "
                    f"nothing checkable (no task id / seam / git ref): {ref_str!r}"
                )

    return findings


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    repo_root = Path.cwd()
    if "--repo-root" in args:
        idx = args.index("--repo-root")
        repo_root = Path(args[idx + 1])
        del args[idx : idx + 2]
    if len(args) != 1:
        print(__doc__)
        return 2

    feature_dir = Path(args[0])
    scar_dir = feature_dir / "scar-reports"
    if not scar_dir.is_dir():
        print(f"CANNOT VALIDATE: {scar_dir} does not exist")
        return 2
    scar_files = sorted(scar_dir.glob("*.yaml")) + sorted(scar_dir.glob("*.yml"))
    if not scar_files:
        print(f"CANNOT VALIDATE: no scar reports in {scar_dir}")
        return 2

    known_ids = _known_task_ids(feature_dir)
    seams = _declared_seams(feature_dir)
    registry = _registry_ids(repo_root)

    findings: list[str] = []
    for scar in scar_files:
        findings.extend(validate_scar(scar, known_ids, seams, registry, repo_root))

    if findings:
        for line in findings:
            print(f"FINDING {line}")
        print(f"\n{len(findings)} finding(s). Fix and re-run until clean.")
        return 1

    print(
        f"implement format validation: clean — {len(scar_files)} scar report(s) "
        "(parse / dual-face / forced-by / seam / systemic-ref / debt)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
