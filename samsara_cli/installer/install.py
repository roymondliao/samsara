"""
Installer — Install converted samsara output to project or global scope.

Design decisions:
- CLI presence check (via PlatformDetector.detect()) is the FIRST operation.
  No files are written before this check passes. This is DC-8-1 enforcement.
- Project scope NEVER modifies ~/.codex/config.toml. It merges native platform files
  into the target project root. This is DC-8-2 enforcement.
- Global scope ALWAYS creates config.toml.bak before modifying config.toml.
  If backup creation fails, install aborts. This is DC-8-3 enforcement.
- Global scope install is idempotent: before appending any TOML section, we check
  if it's already present. This is DC-8-4 enforcement.
- Source validation happens inside _run_convert() via ConversionEngine (which calls
  SourceValidator before running converters). DC-8-6 is enforced by the engine.

config.toml modification strategy:
  We use tomllib (stdlib) for reading and tomli-w for writing. This strips comments
  from config.toml — a known shortcut documented in the scar. For v1, comment-stripping
  is acceptable. If comment preservation becomes a requirement, tomlkit is the solution.

  Idempotency is achieved by checking the TOML structure before writing:
  - [features] flags: check if key already set to the same value

Assumptions:
1. config.toml is at ~/.codex/config.toml (from GlobalInstallConfig.config_path).
   If Codex uses a different config path, installs would modify the wrong file.
2. Feature flags are under [features] table in config.toml.
   If Codex moves feature flags to a different section, flags would be missed.
"""

import json
import logging
import os
import re
import shlex
import shutil
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

import tomli_w
import yaml

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.schema import PlatformConfig
from samsara_cli.converter.engine import ConversionEngine, EngineError
from samsara_cli.installer.detect import PlatformDetector

logger = logging.getLogger(__name__)

Scope = Literal["project", "global"]
DEPRECATED_FEATURE_FLAGS = {"codex_hooks": "hooks"}
_INSTALL_MANIFEST_SCHEMA = 1
_SHARED_CONFIG_PATHS = {".codex/config.toml", ".codex/hooks.json"}


class InstallerError(Exception):
    """Raised when install preconditions fail or the install process fails.

    This is always a user-facing error — the message must be clear and
    actionable. Never wrap with generic 'Installation failed'.
    """


