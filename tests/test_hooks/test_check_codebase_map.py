"""
Tests for hooks/check-codebase-map — churn-based freshness detection.

File layout:
  - Helpers (shared fixture builders)
  - DEATH TESTS (DC-*) — must be RED against the current mtime hook
  - UNIT TESTS — assert (exit code, JSON additionalContext status) contract

Death case taxonomy:
  DC-1: mtime gaming — map touched to now, last_updated old, ≥ threshold files changed
         → verdict MUST be stale (not fresh). Proves mtime dependency is killed.
  DC-2: not a git repo → verdict MUST be unknown; exit 0; no set -u crash.
  DC-3: last_updated missing or malformed → verdict MUST be unknown.
  DC-5: churn 50, threshold 30 → verdict stale; message includes the count.
  DC-7: git log failure (empty repo, no commits) → verdict unknown, never silent fresh.
  DC-8: last_updated is a future date (e.g. "2099-01-01") → verdict MUST be unknown.
         git log --since=<future> returns 0 commits → churn=0 → would silently claim
         fresh, but 0 proves nothing about a future date. Must be UNKNOWN.

Unit test contract source: the hook's emitted output boundary (stable CLI contract).
  fresh   → (returncode=0, stdout="")
  stale   → (returncode=0, stdout=JSON, additionalContext contains "STALE" + count)
  unknown → (returncode=0, stdout=JSON, additionalContext contains "UNKNOWN")
  missing → (returncode=0, stdout=JSON, additionalContext contains "MISSING")
"""

import datetime
import json
import os
import subprocess
import time
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent
HOOK_PATH = REPO_ROOT / "hooks" / "check-codebase-map"

# Paths excluded from churn counting (must match the awk filter in the hook).
# Cross-boundary duplication with the hook's awk regex is intentional — they are
# separate languages; do not try to share the definition across bash/python.
_EXCLUDED_DIRS = ["changes", "docs", "bugfix"]

_GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@test.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@test.com",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_hook(project_dir: Path) -> subprocess.CompletedProcess:
    """Run the hook with CLAUDE_PROJECT_DIR pointing at project_dir."""
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)}
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        env=env,
        capture_output=True,
        text=True,
    )


def additional_context(result: subprocess.CompletedProcess) -> str:
    """Parse additionalContext from hook JSON stdout. Raises on bad JSON."""
    data = json.loads(result.stdout)
    return data["hookSpecificOutput"]["additionalContext"]


def git_cmd(args: list, cwd: Path, date: str | None = None) -> None:
    """Run a git command in cwd. Raises CalledProcessError on failure."""
    env = {**os.environ, **_GIT_IDENTITY}
    if date:
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def init_repo(path: Path) -> None:
    """Initialize a git repo with one empty initial commit (date: 2020-01-01)."""
    path.mkdir(parents=True, exist_ok=True)
    git_cmd(["init"], cwd=path)
    git_cmd(
        ["commit", "--allow-empty", "-m", "init"],
        cwd=path,
        date="2020-01-01T00:00:00",
    )


def write_map(
    project_dir: Path,
    last_updated: str | None = "2025-01-01",
    threshold: int | None = None,
    raw_content: str | None = None,
) -> Path:
    """Write .samsara/codebase-map.yaml.

    If raw_content is given, write it verbatim (ignores other params).
    If last_updated is None, the field is omitted.
    If threshold is None, staleness_churn_threshold is omitted (default fallback).
    """
    samsara_dir = project_dir / ".samsara"
    samsara_dir.mkdir(parents=True, exist_ok=True)
    map_file = samsara_dir / "codebase-map.yaml"
    if raw_content is not None:
        map_file.write_text(raw_content)
        return map_file
    lines = ["project: test\n"]
    if last_updated is not None:
        lines.append(f'last_updated: "{last_updated}"\n')
    if threshold is not None:
        lines.append(f"staleness_churn_threshold: {threshold}\n")
    map_file.write_text("".join(lines))
    return map_file


