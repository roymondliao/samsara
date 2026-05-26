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
import shutil
import tomllib
from pathlib import Path
from typing import Literal

import tomli_w

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.schema import PlatformConfig
from samsara_cli.converter.engine import ConversionEngine, EngineError
from samsara_cli.installer.detect import PlatformDetector

logger = logging.getLogger(__name__)

Scope = Literal["project", "global"]
DEPRECATED_FEATURE_FLAGS = {"codex_hooks": "hooks"}


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
            return self._install_global(converted_dir=converted_dir)
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
        self._install_native_tree(converted_dir=converted_dir, target_root=cwd)

        logger.info("Installed %s native files to: %s", self._platform, cwd)

        # Build post-install instructions
        return self._project_install_instructions(cwd)

    def _project_install_instructions(self, plugin_dir: Path) -> str:
        """Build post-install instructions for project scope install."""
        feature_flags_section = self._format_feature_flags_instructions()

        instructions = (
            f"samsara native {self._platform} files installed to: {plugin_dir}\n\n"
            "Next steps:\n"
            f"  1. Ensure your {self._platform} project is trusted.\n"
            f"  2. Restart {self._platform} to load the skills, agents, and hooks.\n"
            f"  3. Required feature flags are present in the project config:\n"
            f"{feature_flags_section}\n"
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

    def _install_global(self, converted_dir: Path) -> str:
        """Global scope install — copy native platform files under the user's home.

        Args:
            converted_dir: Path to converted output directory.

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

        config_path_raw = global_cfg.config_path
        if not config_path_raw:
            raise InstallerError(
                f"Platform '{self._platform}' global install config is missing "
                "'config_path'. Cannot determine which config file to update."
            )
        config_path = Path(config_path_raw.replace("~", str(home)))

        config_is_json = config_path.suffix == ".json"

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

        if config_is_json:
            return self._global_install_instructions(
                install_root=home,
                config_path=config_path,
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
            )

            config_path.write_bytes(tomli_w.dumps(modified).encode())
            logger.info("Updated config.toml at: %s", config_path)

        except OSError as e:
            raise InstallerError(
                f"Failed to write config.toml at {config_path}: {e}. "
                f"A backup is available at {backup_path}."
            ) from e

        return self._global_install_instructions(
            install_root=home,
            config_path=config_path,
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
            elif source_item.name == "settings.json" and target_item.exists():
                self._merge_settings_json(source_item, target_item)
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

    def _read_json_object(self, path: Path, *, empty_ok: bool = False) -> dict:
        """Read a JSON object config file.

        Empty files are allowed only for newly-created global settings files. Invalid
        non-empty JSON must fail loudly so installs do not overwrite user settings.
        """
        text = path.read_text(encoding="utf-8")
        if not text.strip() and empty_ok:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise InstallerError(
                f"Cannot merge JSON settings because {path} is not valid JSON: {e}"
            ) from e
        if not isinstance(data, dict):
            raise InstallerError(
                f"Cannot merge JSON settings because root is not an object: {path}"
            )
        return data

    def _merge_settings_json(self, source_path: Path, target_path: Path) -> None:
        """Merge Gemini settings.json without duplicating hook entries."""
        source = self._read_json_object(source_path)
        target = self._read_json_object(target_path, empty_ok=True)

        for key, value in source.items():
            if key != "hooks":
                target.setdefault(key, value)

        source_hooks = source.get("hooks", {})
        target_hooks = target.setdefault("hooks", {})
        if not isinstance(source_hooks, dict) or not isinstance(target_hooks, dict):
            raise InstallerError(
                f"Cannot merge Gemini settings because 'hooks' is not an object: {target_path}"
            )

        for event_name, entries in source_hooks.items():
            if not isinstance(entries, list):
                raise InstallerError(
                    f"Cannot merge Gemini hooks event {event_name!r}: expected list."
                )
            existing = target_hooks.setdefault(event_name, [])
            if not isinstance(existing, list):
                raise InstallerError(
                    f"Cannot merge Gemini hooks event {event_name!r}: target is not a list."
                )
            existing_identities = self._hook_entry_identities(existing)
            for entry in entries:
                entry_identities = self._hook_entry_identities([entry])
                if not entry_identities:
                    if entry not in existing:
                        existing.append(entry)
                    continue
                if existing_identities.isdisjoint(entry_identities):
                    existing.append(entry)
                    existing_identities.update(entry_identities)

        target_path.write_text(
            json.dumps(target, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _hook_entry_identities(self, entries: list) -> set[tuple[str, str]]:
        """Return semantic identities for hook commands inside entries.

        Gemini hook entries can differ in matcher/status metadata while still
        invoking the same command. Command identity is the stable duplicate guard.
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

        return result

    def _global_install_instructions(
        self,
        install_root: Path,
        config_path: Path,
    ) -> str:
        """Build post-install instructions for global scope install."""
        return (
            f"samsara native {self._platform} files installed under: {install_root}\n"
            f"Config updated: {config_path}\n\n"
            "Next steps:\n"
            f"  1. Restart {self._platform} to load the skills, agents, and hooks.\n"
            f"  2. A backup of your previous config is at: {config_path}.bak\n"
        )
