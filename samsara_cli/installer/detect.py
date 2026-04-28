"""
PlatformDetector — Detect whether a target platform CLI is installed.

Design decisions:
- detect() NEVER raises on CLI absence — it returns False. Callers (Installer)
  raise InstallerError with a user-readable message. This separates detection
  from error-display concerns.
- detect() DOES raise ValueError for unknown platforms — the platform name is
  a programmer error, not a runtime condition.
- version_cmd is read from the platform config (PlatformConfig.platform.version_cmd).
  If version_cmd is None (platform config doesn't define it), detect() logs a warning
  and returns False (reports as not installed). Detection cannot be skipped silently.
- available_platforms() discovers platforms by listing config/platform/*.yaml files,
  excluding claude-code.yaml (source format, not a target platform). This avoids
  hardcoding a platform list that would drift from actual config files.

Silent failure conditions:
- If subprocess.run is mocked incorrectly in tests (wrong signature), subprocess
  calls could succeed when they should fail. Detection must use check=False (not
  check=True) to avoid CalledProcessError on non-zero exit.
- If version_cmd is None, detect() returns False — a platform without a version_cmd
  is reported as not installed. Callers receive an honest "not detected" signal.

Assumptions:
1. Platform config is at samsara_cli/config/platform/{platform}.yaml
2. version_cmd is a shell command string like "codex --version"
3. A zero exit code from version_cmd means CLI is installed
4. claude-code.yaml is the source format and must be excluded from target platforms
"""

import logging
import subprocess
from pathlib import Path

from hydra.errors import MissingConfigException

from samsara_cli.config.loader import load_platform_config

logger = logging.getLogger(__name__)

# Install URLs for known platforms.
# This is a static map — if new platforms are added, this map must be updated.
# Known gap: if a platform's install URL changes, this must be updated manually.
_INSTALL_URLS: dict[str, str] = {
    "codex": "https://github.com/openai/codex — install Codex CLI first",
}

# Platform YAML directory — used by available_platforms() for discovery.
_PLATFORM_CONFIG_DIR = Path(__file__).parent.parent / "config" / "platform"

# Source format platform — excluded from target platform list.
_SOURCE_PLATFORM = "claude-code"


class PlatformDetector:
    """Detects whether a target platform CLI is installed on the current system.

    Usage:
        detector = PlatformDetector()
        if not detector.detect("codex"):
            url = detector.get_install_url("codex")
            raise InstallerError(f"Codex CLI not installed. Install from: {url}")

    Thread safety: stateless — each detect() call is independent.
    """

    def detect(self, platform: str) -> bool:
        """Check if the target platform CLI is installed.

        Args:
            platform: Platform identifier (e.g., "codex").
                      Must match a YAML file in config/platform/.

        Returns:
            True if the platform CLI is detected (version_cmd exits 0).
            False if the CLI is not found or exits non-zero.

        Raises:
            ValueError: If platform is empty, None, or not a known target platform.
                        Error message includes list of available platforms.
            TypeError: If platform is None.

        Note: This method NEVER raises on CLI absence — it returns False.
        Only programmer errors (invalid platform name) raise.
        """
        if platform is None:
            raise TypeError(
                "platform must be a string, not None. "
                "Pass a platform name like 'codex'."
            )
        if not isinstance(platform, str) or platform.strip() == "":
            raise ValueError(
                f"platform must be a non-empty string, got: {platform!r}. "
                f"Available platforms: {self.available_platforms()}"
            )

        # Validate platform exists in config — fail loud for unknown platforms
        try:
            config = load_platform_config(platform)
        except MissingConfigException:
            available = self.available_platforms()
            raise ValueError(
                f"Unknown platform: {platform!r}. "
                f"Available platforms: {available}. "
                "Add a platform config YAML to samsara_cli/config/platform/ to register a new platform."
            ) from None
        except Exception as e:
            # Config load errors (pydantic validation, hydra) — propagate as ValueError
            raise ValueError(
                f"Failed to load platform config for {platform!r}: {e}"
            ) from e

        version_cmd = config.platform.version_cmd
        if version_cmd is None:
            logger.warning(
                "Platform '%s' has no version_cmd — cannot detect CLI presence. "
                "Reporting as not installed.",
                platform,
            )
            return False

        # Run the version command to detect CLI presence
        try:
            result = subprocess.run(
                version_cmd.split(),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,  # Do NOT raise on non-zero — we handle it below
            )
            if result.returncode == 0:
                logger.debug(
                    "Platform '%s' CLI detected: %s",
                    platform,
                    result.stdout.strip(),
                )
                return True
            else:
                logger.debug(
                    "Platform '%s' CLI returned non-zero exit %d: %s",
                    platform,
                    result.returncode,
                    result.stderr.strip(),
                )
                return False
        except (FileNotFoundError, OSError) as e:
            logger.debug(
                "Platform '%s' CLI not found: %s",
                platform,
                e,
            )
            return False
        except subprocess.TimeoutExpired:
            logger.warning(
                "Platform '%s' version_cmd timed out after 10 seconds. "
                "Assuming not installed.",
                platform,
            )
            return False

    def available_platforms(self) -> list[str]:
        """Return list of known target platform names.

        Discovers platforms by listing YAML files in config/platform/,
        excluding the source format (claude-code).

        Returns:
            List of platform name strings. Always includes 'codex' if the
            config file exists. Never empty in a valid installation.
        """
        if not _PLATFORM_CONFIG_DIR.exists():
            logger.warning(
                "Platform config directory not found: %s. "
                "Returning empty platform list.",
                _PLATFORM_CONFIG_DIR,
            )
            return []

        platforms = []
        for yaml_file in sorted(_PLATFORM_CONFIG_DIR.glob("*.yaml")):
            name = yaml_file.stem
            if name == _SOURCE_PLATFORM:
                # Exclude source format — it's not a conversion target
                continue
            platforms.append(name)

        return platforms

    def get_install_url(self, platform: str) -> str | None:
        """Return install URL/instructions for the given platform.

        Args:
            platform: Platform identifier.

        Returns:
            Install URL string, or None if no URL is registered.
        """
        return _INSTALL_URLS.get(platform)
