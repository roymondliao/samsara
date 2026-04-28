"""
Pydantic schema for platform configuration.

All models use extra='forbid' so typos in YAML keys are caught at load time,
not at conversion time. A misspelled key (e.g., 'formts') would otherwise
create a silently ignored section, causing downstream tasks to receive None.

Assumption: Pydantic v2 with OmegaConf.to_container() output.
OmegaConf returns plain Python dicts/lists, which Pydantic v2 accepts.
Nested structures are coerced via Pydantic's normal dict-to-model conversion.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base model with extra='forbid'. All platform config models inherit this.

    This design assumes: extra fields are always a bug (typo in YAML).
    If a platform legitimately needs extensible fields, use a dedicated
    dict-typed field (e.g., feature_flags: dict[str, Any]).
    If this assumption breaks, the first thing to rot is the 'extra_fields'
    accumulating silently without any validation.
    """

    model_config = ConfigDict(extra="forbid")


class PlatformIdentity(StrictModel):
    """platform: section — identifies the target platform."""

    name: str
    version_cmd: str | None = None


class SourceConfig(StrictModel):
    """source: section — paths to claude-code plugin source files."""

    plugin_dir: str
    skills_dir: str
    agents_dir: str
    hooks_dir: str
    references_dir: str


class PathsConfig(StrictModel):
    """paths: section — target platform output paths."""

    plugin_dir: str
    plugin_manifest: str | None = None
    skills_dir: str | None = None
    agents_dir: str | None = None
    hooks_file: str | None = None


class ProjectInstallConfig(StrictModel):
    """install.project: section — local project installation target."""

    target: str


class GlobalInstallConfig(StrictModel):
    """install.global: section — global/marketplace installation config."""

    marketplace_name: str | None = None
    marketplace_source: str | None = None
    plugin_name: str | None = None
    config_path: str | None = None


class InstallConfig(StrictModel):
    """install: section — installation targets for the converted plugin."""

    project: ProjectInstallConfig
    global_: GlobalInstallConfig | None = Field(None, alias="global")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FormatsConfig(StrictModel):
    """formats: section — output format definitions per artifact type."""

    # Stored as raw dicts because format structure varies per platform.
    # The transformer tasks parse these dicts using their own typed models.
    # This design assumes: format structure is platform-specific enough
    # that a single shared Pydantic model would be more hindrance than help.
    # If this assumption breaks, the first to rot is format validation —
    # wrong template names or missing fields won't be caught until render time.
    agent_format: dict[str, Any] | None = Field(None, alias="agent")
    hook_output: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class NamingConfig(StrictModel):
    """naming: section — naming conventions for output artifacts."""

    skill_prefix: str
    separator: str


class PermissionsConfig(StrictModel):
    """permissions: section — platform permission and feature flag config."""

    sandbox_mode: str | None = None
    feature_flags: dict[str, Any] = Field(default_factory=dict)


class TransformationRule(StrictModel):
    """A single transformation rule for converting agent content.

    Scope controls which part of the source file is targeted:
    - 'body': The main markdown body of the agent/skill file
    - 'frontmatter': The YAML frontmatter block

    Type determines how 'match' is interpreted:
    - 'literal': match is a plain string (str.replace semantics)
    - 'regex': match is a Python regex pattern (re.sub semantics)

    The regex validator runs at Pydantic validation time — before any
    conversion happens. This is intentional: an invalid regex in a YAML
    config file should fail at load time, not when a specific agent file
    happens to be processed (which could be deep in a batch run).
    """

    id: str
    scope: Literal["body", "frontmatter"]
    type: Literal["literal", "regex"]
    match: str
    replace: str
    priority: Literal["high", "medium", "low"]

    @field_validator("replace")
    @classmethod
    def validate_replace_backrefs(cls, v: str, info: Any) -> str:
        """Reject $N backrefs in regex replace strings. Python re.sub uses \\1, not $1.
        $1 silently produces literal '$1' in output — the captured group is lost.

        Fires for ALL rules but only checks when type='regex'. For type='literal',
        $1 is valid literal text. Depends on 'type' being in info.data (validated
        before 'replace' in field declaration order). If Pydantic changes field
        validation order, this silently skips the check — same fragility as
        validate_regex_pattern below."""
        rule_type = info.data.get("type")
        if rule_type == "regex" and re.search(r"\$\d", v):
            raise ValueError(
                f"Replace string contains '$N' backref syntax: {v!r}. "
                "Python re.sub() uses '\\1', '\\2' etc. — not '$1', '$2'. "
                "Using '$1' silently produces literal '$1' in output."
            )
        return v

    @field_validator("match")
    @classmethod
    def validate_regex_pattern(cls, v: str, info: Any) -> str:
        """If type='regex', validate that match is a compilable Python regex.

        This validator fires for ALL rules regardless of type, but only
        validates regex compilation when type='regex'. For type='literal',
        the match string is used as-is without regex interpretation.

        Assumption: field_validator runs after all fields are set, so
        info.data contains the already-validated 'type' field.
        If Pydantic changes field validation order, this could break silently
        by not validating the regex — the first failure would be at apply-time.
        """
        # info.data contains fields validated before 'match' in model order.
        # 'type' is defined before 'match', so it will be present if valid.
        rule_type = info.data.get("type")
        if rule_type == "regex":
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern in transformation rule: {e!r}. "
                    f"Pattern: {v!r}. "
                    "Fix this in the platform config YAML before running conversions."
                ) from e
        return v


class PlatformConfig(StrictModel):
    """Root config model for a target platform.

    Constructed from OmegaConf.to_container(cfg, resolve=True) output,
    which returns a plain Python dict. Pydantic v2 handles nested dicts
    by constructing nested models automatically.

    The source: section is merged from config.yaml (the base config),
    not from the platform YAML. This means source paths are global defaults
    that platform configs cannot override — intentional, because source
    paths describe the claude-code plugin structure which is platform-agnostic.

    If this assumption breaks (a platform needs different source paths),
    the first to rot is the source path lookup in every conversion task.
    """

    platform: PlatformIdentity
    source: SourceConfig
    paths: PathsConfig | None = None
    install: InstallConfig | None = None
    formats: FormatsConfig | None = None
    naming: NamingConfig | None = None
    permissions: PermissionsConfig | None = None
    transformations: list[TransformationRule] = Field(default_factory=list)
