"""Mechanical validator tests for Codebase Map schema v2."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT / "skills" / "codebase-map" / "scripts" / "validate_codebase_map.py"
)


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "codebase_map_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def create_repo(tmp_path: Path, *, ignore_map: bool = True) -> tuple[Path, Path, str]:
    project = tmp_path / "project"
    project.mkdir()
    git(project, "init")
    git(project, "config", "user.email", "tests@example.invalid")
    git(project, "config", "user.name", "Samsara Tests")
    ignore_content = ".samsara/*\n" if ignore_map else "other-output/\n"
    (project / ".gitignore").write_text(ignore_content, encoding="utf-8")
    (project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(project, "add", ".gitignore", "app.py")
    git(project, "commit", "-m", "initial")
    commit = git(project, "rev-parse", "HEAD")

    snapshot = tmp_path / "snapshot"
    git(project, "worktree", "add", "--detach", str(snapshot), commit)
    return project, snapshot, commit


def write_candidate(candidate: Path, commit: str) -> None:
    modules = candidate / "modules"
    modules.mkdir(parents=True)
    root = {
        "schema_version": 2,
        "project": "example",
        "source": {"commit": commit},
        "generated_at": "2026-07-18T12:00:00+08:00",
        "generated_by": "samsara:codebase-map",
        "scan_scope": {
            "roots": ["."],
            "exclusions": [],
            "coverage_gaps": [],
        },
        "summary": {
            "purpose": "Exercise the validator",
            "capabilities": ["example"],
            "silent_failure_surface": "unknown",
            "rot_hotspots": [],
        },
        "modules": [
            {
                "id": "app",
                "name": "App",
                "path": ".",
                "responsibility": "Provide the example value",
                "provides": ["example"],
                "death_impact": {
                    "severity": "low",
                    "effect": "The example value becomes unavailable",
                    "evidence_refs": ["app.py#VALUE"],
                },
                "detail_ref": (f".samsara/codebase-map/{commit}/modules/app.yaml"),
            }
        ],
        "global_nodes": [],
        "cross_module_relationships": [],
        "business_flows": [],
        "infrastructure": {
            "build": {
                "tool": "unknown",
                "test_command": "unknown",
                "build_command": "unknown",
                "ci_config": "unknown",
            },
            "config_sources": [],
            "data_flow": {
                "entry_points": [],
                "storage": [],
                "external_services": [],
            },
        },
    }
    module = {
        "schema_version": 2,
        "id": "app",
        "interfaces": [],
        "nodes": [
            {
                "id": "app.py#VALUE",
                "kind": "config",
                "path": "app.py",
                "responsibility": "Provide the value",
                "provides": ["VALUE"],
                "evidence_refs": ["app.py#VALUE"],
            }
        ],
        "internal_relationships": [],
        "rot_risks": [],
        "hidden_coupling": [],
        "assumptions": [],
    }
    (candidate / "codebase-map.yaml").write_text(
        yaml.safe_dump(root, sort_keys=False),
        encoding="utf-8",
    )
    (modules / "app.yaml").write_text(
        yaml.safe_dump(module, sort_keys=False),
        encoding="utf-8",
    )


def validate(
    candidate: Path,
    project: Path,
    snapshot: Path,
    commit: str,
) -> list[str]:
    errors, _ = VALIDATOR.validate_candidate(
        candidate,
        project,
        snapshot,
        commit,
    )
    return errors


def test_valid_candidate_resolves_against_detached_snapshot(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)

    assert validate(candidate, project, snapshot, commit) == []


def test_dangling_relationship_is_rejected(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)
    root_file = candidate / "codebase-map.yaml"
    root = yaml.safe_load(root_file.read_text(encoding="utf-8"))
    root["cross_module_relationships"] = [
        {
            "from": "app.py#VALUE",
            "to": "missing#node",
            "type": "calls",
            "evidence_refs": ["app.py#VALUE"],
        }
    ]
    root_file.write_text(yaml.safe_dump(root, sort_keys=False), encoding="utf-8")

    errors = validate(candidate, project, snapshot, commit)

    assert any("dangling node id" in error for error in errors)


def test_working_tree_file_cannot_be_snapshot_evidence(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path)
    (project / "uncommitted.py").write_text("VALUE = 2\n", encoding="utf-8")
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)
    module_file = candidate / "modules" / "app.yaml"
    module = yaml.safe_load(module_file.read_text(encoding="utf-8"))
    module["nodes"][0]["path"] = "uncommitted.py"
    module["nodes"][0]["evidence_refs"] = ["uncommitted.py:1"]
    module_file.write_text(
        yaml.safe_dump(module, sort_keys=False),
        encoding="utf-8",
    )

    errors = validate(candidate, project, snapshot, commit)

    assert any("does not exist in snapshot" in error for error in errors)


def test_head_move_before_publish_is_rejected(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)
    (project / "next.py").write_text("NEXT = True\n", encoding="utf-8")
    git(project, "add", "next.py")
    git(project, "commit", "-m", "move head")

    errors = validate(candidate, project, snapshot, commit)

    assert any("changed during generation" in error for error in errors)


def test_non_detached_or_dirty_snapshot_is_rejected(tmp_path: Path) -> None:
    project, _, commit = create_repo(tmp_path)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)

    errors = validate(candidate, project, project, commit)

    assert any("expected a detached worktree" in error for error in errors)


def test_unignored_output_boundary_is_rejected(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path, ignore_map=False)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)

    errors = validate(candidate, project, snapshot, commit)

    assert any("output path must be ignored" in error for error in errors)


def test_publish_writes_generation_then_root_manifest(tmp_path: Path) -> None:
    project, snapshot, commit = create_repo(tmp_path)
    candidate = tmp_path / "candidate"
    write_candidate(candidate, commit)
    candidate_root = candidate / "codebase-map.yaml"
    root_data = yaml.safe_load(candidate_root.read_text(encoding="utf-8"))
    candidate_root.write_text(
        yaml.safe_dump(root_data, default_flow_style=True, sort_keys=False),
        encoding="utf-8",
    )
    errors = validate(candidate, project, snapshot, commit)
    assert errors == []

    VALIDATOR._publish_candidate(candidate, project, commit, None)

    published_root = project / ".samsara" / "codebase-map.yaml"
    published_text = published_root.read_text(encoding="utf-8")
    root = yaml.safe_load(published_text)
    module = project / ".samsara" / "codebase-map" / commit / "modules" / "app.yaml"
    assert root["source"]["commit"] == commit
    assert f"source:\n  commit: {commit}\n" in published_text
    assert module.is_file()
