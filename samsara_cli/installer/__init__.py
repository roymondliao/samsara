"""
samsara_cli.installer — Platform detection and installation logic.

Exports:
- PlatformDetector: detects whether a target platform CLI is installed
- Installer: installs converted output to project or global scope
- InstallerError: raised when install preconditions fail
"""

from samsara_cli.installer.detect import PlatformDetector
from samsara_cli.installer.install import Installer, InstallerError

__all__ = ["PlatformDetector", "Installer", "InstallerError"]
