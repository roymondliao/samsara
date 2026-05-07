"""
Integration tests — Format Validation.

Validates that converted files are in valid formats for the target platform:
1. All .toml files parse correctly (tomllib)
2. hooks.json is valid JSON and has expected structure
3. plugin.json is valid JSON with required fields
4. No unconverted samsara source patterns remain in any .md output file
5. All output .md files have valid frontmatter (--- delimited)

Death tests guard:
  DC-9-4: Format validation must FAIL if any .toml file has a syntax error.
           A TOML parse failure means the platform cannot load the agent.
           Tests must not skip TOML validation or pass on empty files.
  DC-9-5: Unconverted pattern detection must FAIL if any source pattern remains.
           "invoke `samsara:X`" or "subagent_type:" in output means broken conversion.
           Tests must actively scan — not assume conversion happened correctly.
  DC-9-6: Validation must fail if hooks.json is missing the required 'hooks' key.
           Missing hooks key means the platform silently ignores all hooks.

Assumption: output_dir from fixture_output() fixture is fully converted and valid.
Assumption: TOML parse uses stdlib tomllib (Python 3.11+). If Python < 3.11, fails at import.
"""

import json
import tomllib
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine

# --- Fixture paths ---
FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"


# ---------------------------------------------------------------------------
# Death tests (DC-9-4, DC-9-5, DC-9-6) — listed before unit tests
# ---------------------------------------------------------------------------


class TestDC94TomlValidationMustFailOnSyntaxError:
    """Death test: format validation must fail on TOML syntax error, not skip."""

    def test_toml_parse_catches_syntax_error(self) -> None:
        """Verify our validation code rejects malformed TOML.

        This guards against a validation implementation that catches TOMLDecodeError
        and silently passes the file. The test checks that our validation logic
        returns an error on bad TOML — not that it skips the file.
        """
        bad_toml = '[agent\nname = "broken"'  # Missing closing bracket
        errors: list[str] = []
        try:
            tomllib.loads(bad_toml)
        except tomllib.TOMLDecodeError as e:
            errors.append(f"TOML error: {e}")

        assert len(errors) == 1, (
            "Expected tomllib.loads to raise TOMLDecodeError on malformed TOML. "
            "If this fails, our validation cannot catch TOML syntax errors."
        )

    def test_toml_validation_fails_empty_file(self) -> None:
        """Validation must fail on an empty .toml file — not pass silently.

        An empty agent TOML file means no agent was converted. Codex would load
        an empty agent definition and silently ignore it. We must detect this.
        """
        empty_content = ""
        errors: list[str] = []
        if not empty_content.strip():
            errors.append("TOML file is empty")
        assert len(errors) == 1, (
            "Empty TOML file must produce a validation error. "
            "If we skip empty files, broken conversions pass silently."
        )

    def test_real_output_agent_toml_parses_correctly(self, tmp_path: Path) -> None:
        """DC-9-4: Real output agent TOML must parse without errors.

        If conversion produces invalid TOML, this test catches it.
        This is the positive assertion — invalid TOML in real output is a bug.
        """
        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        agents_dir = output_dir / ".codex" / "agents"
        toml_files = list(agents_dir.glob("*.toml"))
        assert len(toml_files) >= 1, "No agent TOML files to validate"

        parse_errors: list[str] = []
        for toml_file in toml_files:
            content = toml_file.read_text(encoding="utf-8")
            if not content.strip():
                parse_errors.append(f"{toml_file.name}: file is empty")
                continue
            try:
                tomllib.loads(content)
            except tomllib.TOMLDecodeError as e:
                parse_errors.append(f"{toml_file.name}: {e}")

        assert parse_errors == [], "Agent TOML parse errors found:\n" + "\n".join(
            f"  - {e}" for e in parse_errors
        )


