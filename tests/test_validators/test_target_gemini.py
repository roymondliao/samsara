"""
Gemini target validator tests.

These tests ensure Gemini output is validated as Gemini output, not accepted by
legacy Codex/fixture fallbacks.
"""

import json
import os
from pathlib import Path

from samsara_cli.validators.target import TargetValidator


def make_gemini_output(tmp_path: Path) -> Path:
    output = tmp_path / "output"
    skill_dir = output / ".gemini" / "skills" / "samsara-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research\n---\n\nResearch body.\n"
    )

    agents_dir = output / ".gemini" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "samsara-implementer.md").write_text(
        "---\n"
        "name: samsara-implementer\n"
        "description: Implementer\n"
        "kind: local\n"
        "---\n\n"
        "# Implementer\n"
    )

    hooks_dir = output / ".gemini" / "hooks"
    hooks_dir.mkdir(parents=True)
    script = hooks_dir / "samsara-session-start.sh"
    script.write_text("#!/usr/bin/env bash\n")
    script.chmod(0o755)
    (output / ".gemini" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": ".gemini/hooks/samsara-session-start.sh",
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    return output


class TestGeminiTargetValidation:
    def test_valid_gemini_output_passes(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")
        assert errors == []

    def test_gemini_rejects_agents_skills_alias(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        alias_dir = output / ".agents" / "skills" / "samsara-research"
        alias_dir.mkdir(parents=True)
        (alias_dir / "SKILL.md").write_text("# Wrong alias\n")

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert ".agents/skills" in " ".join(errors)

    def test_gemini_rejects_toml_agents(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        agent_file = output / ".gemini" / "agents" / "samsara-implementer.toml"
        agent_file.write_text('name = "samsara-implementer"\n')

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "toml" in " ".join(errors).lower()

    def test_gemini_rejects_markdown_agent_without_frontmatter(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        agent_file = output / ".gemini" / "agents" / "samsara-implementer.md"
        agent_file.write_text("# Missing frontmatter\n")

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "frontmatter" in " ".join(errors).lower()

    def test_gemini_rejects_invalid_settings_json(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        (output / ".gemini" / "settings.json").write_text("{not json")

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "settings.json" in " ".join(errors)

    def test_gemini_rejects_missing_session_start_hook(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        (output / ".gemini" / "settings.json").write_text(json.dumps({"hooks": {}}))

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "SessionStart" in " ".join(errors)

    def test_gemini_rejects_missing_referenced_hook_script(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        os.remove(output / ".gemini" / "hooks" / "samsara-session-start.sh")

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "does not exist" in " ".join(errors)

    def test_gemini_rejects_non_executable_referenced_hook_script(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        script = output / ".gemini" / "hooks" / "samsara-session-start.sh"
        script.chmod(0o644)

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "executable" in " ".join(errors).lower()

    def test_gemini_rejects_absolute_hook_command(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        settings_path = output / ".gemini" / "settings.json"
        settings = json.loads(settings_path.read_text())
        settings["hooks"]["SessionStart"][0]["hooks"][0]["command"] = (
            "/tmp/samsara-session-start.sh"
        )
        settings_path.write_text(json.dumps(settings))

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        assert errors
        assert "absolute" in " ".join(errors).lower()

    def test_gemini_detects_source_patterns(self, tmp_path: Path):
        output = make_gemini_output(tmp_path)
        skill_md = output / ".gemini" / "skills" / "samsara-research" / "SKILL.md"
        skill_md.write_text("invoke `samsara:planning`\nsubagent_type: x\n")

        errors = TargetValidator().validate(output_dir=output, platform="gemini-cli")

        text = " ".join(errors)
        assert "invoke" in text
        assert "subagent_type" in text
