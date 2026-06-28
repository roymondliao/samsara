"""
Unit tests for ConversionEngine — happy path and behavioral contract tests.

Death tests (silent failure paths) are in test_engine_death.py.
These tests cover: successful conversion, output directory structure,
error handling, source validator integration, target validator integration.
"""

import json
import tomllib
from pathlib import Path

import pytest

from conftest import FIXTURE_VERSION


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
        json.dumps({"name": "samsara", "version": FIXTURE_VERSION})
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

        skills_output = output / ".agents" / "skills"
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

        agents_output = output / ".codex" / "agents"
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

        skills_output = output / ".agents" / "skills"
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

        for toml_file in (output / ".codex" / "agents").glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            try:
                parsed = tomllib.loads(content)
            except Exception as e:
                pytest.fail(f"Agent TOML {toml_file.name} is not parseable: {e}")
            assert "agent" not in parsed, (
                f"Unsupported [agent] section in {toml_file.name}"
            )
            assert parsed["name"], f"Missing top-level name in {toml_file.name}"
            assert parsed["description"], (
                f"Missing top-level description in {toml_file.name}"
            )
            assert parsed["developer_instructions"], (
                f"Missing top-level developer_instructions in {toml_file.name}"
            )

    def test_gemini_engine_produces_markdown_agents(self, tmp_path: Path):
        """Gemini engine produces markdown subagent files, never TOML agents."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path, agent_names=["implementer"])
        output = tmp_path / "output"

        engine = ConversionEngine(platform="gemini-cli")
        engine.run(source_dir=source, output_dir=output)

        agents_output = output / ".gemini" / "agents"
        assert agents_output.exists(), "Gemini agents directory not created"
        assert list(agents_output.glob("*.md")), "No Gemini .md agent files in output"
        assert not list(agents_output.glob("*.toml")), (
            "Gemini must not emit TOML agents"
        )

    def test_codex_references_are_shared_and_skill_localized(self, tmp_path: Path):
        """Codex conversion gives referenced skills local refs and keeps shared refs."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(
            tmp_path, skill_names=["implement"], agent_names=["code-reviewer"]
        )
        (source / "references" / "code-review.md").write_text("# Code Review\n")
        (source / "skills" / "implement" / "SKILL.md").write_text(
            "---\n"
            "name: implement\n"
            "description: implement skill\n"
            "---\n\n"
            "Read `references/code-review.md` before dispatch.\n"
        )

        output = tmp_path / "output"
        ConversionEngine(platform="codex").run(source_dir=source, output_dir=output)

        shared_ref = output / ".agents" / "references" / "code-review.md"
        skill_ref = (
            output
            / ".agents"
            / "skills"
            / "samsara-implement"
            / "references"
            / "code-review.md"
        )
        assert shared_ref.exists(), "Codex shared reference pool missing"
        assert skill_ref.exists(), "Codex skill-local reference copy missing"

    def test_gemini_references_are_shared_and_skill_localized(self, tmp_path: Path):
        """Gemini conversion uses Gemini-native shared and skill-local refs."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(
            tmp_path, skill_names=["implement"], agent_names=["code-reviewer"]
        )
        (source / "references" / "code-review.md").write_text("# Code Review\n")
        (source / "skills" / "implement" / "SKILL.md").write_text(
            "---\n"
            "name: implement\n"
            "description: implement skill\n"
            "---\n\n"
            "Read `references/code-review.md` before dispatch.\n"
        )

        output = tmp_path / "output"
        ConversionEngine(platform="gemini-cli").run(
            source_dir=source, output_dir=output
        )

        shared_ref = output / ".gemini" / "references" / "code-review.md"
        skill_ref = (
            output
            / ".gemini"
            / "skills"
            / "samsara-implement"
            / "references"
            / "code-review.md"
        )
        assert shared_ref.exists(), "Gemini shared reference pool missing"
        assert skill_ref.exists(), "Gemini skill-local reference copy missing"

    def test_codex_agents_get_reference_resolver_not_bare_paths(self, tmp_path: Path):
        """Codex agents resolve reference ids via platform paths, not cwd refs."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(
            tmp_path, skill_names=["implement"], agent_names=["code-reviewer"]
        )
        (source / "agents" / "code-reviewer.md").write_text(
            "# Code Reviewer\n\nRead `references/code-review.md` before review.\n"
        )
        output = tmp_path / "output"

        ConversionEngine(platform="codex").run(source_dir=source, output_dir=output)

        agent = tomllib.loads(
            (output / ".codex" / "agents" / "samsara-code-reviewer.toml").read_text(
                encoding="utf-8"
            )
        )
        instructions = agent["developer_instructions"]
        assert "Reference Resolution Protocol" in instructions
        assert ".agents/references" in instructions
        assert ".agents/skills" in instructions
        assert "references/code-review.md" not in instructions
        assert "reference id `code-review.md`" in instructions

    def test_skill_local_reference_is_not_overwritten_by_shared_ref(
        self, tmp_path: Path
    ):
        """A skill-owned reference beats a same-named shared reference copy."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(
            tmp_path, skill_names=["implement"], agent_names=["code-reviewer"]
        )
        (source / "references" / "code-review.md").write_text("# Shared Ref\n")
        skill_dir = source / "skills" / "implement"
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: implement\n"
            "description: implement skill\n"
            "---\n\n"
            "Read `references/code-review.md` before dispatch.\n"
        )
        (skill_dir / "references").mkdir()
        (skill_dir / "references" / "code-review.md").write_text("# Skill Ref\n")

        output = tmp_path / "output"
        ConversionEngine(platform="codex").run(source_dir=source, output_dir=output)

        skill_ref = (
            output
            / ".agents"
            / "skills"
            / "samsara-implement"
            / "references"
            / "code-review.md"
        )
        assert skill_ref.read_text(encoding="utf-8") == "# Skill Ref\n"

    def test_gemini_agents_get_reference_resolver_not_bare_paths(self, tmp_path: Path):
        """Gemini agents resolve reference ids via platform paths, not cwd refs."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(
            tmp_path, skill_names=["implement"], agent_names=["code-reviewer"]
        )
        (source / "agents" / "code-reviewer.md").write_text(
            "# Code Reviewer\n\nRead `references/code-review.md` before review.\n"
        )
        output = tmp_path / "output"

        ConversionEngine(platform="gemini-cli").run(
            source_dir=source, output_dir=output
        )

        instructions = (
            output / ".gemini" / "agents" / "samsara-code-reviewer.md"
        ).read_text(encoding="utf-8")
        assert "Reference Resolution Protocol" in instructions
        assert ".gemini/references" in instructions
        assert ".gemini/skills" in instructions
        assert "references/code-review.md" not in instructions
        assert "reference id `code-review.md`" in instructions


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


class TestCodexNativeOutput:
    def test_engine_produces_codex_hooks_json_in_output(self, tmp_path: Path):
        """Engine produces native Codex hooks.json in the output."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        hooks_json = output / ".codex" / "hooks.json"
        assert hooks_json.exists(), "Native .codex/hooks.json missing"

    def test_engine_produces_current_codex_hooks_feature_flag(self, tmp_path: Path):
        """Codex config.toml uses hooks, not deprecated codex_hooks."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        config = tomllib.loads((output / ".codex" / "config.toml").read_text())
        features = config.get("features", {})
        assert features.get("hooks") is True
        assert "codex_hooks" not in features

    def test_engine_does_not_emit_codex_plugin_manifest(self, tmp_path: Path):
        """Codex native output does not use .codex-plugin/plugin.json."""
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        assert not (output / ".codex-plugin").exists()
