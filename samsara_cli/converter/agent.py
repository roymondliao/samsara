"""
AgentConverter -- Markdown to TOML format conversion for Codex agents.

Converts Claude Code agent .md files to Codex .toml format via Jinja2 template.

Design decisions:
- All-or-nothing: empty body raises ValueError immediately. Partial conversion is
  worse than no conversion because a silently empty developer_instructions deploys
  an agent that appears valid but does nothing.
- Triple-quote escaping: TOML basic multiline strings allow backslash escapes.
  Any triple-double-quote in the body is replaced with backslash-escaped equivalents
  before embedding. Without this, the TOML parser terminates the string early.
- Rules applied before embedding: transformation rules run on the body BEFORE it
  is embedded in the TOML template. The template receives the already-transformed body.
- Source path separation: convert() takes an already-extracted body (caller did
  frontmatter parsing). convert_from_text() handles the full flow including
  frontmatter stripping.

Assumptions:
- Body text is valid UTF-8. (Consequence if false: read_text() would have already raised.)
- NamingConfig.separator + skill_prefix + stem produces a unique, valid agent name.
  (If two agents have the same stem after normalization, one will silently overwrite
  the other at the filesystem level. This is detected only at deployment.)
- The agent.toml.j2 template uses StrictUndefined -- missing required variables
  raise UndefinedError immediately, not silently. (Verified: template_env.py enforces this.)
- TOML basic multiline strings accept backslash-escaped double quotes.
  (Verified: TOML 1.0 spec allows \" inside multiline basic strings.)

Silent failure conditions (after implementation):
- If a rule's regex has a capture group side effect that modifies the triple-quote
  escape sequence, the escaping protection breaks silently. Mitigation: escaping
  runs AFTER rules are applied.
- If the template changes the variable name for developer_instructions (e.g., renamed),
  StrictUndefined will raise at render time -- this is detectable, not silent.
- If the Jinja2 trim_blocks setting changes, whitespace in developer_instructions
  may silently shift. This produces valid TOML but different content.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Template

from samsara_cli.config.schema import NamingConfig, TransformationRule
from samsara_cli.converter.rules import RulesEngine


@dataclass
class ConvertedAgent:
    """Result of a successful agent conversion.

    Attributes:
        agent_name: The generated name for the agent (e.g., "samsara-code-reviewer").
                    This must match the name used in skill dispatch references.
        toml_content: The fully rendered TOML string ready to write to disk.
        transformed_body: The body text AFTER rules have been applied but BEFORE
                          TOML embedding (useful for debugging and testing rule application).
        description: Single-line description extracted from the body (first H1 or
                     first non-empty line). May be None if extraction fails.
    """

    agent_name: str
    toml_content: str
    transformed_body: str
    description: str | None = None


def _strip_frontmatter(text: str) -> str:
    """Extract body from a document that may have YAML frontmatter.

    Frontmatter detection:
    - Document must start with '---' on the first line.
    - A second '---' line must exist somewhere after the first.
    - The closing '---' is the first such line after line 0.
    - If either condition fails, the entire text is returned as body.

    Args:
        text: Raw source file text.

    Returns:
        Body text only (everything after the closing --- delimiter and its newline).
        If no frontmatter, the entire input text is returned.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            return "".join(lines[i + 1 :])
    # Opening --- found but no closing --- -- treat as no frontmatter
    return text


def _extract_description(body: str) -> str | None:
    """Extract a single-line description from the agent body.

    Strategy (in order):
    1. If the first non-empty line starts with '#', use the heading text (strip '#' and spaces).
    2. Otherwise, use the first non-empty line as-is (truncated to 200 chars if needed).

    This is a heuristic. Known edge cases:
    - Some agents have a blank line before the first heading.
    - Some have multiple '#' markers (e.g., '## Section').
    - The heuristic uses the FIRST non-empty line, which may be a section heading deep
      in the document if the body starts with blank lines.

    Args:
        body: The agent body text (post-frontmatter-strip, pre-rule-application).

    Returns:
        Single-line description string, or None if body is empty after stripping.
    """
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Remove Markdown heading markers
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        # Plain prose line -- use as-is, truncated if very long
        if len(stripped) > 200:
            return stripped[:197] + "..."
        return stripped
    return None


def _escape_for_toml_multiline(text: str) -> str:
    """Escape content for safe embedding in a TOML basic multiline string.

    TOML basic multiline strings are delimited by triple-double-quotes and
    process backslash escape sequences. Two characters need escaping:

    1. Backslashes ('\\') -- must be doubled ('\\\\') because TOML interprets
       any '\\' as the start of an escape sequence. An invalid sequence like
       '\\U' (for Windows paths like C:\\Users) raises TOMLDecodeError.
       Escape order: backslashes FIRST, before any other substitution.

    2. Triple-double-quotes ('\"\"\"') -- terminate the multiline string early.
       Replace with three individually-escaped double quotes ('\\"\\"\\"').
       Must be done AFTER backslash escaping so the replacement backslashes
       are not themselves double-escaped.

    Args:
        text: Body text to embed in a TOML basic multiline string.

    Returns:
        Text safe for direct embedding between triple-double-quote delimiters.

    Note on roundtrip: the TOML parser decodes the escaped sequences back to
    the original characters, so the content retrieved via tomllib.loads() will
    match the original text.
    """
    # Step 1: Escape backslashes (must come first)
    escaped = text.replace("\\", "\\\\")
    # Step 2: Escape triple-double-quotes (must come after backslash escaping)
    escaped = escaped.replace('"""', '\\"\\"\\"')
    return escaped


