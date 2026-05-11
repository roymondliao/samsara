"""Static contract tests for GitHub Actions workflows."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


def load_workflow(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestCIWorkflow:
    def test_ci_workflow_exists(self):
        assert CI_WORKFLOW.exists(), (
            "CI workflow must exist at .github/workflows/ci.yml"
        )

    def test_ci_uses_read_only_permissions_and_release_check(self):
        workflow = load_workflow(CI_WORKFLOW)

        assert workflow["permissions"] == {"contents": "read"}
        job = workflow["jobs"]["validate"]
        step_text = "\n".join(
            step.get("run", "") for step in job["steps"] if isinstance(step, dict)
        )
        assert "samsara-cli release check-version" in step_text
        assert "uv run pytest" in step_text
        assert "uv run pre-commit run --all-files" in step_text
        assert '-m "not requires_codex and not requires_gemini"' in step_text

    def test_ci_activates_venv_before_python_commands(self):
        workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")

        assert "source .venv/bin/activate" in workflow_text
        assert "uv run pytest" in workflow_text
        assert "uv run pre-commit run --all-files" in workflow_text

    def test_ci_runs_on_pull_requests_to_main(self):
        workflow = load_workflow(CI_WORKFLOW)
        triggers = workflow["on"]

        assert "pull_request" in triggers
        assert triggers["pull_request"]["branches"] == ["main"]
        assert "push" not in triggers


class TestReleaseWorkflow:
    def test_release_workflow_exists(self):
        assert RELEASE_WORKFLOW.exists(), (
            "Release workflow must exist at .github/workflows/release.yml"
        )

    def test_release_workflow_has_trusted_triggers_only(self):
        workflow = load_workflow(RELEASE_WORKFLOW)
        triggers = workflow["on"]

        assert "pull_request" in triggers
        assert "workflow_dispatch" in triggers
        assert triggers["pull_request"]["types"] == ["closed"]
        assert triggers["pull_request"]["branches"] == ["main"]
        assert ".claude-plugin/marketplace.json" in triggers["pull_request"]["paths"]

    def test_release_workflow_uses_merged_pr_gate(self):
        workflow = load_workflow(RELEASE_WORKFLOW)

        release_job = workflow["jobs"]["release"]
        assert release_job["permissions"] == {"contents": "write"}
        assert "github.event.pull_request.merged == true" in release_job["if"]
        assert "github.event.pull_request.base.ref == 'main'" in release_job["if"]

    def test_release_workflow_checks_tag_state_before_mutation(self):
        workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

        assert "uv run samsara-cli release check-version" in workflow_text
        assert "git ls-remote --tags origin" in workflow_text
        assert "gh release view" in workflow_text
        assert "git tag -a" in workflow_text
        assert "git push origin" in workflow_text
        assert "gh release create" in workflow_text
        assert (
            "github.event.pull_request.merge_commit_sha || github.sha" in workflow_text
        )

    def test_release_workflow_activates_venv_and_exports_gh_token(self):
        workflow_text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

        assert "source .venv/bin/activate" in workflow_text
        assert "GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}" in workflow_text
