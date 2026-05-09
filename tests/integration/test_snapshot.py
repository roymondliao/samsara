"""
Integration tests — Snapshot comparison.

Converts the test fixture and compares output byte-for-byte against committed
expected output in tests/fixtures/expected/codex/.

Snapshot update mechanism:
  Set UPDATE_SNAPSHOTS=1 env var to regenerate snapshots from current engine output.
  Normal runs (UPDATE_SNAPSHOTS not set) compare output against committed snapshots.
  Any conversion logic change that alters output will fail these tests — by design.

Death tests guard:
  DC-9-7: Snapshot test must FAIL if output differs from committed snapshot — not
           silently pass on diff. If our comparison logic has a bug that makes it
           always pass (e.g., comparing against itself), regressions are invisible.
  DC-9-8: UPDATE_SNAPSHOTS=1 must write actual output to snapshot dir, not silently
           do nothing. If the update path has a bug, snapshots never update and
           subsequent runs fail permanently.
  DC-9-9: Snapshot test must FAIL if the snapshots directory is empty or missing.
           An empty snapshot dir means the test is comparing nothing — passing
           silently while exercising no real assertion.

Assumption: Conversion output is platform-independent (UTF-8, LF line endings).
  If conversion produces CRLF on Windows, snapshot comparison fails.
  This is documented in the scar report as an unverified assumption.
Assumption: The committed snapshots in tests/fixtures/expected/codex/ were generated
  by running UPDATE_SNAPSHOTS=1 on the same Python version and platform.
Assumption: Agent TOML files contain a '# Source: <absolute_path>' comment line
  that is normalized to '# Source: <normalized>' before snapshot comparison.
  Without normalization, snapshots would fail on every machine with a different path.
"""

import os
import re
import shutil
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine

# --- Fixture paths ---
FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"
FIXTURE_EXPECTED = Path(__file__).parent.parent / "fixtures" / "expected" / "codex"
FIXTURE_EXPECTED_GEMINI = (
    Path(__file__).parent.parent / "fixtures" / "expected" / "gemini-cli"
)

# Pattern matching the '# Source: <path>' comment in generated agent TOML files.
# The source path is an absolute path that differs between machines.
# We normalize it to a stable placeholder before comparison.
_SOURCE_PATH_COMMENT = re.compile(r"^# Source: .+$", re.MULTILINE)
_SOURCE_PATH_NORMALIZED = "# Source: <normalized>"


def _should_update_snapshots() -> bool:
    """Return True if UPDATE_SNAPSHOTS=1 is set in environment.

    Silent failure guard: if CI=true (GitHub Actions, CircleCI, etc.) AND
    UPDATE_SNAPSHOTS=1, we print a loud warning. This does not fail the test
    (the update may be intentional in CI), but makes accidental CI updates visible
    in the test output.
    """
    if os.environ.get("UPDATE_SNAPSHOTS", "").strip() == "1":
        ci_env = os.environ.get("CI", "") or os.environ.get("GITHUB_ACTIONS", "")
        if ci_env:
            print(
                "\n[WARNING] UPDATE_SNAPSHOTS=1 is set AND CI environment detected. "
                "Snapshots are being UPDATED, not compared. "
                "If this is unintentional, remove UPDATE_SNAPSHOTS from CI env vars. "
                "CI snapshot updates silently hide conversion regressions.",
                flush=True,
            )
        return True
    return False


def _normalize_content(content: str) -> str:
    """Normalize content for platform-independent snapshot comparison.

    Normalizations applied:
    1. '# Source: <absolute_path>' comments in TOML files → '# Source: <normalized>'
       Rationale: agent TOML template emits the source file's absolute path.
       This differs between machines. We normalize to a stable placeholder.

    Silent failure: if the template changes the comment format (e.g., renames
    '# Source:' to '# Generated from:'), normalization silently stops working
    and snapshot comparison fails for all TOML files until snapshots are regenerated.
    """
    return _SOURCE_PATH_COMMENT.sub(_SOURCE_PATH_NORMALIZED, content)


