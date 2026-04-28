"""
Config loader using Hydra compose API + Pydantic validation.

Design decisions:
- Uses initialize_config_dir() with an absolute path derived from __file__,
  NOT initialize() with a relative path. This is because initialize() resolves
  config_path relative to the CALLING MODULE's parent directory. When loader.py
  is in samsara_cli/config/, initialize(config_path=".") would correctly resolve
  to samsara_cli/config/ — but this is fragile under refactoring or when called
  from different call stacks (e.g., tests). initialize_config_dir() with an
  explicit absolute path is unambiguous regardless of call location.

- Uses context manager pattern (with initialize_config_dir(...):) which
  automatically calls GlobalHydra.instance().clear() on exit. This ensures
  multiple sequential calls don't leak state. Verified: GlobalHydra IS cleared
  after context exit (tested manually before implementation).

- Calls GlobalHydra.instance().clear() defensively before entering the context.
  This handles the case where a previous failed call left GlobalHydra initialized
  without cleanup (e.g., if the context manager's __exit__ wasn't reached due to
  a hard crash — unlikely but possible in test environments with signal handling).

Assumption: The config directory is always at samsara_cli/config/ relative to
this file. If loader.py moves, CONFIG_DIR must be updated. If this assumption
breaks, the loader will raise FileNotFoundError or HydraException on init.
"""

from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra.core.global_hydra import GlobalHydra
from omegaconf import OmegaConf

from samsara_cli.config.schema import PlatformConfig

# Absolute path to the config directory.
# This file is samsara_cli/config/loader.py
# The config directory IS samsara_cli/config/ — same directory.
_CONFIG_DIR = str(Path(__file__).parent.resolve())


def load_platform_config(platform: str) -> PlatformConfig:
    """Load and validate platform config for the given platform name.

    Args:
        platform: Platform identifier matching a YAML file in config/platform/.
                  E.g., "codex", "claude-code".

    Returns:
        PlatformConfig: Validated Pydantic model with all platform settings.

    Raises:
        hydra.errors.MissingConfigException: If platform YAML does not exist.
        hydra.errors.HydraException: If Hydra config composition fails.
        pydantic.ValidationError: If loaded config fails schema validation.
        TypeError: If platform is None.

    This implementation assumes: all errors from Hydra (MissingConfigException,
    HydraException) will propagate to the caller unchanged. There is no catch-and-
    default behavior. An unknown platform should never silently return empty config.
    """
    if platform is None:
        raise TypeError(
            "platform must be a string, not None. "
            "Passing None would silently load the default platform from config.yaml."
        )
    if not isinstance(platform, str) or platform.strip() == "":
        raise ValueError(
            f"platform must be a non-empty string, got: {platform!r}. "
            "Empty platform name would load an ambiguous default."
        )

    # Clear any leftover GlobalHydra state from previous calls or failed tests.
    # Without this, a second call after a failed first call would raise
    # "GlobalHydra is already initialized" instead of loading correctly.
    GlobalHydra.instance().clear()

    with initialize_config_dir(config_dir=_CONFIG_DIR, version_base="1.3"):
        cfg = compose(
            config_name="config",
            overrides=[f"platform={platform}"],
        )

    # Convert DictConfig to plain Python dict with all interpolations resolved.
    # resolve=True expands ${...} interpolations in OmegaConf configs.
    # throw_on_missing=True ensures missing values raise instead of returning ???.
    data = OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)

    # Pydantic v2 constructs nested models from nested plain dicts automatically.
    # This will raise ValidationError if the YAML structure doesn't match the schema.
    return PlatformConfig(**data)
