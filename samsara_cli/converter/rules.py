"""
Transformation Rules Engine — scoped regex/literal pattern replacement.

Design decisions and assumptions:
- Rules are applied in the order they appear in the list (config-defined order).
  Each rule's output becomes the next rule's input. Order is deterministic.
- Rules are scoped: 'body' rules only transform body text; 'frontmatter' rules
  only transform frontmatter text. Scope is enforced by splitting the document
  before applying any rule.
- Literal rules use str.replace() — no regex interpretation of metacharacters.
  This means '.' is a literal period, not a wildcard; '*' is a literal asterisk.
  Side effect: substring matching (e.g., 'Edit tool' matches inside 'Multi-Edit tool').
  This is documented in the scar report as a known shortcut.
- Regex rules use re.sub() — full Python regex semantics, including capture groups.
  Backreferences in replace strings use \\1, \\2 etc. (Python re.sub convention).

Frontmatter parsing:
- Valid frontmatter: document starts with '---\\n' (line 1 is exactly '---'),
  and there is a second '---' line somewhere after it.
- Opening '---' must be the very first line. If it is not, the document has no
  frontmatter — the entire text is treated as body.
- The closing '---' is the FIRST occurrence of a line matching '---' after line 1.
  This prevents the engine from treating Markdown horizontal rules ('---') deep
  in the body as frontmatter boundaries.
- Edge case: a document starting with '---' but having no closing '---' is treated
  as having no frontmatter (entire text is body). This avoids silently treating the
  entire document as frontmatter.

Assumption: apply() is called with scope='body' or scope='frontmatter'.
  The caller (converter modules) is responsible for which scope to apply.
  If called with scope='body', only body-scoped rules in the list run.
  If called with scope='frontmatter', only frontmatter-scoped rules run.
  This allows a caller to run all rules in one pass or split into two passes —
  both patterns produce correct output.

If this assumption breaks (caller passes unknown scope), the engine currently
silently returns text unchanged (no rules match). This is a known shortcut
documented in the scar report.
"""

import re
from dataclasses import dataclass

from samsara_cli.config.schema import TransformationRule


@dataclass
class _ParsedDocument:
    """Internal representation of a split document.

    Attributes:
        has_frontmatter: True if the document had a valid frontmatter block.
        frontmatter: The frontmatter text (between the two --- delimiters),
                     including the trailing newline but NOT the --- markers.
                     Empty string if has_frontmatter is False.
        body: The body text (everything after the closing --- delimiter and
              its trailing newline). If has_frontmatter is False, this is
              the entire document text.
        opening_delimiter: The opening '---\\n' string, preserved for reassembly.
        closing_delimiter: The closing '---\\n' string, preserved for reassembly.
    """

    has_frontmatter: bool
    frontmatter: str
    body: str
    opening_delimiter: str = "---\n"
    closing_delimiter: str = "---\n"


def _parse_document(text: str) -> _ParsedDocument:
    """Split text into frontmatter and body sections.

    Frontmatter detection rules:
    1. Document must start with '---' on the very first line (no leading spaces).
    2. There must be a second line starting with '---' after the first.
    3. The closing delimiter is the FIRST '---' line found after line 1.
       (Lines in the body with '---' as Markdown horizontal rules are ignored.)

    If either condition fails, the entire document is body (no frontmatter).

    Args:
        text: Raw document text.

    Returns:
        _ParsedDocument with frontmatter and body correctly split.
    """
    if not text:
        return _ParsedDocument(has_frontmatter=False, frontmatter="", body="")

    lines = text.splitlines(keepends=True)

    # Condition 1: First line must be exactly '---' (with optional trailing newline)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return _ParsedDocument(has_frontmatter=False, frontmatter="", body=text)

    # Find the closing '---' delimiter — first '---' line after line index 0
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            closing_idx = i
            break

    # Condition 2: Must have a closing delimiter
    if closing_idx is None:
        return _ParsedDocument(has_frontmatter=False, frontmatter="", body=text)

    # Extract sections
    opening_delimiter = lines[0]
    frontmatter_lines = lines[1:closing_idx]
    closing_delimiter = lines[closing_idx]
    body_lines = lines[closing_idx + 1 :]

    frontmatter = "".join(frontmatter_lines)
    body = "".join(body_lines)

    return _ParsedDocument(
        has_frontmatter=True,
        frontmatter=frontmatter,
        body=body,
        opening_delimiter=opening_delimiter,
        closing_delimiter=closing_delimiter,
    )


