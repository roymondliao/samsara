"""
Installer — Install converted samsara output to project or global scope.

Design decisions:
- CLI presence check (via PlatformDetector.detect()) is the FIRST operation.
  No files are written before this check passes. This is DC-8-1 enforcement.
- Project scope NEVER modifies ~/.codex/config.toml. It only copies to CWD/.codex-plugin
  and returns instructions for the user to configure manually. This is DC-8-2 enforcement.
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
  - marketplace entry: check if [[marketplace]] with matching 'name' already exists
  - [features] flags: check if key already set to the same value

Assumptions:
1. config.toml is at ~/.codex/config.toml (from GlobalInstallConfig.config_path).
   If Codex uses a different config path, installs would modify the wrong file.
2. Marketplace registration format: [[marketplace]] with 'name' and 'path' keys.
   If Codex changes its config format, this installer would write invalid entries.
3. Feature flags are under [features] table in config.toml.
   If Codex moves feature flags to a different section, flags would be missed.
4. The marketplace_source path is the PARENT of where the plugin is placed.
   Plugin is placed at: {marketplace_source}/samsara/.codex-plugin/
   (i.e., {marketplace_source} is registered in config, and {marketplace_source}/samsara/
   is the plugin directory within the marketplace.)
"""

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
        """Install the samsara plugin for the given platform and scope.

        Args:
            source_dir: Root of the samsara source directory.
                        Used for conversion if converted_source_dir is not provided.
            scope: "project" (copy to CWD) or "global" (register in marketplace).
            cwd: Working directory for project scope (target: cwd/.codex-plugin).
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

        Copies the .codex-plugin directory (or equivalent) from converted_dir to CWD.
        Returns instructions for manual feature flag configuration.

        Args:
            converted_dir: Path to converted output directory.
            cwd: Target working directory (plugin is installed to cwd/.codex-plugin).

        Returns:
            Post-install instructions string.
        """
        # Determine source plugin dir from converted output
        plugin_dir_name = ".codex-plugin"
        if self._config.paths and self._config.paths.plugin_dir:
            plugin_dir_name = self._config.paths.plugin_dir

        source_plugin_dir = converted_dir / plugin_dir_name
        if not source_plugin_dir.exists():
            raise InstallerError(
                f"Expected plugin directory '{plugin_dir_name}' not found in "
                f"converted output: {converted_dir}. "
                "Run 'samsara-cli convert' first to produce a valid output."
            )

        target_plugin_dir = cwd / plugin_dir_name

        # Copy to CWD (overwrite if exists)
        if target_plugin_dir.exists():
            shutil.rmtree(target_plugin_dir)
        shutil.copytree(source_plugin_dir, target_plugin_dir)

        logger.info("Installed %s plugin to: %s", self._platform, target_plugin_dir)

        # Build post-install instructions
        return self._project_install_instructions(target_plugin_dir)

    def _project_install_instructions(self, plugin_dir: Path) -> str:
        """Build post-install instructions for project scope install."""
        feature_flags_section = self._format_feature_flags_instructions()

        instructions = (
            f"samsara plugin installed to: {plugin_dir}\n\n"
            "Next steps:\n"
            f"  1. Add the following to your {self._platform} project config:\n"
            f"{feature_flags_section}\n"
            f"  2. Restart {self._platform} to load the plugin.\n"
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
        """Global scope install — marketplace registration + config.toml modification.

        Steps:
        1. Determine marketplace source dir and config.toml path from platform config
        2. Create marketplace source dir structure
        3. Copy converted files to marketplace source dir
        4. Backup config.toml (DC-8-3)
        5. Modify config.toml (idempotent — DC-8-4)
        6. Return post-install instructions

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

        marketplace_source_raw = global_cfg.marketplace_source
        if not marketplace_source_raw:
            raise InstallerError(
                f"Platform '{self._platform}' global install config is missing "
                "'marketplace_source' path. Cannot determine where to install."
            )
        marketplace_source = Path(marketplace_source_raw.replace("~", str(home)))

        config_path_raw = global_cfg.config_path
        if not config_path_raw:
            raise InstallerError(
                f"Platform '{self._platform}' global install config is missing "
                "'config_path'. Cannot determine which config file to update."
            )
        config_path = Path(config_path_raw.replace("~", str(home)))

        plugin_name = global_cfg.plugin_name or "samsara"
        marketplace_name = global_cfg.marketplace_name or "samsara-local"

        # --- Step 1: Create marketplace source dir ---
        # Marketplace source dir: ~/.codex/plugins/samsara
        # Plugin lives at: {marketplace_source}/{plugin_name}/.codex-plugin/
        marketplace_source.mkdir(parents=True, exist_ok=True)
        logger.info("Marketplace source dir: %s", marketplace_source)

        # --- Step 2: Copy converted files to marketplace dir ---
        plugin_dir_name = ".codex-plugin"
        if self._config.paths and self._config.paths.plugin_dir:
            plugin_dir_name = self._config.paths.plugin_dir

        source_plugin_dir = converted_dir / plugin_dir_name
        if not source_plugin_dir.exists():
            raise InstallerError(
                f"Expected plugin directory '{plugin_dir_name}' not found in "
                f"converted output: {converted_dir}. "
                "Run 'samsara-cli convert' first to produce a valid output."
            )

        # Plugin destination: {marketplace_source}/{plugin_name}/.codex-plugin/
        dest_plugin_parent = marketplace_source / plugin_name
        dest_plugin_dir = dest_plugin_parent / plugin_dir_name

        dest_plugin_parent.mkdir(parents=True, exist_ok=True)
        if dest_plugin_dir.exists():
            shutil.rmtree(dest_plugin_dir)
        shutil.copytree(source_plugin_dir, dest_plugin_dir)
        logger.info("Copied plugin to: %s", dest_plugin_dir)

        # Also copy skills, agents, etc. from converted_dir to plugin parent
        # (so the full converted output is available in the marketplace dir)
        for item in converted_dir.iterdir():
            if item.name == plugin_dir_name:
                continue  # Already handled above
            dest = dest_plugin_parent / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # --- Step 3: Ensure config.toml exists ---
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text("")
            logger.info("Created new config.toml at: %s", config_path)

        # --- Step 4: DC-8-3 Backup config.toml BEFORE any modification ---
        backup_path = config_path.parent / (config_path.name + ".bak")
        try:
            shutil.copy2(config_path, backup_path)
            logger.info("Backed up config.toml to: %s", backup_path)
        except OSError as e:
            raise InstallerError(
                f"DC-8-3: Cannot backup config.toml before modification: {e}. "
                "Aborting to prevent config loss. Fix the backup location and retry."
            ) from e

        # --- Step 5: DC-8-4 Modify config.toml (idempotent) ---
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
                marketplace_name=marketplace_name,
                marketplace_source=str(marketplace_source),
                plugin_name=plugin_name,
            )

            config_path.write_bytes(tomli_w.dumps(modified).encode())
            logger.info("Updated config.toml at: %s", config_path)

        except OSError as e:
            raise InstallerError(
                f"Failed to write config.toml at {config_path}: {e}. "
                f"A backup is available at {backup_path}."
            ) from e

        return self._global_install_instructions(
            marketplace_source=marketplace_source,
            config_path=config_path,
        )

    def _update_config_toml(
        self,
        config: dict,
        marketplace_name: str,
        marketplace_source: str,
        plugin_name: str,
    ) -> dict:
        """DC-8-4: Update config dict with marketplace + feature flags (idempotent).

        Does NOT duplicate entries if already present:
        - marketplace: checks for existing entry with matching 'name'
        - features: only sets keys if not already equal to desired value

        Args:
            config: Current TOML config as dict (may be empty).
            marketplace_name: Name for the marketplace registration.
            marketplace_source: Path to the marketplace source directory.
            plugin_name: Plugin name within the marketplace.

        Returns:
            Updated config dict (suitable for tomli_w.dumps()).
        """
        import copy

        result = copy.deepcopy(config)

        # --- Marketplace registration (idempotent) ---
        # TOML: [[marketplace]]
        # name = "samsara-local"
        # path = "~/.codex/plugins/samsara"
        marketplace_list = result.get("marketplace", [])
        if not isinstance(marketplace_list, list):
            marketplace_list = []

        # Check if already registered (by marketplace name)
        already_registered = any(
            isinstance(entry, dict) and entry.get("name") == marketplace_name
            for entry in marketplace_list
        )

        if not already_registered:
            marketplace_list.append(
                {
                    "name": marketplace_name,
                    "path": marketplace_source,
                }
            )
            logger.info(
                "Adding marketplace entry: name=%s, path=%s",
                marketplace_name,
                marketplace_source,
            )
        else:
            logger.info(
                "Marketplace entry already registered: %s (idempotent — skipping)",
                marketplace_name,
            )

        result["marketplace"] = marketplace_list

        # --- Plugin enable (idempotent) ---
        # TOML: [plugins]
        # enabled = ["samsara"]
        plugins_section = result.get("plugins", {})
        if not isinstance(plugins_section, dict):
            plugins_section = {}
        enabled_plugins = plugins_section.get("enabled", [])
        if not isinstance(enabled_plugins, list):
            enabled_plugins = []
        if plugin_name not in enabled_plugins:
            enabled_plugins.append(plugin_name)
            logger.info("Enabling plugin: %s", plugin_name)
        plugins_section["enabled"] = enabled_plugins
        result["plugins"] = plugins_section

        # --- Feature flags (idempotent) ---
        # TOML: [features]
        # codex_hooks = true
        if self._config.permissions and self._config.permissions.feature_flags:
            features_section = result.get("features", {})
            if not isinstance(features_section, dict):
                features_section = {}

            for key, value in self._config.permissions.feature_flags.items():
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

            result["features"] = features_section

        return result

    def _global_install_instructions(
        self,
        marketplace_source: Path,
        config_path: Path,
    ) -> str:
        """Build post-install instructions for global scope install."""
        return (
            f"samsara plugin installed to: {marketplace_source}\n"
            f"Config updated: {config_path}\n\n"
            "Next steps:\n"
            f"  1. Restart {self._platform} to load the plugin.\n"
            "  2. The samsara marketplace and plugin are now registered.\n"
            f"  3. A backup of your previous config is at: {config_path}.bak\n"
        )