def commit_files(
    repo: Path,
    filenames: list,
    date: str,
    subdir: str = "src",
) -> None:
    """Write files under repo/subdir and commit them all with the given date."""
    src = repo / subdir
    src.mkdir(exist_ok=True)
    for name in filenames:
        (src / name).write_text(f"# {name}\n")
    # Add only the specific subdir — avoids picking up untracked map files
    git_cmd(["add", subdir], cwd=repo)
    git_cmd(
        ["commit", "-m", f"add {len(filenames)} files"],
        cwd=repo,
        date=date,
    )


def set_mtime_days_ago(path: Path, days: int) -> None:
    """Set file mtime to N days in the past."""
    old_time = time.time() - (days * 86400)
    os.utime(str(path), (old_time, old_time))


# ---------------------------------------------------------------------------
# DEATH TESTS
# ---------------------------------------------------------------------------


class TestDC1MtimeGaming:
    """DC-1: The hook must NOT use file mtime for freshness.

    Current mtime hook: touches the map file to now → age_days=0 → 'fresh_0_days'
    → exits 0 silently. This test is RED against the current hook.
    New churn hook: last_updated is old, 35 files changed → STALE regardless of mtime.
    """

    def test_touched_map_with_old_last_updated_and_high_churn_is_stale(
        self, tmp_path: Path
    ) -> None:
        """Map mtime=now, last_updated ~90 days ago, 35 files changed → stale.

        Against the OLD mtime hook: mtime=now → age_days=0 → fresh → stdout empty.
        This test asserts stdout is non-empty with STALE → RED vs old hook.
        """
        init_repo(tmp_path)

        # last_updated is ~90 days before today (2026-06-28)
        last_updated = "2026-03-29"
        map_file = write_map(tmp_path, last_updated=last_updated, threshold=30)

        # Commit 35 source files AFTER last_updated (date: 2026-05-01)
        filenames = [f"file_{i}.py" for i in range(35)]
        commit_files(tmp_path, filenames, date="2026-05-01T00:00:00")

        # Touch the map file to NOW — this is the mtime-gaming move
        now = time.time()
        os.utime(str(map_file), (now, now))

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), (
            "Hook produced no output — verdict appears fresh. "
            "The hook is using mtime (file touched to now = 0 days old) "
            "instead of git churn (35 files > threshold 30)."
        )
        ctx = additional_context(result)
        assert "STALE" in ctx, (
            f"Expected STALE verdict, got: {ctx!r}. "
            "Mtime-gamed file is fresh by mtime but stale by churn."
        )


class TestDC2NotAGitRepo:
    """DC-2: No .git directory → unknown verdict; exit 0; no set -u crash.

    Current mtime hook: uses stat on map file, never checks git → returns
    fresh/stale based on mtime. This test is RED vs the current hook.
    """

    def test_no_git_dir_emits_unknown_verdict(self, tmp_path: Path) -> None:
        """Directory with a map but no .git → UNKNOWN, not stale or fresh."""
        # No git init — just write the map file directly
        write_map(tmp_path, last_updated="2025-01-01")
        # Also set mtime old so old hook would say stale (proves the test is RED)
        set_mtime_days_ago(tmp_path / ".samsara" / "codebase-map.yaml", 30)

        result = run_hook(tmp_path)

        assert result.returncode == 0, (
            f"Hook crashed (exit {result.returncode}). stderr: {result.stderr!r}"
        )
        assert result.stdout.strip(), (
            "Hook produced no output for non-git repo — should emit UNKNOWN."
        )
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN verdict for non-git repo, got: {ctx!r}"
        )

    def test_no_git_dir_does_not_crash_under_set_u(self, tmp_path: Path) -> None:
        """set -u must not cause unbound variable crash when git is absent."""
        write_map(tmp_path, last_updated="2025-01-01")

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert "unbound variable" not in result.stderr, (
            f"set -u triggered unbound variable error: {result.stderr!r}"
        )