def _build_agent_name(source_path: Path, naming: NamingConfig) -> str:
    """Build the agent name from the source file path and naming config.

    Name format: {skill_prefix}{separator}{filename_stem}

    Args:
        source_path: Path to the source .md file.
        naming: NamingConfig with skill_prefix and separator.

    Returns:
        Agent name string (e.g., "samsara-code-reviewer").
    """
    stem = source_path.stem  # e.g., "code-reviewer" from "code-reviewer.md"
    return f"{naming.skill_prefix}{naming.separator}{stem}"


class AgentConverter:
    """Converts Claude Code agent .md files to Codex .toml format.

    This class is stateless -- each convert() call is independent.
    The same instance can be reused across multiple files.

    The conversion pipeline per agent:
    1. Validate inputs (empty body raises ValueError)
    2. Apply transformation rules to the body via RulesEngine
    3. Escape the transformed body for TOML multiline string embedding
    4. Extract description from the original body (pre-rules)
    5. Build agent name from source_path and NamingConfig
    6. Render via Jinja2 template (StrictUndefined -- missing vars raise)
    7. Return ConvertedAgent with all artifacts

    Note: rules are applied to the body text wrapped in a synthetic document
    (body only, no frontmatter). RulesEngine.apply() with scope='body'
    handles this correctly -- if no frontmatter is present, the entire text
    is treated as the body.

    Assumption: this class applies body-scoped rules only. Frontmatter rules
    in the rules list are silently skipped (RulesEngine filters by scope).
    If a frontmatter rule is accidentally passed here, it has no effect on
    the body. This is safe but potentially confusing -- documented as a known
    behavior.
    """

    def __init__(self) -> None:
        self._rules_engine = RulesEngine()

    def convert(
        self,
        body: str,
        source_path: Path,
        rules: list[TransformationRule],
        naming: NamingConfig,
        template: Template,
    ) -> ConvertedAgent:
        """Convert an agent body (already extracted from .md) to Codex .toml.

        Args:
            body: The agent's instruction body (raw markdown, no frontmatter).
            source_path: Original source file path (used for name generation and
                         template source_path variable).
            rules: List of TransformationRule objects to apply. Body-scoped rules
                   are applied; others are skipped silently by RulesEngine.
            naming: NamingConfig controlling prefix and separator.
            template: Jinja2 Template object (from get_template_env("codex")).

        Returns:
            ConvertedAgent with agent_name, toml_content, transformed_body, description.

        Raises:
            ValueError: If body is empty (after stripping whitespace).
            jinja2.UndefinedError: If a required template variable is missing.
                                   (Should not happen with correct implementation, but
                                   will raise loudly if template changes break the contract.)
        """
        if not body or not body.strip():
            raise ValueError(
                f"Agent body is empty for source file: {source_path}. "
                "Cannot convert an agent with no instructions -- this would produce a "
                "silently broken agent with empty developer_instructions."
            )

        # Guard: detect if caller passed raw source text (with frontmatter) to convert()
        # instead of the already-stripped body. This is a caller mistake; failing loudly
        # here is better than silently embedding '---\nname: ...\n---' in TOML.
        # Only checks the very first line to keep cost O(1).
        first_line = body.splitlines()[0].rstrip("\r\n") if body.splitlines() else ""
        if first_line == "---":
            raise ValueError(
                f"Agent body appears to still contain frontmatter (starts with '---') "
                f"for source file: {source_path}. "
                "Use convert_from_text() to handle frontmatter stripping, or call "
                "_strip_frontmatter(body) before passing to convert()."
            )

        # Extract description from original body (before rules change content)
        description = _extract_description(body)

        # Build agent name
        agent_name = _build_agent_name(source_path, naming)

        # Apply body-scoped transformation rules
        # RulesEngine.apply() expects a complete document. Since body has no frontmatter,
        # the entire text is treated as body by the engine.
        transformed_body = self._rules_engine.apply(body, rules, scope="body")

        # Escape transformed body for TOML multiline string embedding
        # Must run AFTER rules so that rules cannot accidentally re-introduce
        # triple-quote sequences that bypass the escaping.
        escaped_body = _escape_for_toml_multiline(transformed_body)

        # Render via Jinja2 template
        # StrictUndefined means any missing variable raises UndefinedError immediately.
        toml_content = template.render(
            name=agent_name,
            developer_instructions=escaped_body,
            source_path=str(source_path),
        )

        # Self-validate: parse the rendered output with tomllib.
        # This catches template changes that produce invalid TOML and any escaping
        # gaps that survived the escaping step. All-or-nothing: better to fail loudly
        # here than to write a broken .toml file to disk.
        try:
            tomllib.loads(toml_content)
        except Exception as e:
            raise ValueError(
                f"Rendered TOML output failed TOML parse validation for {source_path}. "
                f"This is a bug in the conversion pipeline (escaping or template). "
                f"TOML error: {e}"
            ) from e

        return ConvertedAgent(
            agent_name=agent_name,
            toml_content=toml_content,
            transformed_body=transformed_body,
            description=description,
        )

    def convert_from_text(
        self,
        source_text: str,
        source_path: Path,
        rules: list[TransformationRule],
        naming: NamingConfig,
        template: Template,
    ) -> ConvertedAgent:
        """Convert a full agent .md file (including frontmatter) to Codex .toml.

        This is a convenience wrapper that strips frontmatter before calling convert().
        Use this when you have the raw file contents (e.g., from Path.read_text()).

        Args:
            source_text: Full .md file text (may include YAML frontmatter).
            source_path: Source file path (for name generation).
            rules: Transformation rules (body-scoped rules applied).
            naming: NamingConfig.
            template: Jinja2 Template.

        Returns:
            ConvertedAgent (same as convert()).

        Raises:
            ValueError: If the body (after frontmatter strip) is empty.
        """
        body = _strip_frontmatter(source_text)
        return self.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )
