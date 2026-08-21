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
- Live-surface exclusion (_LIVE_SURFACE_EXCLUDED_TOP_LEVEL_DIRS, ISSUE-002/SS-1)
  matches by exact top-level path SEGMENT via string equality, not resolved
  path identity. A symlink whose target lies outside the excluded subtree
  (or an excluded directory that is itself a symlink to a live-surface path)
  is not specially handled — the check only looks at the syntactic first
  path segment under output_dir. This is a known shortcut: acceptable
  because the exclusion targets a small, fixed, repo-controlled set of
  top-level directory names, not arbitrary/untrusted input.

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
5. The four live-surface-excluded top-level directories (changes/, docs/,
   bugfix/, tests/) are assumed to fully cover the repo's non-live-surface
   noise sources. Verified empirically for this repo: repo-root validate
   dropped from 36 to 11 issues after this exclusion, and all 11 residual
   issues were classified as genuine live-surface findings (references/,
   skills/) — none were unclassified noise. If a new top-level directory is
   added later that holds historical/demonstrative text (not live surface),
   it will need to be added to the constant, or it will re-introduce noise.
"""

import json
import logging
import os
import re
import subprocess
import tomllib
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Pattern that must NOT appear in any output .md file (architecture death case DC-2).
# "invoke `samsara:X`" where X is a word/hyphen skill name.
_INVOKE_SAMSARA_PATTERN = re.compile(r"invoke `samsara:[\w-]+`")

# Pattern that must NOT appear in any output .md file (agent dispatch death case).
# `subagent_type:` is the Claude Code-specific agent dispatch syntax.
_SUBAGENT_TYPE_PATTERN = re.compile(r"subagent_type:")

# Colon-form namespace residue (strict lane only). Codex uses the unprefixed
# SKILL.md.name for skills and a hyphenated name for Samsara agents. Neither
# target identity uses `samsara:X`, so any surviving colon form is dead. This is
# broader than the two legacy patterns above on purpose: enumerating known
# phrasings ("invoke `samsara:X`") missed 94 residues in a live conversion
# (2026-07-07) while still reporting PASS.
# Strict-only because repo-root validation (ISSUE-002 live-surface mode)
# legitimately contains source-form names everywhere.
_SAMSARA_NAMESPACE_PATTERN = re.compile(r"samsara:[\w-]+")

# Pattern for agent name references in companion files (dispatch-template.md).
# Matches 'agent named "X"' where X is the referenced agent name.
_AGENT_REF_PATTERN = re.compile(r'agent named "([^"]+)"')

# File extensions that receive source pattern scanning.
# YAML files are excluded — they may legitimately contain samsara namespace strings.
_SCAN_EXTENSIONS = {".md", ".txt", ".toml", ".sh"}

_SKILL_REF_PATTERN = re.compile(r"\$([a-z][a-z0-9-]*)")
_SKILL_COMPANION_PATTERN = re.compile(
    r"<installed-([a-z0-9-]+)-skill-directory>/([^\s`]+)"
)
_AGENT_COMPANION_PATTERN = re.compile(
    r"<installed-auto-gatekeeper-companion-directory>/([^\s`]+)"
)
_EXPECTED_SESSION_START_MATCHERS = {"startup", "resume", "clear", "compact"}

# Live-surface source-tree scan boundary (SS-1, ISSUE-002).
#
# `samsara-cli validate` defaults --source to the repo root, so
# `_scan_source_patterns`'s rglob("*") walks the ENTIRE repo tree when run
# there — not just converted output. Top-level directories that hold
# historical/demonstrative documentation (changes/, docs/, bugfix/, tests/)
# legitimately contain sample text that matches the source patterns (e.g.
# "invoke `samsara:X`", "subagent_type:") without being a real unconverted
# chain link. Scanning them inflated the issue count with noise no one could
# act on (ISSUE-002: main 42, branch 36 issues, permanently non-zero).
#
# Live instruction surface — skills/, agents/, references/, hooks/,
# .claude-plugin/ — is never excluded here; a genuine leak in those paths
# must still be reported.
#
# This is the ONLY definition of the exclusion list (SD-1, single source of
# truth). The CLI (`samsara-cli validate` in main.py) and any future direct
# caller of TargetValidator.validate() share this exact behavior — do not
# duplicate this set anywhere else.
_LIVE_SURFACE_EXCLUDED_TOP_LEVEL_DIRS = frozenset(
    {"changes", "docs", "bugfix", "tests"}
)

# A colon in an installed skill directory is invalid. The folder is an install
# path such as samsara-research; Codex invocation identity comes from SKILL.md.name.
_COLON_IN_NAME_MSG = (
    "Skill directory '{}' contains a colon — this is the source format (samsara:X), "
    "not a valid Codex install path. Use a filesystem-safe directory name; keep "
    "the invocation ID in SKILL.md.name."
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
        strict_namespace: bool = False,
    ) -> list[str]:
        """Validate the converted output directory.

        Accumulates all validation errors — does not short-circuit on first error.
        Each check runs independently so all issues are visible in one pass.

        Args:
            output_dir: Path to the converted output directory (temp dir or final).
            platform: Target platform name. Defaults to "codex" for backward
                      compatibility with older tests/callers.
            strict_namespace: When True, ANY colon-form `samsara:X` reference in
                      scannable output files is an error (dead reference on the
                      target platform). Use ONLY on converted output — never on
                      the source repo, where colon-form names are the legitimate
                      source format. The conversion engine always passes True.

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

        native_codex_contract = platform == "codex" and (
            (output_dir / ".codex/config.toml").exists()
            or (output_dir / ".codex/hooks.json").exists()
        )
        if native_codex_contract:
            errors.extend(self._validate_codex_layout(output_dir))

        if native_codex_contract:
            errors.extend(self._validate_skill_identity_graph(output_dir, platform))
            errors.extend(self._validate_companion_references(output_dir, platform))

        # --- Check 2: Source pattern scan across all scannable files ---
        pattern_errors = self._scan_source_patterns(
            output_dir, strict_namespace=strict_namespace
        )
        errors.extend(pattern_errors)

        # --- Check 3: TOML file validation ---
        agents_dir = self._get_agents_dir(output_dir, platform)
        if agents_dir.exists():
            if platform == "codex":
                toml_errors = self._validate_toml_files(agents_dir)
                errors.extend(toml_errors)

        # --- Check 4: Agent cross-validation ---
        cross_errors = self._cross_validate_agent_names(
            output_dir, agents_dir, platform
        )
        errors.extend(cross_errors)

        return errors

    def _validate_codex_layout(self, output_dir: Path) -> list[str]:
        """Validate Codex-native files and executable SessionStart seams."""
        errors: list[str] = []
        skills_dir = output_dir / ".agents/skills"
        agents_dir = output_dir / ".codex/agents"
        hooks_path = output_dir / ".codex/hooks.json"
        config_path = output_dir / ".codex/config.toml"

        if not skills_dir.is_dir():
            errors.append("Codex output is missing .agents/skills directory.")
        if not agents_dir.is_dir():
            errors.append("Codex output is missing .codex/agents directory.")
        if not config_path.is_file():
            errors.append("Codex output is missing .codex/config.toml.")
        else:
            try:
                tomllib.loads(config_path.read_text(encoding="utf-8"))
            except (OSError, tomllib.TOMLDecodeError) as exc:
                errors.append(f"Codex config.toml is invalid: {exc}")

        if not hooks_path.is_file():
            errors.append("Codex output is missing .codex/hooks.json.")
            return errors
        try:
            hooks_doc = json.loads(hooks_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Codex hooks.json is invalid: {exc}")
            return errors

        session_start = hooks_doc.get("hooks", {}).get("SessionStart")
        if not isinstance(session_start, list) or not session_start:
            errors.append("Codex hooks.json has no SessionStart entries.")
            return errors

        commands: list[str] = []
        matchers: set[str] = set()
        for entry in session_start:
            if not isinstance(entry, dict):
                errors.append("Codex SessionStart entry must be an object.")
                continue
            matcher = entry.get("matcher")
            if isinstance(matcher, str):
                matchers.update(part for part in matcher.split("|") if part)
            handlers = entry.get("hooks")
            if not isinstance(handlers, list):
                errors.append("Codex SessionStart entry has no hooks list.")
                continue
            for handler in handlers:
                if not isinstance(handler, dict):
                    errors.append("Codex SessionStart handler must be an object.")
                    continue
                command = handler.get("command")
                if not isinstance(command, str) or not command:
                    errors.append("Codex SessionStart handler is missing command.")
                    continue
                commands.append(command)

        if matchers != _EXPECTED_SESSION_START_MATCHERS:
            errors.append(
                "Codex SessionStart matchers must be startup|resume|clear|compact; "
                f"got {sorted(matchers)}."
            )

        basenames = {Path(command).name for command in commands}
        expected_scripts = {"samsara-session-start.sh", "check-codebase-map.sh"}
        if basenames != expected_scripts:
            errors.append(
                f"Codex SessionStart commands must resolve {sorted(expected_scripts)}; "
                f"got {sorted(basenames)}."
            )

        for command in commands:
            if os.path.isabs(command):
                errors.append(
                    f"Converted Codex hook command must be relative: {command!r}."
                )
                continue
            target = output_dir / command
            if not target.is_file():
                errors.append(f"Codex hook command target does not exist: {command}.")
                continue
            if not os.access(target, os.X_OK):
                errors.append(
                    f"Codex hook command target is not executable: {command}."
                )
                continue
            result = subprocess.run(
                [str(target)],
                cwd=output_dir,
                input=json.dumps(
                    {"cwd": str(output_dir), "hook_event_name": "SessionStart"}
                ),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                errors.append(
                    f"Codex hook command failed during format validation: {command}: "
                    f"{result.stderr.strip()}"
                )
                continue
            if not result.stdout.strip():
                # A current Codebase Map legitimately emits nothing.
                continue
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                errors.append(f"Codex hook output is not JSON for {command}: {exc}")
                continue
            if "systemMessage" in payload:
                errors.append(
                    f"Codex hook {command} uses systemMessage, which is not "
                    "model-visible SessionStart context."
                )
            specific = payload.get("hookSpecificOutput")
            if not isinstance(specific, dict):
                errors.append(f"Codex hook {command} is missing hookSpecificOutput.")
                continue
            if specific.get("hookEventName") != "SessionStart":
                errors.append(f"Codex hook {command} has the wrong hookEventName.")
            context = specific.get("additionalContext")
            if not isinstance(context, str) or not context.strip():
                errors.append(
                    f"Codex hook {command} has no model-visible additionalContext."
                )
        return errors

    def _validate_skill_identity_graph(
        self, output_dir: Path, platform: str
    ) -> list[str]:
        """Resolve every explicit Codex $skill ref through SKILL.md.name."""
        if platform != "codex":
            return []
        errors: list[str] = []
        skills_dir = self._get_skills_dir(output_dir, platform)
        known: set[str] = set()
        for skill_md in skills_dir.glob("*/SKILL.md"):
            content = skill_md.read_text(encoding="utf-8")
            frontmatter, parse_error = self._extract_markdown_frontmatter(content)
            if frontmatter is None:
                errors.append(
                    f"Codex skill {skill_md.parent.name} has invalid frontmatter: "
                    f"{parse_error or 'missing'}."
                )
                continue
            name = frontmatter.get("name")
            description = frontmatter.get("description")
            if not name:
                errors.append(f"Codex skill {skill_md.parent.name} has no name.")
                continue
            if not description:
                errors.append(f"Codex skill {skill_md.parent.name} has no description.")
            if name in known:
                errors.append(f"Duplicate Codex skill identity: {name}.")
            known.add(name)

        for path in output_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".toml"}:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            for ref in _SKILL_REF_PATTERN.findall(content):
                if ref == "skill-name":
                    continue
                if ref not in known:
                    errors.append(
                        f"Unresolved Codex skill reference '${ref}' in "
                        f"{path.relative_to(output_dir)}. Known skill IDs: {sorted(known)}."
                    )
        return errors

    def _validate_companion_references(
        self, output_dir: Path, platform: str
    ) -> list[str]:
        """Resolve installed skill/agent companion placeholders mechanically."""
        if platform != "codex":
            return []
        errors: list[str] = []
        skills_by_name: dict[str, Path] = {}
        skills_dir = self._get_skills_dir(output_dir, platform)
        for skill_md in skills_dir.glob("*/SKILL.md"):
            frontmatter, _ = self._extract_markdown_frontmatter(
                skill_md.read_text(encoding="utf-8")
            )
            if frontmatter and frontmatter.get("name"):
                skills_by_name[frontmatter["name"]] = skill_md.parent

        for path in output_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".toml"}:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            for skill_name, relative in _SKILL_COMPANION_PATTERN.findall(content):
                root = skills_by_name.get(skill_name)
                if root is None or not (root / relative).is_file():
                    errors.append(
                        f"Unresolved companion for skill '{skill_name}': {relative}."
                    )
            for relative in _AGENT_COMPANION_PATTERN.findall(content):
                target = (
                    output_dir
                    / ".codex/agent-resources/samsara-auto-gatekeeper"
                    / relative
                )
                if not target.is_file():
                    errors.append(
                        "Unresolved Auto Gatekeeper companion: "
                        f"{target.relative_to(output_dir)}."
                    )
        return errors

    def _get_skills_dir(self, output_dir: Path, platform: str = "codex") -> Path:
        """Return the skills directory path within the output dir."""
        # Codex native layout uses .agents/skills. Legacy/plugin-style converted
        # output used skills/. Prefer the native path when present, but keep the
        # fallback so older fixture-level tests can still validate legacy output.
        native = output_dir / ".agents" / "skills"
        if native.exists():
            return native
        return output_dir / "skills"

    def _get_agents_dir(self, output_dir: Path, platform: str = "codex") -> Path:
        """Return the agents directory path within the output dir."""
        # Codex native layout uses .codex/agents. Legacy/plugin-style converted
        # output used agents/.
        native = output_dir / ".codex" / "agents"
        if native.exists():
            return native
        return output_dir / "agents"

    def _extract_markdown_frontmatter(
        self, content: str
    ) -> tuple[dict[str, str] | None, str | None]:
        """Extract YAML frontmatter from a markdown file."""
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            return None, None

        closing_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                closing_idx = i
                break
        if closing_idx is None:
            return None, "frontmatter is not closed"

        raw_frontmatter = "\n".join(lines[1:closing_idx])
        try:
            parsed = yaml.safe_load(raw_frontmatter) if raw_frontmatter.strip() else {}
        except yaml.YAMLError as e:
            return None, f"invalid YAML frontmatter: {e}"

        if not isinstance(parsed, dict):
            return None, "YAML frontmatter root is not an object"

        frontmatter: dict[str, str] = {}
        for key, value in parsed.items():
            if isinstance(key, str) and value is not None:
                frontmatter[key] = str(value)
        return frontmatter, None

    def _scan_source_patterns(
        self, output_dir: Path, strict_namespace: bool = False
    ) -> list[str]:
        """Scan all scannable files in output_dir for remaining source patterns.

        Source patterns that must NOT appear in output:
        - invoke `samsara:X` — chain transition death case
        - subagent_type: — agent dispatch source pattern
        - (strict only) any `samsara:X` colon-form reference — dead reference
          on the target platform

        Returns list of error strings (may be empty if no patterns found).
        """
        errors: list[str] = []

        for file_path in output_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in _SCAN_EXTENSIONS:
                continue

            relative = file_path.relative_to(output_dir)

            # Live-surface exclusion (SS-1/SD-1): skip files whose top-level
            # path segment is a non-live-surface directory (changes/, docs/,
            # bugfix/, tests/). Matches the exact first path segment only —
            # a directory merely starting with the same string (e.g.
            # "docs-site/") or a same-named directory nested deeper in the
            # tree (e.g. "skills/x/changes/") is NOT excluded.
            if (
                relative.parts
                and relative.parts[0] in _LIVE_SURFACE_EXCLUDED_TOP_LEVEL_DIRS
            ):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                # Log but do not fail — binary files may be in output
                logger.warning(
                    "Cannot read file for pattern scan: %s: %s", file_path, e
                )
                continue

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

            # Strict lane: any colon-form namespace residue is a dead reference.
            # The correct replacement depends on whether the reference targets a
            # skill (SKILL.md.name) or an agent (hyphenated agent name), so the
            # validator reports the residue without guessing the target identity.
            # Skip files already flagged above to avoid double-reporting.
            if strict_namespace and not match:
                match3 = _SAMSARA_NAMESPACE_PATTERN.search(content)
                if match3:
                    errors.append(
                        f"Colon-form namespace residue '{match3.group()}' found in "
                        f"output file '{relative}'. Codex skills use SKILL.md.name; "
                        "Samsara agents use their generated hyphenated name. Add or "
                        "fix the context-specific transformation rule; do not ship "
                        "this output."
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
