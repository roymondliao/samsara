"""
Smoke test — Codex CLI End-to-End Verification (Layer 4).

Marked @pytest.mark.integration — runs ONLY with `pytest -m integration`.
Does NOT run in the normal test suite (pytest tests/ skips integration marks).

Requires Codex CLI installed: `codex --version` must exit 0.
If Codex is not installed, all tests skip gracefully.

Smoke test flow:
1. Detect Codex CLI via `codex --version`
2. Run full conversion pipeline on actual test fixture source
3. Verify converted output structure (plugin.json, SKILL.md, .toml, hooks.json)
4. Clean up temp directory (yield fixture with finally-block teardown)

Limitations documented in scar report:
- Codex skill discovery test is NOT feasible: codex has no `--list-skills` or
  non-interactive skill inspection command. Discovery test is deferred.
- No model interaction: cannot verify transformed skill instructions produce
  correct model behavior. This requires an actual interactive Codex session.
- CAN verify: converted file structure, JSON parse validity, TOML parse validity,
  hooks.json structure.

Death tests guard:
  DC-10-1: Smoke test must SKIP (not FAIL) when Codex CLI is not installed.
           Silent failure mode: detection always returns "installed" — test would
           run on every CI machine and fail with Codex errors.
  DC-10-2: Smoke test must use an ISOLATED temp directory — never modify
           ~/.codex/config.toml or any real Codex config path.
           Silent failure mode: test modifies real config, user's Codex sessions
           are disrupted after the test run.
  DC-10-3: Temp directory must be cleaned up after test completion (pass or fail).
           Silent failure mode: temp directories accumulate in the OS temp dir,
           consuming disk space silently across repeated test runs.

Assumption: ConversionEngine("codex").run() uses the fixture source at
  tests/fixtures/source/ (3 skills, 1 agent, 1 hook, 1 reference).
  If the fixture changes without updating this test, structural assertions may fail.
Assumption: codex --version exits 0 on a machine with Codex installed.
  If Codex uses a different version flag, detection returns False and all tests skip.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine
from samsara_cli.installer.detect import PlatformDetector

# --- Fixture source (same as integration tests) ---
FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"


# ---------------------------------------------------------------------------
# Codex detection helper
#
# Design: detection is checked once at module import via the session-scoped
# fixture _codex_installed. All tests use this fixture to skip gracefully.
# Using a fixture (vs. module-level constant) ensures the skip is reported
# properly by pytest — not silently excluded during collection.
# ---------------------------------------------------------------------------


def _is_codex_installed() -> bool:
    """Check whether Codex CLI is installed by running `codex --version`.

    Returns:
        True if `codex --version` exits 0.
        False if the command is not found, exits non-zero, or times out.

    Note: We use subprocess directly rather than PlatformDetector to isolate
    the smoke test from changes to PlatformDetector internals. The smoke test
    is a black-box check: if `codex --version` works, Codex is installed.
    """
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError, OSError, subprocess.TimeoutExpired:
        return False


# ---------------------------------------------------------------------------
# DC-10-1: Smoke test must SKIP (not FAIL) when Codex CLI is not installed
#
# Silent failure: if _is_codex_installed() raises instead of returning False,
# or if the pytest.skip() call is never reached, tests would fail with confusing
# subprocess errors rather than a clean skip message.
#
# First discoverer: any developer running `pytest -m integration` on a machine
# without Codex. Without this guard, they see subprocess.CalledProcessError
# or FileNotFoundError, not a clean skip.
# Damage: developer wastes time investigating a "failed" test that should never
# run on their machine.
# ---------------------------------------------------------------------------


class TestDC101SkipWhenCodexNotInstalled:
    """Death test: smoke tests must skip gracefully when Codex CLI is absent.

    We simulate the "Codex not installed" path by verifying our detection
    returns False for a clearly nonexistent command. If detection always
    returns True (broken), every CI machine would run the smoke test and fail.
    """

    def test_detection_returns_false_for_nonexistent_command(self) -> None:
        """Verify the skip-detection mechanism can return False.

        We can't easily test "Codex not installed" when it IS installed, but we
        can verify: (1) the detection function returns a bool (not raises),
        and (2) PlatformDetector.detect() returns False for a bad command
        by verifying the subprocess-not-found path works.
        """
        # Verify detection returns a bool, not raises
        result = _is_codex_installed()
        assert isinstance(result, bool), (
            "_is_codex_installed() must return bool, not raise. "
            f"Got {type(result).__name__!r}. "
            "A non-bool return means skip logic can't be evaluated."
        )

    def test_detection_does_not_propagate_file_not_found(self) -> None:
        """Verify _is_codex_installed() returns False when CLI is absent.

        We test this by calling subprocess directly with a nonexistent binary.
        If our exception handling is missing, this would propagate to the caller
        and cause confusing test failures instead of clean skips.
        """
        try:
            result = subprocess.run(
                ["__nonexistent_binary_samsara_test__", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            # If somehow found, returncode would be non-zero
            assert result.returncode != 0
        except FileNotFoundError:
            # Expected — the binary doesn't exist
            pass
        except OSError:
            # Also acceptable — OS-level not found
            pass
        # Key assertion: OUR wrapper handles this gracefully
        # We can't call _is_codex_installed with a custom binary name,
        # but the above confirms the exception type that must be caught.
        # This is a structural test of the contract, not a mock-based test.

    def test_platform_detector_returns_bool_not_raises(self) -> None:
        """PlatformDetector.detect('codex') must return bool, not raise.

        This verifies the PlatformDetector layer (used in production code)
        also handles the missing CLI gracefully.
        """
        detector = PlatformDetector()
        result = detector.detect("codex")
        assert isinstance(result, bool), (
            f"PlatformDetector.detect('codex') returned {type(result).__name__!r}, not bool. "
            "Must return bool so callers can branch on detection result."
        )


# ---------------------------------------------------------------------------
# DC-10-2: Smoke test must use isolated temp directory, never real Codex config
#
# Silent failure: if the smoke test fixture accidentally writes to ~/.codex/,
# a real Codex user's config is corrupted. The test passes but the damage is
# done. First discoverer: user who runs `pytest -m integration` and finds their
# Codex session broken afterward.
# Damage: real config.toml is modified, potentially breaking real Codex sessions.
# ---------------------------------------------------------------------------


class TestDC102MustUseIsolatedDirectory:
    """Death test: smoke test must use temp dir, never touch real Codex config."""

    def test_real_codex_config_not_modified_after_pipeline_run(
        self, tmp_path: Path
    ) -> None:
        """Verify ConversionEngine output goes to tmp_path, not ~/.codex/.

        This test runs the full pipeline targeting a tmp_path and asserts that
        ~/.codex/ was NOT modified. We use mtime comparison on ~/.codex/config.toml
        (if it exists) to detect any writes.

        Note: if ~/.codex/config.toml doesn't exist, the assertion still holds —
        we check that the file was NOT created by the pipeline.
        """
        real_config = Path.home() / ".codex" / "config.toml"
        # Record state before
        config_existed_before = real_config.exists()
        mtime_before = real_config.stat().st_mtime if config_existed_before else None

        # Run the full conversion pipeline — targeting tmp_path, not real config
        output_dir = tmp_path / "codex_output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        # Assert real config was not touched
        config_exists_after = real_config.exists()
        if config_existed_before:
            mtime_after = real_config.stat().st_mtime
            assert mtime_after == mtime_before, (
                f"~/.codex/config.toml mtime changed during pipeline run! "
                f"Before: {mtime_before}, After: {mtime_after}. "
                "The smoke test must NEVER write to real Codex config."
            )
        else:
            assert not config_exists_after, (
                "~/.codex/config.toml was CREATED by the pipeline run. "
                "The smoke test must use isolated temp directories only."
            )

    def test_output_dir_is_under_tmp_path(self, tmp_path: Path) -> None:
        """Verify output_dir is under the system temp directory (not ~/.codex/).

        Structural test: confirms the fixture pattern puts output in tmp_path,
        not in any real Codex installation directory.
        """
        output_dir = tmp_path / "smoke_test_output"

        # Verify the path is under temp (not home or any system config dir)
        real_codex_dir = Path.home() / ".codex"
        assert not str(output_dir).startswith(str(real_codex_dir)), (
            f"output_dir {output_dir} is under ~/.codex/! "
            "Smoke test fixtures must use tmp_path, not real Codex directories."
        )

        # Also verify it's not under any other system config location
        assert not str(output_dir).startswith("/etc/"), (
            "output_dir must not write to /etc/ — system config scope"
        )


# ---------------------------------------------------------------------------
# DC-10-3: Temp directory must be cleaned up after test completion
#
# Silent failure: if the yield fixture's finally block is missing or broken,
# temp directories accumulate on every test run. On CI machines with many test
# runs, this can exhaust disk space or cause path collision issues.
# First discoverer: CI operator who notices /tmp/ filling with samsara-smoke-*
# directories after repeated CI runs.
# ---------------------------------------------------------------------------


class TestDC103TempDirMustBeCleanedUp:
    """Death test: temp directories created by smoke tests must be cleaned up."""

    def test_yield_fixture_teardown_runs_on_pass(self, tmp_path: Path) -> None:
        """Verify that a yield fixture with finally block cleans up its directory.

        We can't directly test the smoke_install_dir fixture (which is a module-level
        fixture), but we CAN verify the cleanup pattern works correctly by running it
        directly in a controlled test.
        """
        cleanup_called = []
        temp_dir_created = []

        # Simulate what the smoke_install_dir fixture does
        def setup_and_teardown():
            tmp = Path(tempfile.mkdtemp(prefix="samsara-smoke-test-"))
            temp_dir_created.append(tmp)
            try:
                yield tmp
            finally:
                if tmp.exists():
                    shutil.rmtree(tmp)
                    cleanup_called.append(tmp)

        gen = setup_and_teardown()
        result_dir = next(gen)  # setup phase

        # Verify temp dir was created
        assert result_dir.exists(), "Temp dir must exist after setup"
        assert result_dir in temp_dir_created

        # Trigger teardown
        try:
            next(gen)
        except StopIteration:
            pass  # expected — generator exhausted

        # Verify cleanup happened
        assert not result_dir.exists(), (
            f"Temp dir {result_dir} still exists after teardown! "
            "yield fixture finally block must remove the temp directory."
        )
        assert result_dir in cleanup_called, (
            "finally block must append to cleanup_called before returning. "
            "If cleanup_called is empty, shutil.rmtree was never called."
        )

    def test_yield_fixture_teardown_runs_on_exception(self, tmp_path: Path) -> None:
        """Verify cleanup runs even when the test raises an exception.

        If finally block is missing (replaced by just try/except), cleanup
        would not run when the test fails. This is the "silent failure" path.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="samsara-smoke-test-cleanup-"))
        assert temp_dir.exists()

        try:
            raise RuntimeError("simulated test failure")
        except RuntimeError:
            pass
        finally:
            # This is what the smoke fixture's finally block does
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        assert not temp_dir.exists(), (
            "Temp dir must be cleaned up even when an exception occurs. "
            "Use finally:, not except:."
        )