class TestDC3MissingOrMalformedLastUpdated:
    """DC-3: last_updated missing or malformed → unknown verdict.

    Current mtime hook: never reads last_updated. A freshly-written map
    → mtime=now → fresh → silent exit. Tests are RED vs current hook.
    """

    def test_map_without_last_updated_field_is_unknown(self, tmp_path: Path) -> None:
        """Map with no last_updated field → UNKNOWN (cannot verify freshness)."""
        init_repo(tmp_path)
        write_map(tmp_path, last_updated=None)  # omit the field

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), "Expected JSON output when last_updated missing"
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN for missing last_updated, got: {ctx!r}"
        )

    def test_map_with_invalid_date_last_updated_is_unknown(
        self, tmp_path: Path
    ) -> None:
        """Map with last_updated: 'not-a-date' → UNKNOWN."""
        init_repo(tmp_path)
        write_map(
            tmp_path,
            raw_content='project: test\nlast_updated: "not-a-date"\n',
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), "Expected JSON output for malformed last_updated"
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN for malformed last_updated 'not-a-date', got: {ctx!r}"
        )

    def test_map_with_numeric_last_updated_is_unknown(self, tmp_path: Path) -> None:
        """Map with last_updated: 20260101 (no hyphens) → UNKNOWN."""
        init_repo(tmp_path)
        write_map(
            tmp_path,
            raw_content="project: test\nlast_updated: 20260101\n",
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN for numeric last_updated (no hyphens), got: {ctx!r}"
        )


class TestDC5OverThreshold:
    """DC-5: churn=50, threshold=30 → stale, message includes the count '50'.

    Current mtime hook: uses mtime, never counts churn. A freshly-written
    map → fresh → silent exit. Test is RED vs current hook.
    """

    def test_churn_over_threshold_emits_stale_with_count(self, tmp_path: Path) -> None:
        """50 changed files with threshold 30 → STALE verdict including '50'."""
        init_repo(tmp_path)
        write_map(tmp_path, last_updated="2025-01-01", threshold=30)

        # Commit 50 distinct files after last_updated
        filenames = [f"module_{i}.py" for i in range(50)]
        commit_files(tmp_path, filenames, date="2025-06-01T00:00:00")

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), "Expected JSON output for over-threshold churn"
        ctx = additional_context(result)
        assert "STALE" in ctx, (
            f"Expected STALE for 50 files > threshold 30, got: {ctx!r}"
        )
        assert "50" in ctx, (
            f"STALE message must include the churn count (50), got: {ctx!r}"
        )


class TestDC7BoundedComputation:
    """DC-7: git log failure → unknown, never silent fresh.

    A git repo with no commits: git rev-parse --git-dir succeeds (repo exists),
    but git log exits 128 ('branch has no commits'). This pins the failure-path
    to unknown. Current mtime hook: never runs git → fresh if mtime recent → RED.
    """

    def test_git_log_failure_maps_to_unknown_not_fresh(self, tmp_path: Path) -> None:
        """Empty git repo (no commits): git log fails → UNKNOWN, not silent fresh."""
        # Init the dir as a git repo but make NO commits
        tmp_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init"],
            cwd=str(tmp_path),
            check=True,
            capture_output=True,
        )
        write_map(tmp_path, last_updated="2025-01-01")
        # Leave map mtime recent (new hook ignores mtime; old hook → fresh → proves RED)

        result = run_hook(tmp_path)

        assert result.returncode == 0, (
            f"Hook crashed (exit {result.returncode}). stderr: {result.stderr!r}"
        )
        assert result.stdout.strip(), (
            "Hook produced no output after git log failure — "
            "should emit UNKNOWN, not claim fresh silently."
        )
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN when git log fails (no commits), got: {ctx!r}"
        )