class Installer:
    """Installs converted samsara output to project or global scope.

    Usage:
        installer = Installer(platform="codex")
        instructions = installer.install(
            source_dir=Path("."),
            scope="project",
            cwd=Path("."),
        )
        print(instructions)

    All install methods:
    1. Check CLI presence — abort if not installed
    2. Run conversion (if no pre-converted source provided)
    3. Copy/install files
    4. Return post-install instructions string
    """

    def __init__(self, platform: str) -> None:
        """Initialize Installer for the given platform.

        Args:
            platform: Platform identifier (e.g., "codex").

        Raises:
            ValueError: If platform is unknown or config load fails.
        """
        self._platform = platform
        self._detector = PlatformDetector()
        # Load config eagerly — fail fast on invalid platform
        self._config: PlatformConfig = load_platform_config(platform)

    def install(
        self,
        source_dir: Path,
        scope: Scope = "project",
        cwd: Path | None = None,
        converted_source_dir: Path | None = None,
    ) -> str:
        """Install converted samsara files for the given platform and scope.

        Args:
            source_dir: Root of the samsara source directory.
                        Used for conversion if converted_source_dir is not provided.
            scope: "project" (copy to CWD) or "global" (copy under HOME).
            cwd: Working directory for project scope.
                 Defaults to current working directory.
            converted_source_dir: Pre-converted output directory. If provided,
                                   conversion is skipped and this is used directly.

        Returns:
            Post-install instructions string (always non-empty).

        Raises:
            InstallerError: If CLI is not installed, source is invalid, or file
                            operations fail.
        """
        cwd = cwd or Path.cwd()

        # DC-8-1: Check CLI presence FIRST — before any file operations
        self._check_cli_installed()

        # Convert if needed
        if converted_source_dir is not None:
            converted_dir = converted_source_dir
        else:
            output_dir = self._default_output_dir(cwd)
            converted_dir = self._run_convert(
                source_dir=source_dir, output_dir=output_dir
            )

        # Install based on scope
        if scope == "project":
            return self._install_project(converted_dir=converted_dir, cwd=cwd)
        elif scope == "global":
            return self._install_global(converted_dir=converted_dir, cwd=cwd)
        else:
            raise InstallerError(
                f"Unknown scope: {scope!r}. Valid scopes are: 'project', 'global'."
            )

    def update(
        self,
        source_dir: Path,
        scope: Scope = "project",
        cwd: Path | None = None,
    ) -> str:
        """Update = re-convert + re-install. Idempotent.

        Args:
            source_dir: Root of the samsara source directory.
            scope: "project" or "global". Must match the original install scope.
            cwd: Working directory for project scope.

        Returns:
            Post-update instructions string.

        Raises:
            InstallerError: If CLI is not installed or any step fails.
        """
        # update() is simply install() — the install logic is already idempotent
        return self.install(source_dir=source_dir, scope=scope, cwd=cwd)

    def _check_cli_installed(self) -> None:
        """DC-8-1: Verify platform CLI is installed.

        Raises:
            InstallerError: With clear message including install URL.
                            Raised BEFORE any file operations.
        """
        is_installed = self._detector.detect(self._platform)
        if not is_installed:
            install_url = self._detector.get_install_url(self._platform)
            url_msg = f" Install from: {install_url}" if install_url else ""
            raise InstallerError(
                f"The {self._platform} CLI is not installed on this system.{url_msg}\n"
                f"Install the {self._platform} CLI before running samsara-cli install."
            )

    def _default_output_dir(self, cwd: Path) -> Path:
        """Return default output directory for conversion."""
        return cwd / "dist" / self._platform

    def _run_convert(self, source_dir: Path, output_dir: Path) -> Path:
        """Run conversion using ConversionEngine.

        Source validation happens inside ConversionEngine (SourceValidator is run
        before any converters). DC-8-6 is enforced by the engine.

        Args:
            source_dir: Root of samsara source directory.
            output_dir: Target output directory for converted files.

        Returns:
            Path to the converted output directory.

        Raises:
            InstallerError: If source validation fails or conversion fails.
            FileNotFoundError: If source_dir does not exist.
        """
        try:
            engine = ConversionEngine(platform=self._platform)
            engine.run(source_dir=source_dir, output_dir=output_dir)
            return output_dir
        except EngineError as e:
            raise InstallerError(
                f"Conversion failed for platform '{self._platform}': {e}"
            ) from e
        except FileNotFoundError as e:
            raise InstallerError(f"Source directory not found: {e}") from e

    def _install_project(self, converted_dir: Path, cwd: Path) -> str:
        """DC-8-2: Project scope install — copy to CWD, NEVER touch global config.

        Args:
            converted_dir: Path to converted output directory.
            cwd: Target working directory.

        Returns:
            Post-install instructions string.
        """
        old_manifest = self._read_install_manifest(cwd, expected_scope="project")
        self._install_native_tree(converted_dir=converted_dir, target_root=cwd)
        self._rewrite_companion_placeholders(
            converted_dir=converted_dir,
            target_root=cwd,
        )
        self._rewrite_hook_commands_for_scope(install_root=cwd)
        manifest = self._prepare_install_state(
            converted_dir=converted_dir,
            target_root=cwd,
            scope="project",
            old_manifest=old_manifest,
        )
        self._write_install_manifest(cwd, manifest)

        logger.info("Installed %s native files to: %s", self._platform, cwd)

        # Build post-install instructions
        return self._project_install_instructions(
            cwd,
            scope_note=self._scope_overlap_note(scope="project", cwd=cwd),
        )

    def _project_install_instructions(
        self, plugin_dir: Path, *, scope_note: str = ""
    ) -> str:
        """Build post-install instructions for project scope install."""
        feature_flags_section = self._format_feature_flags_instructions()

        instructions = (
            f"samsara native {self._platform} files installed to: {plugin_dir}\n\n"
            "Next steps:\n"
            f"  1. Ensure your {self._platform} project is trusted.\n"
            "  2. Open /hooks and review/trust the generated Samsara hooks.\n"
            f"  3. Restart {self._platform} to load the skills, agents, and hooks.\n"
            f"  4. Required feature flags are present in the project config:\n"
            f"{feature_flags_section}\n"
            f"{scope_note}"
        )
        return instructions

    def _format_feature_flags_instructions(self) -> str:
        """Format feature flags as instructions text."""
        if not self._config.permissions:
            return "     (no feature flags required)"

        flags = self._config.permissions.feature_flags
        if not flags:
            return "     (no feature flags required)"

        lines = ["     [features]"]
        for key, value in flags.items():
            toml_value = (
                "true" if value is True else "false" if value is False else str(value)
            )
            lines.append(f"     {key} = {toml_value}")

        return "\n".join(lines)

    def _install_global(self, converted_dir: Path, cwd: Path) -> str:
        """Global scope install — copy native platform files under the user's home.

        Args:
            converted_dir: Path to converted output directory.
            cwd: Active project directory, used only to disclose overlapping scope.

        Returns:
            Post-install instructions string.

        Raises:
            InstallerError: If global config is missing required settings,
                            backup fails, or config modification fails.
        """
        global_cfg = self._config.install.global_ if self._config.install else None
        if global_cfg is None:
            raise InstallerError(
                f"Platform '{self._platform}' does not support global install "
                "(no 'install.global' section in platform config)."
            )

        # Resolve paths (expand ~ with $HOME from environment)
        # We read HOME from os.environ explicitly so tests can override it.
        # Path.expanduser() also reads HOME from os.environ — both are equivalent,
        # but explicit home resolution makes test patching clearer.
        home = Path(os.environ.get("HOME", str(Path.home())))
        old_manifest = self._read_install_manifest(home, expected_scope="global")

        config_path_raw = global_cfg.config_path
        if not config_path_raw:
            raise InstallerError(
                f"Platform '{self._platform}' global install config is missing "
                "'config_path'. Cannot determine which config file to update."
            )
        config_path = Path(config_path_raw.replace("~", str(home)))

        # --- Step 1: Ensure config file exists ---
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text("")
            logger.info("Created new config file at: %s", config_path)

        # --- Step 2: DC-8-3 Backup config BEFORE any modification ---
        backup_path = config_path.parent / (config_path.name + ".bak")
        try:
            shutil.copy2(config_path, backup_path)
            logger.info("Backed up config to: %s", backup_path)
        except OSError as e:
            raise InstallerError(
                f"DC-8-3: Cannot backup config before modification: {e}. "
                "Aborting to prevent config loss. Fix the backup location and retry."
            ) from e

        # --- Step 3: Copy native output into the user's home directories ---
        self._install_native_tree(converted_dir=converted_dir, target_root=home)
        self._rewrite_companion_placeholders(
            converted_dir=converted_dir,
            target_root=home,
        )

        # --- Step 3b: Rewrite samsara's relative hook commands to absolute ---
        # The converter bakes a scope-agnostic RELATIVE command. Relative paths
        # resolve correctly for project scope (script lives under <project>/),
        # but for global scope the script lives under $HOME while Codex
        # resolve the command against the PROJECT cwd — so the hook silently
        # never fires. Rewriting here (per scope) keeps that decision out of the
        # scope-agnostic converter.
        self._rewrite_hook_commands_for_scope(install_root=home)

        manifest = self._prepare_install_state(
            converted_dir=converted_dir,
            target_root=home,
            scope="global",
            old_manifest=old_manifest,
        )

        # --- Step 4: DC-8-4 Modify config.toml (idempotent) ---
        try:
            current_content = config_path.read_bytes()
            try:
                current_toml = tomllib.loads(current_content.decode())
            except tomllib.TOMLDecodeError as toml_err:
                raise InstallerError(
                    f"config.toml is not valid TOML — refusing to overwrite. "
                    f"Backup was created at: {backup_path}. "
                    f"Fix the TOML syntax and retry. Parse error: {toml_err}"
                ) from toml_err

            modified = self._update_config_toml(
                config=current_toml,
                install_root=home,
            )

            config_path.write_bytes(tomli_w.dumps(modified).encode())
            logger.info("Updated config.toml at: %s", config_path)

        except OSError as e:
            raise InstallerError(
                f"Failed to write config.toml at {config_path}: {e}. "
                f"A backup is available at {backup_path}."
            ) from e

        self._write_install_manifest(home, manifest)
        return self._global_install_instructions(
            install_root=home,
            config_path=config_path,
            scope_note=self._scope_overlap_note(scope="global", cwd=cwd),
        )

    def _install_native_tree(self, converted_dir: Path, target_root: Path) -> None:
        """Merge converted native platform files into target_root.

        Directory contents are copied recursively. JSON/TOML config files that may
        already exist are merged instead of blindly overwritten.
        """
        if not converted_dir.exists():
            raise InstallerError(f"Converted output does not exist: {converted_dir}")

        for item in converted_dir.iterdir():
            dest = target_root / item.name
            if item.is_dir():
                self._copy_dir_merge(item, dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    def _install_manifest_path(self, install_root: Path) -> Path:
        """Return platform-scoped installer state outside shared Codex config."""
        return install_root / ".samsara" / f"install-manifest.{self._platform}.json"

    def _read_install_manifest(
        self, install_root: Path, *, expected_scope: Scope
    ) -> dict:
        """Read the sole record of paths this installer may later delete."""
        path = self._install_manifest_path(install_root)
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallerError(
                f"Cannot read Samsara install ownership manifest {path}: {exc}. "
                "Refusing update because stale-file ownership is unknown."
            ) from exc
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise InstallerError(
                f"Unsupported Samsara install ownership manifest: {path}."
            )
        if data.get("platform") != self._platform:
            raise InstallerError(
                f"Install ownership manifest platform mismatch in {path}: "
                f"expected {self._platform!r}, got {data.get('platform')!r}."
            )
        if data.get("scope") != expected_scope:
            raise InstallerError(
                f"Install ownership manifest scope mismatch in {path}: "
                f"expected {expected_scope!r}, got {data.get('scope')!r}."
            )
        for field in ("owned_paths", "hook_commands", "shared_paths"):
            values = data.get(field)
            if not isinstance(values, list) or not all(
                isinstance(value, str) for value in values
            ):
                raise InstallerError(
                    f"Install ownership manifest field {field!r} must be a list "
                    f"of strings: {path}."
                )
        return data

    def _owned_paths_from_converted(self, converted_dir: Path) -> set[str]:
        """List generated files safe to remove; shared Codex configs are excluded."""
        owned: set[str] = set()
        for path in converted_dir.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(converted_dir).as_posix()
            if relative not in _SHARED_CONFIG_PATHS:
                owned.add(relative)
        return owned

    def _rewrite_companion_placeholders(
        self, *, converted_dir: Path, target_root: Path
    ) -> None:
        """Resolve scope-agnostic companion paths after their install root is known."""
        replacements: dict[str, str] = {}
        skills_dir = converted_dir / ".agents/skills"
        for skill_md in skills_dir.glob("*/SKILL.md"):
            content = skill_md.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) != 3:
                raise InstallerError(
                    f"Cannot resolve companion path; invalid skill frontmatter: {skill_md}."
                )
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError as exc:
                raise InstallerError(
                    f"Cannot resolve companion path; invalid skill YAML: {skill_md}: {exc}."
                ) from exc
            skill_name = (
                frontmatter.get("name") if isinstance(frontmatter, dict) else None
            )
            if not isinstance(skill_name, str) or not skill_name:
                raise InstallerError(
                    f"Cannot resolve companion path; skill name is missing: {skill_md}."
                )
            installed_dir = target_root / skill_md.parent.relative_to(converted_dir)
            replacements[f"<installed-{skill_name}-skill-directory>"] = shlex.quote(
                str(installed_dir)
            )

        agent_resources = target_root / ".codex/agent-resources"
        replacements["<installed-auto-gatekeeper-companion-directory>"] = shlex.quote(
            str(agent_resources / "samsara-auto-gatekeeper")
        )

        unresolved = re.compile(r"<installed-[a-z0-9-]+-(?:skill|companion)-directory>")
        for relative in self._owned_paths_from_converted(converted_dir):
            source = converted_dir / relative
            if source.suffix.lower() not in {".md", ".toml", ".txt"}:
                continue
            target = target_root / relative
            content = target.read_text(encoding="utf-8")
            for placeholder, installed_path in replacements.items():
                content = content.replace(placeholder, installed_path)
            remaining = sorted(set(unresolved.findall(content)))
            if remaining:
                raise InstallerError(
                    f"Installed companion path cannot be resolved in {target}: {remaining}."
                )
            target.write_text(content, encoding="utf-8")

    def _prepare_install_state(
        self,
        *,
        converted_dir: Path,
        target_root: Path,
        scope: Scope,
        old_manifest: dict,
    ) -> dict:
        """Reconcile only paths previously declared as Samsara-owned."""
        new_owned = self._owned_paths_from_converted(converted_dir)
        old_owned = {
            value
            for value in old_manifest.get("owned_paths", [])
            if isinstance(value, str)
        }
        for relative in sorted(old_owned - new_owned):
            self._remove_owned_path(target_root, relative)

        new_hook_commands = self._installed_hook_commands(
            converted_dir=converted_dir,
            target_root=target_root,
        )
        old_hook_commands = {
            value
            for value in old_manifest.get("hook_commands", [])
            if isinstance(value, str)
        }
        self._remove_stale_hook_commands(
            target_root,
            stale_commands=old_hook_commands - new_hook_commands,
        )

        try:
            package_version = version("samsara")
        except PackageNotFoundError:
            package_version = "unknown"
        return {
            "schema_version": _INSTALL_MANIFEST_SCHEMA,
            "platform": self._platform,
            "scope": scope,
            "samsara_version": package_version,
            "owned_paths": sorted(new_owned),
            "hook_commands": sorted(new_hook_commands),
            "shared_paths": sorted(_SHARED_CONFIG_PATHS),
        }

    def _remove_owned_path(self, install_root: Path, relative: str) -> None:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise InstallerError(
                f"Unsafe owned path in install manifest: {relative!r}."
            )
        target = install_root / relative_path
        try:
            target.relative_to(install_root)
        except ValueError as exc:
            raise InstallerError(
                f"Owned path escapes install root: {relative!r}."
            ) from exc
        if target.is_file() or target.is_symlink():
            target.unlink()
        parent = target.parent
        while parent != install_root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent

    def _installed_hook_commands(
        self, *, converted_dir: Path, target_root: Path
    ) -> set[str]:
        hook_file = converted_dir / ".codex/hooks.json"
        if not hook_file.exists():
            return set()
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        hooks = data.get("hooks", {}) if isinstance(data, dict) else {}
        entries = [
            entry
            for event_entries in hooks.values()
            if isinstance(event_entries, list)
            for entry in event_entries
        ]
        commands = {
            command for _hook_type, command in self._hook_entry_identities(entries)
        }
        return {
            str(target_root / command) if not os.path.isabs(command) else command
            for command in commands
        }

    def _remove_stale_hook_commands(
        self, install_root: Path, *, stale_commands: set[str]
    ) -> None:
        """Remove only hook handlers recorded as owned by the prior manifest."""
        if not stale_commands:
            return
        hook_file = install_root / ".codex/hooks.json"
        if not hook_file.exists():
            return
        data = json.loads(hook_file.read_text(encoding="utf-8"))
        hooks = data.get("hooks") if isinstance(data, dict) else None
        if not isinstance(hooks, dict):
            return
        changed = False
        for event, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue
            kept_entries = []
            for entry in entries:
                if not isinstance(entry, dict):
                    kept_entries.append(entry)
                    continue
                handlers = entry.get("hooks")
                if not isinstance(handlers, list):
                    kept_entries.append(entry)
                    continue
                kept_handlers = [
                    handler
                    for handler in handlers
                    if not (
                        isinstance(handler, dict)
                        and handler.get("command") in stale_commands
                    )
                ]
                changed |= len(kept_handlers) != len(handlers)
                if kept_handlers:
                    updated = dict(entry)
                    updated["hooks"] = kept_handlers
                    kept_entries.append(updated)
            hooks[event] = kept_entries
        if changed:
            hook_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    def _write_install_manifest(self, install_root: Path, manifest: dict) -> None:
        path = self._install_manifest_path(install_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def _rewrite_hook_commands_for_scope(self, install_root: Path) -> None:
        """Rewrite Samsara's relative hook commands for the selected install root.

        Only commands that point into our own plugin hooks dir (prefix
        '<plugin_dir>/') are rewritten — a user's pre-existing foreign hook
        command (e.g. 'my-own-tool.sh') is left untouched. If the rewrite scope
        were broader it could mangle unrelated commands; if narrower it would
        silently leave the installed hook unresolvable.

        No-op (not an error) when the platform has no plugin_dir/hooks_file or the
        hook config file is absent — some platforms may not ship a hooks file.
        """
        paths = self._config.paths
        if paths is None or not paths.plugin_dir or not paths.hooks_file:
            return

        hook_file = install_root / paths.plugin_dir / paths.hooks_file
        if not hook_file.exists():
            return

        try:
            data = json.loads(hook_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise InstallerError(
                f"Cannot rewrite hook commands because {hook_file} is not valid "
                f"JSON: {e}. The hook file was written but its commands could not "
                "be made absolute — the global hook would not fire."
            ) from e

        prefix = f"{paths.plugin_dir}/"
        changed = self._rewrite_command_paths(
            data, prefix=prefix, install_root=install_root
        )

        command_prefix = str(install_root / paths.plugin_dir / "hooks")
        changed |= self._dedupe_hook_entries_for_command_prefix(
            data,
            command_prefix=command_prefix,
        )

        if changed:
            hook_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            logger.info("Rewrote samsara hook commands to absolute in: %s", hook_file)

    def _rewrite_command_paths(
        self, node: object, *, prefix: str, install_root: Path
    ) -> bool:
        """Recursively rewrite relative 'command' values that start with prefix.

        Returns True if any command was rewritten. The traversal stays
        structure-agnostic so a target adapter may choose its own nesting.
        """
        changed = False
        if isinstance(node, dict):
            command = node.get("command")
            if isinstance(command, str) and command.startswith(prefix):
                node["command"] = str(install_root / command)
                changed = True
            for value in node.values():
                changed |= self._rewrite_command_paths(
                    value, prefix=prefix, install_root=install_root
                )
        elif isinstance(node, list):
            for item in node:
                changed |= self._rewrite_command_paths(
                    item, prefix=prefix, install_root=install_root
                )
        return changed

    def _dedupe_hook_entries_for_command_prefix(
        self,
        data: object,
        *,
        command_prefix: str,
    ) -> bool:
        """Remove duplicate hook entries for commands owned by this install.

        Global installs first merge converted hooks, then rewrite relative
        commands to absolute paths under the install root. Without this pass,
        repeated installs can append a relative source command that later becomes
        identical to the already-installed absolute command.
        """
        if not isinstance(data, dict):
            return False

        hooks_by_event = data.get("hooks")
        if not isinstance(hooks_by_event, dict):
            return False

        changed = False
        for event_name, entries in hooks_by_event.items():
            if not isinstance(entries, list):
                continue

            seen_owned_identities: set[tuple[str, str]] = set()
            deduped_entries = []
            for entry in entries:
                identities = self._hook_entry_identities([entry])
                owned_identities = {
                    identity
                    for identity in identities
                    if identity[1].startswith(command_prefix)
                }
                if owned_identities and owned_identities.issubset(
                    seen_owned_identities
                ):
                    changed = True
                    logger.info(
                        "Removed duplicate %s hook entry for commands: %s",
                        event_name,
                        sorted(command for _, command in owned_identities),
                    )
                    continue

                deduped_entries.append(entry)
                seen_owned_identities.update(owned_identities)

            if len(deduped_entries) != len(entries):
                hooks_by_event[event_name] = deduped_entries

        return changed

    def _copy_dir_merge(self, source_dir: Path, target_dir: Path) -> None:
        """Recursively merge source_dir into target_dir."""
        for source_item in source_dir.iterdir():
            target_item = target_dir / source_item.name
            if source_item.is_dir():
                self._copy_dir_merge(source_item, target_item)
                continue

            target_item.parent.mkdir(parents=True, exist_ok=True)
            if source_item.name == "hooks.json" and target_item.exists():
                self._merge_hooks_json(source_item, target_item)
            elif source_item.name == "config.toml" and target_item.exists():
                self._merge_config_toml(source_item, target_item)
            else:
                shutil.copy2(source_item, target_item)

    def _merge_hooks_json(self, source_path: Path, target_path: Path) -> None:
        """Merge Codex hooks maps without duplicating existing entries."""
        source = json.loads(source_path.read_text(encoding="utf-8"))
        target = json.loads(target_path.read_text(encoding="utf-8"))

        source_hooks = source.get("hooks", {})
        target_hooks = target.setdefault("hooks", {})
        if not isinstance(source_hooks, dict) or not isinstance(target_hooks, dict):
            raise InstallerError(
                f"Cannot merge hooks config because 'hooks' is not an object: {target_path}"
            )

        for event_name, entries in source_hooks.items():
            if not isinstance(entries, list):
                raise InstallerError(
                    f"Cannot merge hooks event {event_name!r}: expected list."
                )
            existing = target_hooks.setdefault(event_name, [])
            if not isinstance(existing, list):
                raise InstallerError(
                    f"Cannot merge hooks event {event_name!r}: target is not a list."
                )
            for entry in entries:
                if entry not in existing:
                    existing.append(entry)

        target_path.write_text(
            json.dumps(target, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _hook_entry_identities(self, entries: list) -> set[tuple[str, str]]:
        """Return semantic identities for hook commands inside entries.

        Hook entries can differ in matcher/status metadata while still invoking
        the same command. Command identity is the stable duplicate guard.
        """
        identities: set[tuple[str, str]] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            hooks = entry.get("hooks")
            if not isinstance(hooks, list):
                continue
            for hook in hooks:
                if not isinstance(hook, dict):
                    continue
                hook_type = hook.get("type")
                command = hook.get("command")
                if isinstance(hook_type, str) and isinstance(command, str):
                    identities.add((hook_type, command))
        return identities

    def _merge_config_toml(self, source_path: Path, target_path: Path) -> None:
        """Merge required Codex config flags into an existing config.toml."""
        source = tomllib.loads(source_path.read_text(encoding="utf-8"))
        target = tomllib.loads(target_path.read_text(encoding="utf-8"))

        source_features = source.get("features", {})
        if isinstance(source_features, dict):
            target_features = target.setdefault("features", {})
            if not isinstance(target_features, dict):
                raise InstallerError(
                    f"Cannot merge features into non-table config section: {target_path}"
                )
            for key, value in source_features.items():
                target_features[key] = value
            self._remove_deprecated_feature_flags(target_features, source_features)

        target_path.write_text(tomli_w.dumps(target), encoding="utf-8")

    def _remove_deprecated_feature_flags(
        self,
        target_features: dict,
        desired_features: dict,
    ) -> None:
        """Remove old Codex feature flag keys when their replacement is desired."""
        for deprecated_key, replacement_key in DEPRECATED_FEATURE_FLAGS.items():
            if (
                replacement_key in desired_features
                and deprecated_key in target_features
            ):
                del target_features[deprecated_key]
                logger.info(
                    "Removed deprecated feature flag: %s (use %s)",
                    deprecated_key,
                    replacement_key,
                )

    def _update_config_toml(
        self,
        config: dict,
        install_root: Path | None = None,
    ) -> dict:
        """DC-8-4: Update config dict with required feature flags (idempotent).

        Does NOT duplicate entries if already present:
        - features: only sets keys if not already equal to desired value

        Args:
            config: Current TOML config as dict (may be empty).

        Returns:
            Updated config dict (suitable for tomli_w.dumps()).
        """
        import copy

        result = copy.deepcopy(config)

        # --- Feature flags (idempotent) ---
        if self._config.permissions and self._config.permissions.feature_flags:
            features_section = result.get("features", {})
            if not isinstance(features_section, dict):
                features_section = {}

            desired_features = self._config.permissions.feature_flags
            for key, value in desired_features.items():
                existing = features_section.get(key)
                if existing != value:
                    features_section[key] = value
                    logger.info("Setting feature flag: %s = %s", key, value)
                else:
                    logger.debug(
                        "Feature flag already set correctly: %s = %s (idempotent)",
                        key,
                        value,
                    )

            self._remove_deprecated_feature_flags(features_section, desired_features)
            result["features"] = features_section

        if install_root is not None:
            self._remove_stale_hook_state_entries(result, install_root=install_root)

        return result

    def _remove_stale_hook_state_entries(
        self,
        config: dict,
        *,
        install_root: Path,
    ) -> None:
        """Remove Codex hook trust state entries for hook indexes that no longer exist."""
        paths = self._config.paths
        if paths is None or not paths.plugin_dir or not paths.hooks_file:
            return

        hook_file = install_root / paths.plugin_dir / paths.hooks_file
        if not hook_file.exists():
            return

        hooks_section = config.get("hooks")
        if not isinstance(hooks_section, dict):
            return

        state_section = hooks_section.get("state")
        if not isinstance(state_section, dict):
            return

        valid_keys = self._current_hook_state_keys(hook_file)
        hook_file_prefix = f"{hook_file}:"

        for key in list(state_section):
            if key.startswith(hook_file_prefix) and key not in valid_keys:
                del state_section[key]
                logger.info("Removed stale hook state entry: %s", key)

    def _current_hook_state_keys(self, hook_file: Path) -> set[str]:
        """Return Codex hook state keys that correspond to the current hooks file."""
        try:
            data = json.loads(hook_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise InstallerError(
                f"Cannot prune hook state because {hook_file} is not valid JSON: {e}"
            ) from e

        hooks_by_event = data.get("hooks") if isinstance(data, dict) else None
        if not isinstance(hooks_by_event, dict):
            return set()

        valid_keys: set[str] = set()
        for event_name, entries in hooks_by_event.items():
            if not isinstance(event_name, str) or not isinstance(entries, list):
                continue
            state_event_name = self._codex_hook_state_event_name(event_name)
            for entry_index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    continue
                hooks = entry.get("hooks")
                if not isinstance(hooks, list):
                    continue
                for hook_index, _hook in enumerate(hooks):
                    valid_keys.add(
                        f"{hook_file}:{state_event_name}:{entry_index}:{hook_index}"
                    )
        return valid_keys

    def _codex_hook_state_event_name(self, event_name: str) -> str:
        """Convert Codex hook event names to config.toml hook-state key names."""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", event_name).lower()

    def _global_install_instructions(
        self,
        install_root: Path,
        config_path: Path,
        *,
        scope_note: str = "",
    ) -> str:
        """Build post-install instructions for global scope install."""
        return (
            f"samsara native {self._platform} files installed under: {install_root}\n"
            f"Config updated: {config_path}\n\n"
            "Next steps:\n"
            "  1. Open /hooks and review/trust the generated Samsara hooks.\n"
            f"  2. Restart {self._platform} to load the skills, agents, and hooks.\n"
            f"  3. A backup of your previous config is at: {config_path}.bak\n"
            f"{scope_note}"
        )

    def _scope_overlap_note(self, *, scope: Scope, cwd: Path) -> str:
        """Disclose when Codex can load both project and global Samsara installs."""
        home = Path(os.environ.get("HOME", str(Path.home())))
        other_root = home if scope == "project" else cwd
        other_manifest = self._install_manifest_path(other_root)
        if not other_manifest.exists():
            return ""
        other_scope = "global" if scope == "project" else "project"
        return (
            "\nScope note:\n"
            f"  A {other_scope} Samsara install also exists at {other_manifest}.\n"
            "  Codex can load both scopes; project configuration takes precedence. "
            "Review /hooks in the active project before assuming both installs behave "
            "the same.\n"
        )
