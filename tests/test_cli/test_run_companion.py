from pathlib import Path

from typer.testing import CliRunner

from samsara_cli.main import app


def test_run_companion_uses_samsara_runtime_and_forwards_arguments(
    tmp_path: Path,
) -> None:
    script = tmp_path / "companion.py"
    script.write_text(
        "import sys\nimport yaml\nprint(yaml.safe_dump({'args': sys.argv[1:]}).strip())\n"
    )

    result = CliRunner().invoke(
        app,
        ["run-companion", str(script), "--", "one", "two"],
    )

    assert result.exit_code == 0, result.output
    assert "one" in result.output
    assert "two" in result.output


def test_check_companion_loads_dependencies_without_entering_main(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "main-ran"
    script = tmp_path / "companion.py"
    script.write_text(
        "import yaml\n"
        "if __name__ == '__main__':\n"
        f"    open({str(marker)!r}, 'w').write('ran')\n"
    )

    result = CliRunner().invoke(app, ["check-companion", str(script)])

    assert result.exit_code == 0, result.output
    assert "COMPANION READY" in result.output
    assert not marker.exists()
