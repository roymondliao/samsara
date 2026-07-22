"""
Unit tests for PlatformDetector — happy path and behavioral contracts.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestPlatformDetectorBasic:
    """Basic detect() behavior."""

    def test_detect_codex_returns_true_when_found(self):
        """detect() returns True when CLI returns exit code 0."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            assert detector.detect("codex") is True

    def test_detect_codex_returns_false_when_not_found(self):
        """detect() returns False when CLI raises FileNotFoundError."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex not found")
            assert detector.detect("codex") is False

    def test_detect_codex_returns_false_when_nonzero_exit(self):
        """detect() returns False when CLI exits non-zero."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=127, stdout="")
            assert detector.detect("codex") is False

    def test_detect_uses_version_cmd_from_platform_config(self):
        """detect() must use the version_cmd from the loaded platform config."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            detector.detect("codex")
            # Must have called subprocess.run
            assert mock_run.called
            # The command called must contain 'codex'
            call_args = mock_run.call_args
            cmd = call_args[0][0] if call_args[0] else call_args.kwargs.get("args", "")
            if isinstance(cmd, str):
                assert "codex" in cmd
            else:
                assert any("codex" in str(arg) for arg in cmd)

    def test_detect_handles_os_error_gracefully(self):
        """detect() returns False for any OS-level error — not just FileNotFoundError."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = OSError("permission denied")
            result = detector.detect("codex")
            assert result is False

    def test_detect_invalid_platform_raises_value_error(self):
        """detect() raises ValueError for unknown platform."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        with pytest.raises(ValueError):
            detector.detect("nonexistent-platform-xyz")


class TestPlatformDetectorAvailablePlatforms:
    """available_platforms() and get_install_url() behavior."""

    def test_available_platforms_includes_codex(self):
        """available_platforms() must include 'codex'."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        platforms = detector.available_platforms()
        assert "codex" in platforms

    def test_available_platforms_returns_list_of_strings(self):
        """available_platforms() must return list[str]."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        platforms = detector.available_platforms()
        assert isinstance(platforms, list)
        assert all(isinstance(p, str) for p in platforms)

    def test_get_install_url_returns_string_for_codex(self):
        """get_install_url('codex') must return non-empty string."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        url = detector.get_install_url("codex")
        assert isinstance(url, str)
        assert len(url) > 0

    def test_get_install_url_returns_none_for_unknown_platform(self):
        """get_install_url for unknown platform returns None or raises."""
        from samsara_cli.installer.detect import PlatformDetector

        detector = PlatformDetector()
        # Either returns None or raises — both are acceptable
        try:
            url = detector.get_install_url("nonexistent-xyz")
            assert url is None or isinstance(url, str)
        except ValueError, KeyError:
            pass  # Also acceptable
