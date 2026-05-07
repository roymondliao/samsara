"""
Unit tests for config schema — testing happy paths and correct behavior.
"""

from samsara_cli.config.schema import (
    GlobalInstallConfig,
    InstallConfig,
    NamingConfig,
    PathsConfig,
    PermissionsConfig,
    PlatformConfig,
    PlatformIdentity,
    ProjectInstallConfig,
    SourceConfig,
    TransformationRule,
)


class TestTransformationRule:
    def test_valid_literal_rule(self):
        rule = TransformationRule(
            id="tool_read",
            scope="body",
            type="literal",
            match="Read tool",
            replace="file reading (via exec_command with cat/nl)",
            priority="medium",
        )
        assert rule.id == "tool_read"
        assert rule.scope == "body"
        assert rule.type == "literal"
        assert rule.priority == "medium"

    def test_valid_regex_rule(self):
        rule = TransformationRule(
            id="skill_invocation",
            scope="body",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
            priority="high",
        )
        assert rule.id == "skill_invocation"
        assert rule.type == "regex"
        assert rule.priority == "high"

    def test_valid_frontmatter_scope(self):
        rule = TransformationRule(
            id="front_rule",
            scope="frontmatter",
            type="literal",
            match="old_key",
            replace="new_key",
            priority="high",
        )
        assert rule.scope == "frontmatter"

    def test_replace_can_be_empty_string(self):
        """Replace can be empty string (deletion). Must not fail."""
        rule = TransformationRule(
            id="delete_rule",
            scope="body",
            type="literal",
            match="deprecated text",
            replace="",
            priority="low",
        )
        assert rule.replace == ""

    def test_valid_low_priority(self):
        rule = TransformationRule(
            id="test",
            scope="body",
            type="literal",
            match="text",
            replace="other",
            priority="low",
        )
        assert rule.priority == "low"


class TestSourceConfig:
    def test_valid_source_config(self):
        cfg = SourceConfig(
            plugin_dir=".claude-plugin",
            skills_dir="skills",
            agents_dir="agents",
            hooks_dir="hooks",
            references_dir="references",
        )
        assert cfg.plugin_dir == ".claude-plugin"
        assert cfg.skills_dir == "skills"
        assert cfg.agents_dir == "agents"
        assert cfg.hooks_dir == "hooks"
        assert cfg.references_dir == "references"


class TestPlatformIdentity:
    def test_valid_platform_identity(self):
        identity = PlatformIdentity(name="codex", version_cmd="codex --version")
        assert identity.name == "codex"
        assert identity.version_cmd == "codex --version"

    def test_platform_identity_version_cmd_optional(self):
        """version_cmd should be optional — claude-code may not have one."""
        identity = PlatformIdentity(name="claude-code")
        assert identity.name == "claude-code"
        assert identity.version_cmd is None


class TestPathsConfig:
    def test_valid_paths_config(self):
        paths = PathsConfig(
            plugin_dir=".codex",
            plugin_manifest=None,
            skills_dir=".agents/skills",
            agents_dir=".codex/agents",
            hooks_file="hooks.json",
            references_dir=".agents/references",
        )
        assert paths.plugin_dir == ".codex"
        assert paths.plugin_manifest is None
        assert paths.references_dir == ".agents/references"


class TestInstallConfig:
    def test_valid_install_config(self):
        install = InstallConfig(
            project=ProjectInstallConfig(target="$CWD"),
            global_=GlobalInstallConfig(
                config_path="~/.codex/config.toml",
            ),
        )
        assert install.project.target == "$CWD"
        assert install.global_.config_path == "~/.codex/config.toml"


class TestPlatformConfig:
    def _minimal_config(self) -> dict:
        return dict(
            platform=PlatformIdentity(name="test"),
            source=SourceConfig(
                plugin_dir=".claude-plugin",
                skills_dir="skills",
                agents_dir="agents",
                hooks_dir="hooks",
                references_dir="references",
            ),
        )

    def test_minimal_platform_config(self):
        cfg = PlatformConfig(**self._minimal_config())
        assert cfg.platform.name == "test"
        assert cfg.transformations == []

    def test_platform_config_with_transformations(self):
        base = self._minimal_config()
        base["transformations"] = [
            TransformationRule(
                id="rule1",
                scope="body",
                type="literal",
                match="Read tool",
                replace="file reading",
                priority="medium",
            )
        ]
        cfg = PlatformConfig(**base)
        assert len(cfg.transformations) == 1
        assert cfg.transformations[0].id == "rule1"

    def test_platform_config_from_dict(self):
        """Pydantic v2 can construct nested models from plain dicts —
        this is the path that OmegaConf.to_container() uses."""
        data = {
            "platform": {"name": "codex", "version_cmd": "codex --version"},
            "source": {
                "plugin_dir": ".claude-plugin",
                "skills_dir": "skills",
                "agents_dir": "agents",
                "hooks_dir": "hooks",
                "references_dir": "references",
            },
            "transformations": [
                {
                    "id": "rule1",
                    "scope": "body",
                    "type": "literal",
                    "match": "Read tool",
                    "replace": "file reading",
                    "priority": "medium",
                }
            ],
        }
        cfg = PlatformConfig(**data)
        assert cfg.platform.name == "codex"
        assert cfg.transformations[0].id == "rule1"


class TestNamingConfig:
    def test_valid_naming_config(self):
        naming = NamingConfig(skill_prefix="samsara", separator="-")
        assert naming.skill_prefix == "samsara"
        assert naming.separator == "-"


class TestPermissionsConfig:
    def test_valid_permissions_config(self):
        perms = PermissionsConfig(
            sandbox_mode="workspace-write",
            feature_flags={"codex_hooks": True},
        )
        assert perms.sandbox_mode == "workspace-write"
        assert perms.feature_flags["codex_hooks"] is True

    def test_permissions_feature_flags_optional(self):
        perms = PermissionsConfig(sandbox_mode="workspace-write")
        assert perms.feature_flags == {}
