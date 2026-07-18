"""Behavior tests for the SHA-only Codebase Map freshness hook."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "hooks" / "check-codebase-map"


def git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(project: Path) -> str:
    git(project, "init")
    git(project, "config", "user.email", "tests@example.invalid")
    git(project, "config", "user.name", "Samsara Tests")
    (project / ".gitignore").write_text(".samsara/*\n", encoding="utf-8")
    (project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(project, "add", ".gitignore", "app.py")
    git(project, "commit", "-m", "initial")
    return git(project, "rev-parse", "HEAD")


def write_map(project: Path, commit: str, schema_version: int = 2) -> None:
    output = project / ".samsara"
    output.mkdir(exist_ok=True)
    (output / "codebase-map.yaml").write_text(
        f"schema_version: {schema_version}\nsource:\n  commit: {commit}\n",
        encoding="utf-8",
    )


def run_hook(
    project: Path, *, include_project: bool = True
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if include_project:
        env["CLAUDE_PROJECT_DIR"] = str(project)
    else:
        env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run(
        [str(HOOK)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def context(result: subprocess.CompletedProcess[str]) -> str:
    payload = json.loads(result.stdout)
    return payload["hookSpecificOutput"]["additionalContext"]


def test_no_project_context_is_silent(tmp_path: Path) -> None:
    result = run_hook(tmp_path, include_project=False)

    assert result.returncode == 0
    assert result.stdout == ""


def test_missing_map_is_visible(tmp_path: Path) -> None:
    init_repo(tmp_path)

    result = run_hook(tmp_path)

    assert result.returncode == 0
    assert "MISSING" in context(result)


def test_current_map_is_silent(tmp_path: Path) -> None:
    head = init_repo(tmp_path)
    write_map(tmp_path, head)

    result = run_hook(tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_uncommitted_changes_do_not_change_snapshot_state(tmp_path: Path) -> None:
    head = init_repo(tmp_path)
    write_map(tmp_path, head)
    (tmp_path / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("NEW = True\n", encoding="utf-8")

    result = run_hook(tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""


def test_any_new_commit_requires_update_without_counting_files(tmp_path: Path) -> None:
    mapped = init_repo(tmp_path)
    write_map(tmp_path, mapped)
    (tmp_path / "README.md").write_text("small committed doc edit\n", encoding="utf-8")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-m", "docs")
    head = git(tmp_path, "rev-parse", "HEAD")

    result = run_hook(tmp_path)
    message = context(result)

    assert "UPDATE_REQUIRED" in message
    assert mapped in message
    assert head in message
    assert "changed file" not in message.lower()
    assert "threshold" not in message.lower()


def test_non_git_project_is_unknown(tmp_path: Path) -> None:
    write_map(tmp_path, "a" * 40)

    result = run_hook(tmp_path)

    assert "UNKNOWN" in context(result)


def test_legacy_schema_is_unknown_not_current(tmp_path: Path) -> None:
    head = init_repo(tmp_path)
    write_map(tmp_path, head, schema_version=1)

    result = run_hook(tmp_path)

    assert "UNKNOWN" in context(result)


def test_unresolvable_source_commit_is_unknown(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_map(tmp_path, "f" * 40)

    result = run_hook(tmp_path)

    assert "UNKNOWN" in context(result)


def test_uncommitted_ignore_rule_change_does_not_change_snapshot_state(
    tmp_path: Path,
) -> None:
    head = init_repo(tmp_path)
    write_map(tmp_path, head)
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")

    result = run_hook(tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""
