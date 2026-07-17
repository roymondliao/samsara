"""Deterministic format checks for side-route artifacts."""

from importlib import util
from pathlib import Path
from types import ModuleType

import yaml


ROOT = Path(__file__).resolve().parents[2]
FAST_VALIDATOR = ROOT / "skills" / "fast-track" / "scripts" / "validate_format.py"
DEBUG_VALIDATOR = ROOT / "skills" / "debugging" / "scripts" / "validate_format.py"


def _load(path: Path, name: str) -> ModuleType:
    assert path.exists(), f"missing validator: {path}"
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _valid_fast_track() -> dict[str, object]:
    return {
        "type": "fast_track",
        "status": "completed",
        "description": "Bounded change",
        "source_refs": [],
        "entry": {
            "authority": "user confirmation",
            "risk_evidence": [
                {"claim": "No shared state", "evidence_ref": "src/a.py:10"}
            ],
            "affected_surfaces": [{"path": "src/a.py", "role": "leaf helper"}],
            "structural_impact": "none",
            "unknowns": [],
        },
        "acceptance": ["Behavior is observable"],
        "death_evidence": {
            "clause": "If the result is stale, the change failed",
            "pre_change": {"command": "pytest test_a.py", "result": "failed"},
        },
        "verification": [{"command": "pytest test_a.py", "result": "passed"}],
        "review": {
            "domains": ["code"],
            "reference_refs": ["references/code-review.md"],
            "evidence_refs": ["src/a.py:10"],
            "findings": [],
            "unknowns": [],
        },
        "files_changed": ["src/a.py", "test_a.py"],
        "escalation": {"route": None, "reason": None},
    }


def _valid_bug_report() -> dict[str, object]:
    return {
        "schema_version": 1,
        "bug": {
            "title": "Observed failure",
            "reported_by": "user",
            "observable_result": "request returns stale data",
            "evidence_refs": ["logs/request-1.txt"],
        },
        "failure": {"level": 3, "rationale": "success without side effect"},
        "impact": {
            "scope": "unknown",
            "duration": "unknown",
            "detection_delay": "unknown",
            "evidence_refs": [],
        },
        "containment": {
            "required": "unknown",
            "action": None,
            "authorization": "not_requested",
        },
        "unknowns": ["affected request count"],
    }


def _valid_root_cause() -> dict[str, object]:
    return {
        "schema_version": 1,
        "bug_report_ref": "bug-report.yaml",
        "root_cause": {
            "status": "confirmed",
            "hypothesis": "fallback hides the write failure",
            "evidence_refs": ["src/a.py:10"],
            "refuting_evidence": [],
            "why_hidden": "fallback reports success",
        },
        "reproduction": {
            "status": "reproduced",
            "evidence_ref": "logs/repro.txt",
        },
        "rot_path": [
            {
                "from": "request",
                "to": "fallback",
                "failed_guard": "write result unchecked",
                "evidence_ref": "src/a.py:10",
            }
        ],
        "death_test": {
            "status": "specified",
            "evidence_ref": None,
            "specification": "fail when write result is false",
        },
        "repair": {
            "authorized": True,
            "scope": "bounded",
            "route": "fast_track",
            "rationale": "one leaf boundary",
        },
    }


def test_fast_track_validator_accepts_valid_record(tmp_path: Path) -> None:
    module = _load(FAST_VALIDATOR, "fast_track_validator")
    path = tmp_path / "fast-track.yaml"
    _write(path, _valid_fast_track())

    assert module.validate_fast_track(path) == []


def test_fast_track_validator_rejects_retired_scar_fields(tmp_path: Path) -> None:
    module = _load(FAST_VALIDATOR, "fast_track_validator_retired")
    value = _valid_fast_track()
    value["scar_tag"] = "none"
    path = tmp_path / "fast-track.yaml"
    _write(path, value)

    assert any("retired" in error for error in module.validate_fast_track(path))


def test_debugging_validator_accepts_valid_diagnosis(tmp_path: Path) -> None:
    module = _load(DEBUG_VALIDATOR, "debugging_validator")
    _write(tmp_path / "bug-report.yaml", _valid_bug_report())
    _write(tmp_path / "root-cause.yaml", _valid_root_cause())

    assert module.validate_debugging(tmp_path) == []


def test_debugging_validator_rejects_impossible_fast_track_route(
    tmp_path: Path,
) -> None:
    module = _load(DEBUG_VALIDATOR, "debugging_validator_route")
    cause = _valid_root_cause()
    cause["root_cause"]["status"] = "unknown"  # type: ignore[index]
    _write(tmp_path / "bug-report.yaml", _valid_bug_report())
    _write(tmp_path / "root-cause.yaml", cause)

    assert any("fast_track" in error for error in module.validate_debugging(tmp_path))
