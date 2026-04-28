"""
Hook Converter — Script output and hooks.json adaptation for Codex.

Converts Claude Code hook artifacts to Codex format:
  - Hook scripts: renders hook.sh.j2 template with Codex-specific variables.
    The rendered script uses 'systemMessage' JSON output, not Claude Code's
    'hookSpecificOutput.additionalContext'. This difference is SILENT on failure —
    Codex ignores unrecognized output fields without error.
  - hooks.json: renders hooks.json.j2 template using Codex matchers from platform
    config (startup, resume) instead of Claude Code's (startup, clear, compact).

Design assumptions:
  1. platform_config.formats.hook_output is a dict with keys:
     - 'session_start_matchers': list[str]
     - 'context_injection_field': str (expected: 'systemMessage')
     - 'template': str (hooks.json.j2)
     - 'script_template': str (hook.sh.j2)
     If any required key is missing, KeyError is raised immediately (no silent default).
  2. platform_config.paths is not None and paths.plugin_dir is set.
     If paths is None, AttributeError is raised — this is intentional.
  3. platform_config.paths.skills_dir is set (may be None for some platforms).
     If None, skills_dir defaults to 'skills' with a logged warning.
  4. The template variables passed to hooks.json.j2 are:
     - session_start_matchers: list[str]
     - hooks_dir: str (path to hooks scripts dir)
     - system_message: str
  5. The template variables passed to hook.sh.j2 are:
     - hook_name: str
     - event: str
     - plugin_dir: str
     - skills_dir: str

If assumption 1 breaks (missing key), KeyError is raised at access time — not silent.
If assumption 2 breaks (paths is None), AttributeError propagates — not silent.
If assumption 4 or 5 breaks (template variable name mismatch), Jinja2 StrictUndefined
raises UndefinedError at render time — not silent.

Known gap: check-codebase-map hook references ${CLAUDE_PROJECT_DIR} which has no
verified Codex equivalent. The generated script via hook.sh.j2 does NOT replicate
the codebase-map logic — it only generates a structural placeholder. This is
documented in the scar report as a known shortcut.

This design assumes: all-or-nothing. Partial conversion is worse than no conversion.
Any missing required config raises immediately — no fallbacks.
"""

import json
import logging
from typing import Any

from jinja2 import Template

from samsara_cli.config.schema import PlatformConfig

logger = logging.getLogger(__name__)

# Default system message for Codex hook context injection.
# This is a structural placeholder — it identifies samsara is active.
# The actual bootstrap content would be injected by the running hook script.
_DEFAULT_SYSTEM_MESSAGE = (
    "You are operating under the Samsara framework (向死而驗). "
    "Samsara provides structured skills for code review, planning, iteration, "
    "and implementation. Follow the samsara protocols for all tasks."
)


def _extract_hook_output_config(platform_config: PlatformConfig) -> dict[str, Any]:
    """Extract and validate the hook_output config dict from platform config.

    Args:
        platform_config: Validated PlatformConfig.

    Returns:
        The hook_output dict from formats config.

    Raises:
        ValueError: If formats or hook_output is missing from config.

    This guard is explicit — a missing hook_output silently producing no hooks
    would be worse than a loud failure here.
    """
    if platform_config.formats is None:
        raise ValueError(
            "platform_config.formats is None — cannot convert hooks without "
            "format configuration. Ensure the platform YAML has a 'formats:' section "
            "with a 'hook_output:' subsection."
        )
    if platform_config.formats.hook_output is None:
        raise ValueError(
            "platform_config.formats.hook_output is None — cannot convert hooks. "
            "Ensure the platform YAML's 'formats.hook_output' section is populated "
            "with 'session_start_matchers', 'template', and 'script_template'."
        )
    return platform_config.formats.hook_output


def _get_plugin_dir(platform_config: PlatformConfig) -> str:
    """Extract plugin_dir from platform config paths.

    Args:
        platform_config: Validated PlatformConfig.

    Returns:
        Plugin directory path string.

    Raises:
        ValueError: If paths or plugin_dir is not set.

    Rationale: An absent plugin_dir would cause the hook script to reference
    an empty path, silently breaking all plugin file lookups.
    """
    if platform_config.paths is None:
        raise ValueError(
            "platform_config.paths is None — cannot determine plugin directory. "
            "Ensure the platform YAML has a 'paths:' section with 'plugin_dir'."
        )
    if not platform_config.paths.plugin_dir:
        raise ValueError(
            "platform_config.paths.plugin_dir is empty — cannot generate hook script "
            "with empty PLUGIN_DIR. The script would silently fail to find skills."
        )
    return platform_config.paths.plugin_dir


