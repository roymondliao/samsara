"""
Death tests for config loader — targeting silent failure paths.

These test that the loader FAILS LOUDLY on bad input, not silently.
"""

import pytest
from hydra.errors import HydraException, MissingConfigException

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.schema import PlatformConfig


# --- DC-5: Unknown platform must fail explicitly, not return empty config ---
# Silent failure guarded: If an unknown platform returns an empty PlatformConfig,
# the conversion pipeline runs with no transformation rules and no path config.
# Output looks like it ran but produces structurally empty files. The user may
# not notice until reviewing the output files manually.


class TestUnknownPlatformFails:
    def test_unknown_platform_raises_not_returns_empty(self):
        """load_platform_config('nonexistent') must raise, not return empty config."""
        with pytest.raises((MissingConfigException, HydraException, ValueError)):
            load_platform_config("nonexistent")
        # Must fail, not return None or empty PlatformConfig
        # The exception type tells the caller exactly what went wrong

    def test_empty_string_platform_raises(self):
        """Empty string platform name must fail explicitly."""
        with pytest.raises((MissingConfigException, HydraException, ValueError)):
            load_platform_config("")

    def test_none_platform_raises(self):
        """None platform must fail explicitly — not silently load defaults."""
        with pytest.raises(
            (MissingConfigException, HydraException, TypeError, ValueError)
        ):
            load_platform_config(None)


# --- DC-6: Multiple sequential loads must not leak GlobalHydra state ---
# Silent failure guarded: If GlobalHydra state leaks between calls, the second
# call might inherit config overrides from the first. This could silently produce
# a 'codex' config when 'claude-code' was requested (or vice versa), with no
# error raised. The wrong transformation rules would be applied silently.


class TestHydraStateIsolation:
    def test_two_sequential_loads_are_independent(self):
        """Two sequential load_platform_config calls must be independent.
        Each call must load the correct platform without GlobalHydra state pollution."""
        config1 = load_platform_config("codex")
        config2 = load_platform_config("codex")
        # Both should succeed and be equal (same platform, no state leakage)
        assert config1.platform.name == "codex"
        assert config2.platform.name == "codex"

    def test_load_after_failed_load_does_not_poison_state(self):
        """A failed load must not leave GlobalHydra in a broken state that
        prevents subsequent valid loads from working."""
        # First call fails
        with pytest.raises((MissingConfigException, HydraException, ValueError)):
            load_platform_config("nonexistent")
        # Second call must succeed cleanly
        config = load_platform_config("codex")
        assert config.platform.name == "codex"


# --- DC-7: Codex platform config must load with all required sections ---
# Silent failure guarded: If any required section (paths, install, formats,
# naming, permissions, transformations) silently defaults to empty/None,
# downstream tasks have no config to work with and produce empty output.


class TestCodexPlatformLoads:
    def test_codex_loads_with_all_required_sections(self):
        """Codex platform config must have all required sections non-empty."""
        config = load_platform_config("codex")
        assert isinstance(config, PlatformConfig)
        assert config.platform.name == "codex"
        assert config.paths is not None, "paths section must not be None"
        assert config.install is not None, "install section must not be None"
        assert config.formats is not None, "formats section must not be None"
        assert config.naming is not None, "naming section must not be None"
        assert config.permissions is not None, "permissions section must not be None"
        assert config.transformations is not None, "transformations must not be None"
        assert len(config.transformations) > 0, (
            "transformations must not be empty — empty rules silently produce unchanged output"
        )

    def test_codex_transformations_have_all_required_fields(self):
        """Every transformation rule must have id, scope, type, match, replace, priority.
        A rule with a missing field would silently skip or produce wrong output."""
        config = load_platform_config("codex")
        for rule in config.transformations:
            assert rule.id, f"Rule has no id: {rule}"
            assert rule.scope, f"Rule '{rule.id}' has no scope"
            assert rule.type, f"Rule '{rule.id}' has no type"
            assert rule.match, f"Rule '{rule.id}' has no match"
            assert rule.replace is not None, f"Rule '{rule.id}' has no replace"
            assert rule.priority, f"Rule '{rule.id}' has no priority"