class TestDC8FutureLastUpdated:
    """DC-8: last_updated in the future → UNKNOWN, never silent fresh.

    A future date passes the YYYY-MM-DD format check. git log --since=<future>
    returns 0 commits → churn=0 < threshold → would silently claim fresh.
    But 0 commits proves nothing about a future date; freshness is unverifiable.

    Current hook (before fix): no future-date check → 0 churn → fresh → stdout empty.
    This test is RED before the future-date guard is added.
    """

    def test_future_last_updated_emits_unknown_not_fresh(self, tmp_path: Path) -> None:
        """Map with last_updated='2099-01-01': hook MUST emit UNKNOWN, not fresh.

        Contract violation being pinned: churn=0 from a future date is not evidence
        of freshness — it is unverifiable input. Any unverifiable input → UNKNOWN.
        """
        init_repo(tmp_path)
        write_map(tmp_path, last_updated="2099-01-01", threshold=30)

        result = run_hook(tmp_path)

        assert result.returncode == 0, (
            f"Hook crashed (exit {result.returncode}). stderr: {result.stderr!r}"
        )
        assert result.stdout.strip(), (
            "Hook produced no output for future last_updated='2099-01-01' — "
            "silently claiming fresh. A future date is unverifiable; must emit UNKNOWN."
        )
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx, (
            f"Expected UNKNOWN for future last_updated '2099-01-01', got: {ctx!r}. "
            "git log returns 0 commits for any future date, making churn=0 meaningless."
        )

    def test_last_updated_today_is_valid_not_unknown(self, tmp_path: Path) -> None:
        """last_updated = today (runtime) → proceeds to churn, NOT UNKNOWN.

        Guards the strict > (not >=) in the future-date check. If the guard were
        regressed to >=, a map regenerated today would report UNKNOWN — causing
        an auto-regen loop since regen stamps today's date as last_updated.

        With all commits in the far past, churn=0 < threshold → fresh (stdout empty).
        The decisive assertion: stdout is empty, not UNKNOWN.
        """
        today = datetime.date.today().isoformat()  # YYYY-MM-DD, matches date +%Y-%m-%d

        init_repo(tmp_path)
        # Commits in the far past — not counted by git log --since=today
        commit_files(tmp_path, ["past_a.py", "past_b.py"], date="2025-01-01T00:00:00")
        write_map(tmp_path, last_updated=today, threshold=30)

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout == "", (
            f"Expected fresh (empty stdout) for last_updated=today ({today!r}), "
            f"got: {result.stdout!r}. "
            "The future-date guard may use >= instead of > — today is a valid date "
            "(not future), so churn computation must proceed, not emit UNKNOWN."
        )


# ---------------------------------------------------------------------------
# UNIT TESTS — (exit code, JSON additionalContext status) contract
# ---------------------------------------------------------------------------


class TestContractFresh:
    """Fresh map: exit 0, empty stdout (zero token cost).

    Map mtime is set to 30 days ago so the OLD mtime hook would emit stale
    (age > 7 days). The NEW hook ignores mtime and uses churn — these tests
    are RED vs old hook.
    """

    def test_fresh_map_exits_silently(self, tmp_path: Path) -> None:
        """last_updated after all commits, churn=0 < threshold → exit 0, stdout empty.

        Contract: fresh = (returncode=0, stdout="").
        Map mtime is 30 days old so old hook would emit stale → test is RED vs old.
        """
        init_repo(tmp_path)

        # A couple of commits long before last_updated
        commit_files(tmp_path, ["old_a.py", "old_b.py"], date="2025-01-01T00:00:00")

        # last_updated is AFTER all commits → no churn since then
        map_file = write_map(tmp_path, last_updated="2026-01-01", threshold=30)

        # Set mtime to 30 days ago (old hook would say stale; new hook uses churn)
        set_mtime_days_ago(map_file, 30)

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout == "", (
            f"Fresh map (churn=0 < 30) should produce empty stdout. "
            f"Got: {result.stdout!r}. Hook may still use mtime (30 days old > 7)."
        )

    def test_not_applicable_when_claude_project_dir_unset(self) -> None:
        """No CLAUDE_PROJECT_DIR → exit 0, empty stdout (not_applicable path).

        Contract: (returncode=0, stdout="") — no injection outside a project.
        """
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        result = subprocess.run(
            ["bash", str(HOOK_PATH)],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestContractMissing:
    """Missing map: exit 0, JSON additionalContext contains 'MISSING'."""

    def test_missing_map_emits_missing_status(self, tmp_path: Path) -> None:
        """No .samsara/codebase-map.yaml → JSON with 'MISSING' in additionalContext.

        Contract: (returncode=0, 'MISSING' in additionalContext).
        """
        init_repo(tmp_path)
        # Do NOT write a map file

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), "Expected JSON output for missing map"
        ctx = additional_context(result)
        assert "MISSING" in ctx, (
            f"Expected 'MISSING' in additionalContext, got: {ctx!r}"
        )


