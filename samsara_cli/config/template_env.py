"""
Jinja2 environment factory for samsara_cli template rendering.

CRITICAL: All template rendering MUST use StrictUndefined.

Without StrictUndefined, a template referencing {{ developer_instructions }}
when the variable is absent silently renders an empty string. The output file
looks syntactically valid (a TOML with an empty developer_instructions = "")
but is semantically broken — the agent has no instructions.

The user would see a generated file with no errors, run Codex, and wonder why
the agent does nothing. The damage: every agent file in the batch conversion
has empty instructions, all of them deployed silently.

With StrictUndefined, the same missing variable raises UndefinedError at render
time. The conversion fails loudly for the specific file that's missing the field.

This module is imported by conversion tasks (Task 2+). It is NOT optional.
Do not replace StrictUndefined with Undefined or DebugUndefined in production.

Acceptance criteria covered:
- "Template rendering with missing field" → StrictUndefined raises, not silently
  renders empty.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Absolute path to the templates directory.
# This file is samsara_cli/config/template_env.py
# Templates are in samsara_cli/config/templates/
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template_env(platform: str) -> Environment:
    """Get a Jinja2 environment for the given platform's templates.

    Args:
        platform: Platform name (e.g., "codex"). Must have a corresponding
                  subdirectory under samsara_cli/config/templates/.

    Returns:
        Environment: Jinja2 environment with StrictUndefined and the platform's
                     template directory as the loader search path.

    Raises:
        FileNotFoundError: If the platform template directory does not exist.
        jinja2.UndefinedError: At render time if a template variable is missing.
                               This is intentional — missing variables are bugs.

    This design assumes: each platform has its own template directory.
    If a platform shares templates with another, symlinks or explicit path
    configuration should be used — NOT disabling StrictUndefined.
    """
    template_dir = _TEMPLATES_DIR / platform
    if not template_dir.is_dir():
        raise FileNotFoundError(
            f"Template directory not found for platform '{platform}': {template_dir}. "
            "Create the directory and add the required Jinja2 templates."
        )
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        undefined=StrictUndefined,
        # Keep trailing newlines in templates — important for TOML/JSON formatting.
        keep_trailing_newline=True,
        # Trim leading whitespace on block tags ({% %}) for cleaner output.
        trim_blocks=True,
        lstrip_blocks=True,
    )
