"""Documentation contract tests for release version sync instructions."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README_EN = REPO_ROOT / "README.md"
README_ZH = REPO_ROOT / "README.zh-TW.md"


class TestReadmeReleaseDocs:
    def test_readmes_include_release_sync_commands(self):
        readme_en = README_EN.read_text(encoding="utf-8")
        readme_zh = README_ZH.read_text(encoding="utf-8")

        assert "samsara-cli release sync-version" in readme_en
        assert "samsara-cli release check-version" in readme_en
        assert "samsara-cli release sync-version" in readme_zh
        assert "samsara-cli release check-version" in readme_zh

    def test_readmes_describe_marketplace_as_source_of_truth(self):
        readme_en = README_EN.read_text(encoding="utf-8")
        readme_zh = README_ZH.read_text(encoding="utf-8")

        assert "marketplace.json" in readme_en
        assert "source of truth" in readme_en
        assert "marketplace.json" in readme_zh
        assert "source of truth" in readme_zh or "唯一版本來源" in readme_zh