class TestContractStale:
    """Stale map: exit 0, JSON additionalContext contains 'STALE' and churn count."""

    def test_stale_map_emits_stale_status_with_churn_count(
        self, tmp_path: Path
    ) -> None:
        """Churn=10 > threshold=5 → 'STALE' + '10' in additionalContext.

        Contract: (returncode=0, 'STALE' in context, churn count '10' in context).
        """
        init_repo(tmp_path)
        write_map(tmp_path, last_updated="2025-01-01", threshold=5)

        commit_files(
            tmp_path, [f"f{i}.py" for i in range(10)], date="2025-06-01T00:00:00"
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        ctx = additional_context(result)
        assert "STALE" in ctx, f"Expected STALE, got: {ctx!r}"
        assert "10" in ctx, f"Expected churn count '10' in message, got: {ctx!r}"

    def test_churn_equal_to_threshold_is_stale(self, tmp_path: Path) -> None:
        """Churn == threshold → stale (threshold is inclusive: churn >= threshold).

        Contract: equality at threshold boundary produces STALE verdict.
        """
        init_repo(tmp_path)
        threshold = 5
        write_map(tmp_path, last_updated="2025-01-01", threshold=threshold)

        commit_files(
            tmp_path,
            [f"eq{i}.py" for i in range(threshold)],
            date="2025-06-01T00:00:00",
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), (
            f"Hook produced no output for churn={threshold} >= threshold={threshold} — "
            "expected STALE, got silent fresh."
        )
        ctx = additional_context(result)
        assert "STALE" in ctx, (
            f"Expected STALE when churn ({threshold}) equals threshold, got: {ctx!r}"
        )


class TestContractUnknown:
    """Unknown freshness: exit 0, JSON additionalContext contains 'UNKNOWN'."""

    def test_unknown_emits_unknown_status_and_exits_zero(self, tmp_path: Path) -> None:
        """Non-git repo → UNKNOWN, exit 0. (Positive contract for unknown verdict.)

        Contract: (returncode=0, 'UNKNOWN' in additionalContext).
        """
        write_map(tmp_path, last_updated="2025-01-01")
        # No git repo

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), (
            "Hook produced no output for non-git-repo — expected UNKNOWN, got silent fresh."
        )
        ctx = additional_context(result)
        assert "UNKNOWN" in ctx


