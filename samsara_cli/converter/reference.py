"""
ReferenceConverter — Apply transformation rules to reference markdown files.

Critical design requirement: tool name references inside fenced code blocks
MUST NOT be transformed. The same references in prose MUST be transformed.

The RulesEngine (Task 2) has no awareness of Markdown code blocks. If called
on the full text, it will transform tool names inside fenced code blocks.
This module implements code block extraction/protection before rule application.

Code block protection approach:
1. Split text into alternating segments: [prose, code_block, prose, code_block, ...]
2. Apply rules only to prose segments using RulesEngine.
3. Reassemble in original order.

What counts as a fenced code block:
- Opening fence: a line beginning with ``` (triple backtick), optionally followed
  by a language tag (```yaml, ```python, etc.)
- Closing fence: a line beginning with ``` on its own (or with only whitespace after)
- Content: everything between opening and closing fences, inclusive of the fence lines.

What is NOT protected:
- Inline code spans using single backticks: `Read tool`
  These are prose-level formatting and receive rule application.
- Indented code blocks (4-space indent): these are NOT protected.
  Documented as known shortcut — triple-backtick blocks only.

Unclosed code block behavior:
- A ``` that opens but never closes: text from the opening fence to end-of-file
  is treated as inside a code block (protected from rules).
  Rationale: under-converting (not transforming code) is safer than
  over-converting (transforming what should be preserved).

Design assumes:
- Input is UTF-8 text. Binary files must not be passed to convert().
- Rules with scope='body' are the relevant rules. Frontmatter-scoped rules
  in the rules list are passed to RulesEngine which will filter them by scope.
  Since reference .md files have no frontmatter (assumption), this is fine.
  If reference files ever gain frontmatter, the frontmatter would be treated
  as body (RulesEngine body-scope path handles no-frontmatter documents as
  whole-body). Documented in scar report.

If this design assumption breaks (reference files gain YAML frontmatter that
must NOT be rule-transformed), the first to rot is: frontmatter content being
incorrectly processed by body-scope rules.
"""

import re
from pathlib import Path

from samsara_cli.config.schema import TransformationRule
from samsara_cli.converter.rules import RulesEngine

# Pattern matching the opening line of a fenced code block.
# Matches lines starting with ``` (possibly with language tag after).
# The fence can start at column 0 only — we don't handle indented fences.
_FENCE_OPEN_RE = re.compile(r"^```", re.MULTILINE)

# Pattern matching a closing fence line — ``` at start of line, nothing else
# (other than optional whitespace) on that line.
_FENCE_CLOSE_RE = re.compile(r"^```\s*$", re.MULTILINE)


def _split_into_segments(text: str) -> list[tuple[str, bool]]:
    """Split text into alternating prose and code-block segments.

    Returns a list of (segment_text, is_code_block) tuples.
    Segments alternate: prose, code_block, prose, code_block, ...
    The list always starts with a prose segment (which may be empty string).

    Fenced code blocks are detected by ``` at the start of a line.
    Opening fence: line starting with ``` (may have language tag).
    Closing fence: line that is exactly ``` (with optional trailing whitespace).

    Unclosed block behavior: if an opening fence has no closing fence,
    all text from the opening fence to end-of-file is treated as a code block.

    Args:
        text: The full reference file text.

    Returns:
        List of (segment_text, is_code_block) tuples in document order.
        Concatenating all segment_text values reconstructs the original text exactly.

    Implementation notes:
    - We iterate over lines to find fence boundaries.
    - Once inside a code block, we look for a closing ``` on its own line.
    - The fence lines themselves are included in the code block segment,
      so the output reassembles to the exact original text.
    """
    if not text:
        return [("", False)]

    segments: list[tuple[str, bool]] = []
    lines = text.splitlines(keepends=True)
    i = 0
    current_prose_lines: list[str] = []

    while i < len(lines):
        line = lines[i]

        # Detect an opening fence: line starts with ```
        if line.startswith("```"):
            # Flush accumulated prose as a prose segment
            prose = "".join(current_prose_lines)
            segments.append((prose, False))
            current_prose_lines = []

            # Start collecting the code block (fence line included)
            code_block_lines: list[str] = [line]
            i += 1

            # Find closing fence: a line that is exactly ``` (+ optional whitespace)
            while i < len(lines):
                code_block_lines.append(lines[i])
                # Check if this line is a closing fence
                if lines[i].rstrip("\r\n").rstrip() == "```":
                    i += 1
                    break
                i += 1

            # If no closing fence found, the remaining text was consumed into
            # the code block (unclosed block — protect from rules)
            code_block = "".join(code_block_lines)
            segments.append((code_block, True))

        else:
            # Regular prose line
            current_prose_lines.append(line)
            i += 1

    # Flush any remaining prose
    if current_prose_lines:
        segments.append(("".join(current_prose_lines), False))

    return segments


class ReferenceConverter:
    """Convert reference markdown files by applying body transformation rules.

    Code blocks are protected from rule application. Prose sections receive
    rules applied via RulesEngine.

    This converter is stateless — it holds no per-file state. Each call to
    convert() or convert_text() is independent.
    """

    def __init__(self) -> None:
        self._engine = RulesEngine()

    def convert_text(self, text: str, rules: list[TransformationRule]) -> str:
        """Apply transformation rules to text with code block protection.

        Prose sections receive body-scoped rules. Fenced code block sections
        are passed through unchanged.

        Args:
            text: Reference file content (markdown text).
            rules: Transformation rules to apply. Only scope='body' rules
                   will actually transform text (RulesEngine filters by scope).
                   Frontmatter-scoped rules in the list are silently skipped
                   by the rules engine when applying to body scope.

        Returns:
            Transformed text. Code block content is preserved verbatim.
            Prose sections have matching rules applied.
            Empty input returns empty string.
        """
        if not text:
            return text

        if not rules:
            return text

        # Split into prose/code-block segments
        segments = _split_into_segments(text)

        # Apply rules only to prose segments
        result_parts: list[str] = []
        for segment_text, is_code_block in segments:
            if is_code_block:
                # Code block: pass through unchanged
                result_parts.append(segment_text)
            else:
                # Prose: apply body-scoped rules via RulesEngine
                if segment_text:
                    transformed = self._engine.apply(segment_text, rules, scope="body")
                    result_parts.append(transformed)
                else:
                    result_parts.append(segment_text)

        return "".join(result_parts)

    def convert(self, source_ref: Path, rules: list[TransformationRule]) -> str:
        """Read source reference file and apply transformation rules.

        Args:
            source_ref: Path to source reference markdown file.
            rules: Transformation rules to apply.

        Returns:
            Transformed text as string.

        Raises:
            FileNotFoundError: If source_ref does not exist.
        """
        if not source_ref.exists():
            raise FileNotFoundError(
                f"Source reference file not found: {source_ref}. "
                "The source reference file must exist before conversion."
            )

        text = source_ref.read_text(encoding="utf-8")
        return self.convert_text(text, rules)