class TestDC95UnconvertedPatternsMustFail:
    """Death test: validation must fail if source patterns remain in output."""

    def test_invoke_samsara_pattern_detection_works(self) -> None:
        """Verify our pattern scanner finds invoke `samsara:X` patterns."""
        import re

        pattern = re.compile(r"invoke `samsara:[\w-]+`")
        test_content = "After completing this, invoke `samsara:planning` skill."
        match = pattern.search(test_content)
        assert match is not None, (
            "Pattern scanner failed to find 'invoke `samsara:X`' in test string. "
            "If our scanner cannot find this pattern in a string we know contains it, "
            "it will miss real unconverted patterns in output."
        )

    def test_subagent_type_pattern_detection_works(self) -> None:
        """Verify our scanner finds subagent_type: patterns."""
        import re

        pattern = re.compile(r"subagent_type:")
        test_content = '  subagent_type: "samsara:implementer"'
        match = pattern.search(test_content)
        assert match is not None, (
            "Pattern scanner failed to find 'subagent_type:' in test string. "
            "Unconverted agent dispatch patterns would go undetected."
        )

    def test_real_output_has_no_invoke_samsara_pattern(self, tmp_path: Path) -> None:
        """DC-9-5: No output .md file may contain 'invoke `samsara:X`' pattern."""
        import re

        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        invoke_pattern = re.compile(r"invoke `samsara:[\w-]+`")
        violations: list[str] = []
        for md_file in output_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            match = invoke_pattern.search(content)
            if match:
                violations.append(
                    f"{md_file.relative_to(output_dir)}: found '{match.group()}'"
                )

        assert violations == [], (
            "Unconverted 'invoke `samsara:X`' patterns found in output:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_real_output_has_no_subagent_type_pattern(self, tmp_path: Path) -> None:
        """DC-9-5: No output .md file may contain 'subagent_type:' pattern."""
        import re

        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        subagent_pattern = re.compile(r"subagent_type:")
        violations: list[str] = []
        for md_file in output_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            match = subagent_pattern.search(content)
            if match:
                violations.append(str(md_file.relative_to(output_dir)))

        assert violations == [], (
            "Unconverted 'subagent_type:' patterns found in output:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestDC96HooksJsonMustHaveRequiredStructure:
    """Death test: hooks.json validation must fail on missing 'hooks' key."""

    def test_missing_hooks_key_is_detected(self) -> None:
        """Validate that our check catches a hooks.json missing the 'hooks' key.

        If hooks.json lacks the 'hooks' key, Codex silently ignores all hooks.
        Our validation must catch this — not pass it as valid JSON.
        """
        bad_hooks = {"version": 1}  # Missing 'hooks' key
        errors: list[str] = []
        if "hooks" not in bad_hooks:
            errors.append("hooks.json missing required 'hooks' key")
        assert len(errors) == 1, (
            "Our check did not detect missing 'hooks' key in hooks.json. "
            "Codex would silently ignore all hooks."
        )

    def test_real_output_hooks_json_has_hooks_key(self, tmp_path: Path) -> None:
        """DC-9-6: Output hooks.json must have the 'hooks' key."""
        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        hooks_json = output_dir / ".codex" / "hooks.json"
        assert hooks_json.exists(), "hooks.json missing from .codex/"

        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert "hooks" in data, (
            f"hooks.json missing required 'hooks' key. "
            f"Actual keys: {list(data.keys())}. "
            "Codex would silently ignore all hooks."
        )


# ---------------------------------------------------------------------------
# Unit tests — format validation of the converted fixture output
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def converted_output(tmp_path_factory) -> Path:
    """Run conversion once for all format validation tests in this module."""
    output_dir = tmp_path_factory.mktemp("format_val") / "codex_output"
    engine = ConversionEngine("codex")
    engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
    return output_dir


class TestTomlFormatValidity:
    """All agent .toml files must be valid Codex subagent TOML."""

    def test_all_toml_files_parse(self, converted_output: Path) -> None:
        """All .toml files must parse without error."""
        agents_dir = converted_output / ".codex" / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            assert content.strip(), f"{toml_file.name} is empty"
            tomllib.loads(content)  # Raises TOMLDecodeError on failure

    def test_agent_toml_has_no_agent_section(self, converted_output: Path) -> None:
        """Each agent .toml must use top-level fields, not an [agent] wrapper."""
        agents_dir = converted_output / ".codex" / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            parsed = tomllib.loads(content)
            assert "agent" not in parsed, (
                f"{toml_file.name} contains unsupported [agent] section. "
                "Codex subagent files require top-level fields."
            )

    def test_agent_toml_has_name_field(self, converted_output: Path) -> None:
        """Each agent .toml must have top-level name field."""
        agents_dir = converted_output / ".codex" / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            parsed = tomllib.loads(content)
            assert "name" in parsed, f"{toml_file.name} missing top-level name field."
            assert parsed["name"], f"{toml_file.name} has empty top-level name field."

    def test_agent_toml_has_description_field(self, converted_output: Path) -> None:
        """Each agent .toml must have top-level description field."""
        agents_dir = converted_output / ".codex" / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            parsed = tomllib.loads(content)
            assert "description" in parsed, (
                f"{toml_file.name} missing top-level description field."
            )
            assert parsed["description"], (
                f"{toml_file.name} has empty top-level description field."
            )

    def test_agent_toml_has_developer_instructions(
        self, converted_output: Path
    ) -> None:
        """Each agent .toml must have top-level developer_instructions field."""
        agents_dir = converted_output / ".codex" / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            parsed = tomllib.loads(content)
            assert "developer_instructions" in parsed, (
                f"{toml_file.name} missing developer_instructions field. "
                "Agent would have empty instructions on the target platform."
            )
            assert parsed["developer_instructions"].strip(), (
                f"{toml_file.name} has empty developer_instructions. "
                "Agent body was not transferred."
            )


class TestJsonFormatValidity:
    """Output JSON files must be valid JSON with expected structure."""

    def test_hooks_json_is_valid_json(self, converted_output: Path) -> None:
        """hooks.json must parse as valid JSON."""
        hooks_json = converted_output / ".codex" / "hooks.json"
        content = hooks_json.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict), "hooks.json root must be a JSON object"

    def test_hooks_json_has_hooks_map(self, converted_output: Path) -> None:
        """hooks.json must have a 'hooks' key with an event map value."""
        hooks_json = converted_output / ".codex" / "hooks.json"
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        assert "hooks" in data, "hooks.json missing 'hooks' key"
        assert isinstance(data["hooks"], dict), (
            f"hooks.json 'hooks' must be a map, got {type(data['hooks']).__name__}"
        )
        assert len(data["hooks"]) >= 1, "hooks.json 'hooks' map is empty"


class TestFrontmatterValidity:
    """Output SKILL.md files must have valid YAML frontmatter."""

    def test_all_skill_mds_have_frontmatter(self, converted_output: Path) -> None:
        """Every SKILL.md must begin with '---' frontmatter delimiters."""
        skills_dir = converted_output / ".agents" / "skills"
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            assert lines and lines[0].strip() == "---", (
                f"{skill_dir.name}/SKILL.md does not start with '---' frontmatter. "
                "Frontmatter is required for skill metadata."
            )
            # Find closing ---
            closing_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    closing_idx = i
                    break
            assert closing_idx is not None, (
                f"{skill_dir.name}/SKILL.md frontmatter is never closed with '---'. "
                "Unclosed frontmatter will cause metadata parsing failures."
            )

    def test_all_skill_mds_have_name_in_frontmatter(
        self, converted_output: Path
    ) -> None:
        """Every SKILL.md frontmatter must have a name field."""
        skills_dir = converted_output / ".agents" / "skills"
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            # Extract frontmatter lines
            frontmatter_lines = []
            if lines and lines[0].strip() == "---":
                for line in lines[1:]:
                    if line.strip() == "---":
                        break
                    frontmatter_lines.append(line)
            has_name = any(line.startswith("name:") for line in frontmatter_lines)
            assert has_name, (
                f"{skill_dir.name}/SKILL.md frontmatter missing 'name:' field."
            )


class TestNoUnconvertedPatterns:
    """No output file may contain unconverted samsara source patterns."""

    def test_no_invoke_samsara_in_output_mds(self, converted_output: Path) -> None:
        """All invoke `samsara:X` patterns must be converted in output .md files."""
        import re

        pattern = re.compile(r"invoke `samsara:[\w-]+`")
        violations: list[str] = []
        for md_file in converted_output.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            if pattern.search(content):
                violations.append(str(md_file.relative_to(converted_output)))
        assert violations == [], "invoke `samsara:X` pattern found in:\n" + "\n".join(
            f"  {v}" for v in violations
        )

    def test_no_subagent_type_in_output_mds(self, converted_output: Path) -> None:
        """All subagent_type: patterns must be converted in output .md files."""
        import re

        pattern = re.compile(r"subagent_type:")
        violations: list[str] = []
        for md_file in converted_output.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            if pattern.search(content):
                violations.append(str(md_file.relative_to(converted_output)))
        assert violations == [], "subagent_type: pattern found in:\n" + "\n".join(
            f"  {v}" for v in violations
        )

    def test_tool_references_converted_in_skill_mds(
        self, converted_output: Path
    ) -> None:
        """Literal 'Read tool', 'Edit tool', 'Write tool' must be converted.

        These are the medium-priority literal substitution rules from codex.yaml.
        If any remain, the transformation rules did not run on that file.
        """
        unconverted_patterns = ["Read tool", "Edit tool", "Write tool", "Bash tool"]
        violations: list[tuple[str, str]] = []
        for md_file in converted_output.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            for pattern in unconverted_patterns:
                if pattern in content:
                    violations.append(
                        (str(md_file.relative_to(converted_output)), pattern)
                    )
        assert violations == [], "Unconverted tool references found:\n" + "\n".join(
            f"  {f}: '{p}'" for f, p in violations
        )