def _get_skills_dir(platform_config: PlatformConfig) -> str:
    """Extract skills_dir from platform config paths, with fallback warning.

    Args:
        platform_config: Validated PlatformConfig.

    Returns:
        Skills directory name (relative to plugin_dir).

    This is the one place where a fallback is used rather than an error — skills_dir
    is optional in the schema (some platforms may not support skills), and a missing
    value defaults to 'skills' with a warning. This is documented in the scar report.
    """
    if platform_config.paths is None:
        raise ValueError(
            "platform_config.paths is None — cannot determine skills directory."
        )
    skills_dir = platform_config.paths.skills_dir
    if not skills_dir:
        logger.warning(
            "platform_config.paths.skills_dir is not set — defaulting to 'skills'. "
            "If the platform uses a different skills directory, this will silently "
            "point the hook script to the wrong location."
        )
        return "skills"
    return skills_dir


class HookConverter:
    """Converts Claude Code hook artifacts to Codex format.

    This converter handles two artifact types:
    1. Hook shell scripts — rendered via hook.sh.j2 with Codex-specific variables.
       CRITICAL: The rendered script outputs 'systemMessage' JSON, not Claude Code's
       'hookSpecificOutput.additionalContext'. Codex silently ignores the latter.
    2. hooks.json — rendered via hooks.json.j2 with Codex matchers and paths.
       CRITICAL: Matchers must be ['startup', 'resume'] not ['startup', 'clear', 'compact'].

    Usage:
        converter = HookConverter()
        script_content = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=env.get_template("hook.sh.j2"),
        )
        hooks_dict = converter.convert_hooks_json(
            platform_config=codex_config,
            template=env.get_template("hooks.json.j2"),
            system_message="optional custom system message",
        )

    This class is stateless — safe to reuse across multiple conversions.
    """

    def convert_script(
        self,
        hook_name: str,
        event: str,
        platform_config: PlatformConfig,
        template: Template,
    ) -> str:
        """Render a Codex-compatible hook shell script via hook.sh.j2.

        The rendered script is a structural Codex hook that:
        - Sets PLUGIN_DIR to the Codex plugin directory
        - Sources skill env.sh files from SKILLS_DIR
        - Outputs 'systemMessage' JSON (not Claude Code's hookSpecificOutput format)

        Note on ${CLAUDE_PLUGIN_ROOT}: The source hook scripts use this env var,
        which is set by Claude Code's plugin runtime. Codex does NOT set this var.
        This method does NOT read the source script — it renders the hook.sh.j2
        template with Codex config values. The rendered script uses PLUGIN_DIR
        (a literal path from platform config) instead of ${CLAUDE_PLUGIN_ROOT}.

        Note on check-codebase-map: The source check-codebase-map hook checks
        ${CLAUDE_PROJECT_DIR} for map freshness. Codex does not set CLAUDE_PROJECT_DIR.
        For non-session-start hooks (e.g., check-codebase-map), the template renders
        a Codex-compatible hook that outputs 'systemMessage' with a placeholder
        indicating the codebase-map check is not yet adapted for Codex.
        This is an honest behavioral regression documented in the scar report —
        rather than injecting wrong content silently, the script exits 0 with no output
        when the Codex project directory equivalent is not available.

        Args:
            hook_name: The hook's logical name (e.g., "session-start",
                       "check-codebase-map"). Used in the script header comments.
            event: The hook event name (e.g., "session_start"). Used in comments.
            platform_config: Validated PlatformConfig for the target platform.
            template: Jinja2 Template for hook.sh.j2. Must be from a StrictUndefined
                      environment — missing variables raise UndefinedError.

        Returns:
            Rendered bash script string, ready to write to a .sh file.

        Raises:
            ValueError: If platform_config is missing required paths or formats.
            jinja2.UndefinedError: If template references a variable not provided.
        """
        plugin_dir = _get_plugin_dir(platform_config)
        skills_dir = _get_skills_dir(platform_config)

        return template.render(
            hook_name=hook_name,
            event=event,
            plugin_dir=plugin_dir,
            skills_dir=skills_dir,
        )

    def convert_check_codebase_map_script(
        self,
        event: str,
        platform_config: PlatformConfig,
        template: Template,
    ) -> str:
        """Render a Codex-compatible check-codebase-map hook script.

        The source check-codebase-map hook checks ${CLAUDE_PROJECT_DIR} for map
        freshness. Codex does not set CLAUDE_PROJECT_DIR. This method renders a
        hook script that exits 0 silently when CODEX_WORKSPACE is not set,
        avoiding the unbound variable error (set -u) that would occur if the
        original Claude Code env var reference were used.

        This is an intentional behavioral reduction: rather than silently injecting
        wrong content or crashing, the Codex version of this hook is a no-op when
        the project directory env var is unavailable.

        Args:
            event: Hook event name (e.g., "session_start").
            platform_config: Validated PlatformConfig for the target platform.
            template: Jinja2 Template for hook.sh.j2.

        Returns:
            Rendered bash script string for check-codebase-map behavior on Codex.

        Raises:
            ValueError: If platform_config is missing required paths.
        """
        plugin_dir = _get_plugin_dir(platform_config)
        skills_dir = _get_skills_dir(platform_config)

        return template.render(
            hook_name="check-codebase-map",
            event=event,
            plugin_dir=plugin_dir,
            skills_dir=skills_dir,
        )

    def convert_hooks_json(
        self,
        platform_config: PlatformConfig,
        template: Template,
        system_message: str | None = None,
    ) -> dict:
        """Render a Codex-compatible hooks.json and return as a Python dict.

        CRITICAL: This method uses matchers from platform_config.formats.hook_output,
        NOT from the source hooks.json file. This ensures Codex-specific event names
        ('startup', 'resume') replace Claude Code's ('startup', 'clear', 'compact').

        The returned dict has the structure required by Codex:
        {
            "hooks": [
                {
                    "name": "samsara-session-start",
                    "event": "session_start",
                    "matchers": ["startup", "resume"],
                    "command": "<plugin_dir>/hooks/samsara-session-start.sh",
                    "systemMessage": "..."
                }
            ]
        }

        Note on output format: Codex hooks.json uses 'systemMessage' at the hook
        entry level. Claude Code hooks.json does not have this field. If a template
        produces 'additionalContext' or 'hookSpecificOutput' instead, Codex silently
        ignores the context injection.

        Args:
            platform_config: Validated PlatformConfig for the target platform.
            template: Jinja2 Template for hooks.json.j2. Must be from a StrictUndefined
                      environment — missing variables raise UndefinedError.
            system_message: Optional custom system message string. If not provided,
                            uses the default samsara framework description.
                            Pass a Python string — do NOT pre-escape for JSON. Jinja2's
                            tojson filter handles all escaping. Pre-escaping would cause
                            double-escape and produce broken JSON.

        Returns:
            Python dict representing the hooks.json content. Use json.dumps() to
            serialize to a file. Returning a dict (not a string) ensures the caller
            can validate structure before writing.

        Raises:
            ValueError: If platform_config is missing required formats or paths.
            KeyError: If hook_output config dict is missing required keys.
            jinja2.UndefinedError: If template references a variable not provided.
            json.JSONDecodeError: If rendered template is not valid JSON (indicates
                                  template corruption or unexpected content).
        """
        hook_output_config = _extract_hook_output_config(platform_config)
        plugin_dir = _get_plugin_dir(platform_config)

        # Extract matchers from platform config — NOT from source hooks.json.
        # Claude Code matchers: ["startup", "clear", "compact"]
        # Codex matchers: ["startup", "resume"] (from codex.yaml)
        # Accessing a missing key raises KeyError immediately — this is intentional.
        session_start_matchers: list[str] = hook_output_config["session_start_matchers"]

        if not session_start_matchers:
            raise ValueError(
                "hook_output.session_start_matchers is empty in platform config. "
                "An empty matchers list means the hook will never fire — this is a "
                "silent failure. Add at least one matcher (e.g., 'startup')."
            )

        # Validate no Claude Code matchers leaked through
        claude_code_only_matchers = {"clear", "compact"}
        leaked = set(session_start_matchers) & claude_code_only_matchers
        if leaked:
            raise ValueError(
                f"Claude Code-specific matchers found in session_start_matchers: {leaked}. "
                "These matchers ('clear', 'compact') are Claude Code session events — "
                "Codex does not fire on them. Remove them from the platform config or "
                "this is a config error. Codex uses 'startup' and 'resume'."
            )

        # Build hooks directory path: platform plugin_dir + "/hooks"
        # This is where the rendered hook scripts will be placed.
        hooks_dir = f"{plugin_dir}/hooks"

        # Use provided system_message or fall back to default.
        # IMPORTANT: Do NOT pre-escape. Jinja2's tojson filter handles escaping.
        # Pre-escaping causes double-escape in the output (\\n becomes \\\\n).
        effective_system_message = system_message or _DEFAULT_SYSTEM_MESSAGE

        rendered = template.render(
            session_start_matchers=session_start_matchers,
            hooks_dir=hooks_dir,
            system_message=effective_system_message,
        )

        # Parse rendered JSON into a Python dict.
        # If the template produces invalid JSON, this raises json.JSONDecodeError
        # immediately — loud failure, not a silently written broken file.
        try:
            return json.loads(rendered)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Rendered hooks.json.j2 is not valid JSON: {e.msg}. "
                "This indicates a template rendering error or unexpected content "
                "in template variables. Check that system_message does not contain "
                "raw control characters outside of a Python string context.",
                e.doc,
                e.pos,
            ) from e
