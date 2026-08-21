"""Contract tests for Codebase Map schema v2 and authority boundaries."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "codebase-map" / "SKILL.md"
ROOT_TEMPLATE = ROOT / "skills" / "codebase-map" / "templates" / "codebase-map.yaml"
MODULE_TEMPLATE = ROOT / "skills" / "codebase-map" / "templates" / "module.yaml"
EXPLORERS = (
    ROOT / "agents" / "structure-explorer.md",
    ROOT / "agents" / "infra-explorer.md",
    ROOT / "agents" / "yin-explorer.md",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_root_schema_records_snapshot_identity_without_reimplementing_git() -> None:
    template = yaml.safe_load(read(ROOT_TEMPLATE))

    assert template["schema_version"] == 2
    assert set(template["source"]) == {"commit"}
    forbidden = {
        "last_updated",
        "staleness_threshold_days",
        "staleness_churn_threshold",
        "changed_files",
        "changed_file_count",
        "commit_list",
        "update_state",
    }
    assert forbidden.isdisjoint(template)


def test_root_and_module_files_have_distinct_authority() -> None:
    root = yaml.safe_load(read(ROOT_TEMPLATE))
    module = yaml.safe_load(read(MODULE_TEMPLATE))

    assert {
        "summary",
        "modules",
        "global_nodes",
        "cross_module_relationships",
        "business_flows",
        "infrastructure",
    }.issubset(root)
    assert {
        "interfaces",
        "nodes",
        "internal_relationships",
        "rot_risks",
        "hidden_coupling",
        "assumptions",
    }.issubset(module)
    assert {
        "name",
        "path",
        "responsibility",
        "provides",
        "death_impact",
    }.isdisjoint(module)


def test_skill_uses_sha_equality_and_impact_levels_not_file_counts() -> None:
    skill = read(SKILL)
    normalized = " ".join(skill.split())

    for state in ("CURRENT", "UPDATE_REQUIRED", "MISSING", "UNKNOWN"):
        assert state in skill
    for level in ("Level 0", "Level 1", "Level 2", "Level 3"):
        assert level in skill
    assert "source.commit" in skill
    assert "git rev-parse HEAD" in skill
    assert "File count never selects the level" in normalized


def test_skill_maps_detached_committed_snapshot_and_ignored_output() -> None:
    skill = read(SKILL)

    assert "git worktree add --detach" in skill
    assert "git worktree remove --force" in skill
    assert "Never read or persist uncommitted" in skill
    assert "git check-ignore" in skill
    assert "Publish root manifest last" in skill


def test_explorers_share_snapshot_and_scope_contract() -> None:
    for path in EXPLORERS:
        agent = read(path)
        assert "snapshot_root" in agent
        assert "source_commit" in agent
        assert "scan_scope" in agent
        assert "working tree" in agent
        assert "coverage gap" in agent.lower()


def test_repository_ignores_the_snapshot_map_output() -> None:
    ignore = read(ROOT / ".gitignore")

    assert ".samsara/*" in ignore
    assert "!.samsara/systemic-scars.yaml" in ignore