def _reassemble(parsed: _ParsedDocument) -> str:
    """Reassemble a parsed document back into a single string.

    Args:
        parsed: A _ParsedDocument (possibly with modified frontmatter or body).

    Returns:
        Complete document text with original delimiters restored.
    """
    if not parsed.has_frontmatter:
        return parsed.body

    return (
        parsed.opening_delimiter
        + parsed.frontmatter
        + parsed.closing_delimiter
        + parsed.body
    )


def _apply_single_rule(text: str, rule: TransformationRule) -> str:
    """Apply a single transformation rule to text.

    Args:
        text: The text to transform (already scoped — only the relevant section).
        rule: The transformation rule to apply.

    Returns:
        Transformed text.

    Implementation notes:
    - literal: uses str.replace() — exact substring match, no metacharacter
      interpretation. All occurrences are replaced.
    - regex: uses re.sub() — full Python regex semantics. Backreferences
      in replace string (\\1, \\2) are handled by re.sub natively.
    """
    if rule.type == "literal":
        return text.replace(rule.match, rule.replace)
    else:
        # type == "regex"
        return re.sub(rule.match, rule.replace, text)


class RulesEngine:
    """Engine for applying scoped transformation rules to document text.

    This engine is stateless — it holds no per-document state. Each call to
    apply() is independent. Safe to use across multiple documents.

    Usage:
        engine = RulesEngine()
        transformed_body = engine.apply(text, rules, scope="body")
        transformed_fm = engine.apply(text, rules, scope="frontmatter")

    The same engine instance can be reused for multiple apply() calls.
    """

    def apply(
        self,
        text: str,
        rules: list[TransformationRule],
        scope: str,
    ) -> str:
        """Apply transformation rules to the specified scope of a document.

        Rules are filtered by scope: only rules where rule.scope == scope are
        applied. Rules are applied in list order — each rule's output is the
        next rule's input.

        Scope isolation:
        - scope='body': Parse the document, apply rules only to body text,
          reassemble. Frontmatter is passed through unchanged.
        - scope='frontmatter': Parse the document, apply rules only to
          frontmatter text, reassemble. Body is passed through unchanged.

        If the document has no frontmatter, the entire text is treated as body.
        A frontmatter-scoped rule applied to a document without frontmatter
        finds an empty string to transform — the body is returned unchanged.

        Args:
            text: Document text (may contain frontmatter + body).
            rules: List of TransformationRule objects. Order is preserved.
            scope: Which document section to target ('body' or 'frontmatter').
                   Only rules with matching rule.scope are executed.

        Returns:
            Complete document text with transformations applied to the scoped
            section. Structure (frontmatter delimiters, etc.) is preserved.

        Raises:
            ValueError: If scope is not 'body' or 'frontmatter'. This is an
                explicit guard against silent failures from scope typos in callers.

        This method will NOT raise for:
        - Empty text (returns "")
        - Empty rules list (returns text unchanged)
        - Rules with no match in the text (returns text unchanged)
        - Text with no frontmatter when body rules are applied (treats entire
          text as body)
        """
        _VALID_SCOPES = ("body", "frontmatter")
        if scope not in _VALID_SCOPES:
            raise ValueError(
                f"Invalid scope {scope!r}. Must be one of {_VALID_SCOPES}. "
                "A typo here would silently skip all rules — explicit error is safer."
            )

        if not text:
            return text

        # Filter rules to only those matching the requested scope
        scoped_rules = [r for r in rules if r.scope == scope]
        if not scoped_rules:
            return text

        # Parse document into sections
        parsed = _parse_document(text)

        # Select the target section to transform
        if scope == "body":
            target = parsed.body
        else:
            # scope == 'frontmatter'
            target = parsed.frontmatter

        # Apply rules in order — each rule sees the previous rule's output
        for rule in scoped_rules:
            target = _apply_single_rule(target, rule)

        # Write the transformed section back
        if scope == "body":
            parsed.body = target
        else:
            parsed.frontmatter = target

        return _reassemble(parsed)
