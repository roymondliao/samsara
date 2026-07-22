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
