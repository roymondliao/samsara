"""
ConversionEngine — Orchestrates the full samsara → target platform conversion.

Flow:
1. Load platform config via load_platform_config()
2. Validate source structure (SourceValidator)
3. Create temp output directory (tempfile.mkdtemp)
4. Run converter modules in order:
   a. Skills (SkillConverter for each skill dir)
   b. Agents (AgentConverter for each .md in agents/)
   c. Hooks (HookConverter for session-start and hooks.json)
   d. Manifest (ManifestConverter for plugin.json)
   e. References (ReferenceConverter for each .md in references/)
5. Validate converted output (TargetValidator)
6. If all pass: move temp dir to final output path
7. If any fail: delete temp dir, raise EngineError

All-or-nothing contract:
- On ANY failure in steps 4–5, the temp dir is deleted before raising.
- The final output_dir is NEVER created if conversion fails.
- This invariant is enforced by the finally block in run().

Design decisions:
- Temp dir + atomic move (shutil.move) is used instead of writing directly to
  output_dir. This prevents partial output from being visible as the final result.
  Assumption: shutil.move on the same filesystem is atomic enough for this use case.
  Cross-filesystem moves (e.g., temp on /tmp, output on a network mount) are NOT
  atomic — documented in scar report.
- SourceValidator is run BEFORE the temp dir is created. This avoids creating
  and then immediately deleting a temp dir on source validation failure.
- TargetValidator is run BEFORE the temp dir is moved. This catches conversion
  problems before they land in the final output location.
- Agent name uniqueness: duplicate agent names raise EngineError. Names are
  compared case-folded to catch case-insensitive filesystem collisions (macOS
  default). The error message names both the current and prior source files.

Known shortcuts:
- shutil.move atomicity: on cross-filesystem moves, the move is NOT atomic —
  shutil copies to destination then deletes source. Between copy and delete,
  a partial output exists. Documented but not fixed (fixing requires platform-
  specific atomic move APIs or a database-backed write).
- Skills are converted based on the skills/ directory contents, NOT from
  platform config skill_list. Any skill dir present gets converted, even if
  the platform config doesn't expect it. Expected_skills for SourceValidator
  comes from the actual source directory listing.
- References are optional. If references/ dir is empty or missing, no error.
  A platform that expects references but gets none will have no reference docs.
  Caller must validate this separately if needed.

Assumptions:
1. Platform config paths.skills_dir and paths.agents_dir are relative paths
   from the output root (e.g., "skills", "agents").
2. Source structure is fixed: .claude-plugin/, skills/, agents/, hooks/, references/.
   If source structure changes, both source validator and engine path logic must update.
3. tempfile.mkdtemp creates the temp dir in the OS default temp location.
   If the OS temp location is on a different filesystem than the output_dir,
   shutil.move will do a non-atomic copy+delete. This is acceptable for
   non-production use cases (CLI tool, not a daemon).
4. All converter methods are synchronous. No async or threading.
"""

import json
import logging
import shutil
import tempfile
import warnings
from pathlib import Path

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.schema import NamingConfig, PlatformConfig
from samsara_cli.config.template_env import get_template_env
from samsara_cli.converter.agent import AgentConverter
from samsara_cli.converter.hook import HookConverter
from samsara_cli.converter.manifest import ManifestConverter
from samsara_cli.converter.reference import ReferenceConverter
from samsara_cli.converter.skill import SkillConverter
from samsara_cli.validators.source import SourceValidator
from samsara_cli.validators.target import TargetValidator

logger = logging.getLogger(__name__)


class EngineError(Exception):
    """Raised when the conversion engine fails.

    Wraps all engine-level errors (source validation, converter failures,
    target validation). The message includes the specific cause.

    The temp dir is ALWAYS deleted before EngineError is raised.
    When the caller catches EngineError, there is no partial output.
    """


