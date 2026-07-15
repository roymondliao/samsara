#!/usr/bin/env python3
"""Validate and append the Auto Gatekeeper's decision log.

Judgment quality remains with the auto-gatekeeper and later audit. This script
checks only parseable shape, stable identity, append order, decision/action
consistency, gap/supersede rules, and mechanically resolvable evidence refs.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in installed projects
    print("CANNOT VALIDATE: PyYAML is not available")
    raise SystemExit(2)


_HEADING_RE = re.compile(
    r"^## (?P<decision_id>decision-(?P<number>\d+)) — (?P<gate_id>[a-z0-9.-]+)$",
    re.MULTILINE,
)
_BLOCK_RE = re.compile(r"\A\s*```yaml\s*\n(?P<yaml>.*?)\n```\s*\Z", re.DOTALL)
_DECISIONS = {"proceed", "revise", "reject", "accept_gap"}
_ACTORS = {"auto-gatekeeper", "human"}
_STAGES = {
    "research",
    "codebase-map",
    "pre-thinking",
    "planning",
    "implementation",
    "iteration",
    "validation",
}
_UNCERTAINTY = {"low", "medium", "high"}
_ACTION_TYPES = {"continue", "revise_and_rerun", "stop"}
_REQUIRED = {
    "schema_version",
    "decision_id",
    "timestamp",
    "decided_by",
    "stage",
    "gate_id",
    "workflow_prompt",
    "answer",
    "decision",
    "reason",
    "evidence_refs",
    "uncertainty",
    "next_action",
    "gap",
    "supersedes",
}
_GAP_FIELDS = {"summary", "durable_ref", "owner", "recheck_when"}

_GATE_RULES: tuple[tuple[re.Pattern[str], str, set[str]], ...] = (
    (
        re.compile(
            r"research\.(problem-source|do-not-solve|damage-recipient|done-state|transition)"
        ),
        "research",
        _DECISIONS,
    ),
    (
        re.compile(r"codebase-map\.(update-strategy|review)"),
        "codebase-map",
        _DECISIONS,
    ),
    (
        re.compile(r"pre-thinking\.step5\.[a-z0-9-]+\.[a-z0-9-]+"),
        "pre-thinking",
        _DECISIONS,
    ),
    (
        re.compile(r"pre-thinking\.(evaluator|commitment)"),
        "pre-thinking",
        _DECISIONS,
    ),
    (re.compile(r"planning\.transition"), "planning", _DECISIONS),
    (
        re.compile(r"implementation\.strategy"),
        "implementation",
        {"proceed", "revise", "reject"},
    ),
    (
        re.compile(r"implementation\.review-arbitration\.[a-z0-9-]+\.[a-z0-9-]+"),
        "implementation",
        _DECISIONS,
    ),
    (
        re.compile(r"iteration\.entry-unknown"),
        "iteration",
        {"revise", "reject"},
    ),
    (
        re.compile(r"iteration\.(disposition|blocked-fix)\.sc-\d+"),
        "iteration",
        {"proceed", "revise", "reject"},
    ),
    (
        re.compile(r"iteration\.round\.\d+"),
        "iteration",
        {"proceed", "reject"},
    ),
    (
        re.compile(
            r"validation\.(empty-diff|base-branch|security-capability|security-result|security-risk|delivery)"
        ),
        "validation",
        {"proceed", "revise", "reject"},
    ),
)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sections(text: str) -> list[tuple[re.Match[str], str]]:
    matches = list(_HEADING_RE.finditer(text))
    return [
        (
            match,
            text[
                match.end() : matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            ],
        )
        for index, match in enumerate(matches)
    ]


def _parse_entries(text: str, findings: list[str]) -> list[dict[str, Any]]:
    sections = _sections(text)
    if not sections:
        findings.append("shape: no `## decision-NNN — <gate-id>` entries found")
        return []

    entries: list[dict[str, Any]] = []
    for match, body in sections:
        decision_id = match.group("decision_id")
        block = _BLOCK_RE.fullmatch(body)
        if block is None:
            findings.append(
                f"shape: `{decision_id}` requires exactly one fenced YAML block"
            )
            continue
        try:
            parsed = yaml.safe_load(block.group("yaml"))
        except yaml.YAMLError as exc:
            findings.append(f"yaml: `{decision_id}` cannot parse: {exc}")
            continue
        if not isinstance(parsed, dict):
            findings.append(f"shape: `{decision_id}` YAML must be a mapping")
            continue
        parsed["__heading_id"] = decision_id
        parsed["__heading_gate"] = match.group("gate_id")
        entries.append(parsed)
    return entries


def _gate_rule(gate_id: str) -> tuple[str, set[str]] | None:
    for pattern, stage, decisions in _GATE_RULES:
        if pattern.fullmatch(gate_id):
            return stage, decisions
    return None


def _check_evidence_ref(
    ref: str, feature_dir: Path, repo_root: Path, where: str, findings: list[str]
) -> None:
    if ref.startswith(("git:", "test:", "command:")):
        if not ref.split(":", 1)[1].strip():
            findings.append(f"evidence-ref: `{where}` has an empty `{ref}`")
        return

    path_text, separator, anchor = ref.partition("#")
    candidates = (repo_root / path_text, feature_dir / path_text)
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        findings.append(f"evidence-ref: `{where}` cannot resolve `{ref}`")
        return
    if separator and anchor.lower() not in path.read_text(encoding="utf-8").lower():
        findings.append(f"evidence-ref: `{where}` cannot resolve anchor in `{ref}`")


def _validate_entries(
    entries: list[dict[str, Any]], feature_dir: Path, repo_root: Path
) -> list[str]:
    findings: list[str] = []
    seen: dict[str, dict[str, Any]] = {}
    latest_by_gate: dict[str, str] = {}

    for index, entry in enumerate(entries, start=1):
        heading_id = entry.pop("__heading_id")
        heading_gate = entry.pop("__heading_gate")
        where = heading_id
        missing = sorted(_REQUIRED - set(entry))
        extra = sorted(set(entry) - _REQUIRED)
        if missing:
            findings.append(f"shape: `{where}` missing fields: {missing}")
        if extra:
            findings.append(f"shape: `{where}` has unknown fields: {extra}")

        decision_id = entry.get("decision_id")
        expected_id = f"decision-{index:03d}"
        if decision_id != heading_id or decision_id != expected_id:
            findings.append(
                f"decision-id: entry {index} must be `{expected_id}` and match its heading"
            )
        if isinstance(decision_id, str) and decision_id in seen:
            findings.append(f"decision-id: duplicate `{decision_id}`")

        if entry.get("schema_version") != 1:
            findings.append(f"schema-version: `{where}` must use `1`")
        if entry.get("decided_by") not in _ACTORS:
            findings.append(f"actor: `{where}` has invalid `decided_by`")
        if entry.get("stage") not in _STAGES:
            findings.append(f"stage: `{where}` has invalid stage")
        for field in ("timestamp", "workflow_prompt", "answer"):
            if not _nonempty_string(entry.get(field)):
                findings.append(f"shape: `{where}.{field}` must be non-empty")

        gate_id = entry.get("gate_id")
        rule = _gate_rule(gate_id) if isinstance(gate_id, str) else None
        if gate_id != heading_gate:
            findings.append(f"gate-id: `{where}` does not match its heading")
        allowed: set[str]
        if rule is None:
            findings.append(f"gate-id: `{where}` has unknown gate `{gate_id}`")
            allowed = set()
        else:
            expected_stage, allowed = rule
            if entry.get("stage") != expected_stage:
                findings.append(
                    f"gate-id: `{where}` gate `{gate_id}` belongs to `{expected_stage}`"
                )

        decision = entry.get("decision")
        if decision not in _DECISIONS or decision not in allowed:
            findings.append(
                f"decision: `{where}` value `{decision}` is not allowed for `{gate_id}`"
            )

        reason = entry.get("reason")
        if (
            not isinstance(reason, list)
            or not 1 <= len(reason) <= 3
            or any(not _nonempty_string(item) for item in reason)
        ):
            findings.append(f"reason: `{where}` requires one to three concise bullets")

        evidence_refs = entry.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            findings.append(f"evidence-ref: `{where}` requires non-empty evidence refs")
        else:
            for ref in evidence_refs:
                if not _nonempty_string(ref):
                    findings.append(f"evidence-ref: `{where}` contains an empty ref")
                else:
                    _check_evidence_ref(ref, feature_dir, repo_root, where, findings)

        uncertainty = entry.get("uncertainty")
        if not isinstance(uncertainty, dict) or set(uncertainty) != {"level", "notes"}:
            findings.append(f"uncertainty: `{where}` requires level and notes")
        else:
            if uncertainty.get("level") not in _UNCERTAINTY:
                findings.append(f"uncertainty: `{where}` has invalid level")
            if not _nonempty_string(uncertainty.get("notes")):
                findings.append(f"uncertainty: `{where}.notes` must be non-empty")

        next_action = entry.get("next_action")
        if not isinstance(next_action, dict) or set(next_action) != {"type", "target"}:
            findings.append(f"next-action: `{where}` requires type and target")
            action_type = None
        else:
            action_type = next_action.get("type")
            if action_type not in _ACTION_TYPES:
                findings.append(f"next-action: `{where}` has invalid type")
            if not _nonempty_string(next_action.get("target")):
                findings.append(f"next-action: `{where}.target` must be non-empty")

        expected_actions = {
            "proceed": "continue",
            "accept_gap": "continue",
            "revise": "revise_and_rerun",
            "reject": "stop",
        }
        expected_action = (
            expected_actions.get(decision) if isinstance(decision, str) else None
        )
        if expected_action is not None and action_type != expected_action:
            findings.append(
                f"decision-action: `{where}` `{decision}` requires `{expected_action}`"
            )

        gap = entry.get("gap")
        if decision == "accept_gap":
            if not isinstance(gap, dict) or set(gap) != _GAP_FIELDS:
                findings.append(
                    f"accept-gap: `{where}` requires summary, durable_ref, owner, and recheck_when"
                )
            elif any(not _nonempty_string(gap.get(field)) for field in _GAP_FIELDS):
                findings.append(f"accept-gap: `{where}` gap fields must be non-empty")
        elif gap is not None:
            findings.append(
                f"accept-gap: `{where}` must use `gap: null` for `{decision}`"
            )

        supersedes = entry.get("supersedes")
        if supersedes is not None:
            prior = seen.get(supersedes) if isinstance(supersedes, str) else None
            if prior is None:
                findings.append(f"supersedes: `{where}` must name an earlier decision")
            elif prior.get("gate_id") != gate_id:
                findings.append(f"supersedes: `{where}` must supersede the same gate")
        prior_for_gate = (
            latest_by_gate.get(gate_id) if isinstance(gate_id, str) else None
        )
        if prior_for_gate is not None and supersedes != prior_for_gate:
            findings.append(
                f"supersedes: `{where}` repeats `{gate_id}` without superseding `{prior_for_gate}`"
            )

        if isinstance(decision_id, str):
            seen[decision_id] = entry
        if isinstance(gate_id, str) and isinstance(decision_id, str):
            latest_by_gate[gate_id] = decision_id

    return findings


def _committed_prefix(
    feature_dir: Path, repo_root: Path, current: str, findings: list[str]
) -> None:
    try:
        relative = (
            (feature_dir / "auto-decisions.md")
            .resolve()
            .relative_to(repo_root.resolve())
        )
    except ValueError:
        return
    result = subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and not current.startswith(result.stdout):
        findings.append(
            "append-only: current log does not preserve the committed prefix"
        )


def _validate_text(
    text: str, feature_dir: Path, repo_root: Path
) -> tuple[list[str], int]:
    parse_findings: list[str] = []
    entries = _parse_entries(text, parse_findings)
    findings = parse_findings + _validate_entries(entries, feature_dir, repo_root)
    return findings, len(entries)


def _append_candidate(
    feature_dir: Path, repo_root: Path, candidate_path: Path
) -> tuple[int, int]:
    """Validate current history plus one candidate, then replace the log atomically."""
    if not candidate_path.is_file():
        print(f"CANNOT VALIDATE: candidate not found: {candidate_path}")
        return 2, 0

    lock_path = feature_dir / ".auto-decisions.lock"
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        print(f"CANNOT VALIDATE: append lock already exists: {lock_path}")
        return 2, 0

    temp_path: Path | None = None
    try:
        os.write(lock_fd, f"pid={os.getpid()}\n".encode())
        os.close(lock_fd)

        log_path = feature_dir / "auto-decisions.md"
        current = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
        candidate = candidate_path.read_text(encoding="utf-8")
        candidate_sections = _sections(candidate)
        if (
            len(candidate_sections) != 1
            or candidate[: candidate_sections[0][0].start()].strip()
        ):
            print("FINDING: candidate must contain exactly one decision entry")
            return 1, 0

        separator = "\n\n" if current.strip() else ""
        combined = current.rstrip() + separator + candidate.strip() + "\n"
        findings, entry_count = _validate_text(combined, feature_dir, repo_root)
        _committed_prefix(feature_dir, repo_root, current, findings)
        if findings:
            for finding in findings:
                print(f"FINDING: {finding}")
            return 1, entry_count

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=feature_dir,
            prefix=".auto-decisions.",
            delete=False,
        ) as temp_file:
            temp_file.write(combined)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        os.replace(temp_path, log_path)
        temp_path = None
        print(f"APPENDED: decision-{entry_count:03d}")
        return 0, entry_count
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        lock_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_dir", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--append-candidate", type=Path)
    args = parser.parse_args()

    feature_dir = args.feature_dir.resolve()
    repo_root = args.repo_root.resolve()
    log_path = feature_dir / "auto-decisions.md"
    if not feature_dir.is_dir():
        print(f"CANNOT VALIDATE: feature directory not found: {feature_dir}")
        return 2

    if args.append_candidate:
        result, _ = _append_candidate(feature_dir, repo_root, args.append_candidate)
        return result
    if not log_path.is_file():
        print(f"CANNOT VALIDATE: decision log not found: {log_path}")
        return 2

    current = log_path.read_text(encoding="utf-8")
    findings, entry_count = _validate_text(current, feature_dir, repo_root)
    _committed_prefix(feature_dir, repo_root, current, findings)

    if findings:
        for finding in findings:
            print(f"FINDING: {finding}")
        return 1

    print(
        f"CLEAN: {entry_count} auto decision entr{'y' if entry_count == 1 else 'ies'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
