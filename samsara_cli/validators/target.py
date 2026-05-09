"""
TargetValidator — Post-conversion validation of converted output directory.

Validates the output directory AFTER all converters have run but BEFORE the temp
dir is moved to the final output path. This is the last line of defense against
shipping broken output.

Validation checks:
1. Source pattern scan: no "invoke `samsara:X`" patterns in ANY .md file
2. Source pattern scan: no "subagent_type:" patterns in ANY .md file
3. TOML validation: all .toml files in agents/ parse correctly
4. Skill directory name validation: no colon in skill dir names
5. Agent cross-validation: every agent name referenced in dispatch-template.md
   exists as a converted agent (matched by top-level TOML name field)

Design decisions:
- All errors are accumulated — validation never short-circuits on first error.
  Rationale: full error report enables single-pass fix cycle.
- validate() returns list[str]. Empty = valid. Non-empty = errors.
  Callers decide whether to raise. The engine raises on non-empty errors.
- TOML parsing uses tomllib (stdlib since Python 3.11). No third-party dep.
- Agent cross-validation: parses agent TOML to extract the top-level name field,
  then searches all .md companion files for references to that name. A reference
  is any occurrence of the agent name string. This is intentionally broad —
  false positives (unrelated text matching agent name) are acceptable because
  the cost of a false negative (missed mismatch) is higher.

Known shortcuts:
- Pattern scanning uses simple regex, not AST parsing. Variant patterns like
  "invoke\\n`samsara:" (newline between invoke and backtick) are NOT detected.
  This is documented as a known shortcut — the primary death case pattern
  "invoke `samsara:X`" (on one line) is covered.
- Agent name cross-validation searches dispatch-template.md for agent name strings.
  If an agent is referenced in SKILL.md body (not a companion file), the validator
  may miss it. The primary death case (dispatch-template.md) is covered.
- YAML files (.yaml, .yml) in the output are NOT scanned for source patterns.
  Rationale: YAML files may legitimately contain samsara namespace references
  in documentation text (scar-schema.yaml, etc.). Scanning them would produce
  false positives. This is consistent with SkillConverter's YAML exclusion.

Assumptions:
1. TOML agent files are in output/agents/*.toml (platform-specific path).
   If the platform places agents elsewhere, the agent scan path must be updated.
   Currently hardcoded to PlatformConfig.paths.agents_dir if available, else "agents".
2. Skill directories are in output/skills/*.
   If the platform uses a different skill dir structure, the scan is wrong.
3. Agent name extraction from TOML: the top-level name field holds the agent's
   canonical name. If the TOML structure differs (e.g., [codex.agent].name),
   extraction will return None and cross-validation may miss mismatches.
4. Dispatch-template.md is the primary file that references agent names.
   Other companion files (e.g., SKILL.md body) may also reference agents —
   not currently validated. First-priority coverage is dispatch-template.md.
"""

import json
import logging
import os
import re
import tomllib
from pathlib import Path

logger = logging.getLogger(__name__)

# Pattern that must NOT appear in any output .md file (architecture death case DC-2).
# "invoke `samsara:X`" where X is a word/hyphen skill name.
_INVOKE_SAMSARA_PATTERN = re.compile(r"invoke `samsara:[\w-]+`")

# Pattern that must NOT appear in any output .md file (agent dispatch death case).
# `subagent_type:` is the Claude Code-specific agent dispatch syntax.
_SUBAGENT_TYPE_PATTERN = re.compile(r"subagent_type:")

# Pattern for agent name references in companion files (dispatch-template.md).
# Matches 'agent named "X"' where X is the referenced agent name.
_AGENT_REF_PATTERN = re.compile(r'agent named "([^"]+)"')

# File extensions that receive source pattern scanning.
# YAML files are excluded — they may legitimately contain samsara namespace strings.
_SCAN_EXTENSIONS = {".md", ".txt"}

# Colon character in skill directory names indicates source format (samsara:X).
# Target format uses hyphen (samsara-X).
_COLON_IN_NAME_MSG = (
    "Skill directory '{}' contains a colon — this is the source format (samsara:X), "
    "not the target format (samsara-X). Rename to use the separator character."
)


