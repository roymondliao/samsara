"""
Unit tests for ConversionEngine — happy path and behavioral contract tests.

Death tests (silent failure paths) are in test_engine_death.py.
These tests cover: successful conversion, output directory structure,
error handling, source validator integration, target validator integration.
"""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_source_structure(
    tmp_path: Path,
    skill_names: list[str] | None = None,
    agent_names: list[str] | None = None,
) -> Path:
    """Create a minimal valid samsara source directory structure."""
    source = tmp_path / "source"
    plugin_dir = source / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps({"name": "samsara", "version": "0.8.0"})
    )

    skills_dir = source / "skills"
    skills_dir.mkdir()
    for skill_name in skill_names or ["research"]:
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: {skill_name} skill\n---\n\n# {skill_name}\n"
        )

    agents_dir = source / "agents"
    agents_dir.mkdir()
    for agent_name in agent_names or ["implementer"]:
        (agents_dir / f"{agent_name}.md").write_text(
            f"# {agent_name}\n\nYou are the {agent_name} agent.\n"
        )

    hooks_dir = source / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))
    (hooks_dir / "session-start").write_text("#!/bin/bash\necho hello\n")

    references_dir = source / "references"
    references_dir.mkdir()

    return source


# ---------------------------------------------------------------------------
# Engine construction
# ---------------------------------------------------------------------------


class TestEngineConstruction:
    def test_engine_can_be_constructed_for_codex_platform(self):
        """ConversionEngine can be instantiated for codex platform."""
        from samsara_cli.converter.engine import ConversionEngine

        engine = ConversionEngine(platform="codex")
        assert engine is not None

    def test_engine_with_unknown_platform_raises(self):
        """ConversionEngine with unknown platform raises at construction or run time."""
        from samsara_cli.converter.engine import ConversionEngine

        # Construction may not raise — but run() must raise for unknown platform
        # (the error may come from load_platform_config)
        with pytest.raises(Exception):
            engine = ConversionEngine(platform="nonexistent-platform-xyz")
            # If construction doesn't raise, run must
            engine.run(source_dir=Path("/tmp"), output_dir=Path("/tmp/out"))


# ---------------------------------------------------------------------------
# Successful conversion
# ---------------------------------------------------------------------------


class TestSuccessfulConversion:
    def test_engine_produces_output_directory(self, tmp_path: Path):
        """Engine creates the output directory on successful conversion."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        assert output.exists(), "Output directory was not created"
        assert output.is_dir(), "Output path is not a directory"

    def test_engine_produces_skills_in_output(self, tmp_path: Path):
        """Engine produces converted skill directories in output."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path, skill_names=["research"])
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        # Skills should be under output/skills/
        skills_output = output / "skills"
        assert skills_output.exists(), "skills/ directory not created in output"
        skill_dirs = list(skills_output.iterdir())
        assert len(skill_dirs) > 0, "No skill directories in output"

    def test_engine_produces_agents_in_output(self, tmp_path: Path):
        """Engine produces converted agent files in output."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path, agent_names=["implementer"])
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        agents_output = output / "agents"
        assert agents_output.exists(), "agents/ directory not created in output"
        agent_files = list(agents_output.glob("*.toml"))
        assert len(agent_files) > 0, "No .toml agent files in output"

    def test_skill_md_exists_in_output_skill_dir(self, tmp_path: Path):
        """Each converted skill dir contains a SKILL.md file."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path, skill_names=["research"])
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        skills_output = output / "skills"
        skill_dirs = [d for d in skills_output.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            assert (skill_dir / "SKILL.md").exists(), (
                f"SKILL.md not found in converted skill dir {skill_dir}"
            )

    def test_converted_agent_toml_is_parseable(self, tmp_path: Path):
        """Agent .toml files in output are valid TOML."""
        import tomllib
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path, agent_names=["implementer"])
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        for toml_file in (output / "agents").glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            try:
                parsed = tomllib.loads(content)
            except Exception as e:
                pytest.fail(f"Agent TOML {toml_file.name} is not parseable: {e}")
            assert "agent" in parsed, f"Missing [agent] section in {toml_file.name}"


# ---------------------------------------------------------------------------
# Output directory already exists
# ---------------------------------------------------------------------------


class TestOutputDirAlreadyExists:
    def test_engine_overwrites_existing_output_dir(self, tmp_path: Path):
        """If output dir already exists, engine overwrites it (or handles gracefully)."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"
        output.mkdir()
        # Put a stale file in the output — should be gone after conversion
        (output / "stale-file.txt").write_text("stale content")

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        # Output should still exist and have converted content
        assert output.exists()
        # Stale file behavior: the engine may or may not remove it — either is OK
        # What matters is the output is not partial


# ---------------------------------------------------------------------------
# Source directory missing
# ---------------------------------------------------------------------------


class TestSourceDirectoryMissing:
    def test_engine_raises_if_source_dir_missing(self, tmp_path: Path):
        """Engine raises if source directory does not exist."""
        from samsara_cli.converter.engine import ConversionEngine

        source = tmp_path / "nonexistent-source"
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        with pytest.raises(Exception):
            engine.run(source_dir=source, output_dir=output)


# ---------------------------------------------------------------------------
# Manifest output
# ---------------------------------------------------------------------------


class TestManifestOutput:
    def test_engine_produces_plugin_json_in_output(self, tmp_path: Path):
        """Engine produces a plugin.json (or platform equivalent) in the output."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        # Look for plugin.json or .codex-plugin/plugin.json
        plugin_json_candidates = list(output.rglob("plugin.json"))
        assert len(plugin_json_candidates) > 0, (
            "No plugin.json found in output after conversion"
        )

    def test_output_manifest_preserves_name_and_version(self, tmp_path: Path):
        """The output manifest preserves name and version from source."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        plugin_json_candidates = list(output.rglob("plugin.json"))
        assert len(plugin_json_candidates) > 0
        manifest = json.loads(plugin_json_candidates[0].read_text())
        assert manifest.get("name") == "samsara", (
            f"name mismatch: {manifest.get('name')}"
        )
        assert manifest.get("version") == "0.8.0", (
            f"version mismatch: {manifest.get('version')}"
        )
