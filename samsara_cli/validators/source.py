"""
SourceValidator — Pre-conversion validation of samsara source directory structure.

Validates the source directory BEFORE any conversion begins. This gives early,
unambiguous attribution of problems: "source is malformed" vs "converter bug".

Validation checks:
1. Required directories exist: .claude-plugin/, skills/, agents/, hooks/, references/
2. plugin.json exists and has required fields (name, version)
3. Each expected skill directory exists and contains SKILL.md
4. agents/ directory has at least one .md file
5. hooks/hooks.json exists

Design decisions:
- All errors are accumulated into a list — validation never short-circuits on first error.
  Rationale: showing the user all problems at once is better than showing one, fixing it,
  and then showing the next. A full error report means one pass to fix all issues.
- ValidationError is a marker exception — it is NOT raised by validate(). It is available
  for callers that want to raise programmatically from the error list.
- validate() returns a list[str]. Empty list = valid. Populated list = errors.

Silent failure conditions:
- If expected_skills is empty, skill directory validation is skipped entirely.
  A caller that passes an empty list will receive no skill errors even if all
  11 skills are missing. The expected_skills parameter must come from a canonical
  source (e.g., platform config or a hardcoded list of required skills).
- Assumption: .claude-plugin/plugin.json is flat JSON with 'name' and 'version'
  at the root. Nested structures (e.g., {"metadata": {"name": "samsara"}}) would
  pass required-field validation silently if the root has no 'name' key.
  This is the same assumption as ManifestConverter — consistent by design.

Assumption: The source directory paths (plugin_dir, skills_dir, etc.) are derived
from the actual samsara source structure, which is stable. If the source structure
changes (e.g., plugin dir renamed from .claude-plugin to .plugin), the validator
must be updated. There is no automatic synchronization with the source layout.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Required fields in plugin.json (same as ManifestConverter._REQUIRED_FIELDS)
_REQUIRED_PLUGIN_FIELDS: tuple[str, ...] = ("name", "version")

# Source directory structure constants
_PLUGIN_DIR_NAME = ".claude-plugin"
_PLUGIN_JSON_NAME = "plugin.json"
_SKILLS_DIR_NAME = "skills"
_AGENTS_DIR_NAME = "agents"
_HOOKS_DIR_NAME = "hooks"
_HOOKS_JSON_NAME = "hooks.json"
_REFERENCES_DIR_NAME = "references"
_SKILL_MD_NAME = "SKILL.md"


class ValidationError(Exception):
    """Marker exception for source validation failures.

    Not raised by SourceValidator.validate() directly — validate() returns
    a list of error strings. This exception is available for callers who
    want to raise programmatically after inspect the error list.
    """


class SourceValidator:
    """Validates the samsara source directory structure before conversion.

    This validator is stateless — each call to validate() is independent.
    Safe to reuse across multiple source directories.

    Usage:
        validator = SourceValidator()
        errors = validator.validate(source_dir, expected_skills=["research", "implement"])
        if errors:
            for error in errors:
                print(f"Source validation error: {error}")
            raise ValidationError("Source structure is invalid")
    """

    def validate(
        self,
        source_dir: Path,
        expected_skills: list[str],
    ) -> list[str]:
        """Validate the source directory structure.

        Accumulates all validation errors — does not short-circuit on first error.
        Each check runs independently so all issues are visible in one pass.

        Args:
            source_dir: Path to the samsara source directory root.
            expected_skills: List of skill directory names expected to exist.
                             Each name is checked for existence AND for SKILL.md.
                             Pass an empty list to skip skill-specific validation.

        Returns:
            List of error strings. Empty list means the source is valid.
            Each error string is human-readable and names the specific problem.

        Does NOT raise ValidationError — callers decide whether to raise.
        """
        errors: list[str] = []

        # --- Check 1: Source directory itself exists ---
        if not source_dir.exists():
            errors.append(
                f"Source directory does not exist: {source_dir}. "
                "Cannot validate a non-existent source."
            )
            # Cannot continue — all subsequent checks depend on source_dir existing
            return errors

        if not source_dir.is_dir():
            errors.append(f"Source path is not a directory: {source_dir}.")
            return errors

        # --- Check 2: Required top-level directories ---
        required_dirs = [
            (_PLUGIN_DIR_NAME, ".claude-plugin/ directory"),
            (_SKILLS_DIR_NAME, "skills/ directory"),
            (_AGENTS_DIR_NAME, "agents/ directory"),
            (_HOOKS_DIR_NAME, "hooks/ directory"),
        ]
        for dir_name, description in required_dirs:
            dir_path = source_dir / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                errors.append(
                    f"Required {description} is missing: {dir_path}. "
                    "The samsara source structure requires this directory."
                )

        # --- Check 3: plugin.json exists and has required fields ---
        plugin_json_path = source_dir / _PLUGIN_DIR_NAME / _PLUGIN_JSON_NAME
        if not plugin_json_path.exists():
            errors.append(
                f"Required plugin.json not found: {plugin_json_path}. "
                "The source plugin directory must contain a plugin.json manifest."
            )
        else:
            # Validate plugin.json content
            plugin_errors = self._validate_plugin_json(plugin_json_path)
            errors.extend(plugin_errors)

        # --- Check 4: Expected skill directories and SKILL.md files ---
        skills_dir_path = source_dir / _SKILLS_DIR_NAME
        if skills_dir_path.exists():
            for skill_name in expected_skills:
                skill_dir = skills_dir_path / skill_name
                if not skill_dir.exists() or not skill_dir.is_dir():
                    errors.append(
                        f"Required skill directory is missing: '{skill_name}' "
                        f"(expected at {skill_dir}). "
                        "The source must contain this skill directory. "
                        "This is NOT a silently skippable case — missing skill = missing output."
                    )
                else:
                    # Check that SKILL.md exists within the skill dir
                    skill_md = skill_dir / _SKILL_MD_NAME
                    if not skill_md.exists():
                        errors.append(
                            f"SKILL.md not found in skill directory '{skill_name}': {skill_md}. "
                            "Every skill directory must contain a SKILL.md file. "
                            "A skill directory without SKILL.md produces no skill output."
                        )

        # --- Check 5: agents/ has at least one .md file ---
        agents_dir_path = source_dir / _AGENTS_DIR_NAME
        if agents_dir_path.exists():
            agent_files = list(agents_dir_path.glob("*.md"))
            if not agent_files:
                errors.append(
                    f"No .md agent files found in agents/ directory: {agents_dir_path}. "
                    "The agents/ directory must contain at least one .md agent definition. "
                    "An empty agents/ directory means no agents will be converted."
                )

        # --- Check 6: hooks/hooks.json exists ---
        hooks_dir_path = source_dir / _HOOKS_DIR_NAME
        if hooks_dir_path.exists():
            hooks_json_path = hooks_dir_path / _HOOKS_JSON_NAME
            if not hooks_json_path.exists():
                errors.append(
                    f"hooks.json not found in hooks/ directory: {hooks_json_path}. "
                    "The hooks configuration file is required for hook conversion."
                )

        return errors

    def _validate_plugin_json(self, plugin_json_path: Path) -> list[str]:
        """Validate plugin.json content.

        Returns list of error strings (may be empty).
        """
        errors: list[str] = []

        try:
            raw = plugin_json_path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(f"Cannot read plugin.json at {plugin_json_path}: {e}.")
            return errors

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            errors.append(
                f"plugin.json contains malformed JSON at {plugin_json_path}: {e.msg} "
                f"(line {e.lineno}, col {e.colno}). "
                "Fix the JSON syntax before running conversion."
            )
            return errors

        if not isinstance(data, dict):
            errors.append(
                f"plugin.json root must be a JSON object (dict), got: {type(data).__name__}. "
                f"File: {plugin_json_path}."
            )
            return errors

        # Check required fields
        for field in _REQUIRED_PLUGIN_FIELDS:
            if field not in data:
                errors.append(
                    f"plugin.json is missing required field '{field}': {plugin_json_path}. "
                    f"Required fields: {list(_REQUIRED_PLUGIN_FIELDS)}. "
                    "Conversion would fail at manifest conversion time — catching it here instead."
                )
            elif data[field] is None:
                errors.append(
                    f"plugin.json field '{field}' is null (JSON null → Python None): "
                    f"{plugin_json_path}. "
                    "A null required field is semantically absent — cannot use it for naming."
                )

        return errors