class ValidationError(Exception):
    """Marker exception for target validation failures.

    Not raised by TargetValidator.validate() directly — validate() returns
    a list of error strings. This exception is available for callers who
    want to raise programmatically after inspecting the error list.
    """


class TargetValidator:
    """Validates converted output before it is committed to the final output path.

    This validator is stateless — each call to validate() is independent.
    Safe to reuse across multiple validation runs.

    Usage:
        validator = TargetValidator()
        errors = validator.validate(output_dir=temp_dir, platform="codex")
        if errors:
            shutil.rmtree(temp_dir)
            raise ValidationError(f"Target validation failed: {errors}")
        shutil.move(temp_dir, final_output_dir)
    """

    def validate(
        self,
        output_dir: Path,
        platform: str = "codex",
    ) -> list[str]:
        """Validate the converted output directory.

        Accumulates all validation errors — does not short-circuit on first error.
        Each check runs independently so all issues are visible in one pass.

        Args:
            output_dir: Path to the converted output directory (temp dir or final).
            platform: Target platform name. Defaults to "codex" for backward
                      compatibility with older tests/callers.

        Returns:
            List of error strings. Empty list means the output is valid.
            Each error string is human-readable and names the specific problem.

        Does NOT raise ValidationError — callers decide whether to raise.
        """
        errors: list[str] = []

        if not output_dir.exists():
            errors.append(
                f"Output directory does not exist: {output_dir}. "
                "Cannot validate a non-existent output directory."
            )
            return errors

        # --- Check 1: Skill directory names (no colon allowed) ---
        skills_dir = self._get_skills_dir(output_dir, platform)
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and ":" in skill_dir.name:
                    errors.append(_COLON_IN_NAME_MSG.format(skill_dir.name))

        if platform == "gemini-cli":
            errors.extend(self._validate_gemini_layout(output_dir))

        # --- Check 2: Source pattern scan across all scannable files ---
        pattern_errors = self._scan_source_patterns(output_dir)
        errors.extend(pattern_errors)

        # --- Check 3: TOML file validation ---
        agents_dir = self._get_agents_dir(output_dir, platform)
        if agents_dir.exists():
            if platform == "gemini-cli":
                errors.extend(self._validate_gemini_agents(agents_dir))
            else:
                toml_errors = self._validate_toml_files(agents_dir)
                errors.extend(toml_errors)

        # --- Check 4: Agent cross-validation ---
        cross_errors = self._cross_validate_agent_names(
            output_dir, agents_dir, platform
        )
        errors.extend(cross_errors)

        return errors

    def _get_skills_dir(self, output_dir: Path, platform: str = "codex") -> Path:
        """Return the skills directory path within the output dir."""
        if platform == "gemini-cli":
            return output_dir / ".gemini" / "skills"
        # Codex native layout uses .agents/skills. Legacy/plugin-style converted
        # output used skills/. Prefer the native path when present, but keep the
        # fallback so older fixture-level tests can still validate legacy output.
        native = output_dir / ".agents" / "skills"
        if native.exists():
            return native
        return output_dir / "skills"

    def _get_agents_dir(self, output_dir: Path, platform: str = "codex") -> Path:
        """Return the agents directory path within the output dir."""
        if platform == "gemini-cli":
            return output_dir / ".gemini" / "agents"
        # Codex native layout uses .codex/agents. Legacy/plugin-style converted
        # output used agents/.
        native = output_dir / ".codex" / "agents"
        if native.exists():
            return native
        return output_dir / "agents"

    def _validate_gemini_layout(self, output_dir: Path) -> list[str]:
        """Validate Gemini-specific output layout and settings JSON."""
        errors: list[str] = []

        alias_skills = output_dir / ".agents" / "skills"
        if alias_skills.exists():
            errors.append(
                "Gemini output must not create .agents/skills. "
                "Use .gemini/skills for Gemini skill discovery."
            )

        gemini_dir = output_dir / ".gemini"
        skills_dir = gemini_dir / "skills"
        agents_dir = gemini_dir / "agents"
        settings_path = gemini_dir / "settings.json"

        if not skills_dir.is_dir():
            errors.append("Gemini output is missing .gemini/skills directory.")
        if not agents_dir.is_dir():
            errors.append("Gemini output is missing .gemini/agents directory.")
        if not settings_path.exists():
            errors.append("Gemini output is missing .gemini/settings.json.")
            return errors

        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"Gemini settings.json is invalid JSON: {e}")
            return errors
        except OSError as e:
            errors.append(f"Cannot read Gemini settings.json: {e}")
            return errors

        hooks = settings.get("hooks")
        if not isinstance(hooks, dict):
            errors.append("Gemini settings.json missing object field hooks.")
            return errors

        session_start = hooks.get("SessionStart")
        if not isinstance(session_start, list) or not session_start:
            errors.append("Gemini settings.json missing hooks.SessionStart entries.")
        else:
            errors.extend(
                self._validate_gemini_session_start_commands(
                    output_dir=output_dir,
                    entries=session_start,
                )
            )

        return errors

    def _validate_gemini_session_start_commands(
        self,
        output_dir: Path,
        entries: list,
    ) -> list[str]:
        """Validate Gemini SessionStart hook command targets."""
        errors: list[str] = []

        for entry_idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(
                    f"Gemini SessionStart entry {entry_idx} is not an object."
                )
                continue
            hooks = entry.get("hooks")
            if not isinstance(hooks, list) or not hooks:
                errors.append(
                    f"Gemini SessionStart entry {entry_idx} has no hooks list."
                )
                continue

            for hook_idx, hook in enumerate(hooks):
                if not isinstance(hook, dict):
                    errors.append(
                        f"Gemini SessionStart hook {entry_idx}.{hook_idx} is not an object."
                    )
                    continue
                command = hook.get("command")
                if not isinstance(command, str) or not command.strip():
                    errors.append(
                        f"Gemini SessionStart hook {entry_idx}.{hook_idx} missing command."
                    )
                    continue
                if command.startswith("/") or Path(command).is_absolute():
                    errors.append(
                        f"Gemini SessionStart hook command is absolute: {command!r}. "
                        "Commands must be relative to the project root."
                    )
                    continue

                command_path = output_dir / command
                if not command_path.exists():
                    errors.append(
                        f"Gemini SessionStart hook command target does not exist: {command}."
                    )
                    continue
                if not os.access(command_path, os.X_OK):
                    errors.append(
                        f"Gemini SessionStart hook command target is not executable: {command}."
                    )

        return errors

    def _validate_gemini_agents(self, agents_dir: Path) -> list[str]:
        """Validate Gemini markdown agent files."""
        errors: list[str] = []

        for toml_file in agents_dir.glob("*.toml"):
            errors.append(f"Gemini agent must be markdown, not TOML: {toml_file.name}.")

        for md_file in agents_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                errors.append(f"Cannot read Gemini agent {md_file.name}: {e}")
                continue

            frontmatter = self._extract_markdown_frontmatter(content)
            if frontmatter is None:
                errors.append(
                    f"Gemini agent {md_file.name} is missing YAML frontmatter."
                )
                continue

            if not frontmatter.get("name"):
                errors.append(f"Gemini agent {md_file.name} missing frontmatter name.")
            if not frontmatter.get("description"):
                errors.append(
                    f"Gemini agent {md_file.name} missing frontmatter description."
                )

        return errors

    def _extract_markdown_frontmatter(self, content: str) -> dict[str, str] | None:
        """Extract simple key/value YAML frontmatter from a markdown file."""
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            return None

        closing_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_idx = i
                break
        if closing_idx is None:
            return None

        frontmatter: dict[str, str] = {}
        for line in lines[1:closing_idx]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip().strip('"').strip("'")
        return frontmatter

    def _scan_source_patterns(self, output_dir: Path) -> list[str]:
        """Scan all scannable files in output_dir for remaining source patterns.

        Source patterns that must NOT appear in output:
        - invoke `samsara:X` — chain transition death case
        - subagent_type: — agent dispatch source pattern

        Returns list of error strings (may be empty if no patterns found).
        """
        errors: list[str] = []

        for file_path in output_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in _SCAN_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                # Log but do not fail — binary files may be in output
                logger.warning(
                    "Cannot read file for pattern scan: %s: %s", file_path, e
                )
                continue

            relative = file_path.relative_to(output_dir)

            # Check for invoke `samsara:X` pattern
            match = _INVOKE_SAMSARA_PATTERN.search(content)
            if match:
                errors.append(
                    f"Source transition pattern '{match.group()}' found in output file "
                    f"'{relative}'. This is an unconverted chain link — a Codex user "
                    "following this skill would hit a dead reference. "
                    "All `invoke `samsara:X`` patterns must be converted before output is valid."
                )

            # Check for subagent_type: pattern
            match2 = _SUBAGENT_TYPE_PATTERN.search(content)
            if match2:
                errors.append(
                    f"Source dispatch pattern 'subagent_type:' found in output file "
                    f"'{relative}'. This is Claude Code-specific agent dispatch syntax. "
                    "It must be converted to the target platform format before output is valid."
                )

        return errors

    def _validate_toml_files(self, agents_dir: Path) -> list[str]:
        """Validate all .toml files in agents_dir parse correctly.

        Returns list of error strings (may be empty).
        """
        errors: list[str] = []

        for toml_file in agents_dir.glob("*.toml"):
            content = toml_file.read_text(encoding="utf-8")
            if not content.strip():
                errors.append(
                    f"Agent TOML file is empty: {toml_file.name}. "
                    "An empty agent file means no agent was converted — "
                    "the file will fail to load on the target platform."
                )
                continue

            try:
                tomllib.loads(content)
            except tomllib.TOMLDecodeError as e:
                errors.append(
                    f"Agent TOML file failed to parse: {toml_file.name}. "
                    f"TOML error: {e}. "
                    "This TOML file cannot be loaded by the target platform."
                )

        return errors

    def _extract_agent_name_from_toml(self, toml_content: str) -> str | None:
        """Extract the top-level name field from TOML content.

        Returns the agent name string, or None if extraction fails.
        """
        try:
            parsed = tomllib.loads(toml_content)
            name = parsed.get("name")
            return name if isinstance(name, str) else None
        except tomllib.TOMLDecodeError:
            return None

    def _cross_validate_agent_names(
        self,
        output_dir: Path,
        agents_dir: Path,
        platform: str = "codex",
    ) -> list[str]:
        """Cross-validate agent name references in skills against actual agent files.

        Finds all agent names referenced in dispatch-template.md files and checks
        that a corresponding agent exists (by top-level name in TOML, not by filename).

        Returns list of error strings (may be empty).

        Assumption: agent references appear as string matches for the agent name in
        companion files named "dispatch-template.md". This is the primary dispatch
        template pattern. References in other files are not currently validated.
        """
        errors: list[str] = []

        if not agents_dir.exists():
            return errors

        # Build a set of known agent names from target agent files.
        known_agent_names: set[str] = set()
        if platform == "gemini-cli":
            for md_file in agents_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    frontmatter = self._extract_markdown_frontmatter(content)
                    if frontmatter and frontmatter.get("name"):
                        known_agent_names.add(frontmatter["name"])
                except OSError, UnicodeDecodeError:
                    pass
        else:
            for toml_file in agents_dir.glob("*.toml"):
                try:
                    content = toml_file.read_text(encoding="utf-8")
                    name = self._extract_agent_name_from_toml(content)
                    if name:
                        known_agent_names.add(name)
                except OSError, UnicodeDecodeError:
                    # Malformed TOML is caught by _validate_toml_files — skip here
                    pass

        if not known_agent_names:
            # No agents converted — cannot cross-validate
            # This is not itself an error (platform may have no agents)
            return errors

        skills_dir = self._get_skills_dir(output_dir, platform)
        if not skills_dir.exists():
            return errors

        for md_file in skills_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except OSError, UnicodeDecodeError:
                continue

            for match in _AGENT_REF_PATTERN.finditer(content):
                referenced_name = match.group(1)
                if referenced_name not in known_agent_names:
                    relative = md_file.relative_to(output_dir)
                    errors.append(
                        f"Agent name mismatch: '{relative}' references agent "
                        f"'{referenced_name}' but no converted agent has that name. "
                        f"Known agent names: {sorted(known_agent_names)}. "
                        "This would cause agent dispatch to fail at runtime — the skill "
                        "would try to invoke an agent that doesn't exist."
                    )

        return errors