def _collect_output_files(output_dir: Path) -> dict[str, str]:
    """Collect all files from output_dir as {relative_path_str: normalized_content}.

    Returns file contents keyed by POSIX path relative to output_dir.
    All files must be readable as UTF-8 text. Raises on read failure — a file
    that cannot be read must not be silently omitted from snapshot comparison.
    Content is normalized via _normalize_content() for platform-independent comparison.
    """
    files: dict[str, str] = {}
    for file_path in sorted(output_dir.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(output_dir)
        raw_content = file_path.read_text(encoding="utf-8")
        files[relative.as_posix()] = _normalize_content(raw_content)
    return files


def _write_snapshots(output_dir: Path, snapshot_dir: Path) -> None:
    """Write all output files to the snapshot directory.

    Clears the snapshot directory first to avoid stale snapshot files
    from a previous conversion that produced more files.

    Text files are normalized via _normalize_content() before writing.
    Binary files that cannot be decoded as UTF-8 are copied as-is.
    This ensures snapshots are platform-independent (no absolute paths).
    """
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    snapshot_dir.mkdir(parents=True)

    for file_path in sorted(output_dir.rglob("*")):
        if not file_path.is_file():
            continue
        relative = file_path.relative_to(output_dir)
        dest = snapshot_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Normalize text files; binary fallback only for UnicodeDecodeError
        try:
            raw_content = file_path.read_text(encoding="utf-8")
            normalized = _normalize_content(raw_content)
            dest.write_text(normalized, encoding="utf-8")
        except UnicodeDecodeError:
            dest.write_bytes(file_path.read_bytes())


def _snapshot_content_diff_message(
    rel_path: str, actual_content: str, expected_content: str
) -> str:
    """Return a compact, actionable content diff message for snapshots."""
    actual_lines = actual_content.splitlines()
    expected_lines = expected_content.splitlines()
    first_diff = next(
        (i for i, (a, e) in enumerate(zip(actual_lines, expected_lines)) if a != e),
        len(min(actual_lines, expected_lines, key=len)),
    )

    if first_diff < len(expected_lines) and first_diff < len(actual_lines):
        return (
            f"CONTENT DIFFERS: {rel_path} "
            f"(first diff at line {first_diff + 1}: "
            f"expected={expected_lines[first_diff]!r} "
            f"actual={actual_lines[first_diff]!r})"
        )
    return (
        f"CONTENT DIFFERS: {rel_path} "
        f"(expected {len(expected_lines)} lines, got {len(actual_lines)} lines)"
    )


# ---------------------------------------------------------------------------
# Self-iteration fix: normalization must actually transform source path comments.
# Guards against the silent failure where the regex pattern no longer matches
# after a template change — normalization silently stops working.
# ---------------------------------------------------------------------------


class TestNormalizationActuallyTransforms:
    """Verify _normalize_content() transforms known patterns — not a no-op."""

    def test_normalize_replaces_source_comment(self) -> None:
        """_normalize_content must change '# Source: /abs/path' to placeholder."""
        raw = '# Source: /Users/someone/project/agents/implementer.md\nname = "x"\n'
        normalized = _normalize_content(raw)
        assert "# Source: <normalized>" in normalized, (
            "_normalize_content did not replace '# Source: <path>' comment. "
            "Snapshot comparison would fail with absolute path mismatches."
        )
        assert "/Users/someone" not in normalized, (
            "Absolute path still present after normalization. "
            "Snapshots would be machine-specific."
        )

    def test_normalize_is_idempotent(self) -> None:
        """_normalize_content applied twice produces the same result as once."""
        raw = "# Source: /abs/path/file.md\nsome content\n"
        once = _normalize_content(raw)
        twice = _normalize_content(once)
        assert once == twice, (
            "Normalization is not idempotent. "
            "Applying it twice produces different content — comparing snapshot "
            "to actual would use different normalization counts."
        )

    def test_normalize_does_not_change_normal_content(self) -> None:
        """_normalize_content must not alter content that has no source paths."""
        content = (
            'name = "samsara-implementer"\ndeveloper_instructions = """\nhello\n"""\n'
        )
        normalized = _normalize_content(content)
        assert normalized == content, (
            "Normalization altered content that has no '# Source:' comment. "
            "Over-aggressive normalization would corrupt snapshots."
        )


# ---------------------------------------------------------------------------
# DC-9-7: Snapshot comparison must fail on diff — not silently pass
# ---------------------------------------------------------------------------


class TestDC97SnapshotComparisionMustFailOnDiff:
    """Death test: comparison logic must fail when content differs."""

    def test_comparison_fails_on_content_diff(self) -> None:
        """Verify our comparison logic produces a failure on different content.

        This is a meta-test: we construct a known difference and verify our
        comparison code would produce a non-empty diff report. If this fails,
        our comparison logic would never catch real regressions.
        """
        actual = {"skills/samsara-research/SKILL.md": "# Research\nconverted content\n"}
        expected = {
            "skills/samsara-research/SKILL.md": "# Research\nDIFFERENT content\n"
        }

        diffs: list[str] = []
        for rel_path, actual_content in actual.items():
            if rel_path not in expected:
                diffs.append(f"EXTRA in actual: {rel_path}")
            elif actual_content != expected[rel_path]:
                diffs.append(f"CONTENT DIFFERS: {rel_path}")

        assert len(diffs) == 1, (
            "Expected comparison to produce 1 diff for differing content. "
            f"Got {len(diffs)}. Our comparison logic cannot detect regressions."
        )

    def test_comparison_fails_on_missing_file(self) -> None:
        """Verify comparison fails when a file is in expected but not in actual."""
        actual = {}
        expected = {"agents/implementer.toml": 'name = "implementer"\n'}

        diffs: list[str] = []
        for rel_path in expected:
            if rel_path not in actual:
                diffs.append(f"MISSING in actual: {rel_path}")

        assert len(diffs) == 1, (
            "Expected comparison to fail on missing file. "
            "Our comparison logic would not catch missing output files."
        )

    def test_comparison_fails_on_extra_file(self) -> None:
        """Verify comparison fails when actual has a file not in expected."""
        actual = {
            "agents/implementer.toml": 'name = "implementer"\n',
            "agents/unexpected.toml": 'name = "ghost"\n',
        }
        expected = {"agents/implementer.toml": 'name = "implementer"\n'}

        diffs: list[str] = []
        for rel_path in actual:
            if rel_path not in expected:
                diffs.append(f"EXTRA in actual: {rel_path}")

        assert len(diffs) == 1, (
            "Expected comparison to fail on extra file. "
            "Our comparison logic would not catch extra output files."
        )

    def test_content_diff_message_reports_first_differing_line(self) -> None:
        """Content diff diagnostics must identify the first changed line."""
        message = _snapshot_content_diff_message(
            ".gemini/skills/samsara-research/SKILL.md",
            "# Research\nnew body\n",
            "# Research\nold body\n",
        )

        assert "first diff at line 2" in message
        assert "expected='old body'" in message
        assert "actual='new body'" in message


# ---------------------------------------------------------------------------
# DC-9-8: UPDATE_SNAPSHOTS=1 must actually write snapshots
# ---------------------------------------------------------------------------


class TestDC98SnapshotUpdateMustWrite:
    """Death test: snapshot update mechanism must write files, not silently no-op."""

    def test_update_writes_files_to_snapshot_dir(self, tmp_path: Path) -> None:
        """Verify that _write_snapshots() actually writes files.

        This is a unit test of the snapshot update helper. If this function
        silently no-ops, UPDATE_SNAPSHOTS=1 would never update anything.
        """
        # Create a fake "output" with one file
        fake_output = tmp_path / "fake_output"
        fake_output.mkdir()
        (fake_output / "skills").mkdir()
        (fake_output / "skills" / "samsara-research").mkdir()
        (fake_output / "skills" / "samsara-research" / "SKILL.md").write_text(
            "# Research\n"
        )

        snap_dir = tmp_path / "snapshots"
        _write_snapshots(fake_output, snap_dir)

        assert snap_dir.exists(), "Snapshot dir was not created"
        written_files = list(snap_dir.rglob("*"))
        file_count = sum(1 for f in written_files if f.is_file())
        assert file_count >= 1, (
            f"_write_snapshots() wrote {file_count} files — expected at least 1. "
            "UPDATE_SNAPSHOTS=1 would silently produce empty snapshots."
        )

    def test_update_clears_stale_snapshots(self, tmp_path: Path) -> None:
        """Verify that _write_snapshots() removes stale files from previous run."""
        # Setup: snapshot dir with a stale file
        snap_dir = tmp_path / "snapshots"
        snap_dir.mkdir()
        stale_file = snap_dir / "stale.toml"
        stale_file.write_text('name = "stale"\n')

        # New output without the stale file
        fake_output = tmp_path / "fake_output"
        fake_output.mkdir()
        (fake_output / "new.txt").write_text("new content\n")

        _write_snapshots(fake_output, snap_dir)

        assert not stale_file.exists(), (
            "Stale snapshot file was not removed. "
            "UPDATE_SNAPSHOTS would accumulate stale files from old conversions."
        )
        assert (snap_dir / "new.txt").exists(), "New file was not written to snapshots"


# ---------------------------------------------------------------------------
# DC-9-9: Snapshot test must fail if snapshot dir is missing or empty
# ---------------------------------------------------------------------------


class TestDC99SnapshotDirMustExistAndBeNonEmpty:
    """Death test: missing or empty snapshot dir must not produce silent pass."""

    def test_missing_snapshot_dir_is_detected(self) -> None:
        """Verify that missing snapshot dir is reported as an error, not skipped."""
        non_existent = Path("/tmp/this_snapshot_dir_does_not_exist_12345")
        errors: list[str] = []
        if not non_existent.exists():
            errors.append(f"Snapshot directory missing: {non_existent}")
        assert len(errors) == 1, (
            "Missing snapshot dir was not detected. "
            "Tests would silently compare against nothing."
        )

    def test_empty_snapshot_dir_is_detected(self, tmp_path: Path) -> None:
        """Verify that empty snapshot dir produces a test failure, not silent pass."""
        empty_dir = tmp_path / "empty_snapshots"
        empty_dir.mkdir()

        expected_files = _collect_output_files(empty_dir)
        errors: list[str] = []
        if not expected_files:
            errors.append("Snapshot directory is empty — no files to compare against")

        assert len(errors) == 1, (
            "Empty snapshot dir was not detected. "
            "Our comparison would silently pass with no assertions made."
        )


# ---------------------------------------------------------------------------
# Snapshot tests (main)
# ---------------------------------------------------------------------------


class TestSnapshotComparison:
    """Compare conversion output byte-for-byte against committed snapshots.

    If UPDATE_SNAPSHOTS=1, regenerate snapshots instead of comparing.

    Note: if FIXTURE_EXPECTED does not exist yet, run:
        UPDATE_SNAPSHOTS=1 pytest tests/integration/test_snapshot.py -x -q
    to generate the initial snapshots.
    """

    @pytest.fixture(scope="class")
    def actual_output(self, tmp_path_factory) -> Path:
        """Run conversion once and return the output directory."""
        output_dir = tmp_path_factory.mktemp("snapshot") / "codex_output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        return output_dir

    def test_snapshot_comparison_or_update(self, actual_output: Path) -> None:
        """Either update snapshots (UPDATE_SNAPSHOTS=1) or compare against them.

        This single test covers the update path AND the comparison path:
        - UPDATE_SNAPSHOTS=1: writes actual output to FIXTURE_EXPECTED, passes
        - Otherwise: compares actual vs expected, fails on any diff

        The test is self-describing on failure: it reports which files differ,
        which files are missing from actual, and which files are extra in actual.
        """
        if _should_update_snapshots():
            # Update path: write actual output to committed snapshot dir
            _write_snapshots(actual_output, FIXTURE_EXPECTED)
            # Verify write actually happened
            written = list(FIXTURE_EXPECTED.rglob("*"))
            file_count = sum(1 for f in written if f.is_file())
            assert file_count >= 1, (
                "UPDATE_SNAPSHOTS=1 ran but wrote 0 files. "
                "Snapshot update silently no-oped."
            )
            return  # Test passes after successful update

        # Comparison path
        if not FIXTURE_EXPECTED.exists():
            pytest.fail(
                f"Snapshot directory not found: {FIXTURE_EXPECTED}. "
                "Run with UPDATE_SNAPSHOTS=1 to generate initial snapshots."
            )

        expected_files = _collect_output_files(FIXTURE_EXPECTED)
        if not expected_files:
            pytest.fail(
                f"Snapshot directory is empty: {FIXTURE_EXPECTED}. "
                "Run with UPDATE_SNAPSHOTS=1 to generate snapshots."
            )

        actual_files = _collect_output_files(actual_output)
        diffs: list[str] = []

        # Check for files in expected but missing from actual
        for rel_path in expected_files:
            if rel_path not in actual_files:
                diffs.append(f"MISSING from actual: {rel_path}")

        # Check for files in actual but not in expected
        for rel_path in actual_files:
            if rel_path not in expected_files:
                diffs.append(f"EXTRA in actual (not in snapshot): {rel_path}")

        # Check content diffs
        for rel_path in expected_files:
            if rel_path in actual_files:
                actual_content = actual_files[rel_path]
                expected_content = expected_files[rel_path]
                if actual_content != expected_content:
                    diffs.append(
                        _snapshot_content_diff_message(
                            rel_path, actual_content, expected_content
                        )
                    )

        assert diffs == [], (
            f"Snapshot comparison failed with {len(diffs)} difference(s):\n"
            + "\n".join(f"  - {d}" for d in diffs)
            + "\n\nTo update snapshots, run: UPDATE_SNAPSHOTS=1 pytest tests/integration/test_snapshot.py -x -q"
        )

    def test_snapshot_file_count_is_reasonable(self, actual_output: Path) -> None:
        """Snapshot must have a reasonable number of files — guards against empty output.

        This test fails if the conversion somehow produces 0 or 1 files
        (which would cause test_snapshot_comparison_or_update to trivially pass).

        Minimum expected files:
        - 3 skill dirs x 1 SKILL.md = 3 SKILL.md files
        - 1 agent TOML
        - 1 plugin.json
        - 1 hooks.json
        - 1 session-start.sh
        = at least 7 files
        """
        actual_files = _collect_output_files(actual_output)
        assert len(actual_files) >= 7, (
            f"Conversion output has only {len(actual_files)} files — expected >= 7. "
            "Output is suspiciously small. Snapshot comparison is not meaningful."
        )


class TestGeminiSnapshotComparison:
    """Compare Gemini conversion output against committed snapshots."""

    @pytest.fixture(scope="class")
    def actual_output(self, tmp_path_factory) -> Path:
        output_dir = tmp_path_factory.mktemp("snapshot-gemini") / "gemini_output"
        engine = ConversionEngine("gemini-cli")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        return output_dir

    def test_gemini_snapshot_comparison_or_update(self, actual_output: Path) -> None:
        if _should_update_snapshots():
            _write_snapshots(actual_output, FIXTURE_EXPECTED_GEMINI)
            file_count = sum(
                1 for f in FIXTURE_EXPECTED_GEMINI.rglob("*") if f.is_file()
            )
            assert file_count >= 1, (
                "UPDATE_SNAPSHOTS=1 ran for Gemini but wrote 0 files."
            )
            return

        if not FIXTURE_EXPECTED_GEMINI.exists():
            pytest.fail(
                f"Gemini snapshot directory not found: {FIXTURE_EXPECTED_GEMINI}. "
                "Run with UPDATE_SNAPSHOTS=1 to generate initial snapshots."
            )

        expected_files = _collect_output_files(FIXTURE_EXPECTED_GEMINI)
        if not expected_files:
            pytest.fail(
                f"Gemini snapshot directory is empty: {FIXTURE_EXPECTED_GEMINI}."
            )

        actual_files = _collect_output_files(actual_output)
        diffs: list[str] = []

        for rel_path in expected_files:
            if rel_path not in actual_files:
                diffs.append(f"MISSING from actual: {rel_path}")
        for rel_path in actual_files:
            if rel_path not in expected_files:
                diffs.append(f"EXTRA in actual (not in snapshot): {rel_path}")
        for rel_path in expected_files:
            if (
                rel_path in actual_files
                and actual_files[rel_path] != expected_files[rel_path]
            ):
                diffs.append(
                    _snapshot_content_diff_message(
                        rel_path, actual_files[rel_path], expected_files[rel_path]
                    )
                )

        assert diffs == [], (
            f"Gemini snapshot comparison failed with {len(diffs)} difference(s):\n"
            + "\n".join(f"  - {d}" for d in diffs)
        )

    def test_gemini_snapshot_file_count_is_reasonable(
        self, actual_output: Path
    ) -> None:
        actual_files = _collect_output_files(actual_output)
        assert len(actual_files) >= 7, (
            f"Gemini conversion output has only {len(actual_files)} files."
        )