class TestContractThreshold:
    """Threshold field: read from map when present; default 30 when absent."""

    def test_threshold_read_from_map(self, tmp_path: Path) -> None:
        """staleness_churn_threshold=2 in map: 3 files > 2 → STALE.

        Contract: hook reads threshold from the map field, not a hardcoded value.
        (3 files < default 30 → would be fresh if default were used.)
        """
        init_repo(tmp_path)
        write_map(tmp_path, last_updated="2025-01-01", threshold=2)

        # 3 files changed (< default 30, but > threshold 2 from map)
        commit_files(tmp_path, ["a.py", "b.py", "c.py"], date="2025-06-01T00:00:00")

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), (
            "Hook produced no output for 3 files > threshold 2 — expected STALE, got silent fresh. "
            "Hook may be using hardcoded threshold instead of reading from map."
        )
        ctx = additional_context(result)
        assert "STALE" in ctx, (
            f"Expected STALE (3 files > threshold 2 from map), got: {ctx!r}. "
            "Hook may be using hardcoded threshold instead of reading from map."
        )

    def test_default_threshold_30_when_field_absent(self, tmp_path: Path) -> None:
        """No staleness_churn_threshold field → default 30.

        Contract: 29 files changed < 30 (default) → fresh.
        This is the dogfood case: this repo's live map has staleness_threshold_days
        (old field), not staleness_churn_threshold — absent-field fallback must work.
        Map mtime set 30 days ago → RED vs old mtime hook.
        """
        init_repo(tmp_path)
        # Map with old field name (not the new one) — simulates this repo's live map
        map_file = write_map(
            tmp_path,
            raw_content='project: test\nlast_updated: "2025-01-01"\nstaleness_threshold_days: 7\n',
        )
        set_mtime_days_ago(map_file, 30)

        # 29 files changed after last_updated (< default threshold 30)
        commit_files(
            tmp_path, [f"f{i}.py" for i in range(29)], date="2025-06-01T00:00:00"
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout == "", (
            f"Expected fresh (29 < default threshold 30), got: {result.stdout!r}. "
            "Hook may not be defaulting to 30 when staleness_churn_threshold absent."
        )

    def test_default_threshold_30_stale_at_boundary(self, tmp_path: Path) -> None:
        """No staleness_churn_threshold field, 30 files → stale at default boundary.

        Contract: churn=30 >= default 30 → STALE.
        """
        init_repo(tmp_path)
        write_map(
            tmp_path,
            raw_content='project: test\nlast_updated: "2025-01-01"\n',
        )

        commit_files(
            tmp_path, [f"g{i}.py" for i in range(30)], date="2025-06-01T00:00:00"
        )

        result = run_hook(tmp_path)

        assert result.returncode == 0
        assert result.stdout.strip(), (
            "Hook produced no output for 30 files >= default threshold 30 — "
            "expected STALE, got silent fresh."
        )
        ctx = additional_context(result)
        assert "STALE" in ctx, (
            f"Expected STALE (30 >= default threshold 30), got: {ctx!r}"
        )


class TestContractExclusionPaths:
    """Files under changes/, docs/, bugfix/ are excluded from churn count."""

    def test_files_under_excluded_paths_not_counted_toward_churn(
        self, tmp_path: Path
    ) -> None:
        """15 files committed ONLY under excluded paths → churn=0 → fresh.

        Contract: excluded paths (changes/, docs/, bugfix/) do not count toward
        churn. Map mtime 30 days old → RED vs old mtime hook (would say stale).
        """
        init_repo(tmp_path)
        map_file = write_map(tmp_path, last_updated="2025-01-01", threshold=5)
        set_mtime_days_ago(map_file, 30)

        # Commit 15 files ONLY under excluded paths (> threshold 5)
        for excluded_dir in _EXCLUDED_DIRS:
            d = tmp_path / excluded_dir
            d.mkdir(exist_ok=True)
            for i in range(5):
                (d / f"note_{i}.md").write_text("excluded content\n")

        # Add only excluded dirs — avoid staging untracked .samsara/codebase-map.yaml
        git_cmd(["add", *_EXCLUDED_DIRS], cwd=tmp_path)
        git_cmd(
            ["commit", "-m", "add excluded files only"],
            cwd=tmp_path,
            date="2025-06-01T00:00:00",
        )

        result = run_hook(tmp_path)

        # Only excluded files changed → churn=0 < threshold 5 → fresh
        assert result.returncode == 0
        assert result.stdout == "", (
            f"Expected fresh (only excluded paths changed, churn=0 < 5), "
            f"got: {result.stdout!r}"
        )

    def test_mixed_files_excluded_and_source_counted(self, tmp_path: Path) -> None:
        """Excluded files + 3 source files: only source files count toward churn.

        Contract: excluded files do not inflate churn; source files do.
        threshold=5, source count=3 → fresh (3 < 5).
        """
        init_repo(tmp_path)
        map_file = write_map(tmp_path, last_updated="2025-01-01", threshold=5)
        set_mtime_days_ago(map_file, 30)

        # Write 9 excluded files + 3 source files in one commit
        for excluded_dir in _EXCLUDED_DIRS:
            d = tmp_path / excluded_dir
            d.mkdir(exist_ok=True)
            for i in range(3):
                (d / f"doc_{i}.md").write_text("excluded\n")

        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        for i in range(3):
            (src / f"src_{i}.py").write_text(f"# src file {i}\n")

        # Add only the intended dirs — avoid staging untracked .samsara/codebase-map.yaml
        git_cmd(["add", *_EXCLUDED_DIRS, "src"], cwd=tmp_path)
        git_cmd(
            ["commit", "-m", "mixed: excluded + source files"],
            cwd=tmp_path,
            date="2025-06-01T00:00:00",
        )

        result = run_hook(tmp_path)

        # 3 source files < threshold 5 → fresh
        assert result.returncode == 0
        assert result.stdout == "", (
            f"Expected fresh (3 source files < threshold 5), got: {result.stdout!r}. "
            "Excluded files may be counted toward churn."
        )
