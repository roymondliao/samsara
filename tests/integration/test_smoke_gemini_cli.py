"""
Smoke test — Gemini CLI structural verification.

These tests are skip-safe when Gemini CLI is absent and use isolated temp
directories only. They never write to real ~/.gemini.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine

FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"


def _is_gemini_installed() -> bool:
    """Return True if Gemini CLI appears available."""
    try:
        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError, OSError, subprocess.TimeoutExpired:
        return False


class TestGeminiSmokeDetection:
    def test_detection_returns_bool_not_raises(self) -> None:
        result = _is_gemini_installed()
        assert isinstance(result, bool)

    def test_nonexistent_binary_exception_shape_is_handled(self) -> None:
        try:
            subprocess.run(
                ["__nonexistent_binary_samsara_gemini_test__", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except FileNotFoundError, OSError:
            pass


@pytest.fixture(scope="module")
def smoke_output_dir() -> Path:
    """Convert Gemini output into an isolated temp directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="samsara-gemini-smoke-"))
    output_dir = temp_dir / "gemini_output"
    try:
        engine = ConversionEngine("gemini-cli")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        yield output_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@pytest.mark.integration
class TestGeminiNativeStructure:
    def test_gemini_directory_exists(self, smoke_output_dir: Path) -> None:
        assert (smoke_output_dir / ".gemini").is_dir()

    def test_settings_json_exists_and_has_session_start(
        self, smoke_output_dir: Path
    ) -> None:
        settings_path = smoke_output_dir / ".gemini" / "settings.json"
        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["hooks"]["SessionStart"]

    def test_skills_use_gemini_path(self, smoke_output_dir: Path) -> None:
        assert (smoke_output_dir / ".gemini" / "skills").is_dir()
        assert not (smoke_output_dir / ".agents" / "skills").exists()

    def test_agents_are_markdown(self, smoke_output_dir: Path) -> None:
        agents_dir = smoke_output_dir / ".gemini" / "agents"
        assert agents_dir.is_dir()
        assert list(agents_dir.glob("*.md"))
        assert not list(agents_dir.glob("*.toml"))

    def test_hook_script_exists_and_is_executable(self, smoke_output_dir: Path) -> None:
        script = smoke_output_dir / ".gemini" / "hooks" / "samsara-session-start.sh"
        assert script.exists()
        assert os.access(script, os.X_OK)

    def test_hook_script_outputs_json(self, smoke_output_dir: Path) -> None:
        script = smoke_output_dir / ".gemini" / "hooks" / "samsara-session-start.sh"
        result = subprocess.run(
            ["bash", str(script)],
            input=json.dumps({"hookEventName": "SessionStart"}),
            capture_output=True,
            text=True,
            cwd=smoke_output_dir,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["hookSpecificOutput"]["additionalContext"]


@pytest.mark.integration
@pytest.mark.requires_gemini
class TestGeminiLiveCli:
    def test_live_gemini_cli_presence_or_skip(self) -> None:
        if not _is_gemini_installed():
            pytest.skip("Gemini CLI is not installed; live discovery smoke skipped.")

        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        assert result.returncode == 0

    def test_live_gemini_cli_discovers_project_skills(
        self, smoke_output_dir: Path, tmp_path: Path
    ) -> None:
        if not _is_gemini_installed():
            pytest.skip("Gemini CLI is not installed; live discovery smoke skipped.")

        env = os.environ.copy()
        env["GEMINI_CLI_HOME"] = str(tmp_path / "gemini-home")
        env["GEMINI_CLI_TRUST_WORKSPACE"] = "true"
        result = subprocess.run(
            ["gemini", "skills", "list", "--all"],
            capture_output=True,
            text=True,
            cwd=smoke_output_dir,
            env=env,
            timeout=20,
            check=False,
        )
        output = result.stdout + result.stderr

        assert result.returncode == 0
        assert "implement [Enabled]" in output
        assert ".gemini/skills/samsara-implement/SKILL.md" in output
        assert "untrusted" not in output.lower()
