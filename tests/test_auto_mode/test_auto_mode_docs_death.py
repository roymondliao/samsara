from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README_EN = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"
OVERVIEW = ROOT / "changes" / "2026-05-27_samsara-auto-mode" / "overview.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    assert marker in text, f"Missing required section: {marker}"
    tail = text.split(marker, 1)[1]
    return tail.split("\n## ", 1)[0]


class TestReadmeAutoModeContractDeath:
    def test_english_readme_documents_session_auto_mode_without_config_support(self):
        auto_section = section(read(README_EN), "Auto Mode")

        required = (
            "human-in-the-loop",
            "`auto`",
            "before `samsara:research`",
            "samsara:auto-gatekeeper",
            "research -> pre-thinking -> planning -> implement -> iteration -> security-privacy-review -> validate-and-ship",
            "changes/<feature>/auto-decisions.md",
            "append-only",
            "`samsara_config.yaml` is not supported",
        )
        missing = [term for term in required if term not in auto_section]
        assert not missing, (
            "SILENT FAILURE [AUTO-DOCS-1]: README can describe auto mode "
            f"without the first-cut session contract. Missing: {missing}"
        )

    def test_traditional_chinese_readme_documents_session_auto_mode_without_config_support(
        self,
    ):
        auto_section = section(read(README_ZH), "Auto Mode")

        required = (
            "human-in-the-loop",
            "`auto`",
            "`samsara:research` 之前",
            "samsara:auto-gatekeeper",
            "research -> pre-thinking -> planning -> implement -> iteration -> security-privacy-review -> validate-and-ship",
            "changes/<feature>/auto-decisions.md",
            "append-only",
            "不支援 `samsara_config.yaml`",
        )
        missing = [term for term in required if term not in auto_section]
        assert not missing, (
            "SILENT FAILURE [AUTO-DOCS-2]: Chinese README can describe auto mode "
            f"without the first-cut session contract. Missing: {missing}"
        )

    def test_readmes_do_not_claim_persistent_config_or_human_fallback(self):
        prohibited = (
            "supports `samsara_config.yaml`",
            "reads `samsara_config.yaml`",
            "configured in `samsara_config.yaml`",
            "fall back to human-in-the-loop",
            "fallback to human-in-the-loop",
            "switch back to human-in-the-loop",
            "可以用 `samsara_config.yaml`",
            "讀取 `samsara_config.yaml`",
            "切回 human-in-the-loop",
            "回退到 human-in-the-loop",
        )

        for path in (README_EN, README_ZH):
            text = read(path)
            found = [term for term in prohibited if term in text]
            assert not found, (
                "SILENT FAILURE [AUTO-DOCS-3]: README claims unsupported "
                f"auto-mode behavior in {path.name}: {found}"
            )


class TestAutoModeOverviewValidationDeath:
    def test_overview_lists_primary_evaluator_and_converter_validation_surface(self):
        text = read(OVERVIEW)

        required = (
            "primary evaluator",
            "tests/test_auto_mode",
            "tests/test_converter/test_agent.py",
            "tests/test_converter/test_agent_death.py",
            "tests/integration/test_pipeline.py",
            "tests/integration/test_format_validation.py",
        )
        missing = [term for term in required if term not in text]
        assert not missing, (
            "SILENT FAILURE [AUTO-DOCS-4]: final validation can skip the "
            f"primary evaluator or converter coverage. Missing: {missing}"
        )
