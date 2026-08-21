"""Contract tests for local-only CLI smoke markers."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CODEX_SMOKE = REPO_ROOT / "tests" / "integration" / "test_smoke_codex.py"


class TestLocalCliMarkers:
    def test_codex_structural_smoke_is_not_marked_local_only(self):
        content = CODEX_SMOKE.read_text(encoding="utf-8")

        assert "@pytest.mark.requires_codex" not in content
