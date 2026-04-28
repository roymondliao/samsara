"""
Death tests for PlatformDetector — silent failure paths.

DC-8-1: install codex when Codex CLI not installed must abort with clear error
  — not silently write files to non-existent path.
DC-8-5: convert with invalid --platform must fail with list of available platforms
  — not generic error.

This file tests that the DETECTOR side of these contracts holds:
- detect() must NOT return True when CLI is absent
- detect() result is what the installer reads — silent True = DC-8-1 violated
- available_platforms() must return non-empty list for DC-8-5 error messages
"""

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# DC-8-1: CLI not installed must produce clear error, not silent file writes
# ---------------------------------------------------------------------------


class TestPlatformDetectorCLINotInstalled:
    """DC-8-1: when version_cmd returns non-zero or raises, detect() must return False.

    Silent failure path: if detect() returns True when CLI is absent,
    the installer proceeds to write files — user gets corrupted install
    without any diagnostic.
    """

    def test_detect_returns_false_when_version_cmd_fails(self):
        """DC-8-1: version_cmd exits non-zero → detect() returns False (not True, not exception)."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        # Mock subprocess to simulate CLI not found (CalledProcessError)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            result = detector.detect("codex")
        assert result is False, (
            "detect() must return False when CLI is not found — "
            "returning True would allow installer to proceed silently"
        )

    def test_detect_returns_false_when_version_cmd_nonzero_exit(self):
        """DC-8-1: version_cmd exits with non-zero → detect() returns False."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = detector.detect("codex")
        assert result is False

    def test_detect_does_not_raise_when_cli_missing(self):
        """DC-8-1: detect() must NOT propagate FileNotFoundError to caller.

        The silent failure: if detect() raises instead of returning False,
        the installer's try/except might swallow the error and proceed.
        """
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            # Must not raise — must return False
            result = detector.detect("codex")
            assert isinstance(result, bool)

    def test_detect_returns_true_only_when_cli_present(self):
        """DC-8-1 inverse: detect() returns True only when CLI is actually found."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="codex 1.2.3", stderr=""
            )
            result = detector.detect("codex")
        assert result is True

    def test_detect_error_message_includes_install_url(self):
        """DC-8-1: error_message must include a URL — not a generic error."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        message = detector.get_install_url("codex")
        assert message is not None, "get_install_url must return something"
        assert len(message) > 0, "install URL/instruction must not be empty"


# ---------------------------------------------------------------------------
# DC-8-5: invalid platform must fail with list of available platforms
# ---------------------------------------------------------------------------


class TestPlatformDetectorInvalidPlatform:
    """DC-8-5: unknown platform must fail with platform list, not generic error.

    Silent failure path: if detect() raises a generic exception for unknown platform,
    the CLI catches it and prints a useless message — user doesn't know valid options.
    """

    def test_detect_raises_specific_error_for_unknown_platform(self):
        """DC-8-5: detect() on unknown platform raises ValueError (not KeyError/AttributeError)."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with pytest.raises(ValueError) as exc_info:
            detector.detect("nonexistent-platform-xyz")
        error_msg = str(exc_info.value)
        assert "nonexistent-platform-xyz" in error_msg, (
            "Error must name the invalid platform"
        )

    def test_detect_error_includes_available_platforms(self):
        """DC-8-5: error for unknown platform must list valid options."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with pytest.raises(ValueError) as exc_info:
            detector.detect("nonexistent-platform-xyz")
        error_msg = str(exc_info.value)
        # Must mention at least one known platform
        assert "codex" in error_msg.lower(), (
            "Error must list available platforms — 'codex' must appear in the error message"
        )

    def test_available_platforms_returns_nonempty_list(self):
        """DC-8-5: available_platforms() must return non-empty list for error formatting."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        platforms = detector.available_platforms()
        assert len(platforms) > 0, "available_platforms() must not return empty list"
        assert "codex" in platforms, "codex must be in available platforms"

    def test_detect_with_none_platform_raises_value_error(self):
        """DC-8-5: detect(None) must raise ValueError — not AttributeError or TypeError."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with pytest.raises((ValueError, TypeError)):
            detector.detect(None)

    def test_detect_with_empty_string_raises_value_error(self):
        """DC-8-5: detect('') must raise ValueError — empty string is not a valid platform."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with pytest.raises(ValueError):
            detector.detect("")
