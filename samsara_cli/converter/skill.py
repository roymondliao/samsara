"""
SkillConverter — SKILL.md content transformation and naming.

Converts a samsara skill directory (source format) to Codex format:
1. Parses SKILL.md frontmatter (name, description) and body
2. Applies body transformation rules to SKILL.md body only
3. Derives output directory name from naming config (prefix + separator + skill name)
4. Processes companion files recursively:
   - .md files: body rules applied
   - .yaml files: copied as-is (YAML structure must not be touched by markdown rules)
   - other files: copied as-is
5. Runs a target validator that scans all output for remaining source patterns;
   any match raises ConversionError (all-or-nothing — partial conversion is worse
   than no conversion)

Design decisions:
- All-or-nothing: If the target validator finds an unconverted source pattern,
  ConversionError is raised. The caller receives no partial output.
  Assumption: partial output that LOOKS valid but has unconverted patterns is
  worse than no output. If this assumption breaks, the validator behavior must
  be changed explicitly, not silently.

- Frontmatter parsed separately from rule application. RulesEngine handles
  frontmatter isolation for rule application (body rules don't touch frontmatter).
  But we also need to READ the frontmatter fields (name, description) to:
    (a) populate ConvertedSkill.name / .description
    (b) derive output_dir_name
  We parse frontmatter ourselves using the same '---' line detection the engine
  uses. If the engine's parsing logic ever changes, this parser must be updated.

- YAML files are explicitly excluded from rule application. The known shortcut
  from Task 2 (code-block-unawareness) is especially dangerous for YAML files
  where a literal match like 'Read tool' inside a YAML value would corrupt the
  data structure.

- The source pattern scanner (target validator) only scans for the specific
  pattern 'invoke `samsara:X`' because that is the architecture-specified
  death case (chain break). Other unconverted patterns (tool names) are not
  scanned for — this is a known shortcut documented in the scar report.

Assumptions:
1. SKILL.md always has frontmatter (---...---) with at least 'name' field.
   If not: ConversionError raised.
2. All 11 skills have only 'name' and 'description' in frontmatter.
   If extra fields exist: they are preserved unchanged (simple line-by-line
   YAML parsing extracts only name/description; other lines pass through).
3. The source directory name need not match the SKILL.md name field.
   output_dir_name is always derived from frontmatter name.
4. File encoding is UTF-8 throughout. If a file is not UTF-8, read() will
   raise UnicodeDecodeError — propagated as-is (not wrapped in ConversionError).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from samsara_cli.config.schema import NamingConfig, TransformationRule
from samsara_cli.converter.rules import RulesEngine


class ConversionError(Exception):
    """Raised when skill conversion fails in a way that must not produce partial output.

    Callers must treat ConversionError as a hard abort. Any output produced
    before the error is invalid and must not be written.
    """


@dataclass
class ConvertedSkill:
    """Result of a successful skill conversion.

    All content is in-memory. Writing to disk is the caller's responsibility.

    Attributes:
        name: Skill name from SKILL.md frontmatter (unchanged — not rule-applied).
        description: Skill description from frontmatter (unchanged — not rule-applied).
        output_dir_name: Target directory name (e.g., 'samsara-research').
        skill_md_content: Complete transformed SKILL.md text (frontmatter + body).
        companion_files: Dict mapping relative path string -> transformed content.
                         Keys are relative to source skill dir (e.g., 'problem-autopsy.md',
                         'templates/kickoff.md'). Values are file content strings.
                         YAML files are copied verbatim; .md files have body rules applied.
    """

    name: str
    description: str
    output_dir_name: str
    skill_md_content: str
    companion_files: dict[str, str] = field(default_factory=dict)


# Pattern that must NOT appear in converted output (architecture death case DC-2).
# Assumption: this is the canonical source pattern for skill transitions.
# If the source format changes (e.g., uses a different invocation syntax),
# this pattern must be updated — there is no automatic synchronization.
_SOURCE_TRANSITION_PATTERN = re.compile(r"invoke `samsara:[\w-]+`")

# File extensions treated as YAML — copy as-is, no rule application.
# Assumption: .yml is also YAML. If other extensions are used (e.g., .toml),
# they would receive .md treatment (rules applied), which would be wrong.
_YAML_EXTENSIONS = {".yaml", ".yml"}

# File extensions that receive body rule application.
_MD_EXTENSIONS = {".md"}


def _parse_frontmatter(text: str) -> tuple[str, str, str]:
    """Extract name, description, and body from SKILL.md text.

    Parses the YAML frontmatter block (between --- delimiters) to extract
    the 'name' and 'description' fields. Uses the same line-based '---'
    detection as the RulesEngine to guarantee consistent parsing behavior.

    Args:
        text: Complete SKILL.md file content.

    Returns:
        Tuple of (name, description, body) where body is everything after
        the closing '---' delimiter.

    Raises:
        ConversionError: If frontmatter is missing, malformed, or 'name'
                         field is absent.

    Assumption: 'description' is optional. If absent, empty string returned.
    Assumption: Simple line-by-line key: value parsing. Does not handle
                YAML multi-line values or nested structures in frontmatter.
                If a skill has complex frontmatter, name/description may not
                be correctly extracted — but the file content is still
                passed through unchanged.
    """
    lines = text.splitlines(keepends=True)

    # Validate frontmatter opening delimiter
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ConversionError(
            "SKILL.md has no valid frontmatter. "
            "Expected '---' on the first line. "
            "Every samsara skill must have frontmatter with at least 'name'."
        )

    # Find closing '---' delimiter
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            closing_idx = i
            break

    if closing_idx is None:
        raise ConversionError(
            "SKILL.md frontmatter has no closing '---' delimiter. "
            "Frontmatter started but was never closed. "
            "Cannot safely determine where frontmatter ends and body begins."
        )

    # Extract frontmatter lines (between delimiters)
    frontmatter_lines = lines[1:closing_idx]
    body = "".join(lines[closing_idx + 1 :])

    # Parse name and description from frontmatter
    name: str | None = None
    description: str | None = None

    for fm_line in frontmatter_lines:
        stripped = fm_line.strip()
        if stripped.startswith("name:"):
            name = stripped[len("name:") :].strip()
        elif stripped.startswith("description:"):
            description = stripped[len("description:") :].strip()

    if name is None:
        raise ConversionError(
            "SKILL.md frontmatter is missing the 'name' field. "
            "The 'name' field is required for output directory naming and skill identity. "
            f"Frontmatter content: {repr(''.join(frontmatter_lines))}"
        )

    return name, description or "", body


def _derive_output_dir_name(name: str, naming: NamingConfig) -> str:
    """Derive the output directory name from skill name and naming config.

    Applies the naming convention: prefix + separator + name.
    The colon (':') from samsara source format (samsara:X) is replaced by
    the separator from the naming config (e.g., '-' → 'samsara-X').

    Args:
        name: Skill name from SKILL.md frontmatter.
        naming: NamingConfig with skill_prefix and separator.

    Returns:
        Output directory name string (e.g., 'samsara-research').

    Assumption: skill_prefix is non-empty. If prefix is empty, output is
    'separator + name' which may be invalid. NamingConfig.skill_prefix
    is typed as str with no minimum length constraint.
    """
    return f"{naming.skill_prefix}{naming.separator}{name}"


def _scan_for_source_patterns(content: str, context_label: str) -> None:
    """Scan converted content for remaining source patterns.

    If any source transition pattern is found, raises ConversionError.
    This is the target validator from the architecture death cases — ensures
    all-or-nothing: no partial output ships with unconverted chain links.

    Args:
        content: Converted file content to scan.
        context_label: Human-readable label for error message (e.g., 'SKILL.md').

    Raises:
        ConversionError: If any source pattern is found in the content.

    Assumption: Only scans for the _SOURCE_TRANSITION_PATTERN. Other
    unconverted patterns (tool names) are not validated here. This is a
    known shortcut — tool name misses are observable by the user (wrong
    tool syntax in instructions) whereas transition misses are chain breaks
    (hard errors at runtime). The validator focuses on the higher-severity case.
    """
    match = _SOURCE_TRANSITION_PATTERN.search(content)
    if match:
        raise ConversionError(
            f"Source pattern '{match.group()}' found in converted output ({context_label}). "
            "Conversion is incomplete — this would create a broken chain link for Codex users. "
            "All transformation rules must cover this pattern, or the pattern must be "
            "explicitly excluded from validation if intentional."
        )


def _apply_body_rules(text: str, rules: list[TransformationRule]) -> str:
    """Apply body-scoped rules to text via RulesEngine.

    Passes the full document text (with frontmatter if present) to the engine.
    The engine handles frontmatter isolation internally — body rules will not
    touch frontmatter content.

    Args:
        text: Complete file content (may have frontmatter).
        rules: Transformation rules (mixed scopes allowed — engine filters).

    Returns:
        Transformed text with body rules applied.
    """
    engine = RulesEngine()
    return engine.apply(text, rules, scope="body")


def _process_companion_file(
    file_path: Path,
    rules: list[TransformationRule],
) -> str:
    """Read and process a single companion file.

    Processing logic:
    - .md files: apply body transformation rules
    - .yaml / .yml files: read and return verbatim (no rules)
    - Other extensions: read and return verbatim (no rules)

    Args:
        file_path: Absolute path to the companion file.
        rules: Transformation rules to apply (for .md files only).

    Returns:
        File content as string (transformed if .md, verbatim otherwise).

    Note: Reads as UTF-8. Binary files will fail with UnicodeDecodeError —
    propagated to caller (not wrapped). All samsara companion files are text.
    """
    content = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()

    if suffix in _MD_EXTENSIONS:
        return _apply_body_rules(content, rules)
    else:
        # YAML, binary, or other — copy as-is
        return content


class SkillConverter:
    """Converts a samsara skill directory to Codex format.

    Stateless — no per-conversion state is held between calls. Safe to reuse
    across multiple convert() calls.

    This converter is intentionally narrow: it handles SKILL.md parsing,
    content transformation, naming, and companion file processing. It does NOT:
    - Write output to disk (caller's responsibility)
    - Load config (caller provides rules and naming)
    - Handle batch conversion of all 11 skills (caller orchestrates)

    Usage:
        converter = SkillConverter()
        result = converter.convert(source_skill_dir, rules, naming_config)
        # result.skill_md_content — transformed SKILL.md text
        # result.companion_files — {relative_path: content}
        # result.output_dir_name — e.g., 'samsara-research'
    """

    def convert(
        self,
        source_skill_dir: Path,
        rules: list[TransformationRule],
        naming_config: NamingConfig,
    ) -> ConvertedSkill:
        """Convert a single skill directory.

        Steps:
        1. Read SKILL.md and parse frontmatter (name, description)
        2. Apply body rules to SKILL.md (frontmatter preserved by RulesEngine)
        3. Derive output_dir_name from naming config
        4. Process companion files (apply rules to .md, copy others as-is)
        5. Scan all converted content for remaining source patterns
        6. Return ConvertedSkill if validation passes

        Args:
            source_skill_dir: Path to the source skill directory.
                              Must contain SKILL.md.
            rules: Transformation rules to apply. Body-scoped rules apply to
                   SKILL.md body and companion .md files. Other scopes are
                   passed to the engine but have no effect on skills (all skill
                   content is body).
            naming_config: Naming convention config for output directory naming.

        Returns:
            ConvertedSkill with all transformed content in memory.

        Raises:
            ConversionError: If SKILL.md is missing, malformed (no frontmatter,
                             no 'name' field), or if target validation fails
                             (source patterns remain in output).
            FileNotFoundError: If source_skill_dir does not exist.

        This method will NOT silently produce partial output. Any failure raises
        ConversionError and no ConvertedSkill is returned.
        """
        # --- Guard: directory must exist ---
        if not source_skill_dir.exists():
            raise FileNotFoundError(
                f"Skill directory does not exist: {source_skill_dir}"
            )
        if not source_skill_dir.is_dir():
            raise ConversionError(f"Source path is not a directory: {source_skill_dir}")

        # --- Step 1: Read and parse SKILL.md ---
        skill_md_path = source_skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            raise ConversionError(
                f"SKILL.md not found in skill directory: {source_skill_dir}. "
                "Every skill directory must contain a SKILL.md file."
            )

        skill_md_raw = skill_md_path.read_text(encoding="utf-8")

        # Parse frontmatter to extract name and description
        # (raises ConversionError if malformed)
        name, description, _body = _parse_frontmatter(skill_md_raw)

        # --- Step 2: Apply body rules to SKILL.md ---
        # RulesEngine scopes body rules to body only — frontmatter is preserved.
        skill_md_converted = _apply_body_rules(skill_md_raw, rules)

        # --- Step 3: Derive output directory name ---
        output_dir_name = _derive_output_dir_name(name, naming_config)

        # --- Step 4: Process companion files ---
        companion_files: dict[str, str] = {}

        for item in sorted(source_skill_dir.rglob("*")):
            # Skip directories themselves
            if item.is_dir():
                continue
            # Skip SKILL.md — handled separately
            if item.name == "SKILL.md" and item.parent == source_skill_dir:
                continue

            # Compute relative path from skill dir root
            relative = item.relative_to(source_skill_dir)
            relative_str = str(relative)

            companion_content = _process_companion_file(item, rules)
            companion_files[relative_str] = companion_content

        # --- Step 5: Target validator — scan all output for source patterns ---
        # Scan SKILL.md body only (frontmatter preserved intentionally).
        # Use the already-parsed _body from _parse_frontmatter() — this avoids
        # the '---' re-split truncation risk: if body contained a line that was
        # exactly '---', a re-split would produce wrong sections. The _body
        # variable was parsed from the raw text using the same line-by-line
        # logic as the RulesEngine; it is the authoritative body text.
        # Note: _body is from the RAW (pre-transformation) text. We must scan
        # the CONVERTED body. Re-parse the converted SKILL.md for the body.
        _, _desc_unused, converted_body = _parse_frontmatter(skill_md_converted)
        _scan_for_source_patterns(converted_body, "SKILL.md body")

        # Scan companion files that received rule application (.md files and
        # any other text file that is not explicitly YAML).
        # YAML files are intentionally excluded — they are copied verbatim and
        # may legitimately contain source-format patterns in YAML keys/values
        # (e.g., scar-schema.yaml documentation text).
        # All other files that could contain unconverted patterns are scanned.
        for rel_path, content in companion_files.items():
            file_path = Path(rel_path)
            suffix = file_path.suffix.lower()
            if suffix not in _YAML_EXTENSIONS:
                # Includes .md, .txt, .rst, and any other text extensions —
                # all received body rules and must not have unconverted patterns
                _scan_for_source_patterns(content, rel_path)

        # --- Step 6: Return result ---
        return ConvertedSkill(
            name=name,
            description=description,
            output_dir_name=output_dir_name,
            skill_md_content=skill_md_converted,
            companion_files=companion_files,
        )