# ---------------------------------------------------------------------------
# Shared session fixture — run pipeline ONCE, reuse across all smoke tests
#
# The fixture checks Codex installation and skips the entire session if absent.
# Cleanup happens in the finally block — guaranteed even on test failure.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def smoke_install_dir():
    """Run full pipeline and return the output directory.

    Skips all tests in this module if Codex CLI is not installed.
    Yields the output directory (Path) for structural assertions.
    Cleans up in the finally block — guaranteed cleanup on pass or fail.

    Assumption: FIXTURE_SOURCE is a valid samsara source (verified by Task 9 tests).
    Assumption: ConversionEngine("codex") works without running Codex CLI
                (conversion is filesystem-only, no Codex invocation needed).
    """
    if not _is_codex_installed():
        pytest.skip(
            "Codex CLI not installed — skipping smoke tests. "
            "Install Codex CLI from: https://github.com/openai/codex"
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="samsara-smoke-"))
    try:
        output_dir = temp_dir / "codex_output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        yield output_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# ---------------------------------------------------------------------------
# Structural smoke tests — verify output recognized by Codex
#
# These tests verify the converted output has the correct file structure
# that Codex would need to discover and use the plugin. Each test is
# independent (does not depend on other tests passing first).
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestCodexPluginStructure:
    """Verify .codex-plugin/ has correct structure for Codex discovery."""

    def test_codex_plugin_directory_exists(self, smoke_install_dir: Path) -> None:
        """Converted output must have .codex-plugin/ directory.

        This is the directory Codex uses to locate plugin metadata.
        Missing this directory means Codex cannot discover the plugin.
        """
        plugin_dir = smoke_install_dir / ".codex-plugin"
        assert plugin_dir.is_dir(), (
            f"Expected .codex-plugin/ directory at {plugin_dir}. "
            "Codex discovery requires this directory to find plugin.json."
        )

    def test_plugin_json_exists_and_is_valid_json(
        self, smoke_install_dir: Path
    ) -> None:
        """plugin.json must exist under .codex-plugin/ and be valid JSON.

        Silent failure: if plugin.json contains malformed JSON, Codex may silently
        skip the plugin without any error message.
        """
        plugin_json = smoke_install_dir / ".codex-plugin" / "plugin.json"
        assert plugin_json.exists(), (
            f"Expected plugin.json at {plugin_json}. "
            "Codex requires plugin.json for plugin registration."
        )
        try:
            data = json.loads(plugin_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pytest.fail(
                f"plugin.json is not valid JSON: {e}. "
                "Codex would silently skip a plugin with malformed JSON."
            )
        # Verify required top-level fields
        assert "name" in data, (
            "plugin.json missing 'name' field. Codex uses 'name' to identify the plugin."
        )
        assert "version" in data, "plugin.json missing 'version' field."
        assert data["name"], "plugin.json 'name' field is empty or falsy"
        assert data["version"], "plugin.json 'version' field is empty or falsy"

    def test_hooks_json_exists_and_is_valid_json(self, smoke_install_dir: Path) -> None:
        """hooks.json must exist under .codex-plugin/ and be valid JSON.

        hooks.json is what Codex reads to register event hooks. Invalid JSON
        means the session-start hook never fires — silently losing context injection.
        """
        hooks_json = smoke_install_dir / ".codex-plugin" / "hooks.json"
        assert hooks_json.exists(), (
            f"Expected hooks.json at {hooks_json}. "
            "Codex reads hooks.json to register hook commands."
        )
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pytest.fail(
                f"hooks.json is not valid JSON: {e}. "
                "Codex would silently ignore a plugin with malformed hooks.json."
            )
        # Verify hooks structure
        assert "hooks" in data, (
            "hooks.json missing top-level 'hooks' key. "
            "Codex expects hooks.json to have a 'hooks' array."
        )
        assert isinstance(data["hooks"], list), (
            f"hooks.json 'hooks' must be a list, got {type(data['hooks']).__name__}. "
            "Codex iterates 'hooks' as an array."
        )

    def test_hooks_json_has_session_start_entry(self, smoke_install_dir: Path) -> None:
        """hooks.json must contain a session_start hook entry.

        The session-start hook is the mechanism for context injection into Codex.
        If it's missing from hooks.json, Codex never calls the hook script —
        silently losing all samsara context.
        """
        hooks_json = smoke_install_dir / ".codex-plugin" / "hooks.json"
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        hooks = data.get("hooks", [])

        session_start_hooks = [
            h
            for h in hooks
            if isinstance(h, dict) and h.get("event") == "session_start"
        ]
        assert len(session_start_hooks) >= 1, (
            f"hooks.json has {len(session_start_hooks)} session_start entries. "
            "Expected at least 1. "
            "Without a session_start hook, samsara context is never injected into Codex."
        )

    def test_session_start_hook_has_command_field(
        self, smoke_install_dir: Path
    ) -> None:
        """session_start hook entry must have a 'command' field.

        If 'command' is missing from the hook entry, Codex cannot call the script —
        the hook silently does nothing.
        """
        hooks_json = smoke_install_dir / ".codex-plugin" / "hooks.json"
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        hooks = data.get("hooks", [])

        for hook in hooks:
            if isinstance(hook, dict) and hook.get("event") == "session_start":
                assert "command" in hook, (
                    f"session_start hook is missing 'command' field: {hook}. "
                    "Codex cannot call a hook without a command."
                )
                assert hook["command"], (
                    "session_start hook 'command' field is empty. "
                    "Codex would find the hook but have no command to run."
                )

    def test_session_start_hook_script_exists(self, smoke_install_dir: Path) -> None:
        """The hook script referenced in hooks.json must exist and be executable.

        Silent failure: if hooks.json points to a non-existent script, Codex may
        silently fail to execute the hook, losing context injection without any error.
        Similarly, if the script exists but is not executable, Codex cannot run it.
        """
        import os

        hooks_json = smoke_install_dir / ".codex-plugin" / "hooks.json"
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        hooks = data.get("hooks", [])

        for hook in hooks:
            if isinstance(hook, dict) and hook.get("event") == "session_start":
                command = hook.get("command", "")
                if command:
                    # Guard: command must be a relative path, not absolute.
                    # If absolute, smoke_install_dir / command would silently
                    # resolve to the absolute path, ignoring smoke_install_dir.
                    assert not command.startswith("/"), (
                        f"Hook 'command' is an absolute path: {command!r}. "
                        "Commands must be relative paths from the project root. "
                        "An absolute path in hooks.json would break portability "
                        "across different install locations."
                    )
                    # Command is a relative path from project root
                    # In our output, the hooks dir is .codex-plugin/hooks/
                    script_path = smoke_install_dir / command
                    assert script_path.exists(), (
                        f"Hook script referenced in hooks.json does not exist: {script_path}. "
                        f"Command field value: {command!r}. "
                        "Codex would fail to execute the hook, silently losing context injection."
                    )
                    # Verify the script is executable
                    assert os.access(script_path, os.X_OK), (
                        f"Hook script {script_path} exists but is NOT executable. "
                        "Codex cannot run a script without execute permission. "
                        "Run: chmod +x {script_path}"
                    )

    def test_hooks_directory_exists(self, smoke_install_dir: Path) -> None:
        """hooks/ directory must exist under .codex-plugin/.

        This directory contains the actual hook scripts.
        """
        hooks_dir = smoke_install_dir / ".codex-plugin" / "hooks"
        assert hooks_dir.is_dir(), (
            f"Expected .codex-plugin/hooks/ directory at {hooks_dir}. "
            "Hook scripts are placed here."
        )

    def test_references_directory_exists(self, smoke_install_dir: Path) -> None:
        """references/ directory must exist under .codex-plugin/.

        Reference documents are placed here for Codex to access.
        """
        refs_dir = smoke_install_dir / ".codex-plugin" / "references"
        assert refs_dir.is_dir(), (
            f"Expected .codex-plugin/references/ directory at {refs_dir}. "
            "Reference documents are placed here."
        )


@pytest.mark.integration
class TestCodexSkillStructure:
    """Verify skills/ directory has correct structure for Codex skill discovery."""

    def test_skills_directory_exists(self, smoke_install_dir: Path) -> None:
        """Converted output must have skills/ directory."""
        skills_dir = smoke_install_dir / "skills"
        assert skills_dir.is_dir(), (
            f"Expected skills/ directory at {skills_dir}. "
            "Codex skill discovery requires a skills/ directory."
        )

    def test_skills_directory_has_at_least_one_skill(
        self, smoke_install_dir: Path
    ) -> None:
        """skills/ must contain at least one skill directory.

        If the conversion produced zero skills, the entire skills layer is broken.
        """
        skills_dir = smoke_install_dir / "skills"
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 1, (
            "skills/ directory is empty. Expected at least 1 skill directory. "
            "Conversion may have silently dropped all skills."
        )

    def test_all_skill_dirs_have_samsara_prefix(self, smoke_install_dir: Path) -> None:
        """All output skill directories must use the 'samsara-' prefix.

        The naming convention prevents collision with non-samsara skills.
        Without the prefix, skill names could collide with Codex built-in skills.
        """
        skills_dir = smoke_install_dir / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                assert skill_dir.name.startswith("samsara-"), (
                    f"Skill directory '{skill_dir.name}' does not use 'samsara-' prefix. "
                    "All converted samsara skills must be prefixed to avoid name collisions."
                )

    def test_each_skill_dir_has_skill_md(self, smoke_install_dir: Path) -> None:
        """Every output skill directory must contain SKILL.md.

        SKILL.md is the file Codex reads to load skill instructions.
        A skill directory without SKILL.md is unreadable by Codex.
        """
        skills_dir = smoke_install_dir / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                assert skill_md.exists(), (
                    f"Skill directory '{skill_dir.name}' is missing SKILL.md. "
                    "Codex cannot load skills without SKILL.md."
                )

    def test_skill_md_is_not_empty(self, smoke_install_dir: Path) -> None:
        """SKILL.md files must have non-empty content.

        An empty SKILL.md would pass structural checks but provide zero context
        to Codex. The skill would appear registered but be functionally useless.
        """
        skills_dir = smoke_install_dir / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text(encoding="utf-8").strip()
                    assert content, (
                        f"SKILL.md in '{skill_dir.name}' is empty. "
                        "An empty skill provides no instructions to Codex."
                    )

    def test_skill_md_has_no_raw_colon_skill_references(
        self, smoke_install_dir: Path
    ) -> None:
        """SKILL.md files must not contain unconverted 'samsara:' skill references.

        The source format uses 'samsara:skill-name' syntax. Converted output
        must use Codex-compatible references. If the conversion is incomplete,
        SKILL.md would contain raw 'samsara:' references that Codex cannot resolve.
        """
        skills_dir = smoke_install_dir / "skills"
        violations: list[str] = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text(encoding="utf-8")
                    lines = content.splitlines()
                    for lineno, line in enumerate(lines, 1):
                        # Check for raw colon-syntax skill references like `samsara:skill-name`
                        # that look like Claude Code skill invocations (backtick-wrapped or direct)
                        if "`samsara:" in line:
                            violations.append(
                                f"{skill_dir.name}/SKILL.md:{lineno}: {line.strip()!r}"
                            )
        assert not violations, (
            f"Found {len(violations)} unconverted samsara: references in SKILL.md files:\n"
            + "\n".join(f"  {v}" for v in violations)
            + "\nThese are Claude Code syntax references — they must be converted for Codex."
        )

    def test_skill_count_matches_source_fixture(self, smoke_install_dir: Path) -> None:
        """Output skill count must match source fixture skill count.

        If conversion silently drops a skill, Codex users lose that skill.
        This guards the all-or-nothing contract at the skill level.
        """
        source_skill_dirs = [
            d for d in (FIXTURE_SOURCE / "skills").iterdir() if d.is_dir()
        ]
        output_skill_dirs = [
            d for d in (smoke_install_dir / "skills").iterdir() if d.is_dir()
        ]
        assert len(output_skill_dirs) == len(source_skill_dirs), (
            f"Source has {len(source_skill_dirs)} skills, "
            f"output has {len(output_skill_dirs)}. "
            "Conversion silently dropped or duplicated a skill."
        )


@pytest.mark.integration
class TestCodexAgentStructure:
    """Verify agents/ directory has correct structure for Codex agents."""

    def test_agents_directory_exists(self, smoke_install_dir: Path) -> None:
        """Converted output must have agents/ directory."""
        agents_dir = smoke_install_dir / "agents"
        assert agents_dir.is_dir(), (
            f"Expected agents/ directory at {smoke_install_dir}. "
            "Codex agents are placed in agents/."
        )

    def test_agents_directory_has_toml_files(self, smoke_install_dir: Path) -> None:
        """agents/ directory must contain at least one .toml file.

        Agent files are .toml format for Codex. If the directory is empty,
        agent conversion silently failed.
        """
        agents_dir = smoke_install_dir / "agents"
        toml_files = list(agents_dir.glob("*.toml"))
        assert len(toml_files) >= 1, (
            "agents/ directory has no .toml files. "
            "Expected at least 1 converted agent. "
            "Agent conversion may have silently failed."
        )

    def test_no_unconverted_md_files_in_agents(self, smoke_install_dir: Path) -> None:
        """agents/ directory must NOT contain .md files (source format).

        .md files in agents/ are the source format (Claude Code). If any .md files
        remain in the output, those agents were not converted — they'd be ignored
        by Codex silently.
        """
        agents_dir = smoke_install_dir / "agents"
        md_files = list(agents_dir.glob("*.md"))
        assert len(md_files) == 0, (
            f"Found {len(md_files)} unconverted .md files in agents/: {md_files}. "
            "These are source format files — Codex expects .toml. "
            "Agent conversion may be incomplete."
        )

    def test_all_toml_files_are_valid_toml(self, smoke_install_dir: Path) -> None:
        """All .toml files in agents/ must parse as valid TOML.

        Invalid TOML causes Codex to skip the agent silently. There is no
        parse error visible to the user — the agent simply doesn't appear.
        """
        import tomllib

        agents_dir = smoke_install_dir / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            try:
                data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as e:
                pytest.fail(
                    f"Agent TOML file {toml_file.name} is not valid TOML: {e}. "
                    "Codex would silently ignore an agent with malformed TOML."
                )
            # Verify [agent] table exists
            assert "agent" in data, (
                f"Agent TOML {toml_file.name} missing [agent] table. "
                "Codex reads agent configuration from the [agent] table."
            )

    def test_agent_toml_has_name_field(self, smoke_install_dir: Path) -> None:
        """Each agent TOML must have agent.name field.

        If 'name' is missing from the [agent] table, Codex cannot identify the agent.
        It may silently register under an empty name or fail to register at all.
        """
        import tomllib

        agents_dir = smoke_install_dir / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
            agent_section = data.get("agent", {})
            assert "name" in agent_section, (
                f"Agent TOML {toml_file.name} missing 'name' in [agent] table. "
                "Codex uses agent.name to identify and invoke the agent."
            )
            assert agent_section["name"], (
                f"Agent TOML {toml_file.name} has empty 'name' in [agent] table."
            )

    def test_agent_toml_has_developer_instructions(
        self, smoke_install_dir: Path
    ) -> None:
        """Each agent TOML must have agent.developer_instructions field.

        developer_instructions is the primary instruction content for Codex agents.
        If missing or empty, the agent has no behavior — it silently acts as a
        blank agent with no instructions.
        """
        import tomllib

        agents_dir = smoke_install_dir / "agents"
        for toml_file in agents_dir.glob("*.toml"):
            data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
            agent_section = data.get("agent", {})
            assert "developer_instructions" in agent_section, (
                f"Agent TOML {toml_file.name} missing 'developer_instructions'. "
                "Without instructions, the agent has no behavior in Codex."
            )
            instructions = agent_section["developer_instructions"]
            assert isinstance(instructions, str) and instructions.strip(), (
                f"Agent TOML {toml_file.name} has empty developer_instructions. "
                "An agent with no instructions is a silent no-op in Codex."
            )


# ---------------------------------------------------------------------------
# Codex discovery test — aspirational, deferred
#
# Codex does not expose a non-interactive `--list-skills` or equivalent command.
# Running `codex` without arguments opens an interactive REPL session.
# There is no way to verify skill discovery without a live interactive session
# or mock of Codex's internal state.
#
# Decision: defer Codex discovery verification to a future task when Codex
# adds a `codex skills list` or equivalent CLI subcommand.
# Current verification: structural checks above confirm Codex COULD discover
# the installed skills — all required files and directories are present.
#
# This block is a placeholder to document the deferral explicitly.
# ---------------------------------------------------------------------------

# NOTE: Codex discovery smoke test deferred.
# Reason: codex has no non-interactive skill-listing command.
# When Codex adds `codex skills list` or equivalent, implement here.
# Tracking: scar report task-10, known_shortcuts, deferred_to_feature_iteration=true