class ConversionEngine:
    """Orchestrates the full samsara → target platform conversion.

    Usage:
        engine = ConversionEngine(platform="codex")
        engine.run(
            source_dir=Path("."),  # root of samsara repo
            output_dir=Path("./output/codex"),
        )

    On success: output_dir contains the fully converted plugin.
    On failure: output_dir does NOT exist (or is left empty if it existed before).
                EngineError is raised with the cause.
    """

    def __init__(self, platform: str) -> None:
        """Initialize the engine for the given platform.

        Args:
            platform: Platform identifier (e.g., "codex"). Must match a platform
                      YAML file in samsara_cli/config/platform/.

        Raises:
            hydra.errors.MissingConfigException: If platform YAML does not exist.
            pydantic.ValidationError: If platform config fails schema validation.

        Note: Platform config is loaded eagerly at construction time so that
        invalid platform names fail loudly here, not during run().
        """
        self._platform = platform
        # Load platform config eagerly — fail fast on invalid platform
        self._config: PlatformConfig = load_platform_config(platform)
        self._template_env = get_template_env(platform)

    def run(
        self,
        source_dir: Path,
        output_dir: Path,
    ) -> None:
        """Execute the full conversion pipeline.

        All-or-nothing: either ALL steps succeed and output_dir is populated,
        or NO output is produced and EngineError is raised.

        Args:
            source_dir: Root of the samsara source directory.
                        Must contain .claude-plugin/, skills/, agents/, hooks/.
            output_dir: Target output directory. Created on success.
                        Must NOT be the same as source_dir.

        Raises:
            EngineError: If source validation fails, any converter fails, or
                         target validation fails. Temp dir is always deleted
                         before this exception is raised.
            FileNotFoundError: If source_dir does not exist.
        """
        source_dir = source_dir.resolve()
        output_dir = output_dir.resolve()

        if not source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {source_dir}. "
                "Cannot run conversion without a valid source."
            )

        # --- Step 1: Source validation (before temp dir creation) ---
        logger.info("Validating source structure: %s", source_dir)
        source_errors = self._run_source_validation(source_dir)
        if source_errors:
            raise EngineError(
                f"Source validation failed with {len(source_errors)} error(s). "
                "Fix source structure before converting.\n"
                + "\n".join(f"  - {e}" for e in source_errors)
            )

        # --- Step 2: Create temp output directory ---
        # All conversion work happens in temp_dir. Only moved to output_dir on full success.
        temp_dir = Path(tempfile.mkdtemp(prefix="samsara-convert-"))
        logger.info("Created temp output directory: %s", temp_dir)

        try:
            # --- Step 3: Run all converter modules ---
            self._run_all_converters(source_dir, temp_dir)

            # --- Step 4: Target validation ---
            logger.info("Validating converted output: %s", temp_dir)
            target_errors = self._run_target_validation(temp_dir)
            if target_errors:
                raise EngineError(
                    f"Target validation failed with {len(target_errors)} error(s). "
                    "Output is invalid and has been discarded.\n"
                    + "\n".join(f"  - {e}" for e in target_errors)
                )

            # --- Step 5: Move temp dir to final output (all-or-nothing commit) ---
            # If output_dir already exists, remove it first (overwrite semantics).
            if output_dir.exists():
                logger.info("Output dir already exists, removing: %s", output_dir)
                shutil.rmtree(output_dir)

            # Detect cross-filesystem move: os.stat().st_dev differs between dirs.
            # Cross-filesystem moves are non-atomic (copy+delete), not os.rename().
            # Warn rather than fail — this is a non-fatal risk disclosure.
            try:
                temp_dev = temp_dir.stat().st_dev
                output_parent_dev = output_dir.parent.stat().st_dev
                if temp_dev != output_parent_dev:
                    warnings.warn(
                        f"Temp dir ({temp_dir}) and output dir parent ({output_dir.parent}) "
                        "are on different filesystems. shutil.move will use copy+delete "
                        "instead of os.rename — the move is NOT atomic. If the process "
                        "is killed between copy and delete, partial output will exist at "
                        f"{output_dir}. Consider pointing both paths to the same filesystem.",
                        UserWarning,
                        stacklevel=2,
                    )
            except OSError:
                # Cannot stat — skip the check, proceed with move
                pass

            logger.info("Moving temp output to final location: %s", output_dir)
            shutil.move(str(temp_dir), str(output_dir))
            # After move, temp_dir no longer exists — the finally block must handle this

        except Exception:
            # ALL-OR-NOTHING: delete temp dir on any failure
            # This runs for both EngineError (target validation) and converter errors.
            if temp_dir.exists():
                logger.info("Deleting temp dir after failure: %s", temp_dir)
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def _run_source_validation(self, source_dir: Path) -> list[str]:
        """Run source validation. Returns list of errors (empty = valid)."""
        # Determine expected skills from the source directory contents
        # (convert whatever skills are present — caller doesn't need to enumerate them)
        skills_dir = source_dir / self._config.source.skills_dir
        expected_skills: list[str] = []
        if skills_dir.exists():
            expected_skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]

        validator = SourceValidator()
        return validator.validate(
            source_dir=source_dir, expected_skills=expected_skills
        )

    def _run_target_validation(self, output_dir: Path) -> list[str]:
        """Run target validation. Returns list of errors (empty = valid)."""
        validator = TargetValidator()
        return validator.validate(output_dir=output_dir)

    def _run_all_converters(self, source_dir: Path, temp_dir: Path) -> None:
        """Run all converter modules in order.

        Order matters:
        1. Skills first — they are the primary content
        2. Agents — referenced by skills
        3. Hooks — infrastructure
        4. Manifest — metadata
        5. References — supplementary docs

        Raises:
            EngineError: If any converter fails. Wraps the original exception.
        """
        try:
            self._convert_skills(source_dir, temp_dir)
        except Exception as e:
            raise EngineError(
                f"Skills conversion failed: {e}. No partial output will be kept."
            ) from e

        try:
            self._convert_agents(source_dir, temp_dir)
        except Exception as e:
            raise EngineError(
                f"Agents conversion failed: {e}. No partial output will be kept."
            ) from e

        try:
            self._convert_hooks(source_dir, temp_dir)
        except Exception as e:
            raise EngineError(
                f"Hooks conversion failed: {e}. No partial output will be kept."
            ) from e

        try:
            self._convert_manifest(source_dir, temp_dir)
        except Exception as e:
            raise EngineError(
                f"Manifest conversion failed: {e}. No partial output will be kept."
            ) from e

        try:
            self._convert_references(source_dir, temp_dir)
        except Exception as e:
            raise EngineError(
                f"References conversion failed: {e}. No partial output will be kept."
            ) from e

    def _get_naming(self) -> NamingConfig:
        """Get NamingConfig from platform config.

        Raises:
            EngineError: If naming config is missing.
        """
        if self._config.naming is None:
            raise EngineError(
                f"Platform '{self._platform}' has no naming config. "
                "A NamingConfig with skill_prefix and separator is required."
            )
        return self._config.naming

    def _get_output_skills_dir(self, temp_dir: Path) -> Path:
        """Get output skills directory path."""
        skills_dir_name = "skills"
        if self._config.paths and self._config.paths.skills_dir:
            skills_dir_name = self._config.paths.skills_dir
        return temp_dir / skills_dir_name

    def _get_output_agents_dir(self, temp_dir: Path) -> Path:
        """Get output agents directory path."""
        agents_dir_name = "agents"
        if self._config.paths and self._config.paths.agents_dir:
            agents_dir_name = self._config.paths.agents_dir
        return temp_dir / agents_dir_name

    def _get_output_plugin_dir(self, temp_dir: Path) -> Path:
        """Get platform config directory path."""
        plugin_dir_name = ".codex-plugin"
        if self._config.paths and self._config.paths.plugin_dir:
            plugin_dir_name = self._config.paths.plugin_dir
        return temp_dir / plugin_dir_name

    def _convert_skills(self, source_dir: Path, temp_dir: Path) -> None:
        """Convert all skill directories from source to output.

        Each skill is converted independently. Companion files (non-SKILL.md files
        in the skill dir) are included in the output — this preserves unknown files
        (DC-7-5 death case: extra files must not be silently dropped).
        """
        source_skills_dir = source_dir / self._config.source.skills_dir
        if not source_skills_dir.exists():
            # No skills dir — not an error (handled by source validator)
            logger.warning("No skills directory found in source: %s", source_skills_dir)
            return

        output_skills_dir = self._get_output_skills_dir(temp_dir)
        output_skills_dir.mkdir(parents=True, exist_ok=True)

        naming = self._get_naming()
        rules = self._config.transformations
        converter = SkillConverter()

        for skill_dir in sorted(source_skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            logger.info("Converting skill: %s", skill_dir.name)
            converted = converter.convert(
                source_skill_dir=skill_dir,
                rules=rules,
                naming_config=naming,
            )

            # Write converted skill to output
            out_skill_dir = output_skills_dir / converted.output_dir_name
            out_skill_dir.mkdir(exist_ok=True)

            # Write SKILL.md
            (out_skill_dir / "SKILL.md").write_text(
                converted.skill_md_content, encoding="utf-8"
            )

            # Write companion files (preserves all files including unknown ones)
            for rel_path, content in converted.companion_files.items():
                out_file = out_skill_dir / rel_path
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_text(content, encoding="utf-8")

    def _convert_agents(self, source_dir: Path, temp_dir: Path) -> None:
        """Convert all agent .md files from source to .toml output."""
        source_agents_dir = source_dir / self._config.source.agents_dir
        if not source_agents_dir.exists():
            logger.warning("No agents directory found in source: %s", source_agents_dir)
            return

        output_agents_dir = self._get_output_agents_dir(temp_dir)
        output_agents_dir.mkdir(parents=True, exist_ok=True)

        naming = self._get_naming()
        rules = self._config.transformations

        # Get template for agent conversion
        agent_format = None
        if self._config.formats and self._config.formats.agent_format:
            agent_format = self._config.formats.agent_format

        template_name = "agent.toml.j2"
        if agent_format and "template" in agent_format:
            template_name = agent_format["template"]

        template = self._template_env.get_template(template_name)
        converter = AgentConverter()

        seen_agent_names: dict[str, str] = {}

        for agent_file in sorted(source_agents_dir.glob("*.md")):
            logger.info("Converting agent: %s", agent_file.name)
            source_text = agent_file.read_text(encoding="utf-8")
            converted = converter.convert_from_text(
                source_text=source_text,
                source_path=agent_file,
                rules=rules,
                naming=naming,
                template=template,
            )

            name_key = converted.agent_name.casefold()
            if name_key in seen_agent_names:
                prior_file = seen_agent_names[name_key]
                raise EngineError(
                    f"Duplicate agent name '{converted.agent_name}' produced from "
                    f"'{agent_file.name}'. Collides with '{prior_file}' which produced "
                    f"the same name. On case-insensitive filesystems (macOS default), "
                    "this would silently overwrite the first agent."
                )
            seen_agent_names[name_key] = agent_file.name

            out_file = output_agents_dir / f"{converted.agent_name}.toml"
            out_file.write_text(converted.toml_content, encoding="utf-8")

    def _convert_hooks(self, source_dir: Path, temp_dir: Path) -> None:
        """Convert hook artifacts (session-start script and hooks.json)."""
        source_hooks_dir = source_dir / self._config.source.hooks_dir
        if not source_hooks_dir.exists():
            logger.warning("No hooks directory in source: %s", source_hooks_dir)
            return

        output_plugin_dir = self._get_output_plugin_dir(temp_dir)
        output_hooks_dir = output_plugin_dir / "hooks"
        output_hooks_dir.mkdir(parents=True, exist_ok=True)

        converter = HookConverter()

        # Render session-start hook script
        hook_script_template_name = "hook.sh.j2"
        if (
            self._config.formats
            and self._config.formats.hook_output
            and "script_template" in self._config.formats.hook_output
        ):
            hook_script_template_name = self._config.formats.hook_output[
                "script_template"
            ]

        script_template = self._template_env.get_template(hook_script_template_name)
        session_start_script = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=self._config,
            template=script_template,
        )
        script_path = output_hooks_dir / "samsara-session-start.sh"
        script_path.write_text(session_start_script, encoding="utf-8")
        # Hook scripts must be executable — Codex runs them as shell commands.
        # write_text() does not set execute bit; set it explicitly.
        # Using os.chmod with explicit flags rather than stat module constants
        # for clarity: 0o755 = rwxr-xr-x (owner rwx, group rx, other rx).
        script_path.chmod(0o755)

        # Render hooks.json
        hooks_json_template_name = "hooks.json.j2"
        if (
            self._config.formats
            and self._config.formats.hook_output
            and "template" in self._config.formats.hook_output
        ):
            hooks_json_template_name = self._config.formats.hook_output["template"]

        hooks_json_template = self._template_env.get_template(hooks_json_template_name)
        hooks_dict = converter.convert_hooks_json(
            platform_config=self._config,
            template=hooks_json_template,
        )

        # Determine output hooks.json path
        hooks_file_name = "hooks.json"
        if self._config.paths and self._config.paths.hooks_file:
            hooks_file_name = self._config.paths.hooks_file

        hooks_output_path = output_plugin_dir / hooks_file_name
        hooks_output_path.write_text(
            json.dumps(hooks_dict, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if self._config.permissions and self._config.permissions.feature_flags:
            config_lines = ["[features]"]
            for key, value in self._config.permissions.feature_flags.items():
                toml_value = (
                    "true"
                    if value is True
                    else "false"
                    if value is False
                    else json.dumps(value)
                )
                config_lines.append(f"{key} = {toml_value}")
            (output_plugin_dir / "config.toml").write_text(
                "\n".join(config_lines) + "\n",
                encoding="utf-8",
            )

    def _convert_manifest(self, source_dir: Path, temp_dir: Path) -> None:
        """Convert the source plugin.json to target platform manifest."""
        if (
            self._config.formats
            and self._config.formats.manifest
            and self._config.formats.manifest.get("enabled") is False
        ):
            logger.info(
                "Skipping manifest conversion for platform '%s' because "
                "formats.manifest.enabled is false.",
                self._platform,
            )
            return

        source_manifest = source_dir / self._config.source.plugin_dir / "plugin.json"
        if not source_manifest.exists():
            raise FileNotFoundError(
                f"Source manifest not found: {source_manifest}. "
                "SourceValidator should have caught this — this is an engine bug."
            )

        # Extract extra_fields from platform config
        extra_fields: dict = {}
        if (
            self._config.formats
            and self._config.formats.manifest
            and "extra_fields" in self._config.formats.manifest
        ):
            extra_fields = self._config.formats.manifest["extra_fields"] or {}

        converter = ManifestConverter()
        manifest_dict = converter.convert(
            source_manifest=source_manifest,
            extra_fields=extra_fields,
        )

        # Write output manifest to platform config dir when that platform uses one.
        output_plugin_dir = self._get_output_plugin_dir(temp_dir)
        output_plugin_dir.mkdir(parents=True, exist_ok=True)

        manifest_file_name = "plugin.json"
        if self._config.paths and self._config.paths.plugin_manifest:
            manifest_file_name = self._config.paths.plugin_manifest

        out_manifest = output_plugin_dir / manifest_file_name
        out_manifest.write_text(
            json.dumps(manifest_dict, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _convert_references(self, source_dir: Path, temp_dir: Path) -> None:
        """Convert reference .md files from source to output.

        References are optional. If references/ is empty or missing, logs a warning
        but does not fail.
        """
        source_refs_dir = source_dir / self._config.source.references_dir
        if not source_refs_dir.exists():
            logger.info(
                "No references directory in source (optional): %s", source_refs_dir
            )
            return

        ref_files = list(source_refs_dir.glob("*.md"))
        if not ref_files:
            logger.info(
                "No reference .md files in source (optional): %s", source_refs_dir
            )
            return

        # Output location is platform-specific. Codex native installs use
        # .agents/references; plugin-style platforms may keep references under
        # the platform plugin directory.
        if self._config.paths and self._config.paths.references_dir:
            output_refs_dir = temp_dir / self._config.paths.references_dir
        else:
            output_plugin_dir = self._get_output_plugin_dir(temp_dir)
            output_refs_dir = output_plugin_dir / "references"
        output_refs_dir.mkdir(parents=True, exist_ok=True)

        rules = self._config.transformations
        converter = ReferenceConverter()

        for ref_file in sorted(ref_files):
            logger.info("Converting reference: %s", ref_file.name)
            converted_content = converter.convert(
                source_ref=ref_file,
                rules=rules,
            )
            (output_refs_dir / ref_file.name).write_text(
                converted_content, encoding="utf-8"
            )
