"""
samsara-cli — Multi-platform agent conversion CLI.

Entry point: samsara-cli = "samsara_cli.main:app"

Commands:
- version: Show samsara-cli version
- list-platforms: List available target platforms
- convert: Convert samsara source to a target platform format
- install: Install converted output to project or global scope
- update: Re-convert + re-install (idempotent)
- validate: Validate converted output for a platform

Design assumptions:
- Typer manages CLI argument parsing. Rich is used for formatted output.
- ConversionEngine handles all conversion logic (source validation is inside the engine).
- Installer handles CLI detection and file placement.
- CLI exits non-zero on any error — callers/CI tools can detect failure.
- Imports of ConversionEngine and TargetValidator are at module level for testability
  (tests can patch 'samsara_cli.main.ConversionEngine').

Source discovery convention:
- --source defaults to CWD
- A valid samsara source directory contains .claude-plugin/plugin.json
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from samsara_cli.converter.engine import ConversionEngine, EngineError
from samsara_cli.installer.detect import PlatformDetector
from samsara_cli.installer.install import Installer, InstallerError
from samsara_cli.validators.target import TargetValidator

app = typer.Typer(
    name="samsara-cli",
    help="Convert samsara Claude Code plugins to other platform formats.",
    no_args_is_help=True,
)

console = Console()
error_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exit_with_error(message: str, exit_code: int = 1) -> None:
    """Print error message and exit with given code."""
    error_console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(code=exit_code)


def _validate_platform(platform: str) -> None:
    """Validate platform name. Exits with error if invalid."""
    detector = PlatformDetector()
    available = detector.available_platforms()
    if platform not in available:
        _exit_with_error(
            f"Unknown platform: {platform!r}\n"
            f"Available platforms: {', '.join(available) or 'none'}\n"
            "Use 'samsara-cli list-platforms' to see all available platforms."
        )


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show samsara-cli version."""
    from importlib.metadata import version as pkg_version

    try:
        ver = pkg_version("samsara")
    except Exception:
        ver = "unknown"
    typer.echo(f"samsara-cli {ver}")


# ---------------------------------------------------------------------------
# list-platforms
# ---------------------------------------------------------------------------


@app.command(name="list-platforms")
def list_platforms() -> None:
    """List available target platforms for conversion."""
    detector = PlatformDetector()
    platforms = detector.available_platforms()
    if not platforms:
        console.print("[yellow]No target platforms found.[/yellow]")
        return

    console.print("[bold]Available platforms:[/bold]")
    for platform in platforms:
        console.print(f"  • {platform}")


# ---------------------------------------------------------------------------
# convert
# ---------------------------------------------------------------------------


@app.command()
def convert(
    platform: Annotated[
        str,
        typer.Option("--platform", "-p", help="Target platform (e.g., codex)"),
    ],
    source: Annotated[
        Optional[Path],
        typer.Option(
            "--source",
            "-s",
            help="Source samsara directory (default: current working directory)",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output directory for converted files (default: ./dist/{platform}/)",
        ),
    ] = None,
) -> None:
    """Convert samsara source to a target platform format.

    Validates source structure first. Fails at source validation if the source
    is not a valid samsara directory (DC-8-6).
    """
    # Validate platform first — DC-8-5: list available platforms in error
    _validate_platform(platform)

    source_dir = source or Path.cwd()
    output_dir = output or (Path.cwd() / "dist" / platform)

    if not source_dir.exists():
        _exit_with_error(
            f"Source directory does not exist: {source_dir}\n"
            "Pass a valid --source path or run from the samsara root directory."
        )

    console.print(f"Converting [bold]{platform}[/bold] from: {source_dir}")
    console.print(f"Output to: {output_dir}")

    try:
        engine = ConversionEngine(platform=platform)
        engine.run(source_dir=source_dir, output_dir=output_dir)
    except EngineError as e:
        _exit_with_error(str(e))
    except FileNotFoundError as e:
        _exit_with_error(str(e))
    except Exception as e:
        _exit_with_error(f"Unexpected error during conversion: {e}")

    console.print(f"[green]Conversion complete:[/green] {output_dir}")


# ---------------------------------------------------------------------------
# install
# ---------------------------------------------------------------------------


@app.command()
def install(
    platform: Annotated[str, typer.Argument(help="Target platform (e.g., codex)")],
    scope: Annotated[
        str,
        typer.Option("--scope", help="Install scope: 'project' or 'global'"),
    ] = "project",
    source: Annotated[
        Optional[Path],
        typer.Option(
            "--source",
            "-s",
            help="Source samsara directory (default: current working directory)",
        ),
    ] = None,
    converted_source: Annotated[
        Optional[Path],
        typer.Option(
            "--converted-source",
            help="Pre-converted output directory (skips conversion step)",
        ),
    ] = None,
) -> None:
    """Install samsara files for a target platform.

    Project scope (default): copies native platform files to CWD.
    Global scope: copies native platform files under HOME and updates config.toml.

    Aborts if the platform CLI is not installed (DC-8-1).
    Project scope never modifies global config (DC-8-2).
    Global scope backs up config before modification (DC-8-3).
    Global scope install is idempotent (DC-8-4).
    """
    # Validate platform — DC-8-5
    _validate_platform(platform)

    if scope not in ("project", "global"):
        _exit_with_error(
            f"Invalid scope: {scope!r}. Valid scopes are: 'project', 'global'."
        )

    source_dir = source or Path.cwd()

    console.print(
        f"Installing [bold]{platform}[/bold] files (scope: [bold]{scope}[/bold])"
    )

    try:
        installer = Installer(platform=platform)
        instructions = installer.install(
            source_dir=source_dir,
            scope=scope,  # type: ignore[arg-type]
            cwd=Path.cwd(),
            converted_source_dir=converted_source,
        )
    except InstallerError as e:
        _exit_with_error(str(e))
    except Exception as e:
        _exit_with_error(f"Unexpected error during installation: {e}")

    console.print(
        Panel(instructions, title="[green]Installation complete[/green]", expand=False)
    )


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


@app.command()
def update(
    platform: Annotated[str, typer.Argument(help="Target platform (e.g., codex)")],
    scope: Annotated[
        str,
        typer.Option("--scope", help="Install scope: 'project' or 'global'"),
    ] = "project",
    source: Annotated[
        Optional[Path],
        typer.Option(
            "--source",
            "-s",
            help="Source samsara directory (default: current working directory)",
        ),
    ] = None,
) -> None:
    """Update the samsara plugin installation (re-convert + re-install).

    Idempotent: running update multiple times produces the same result.
    Scope must match the original install scope.
    """
    # Validate platform — DC-8-5
    _validate_platform(platform)

    if scope not in ("project", "global"):
        _exit_with_error(
            f"Invalid scope: {scope!r}. Valid scopes are: 'project', 'global'."
        )

    source_dir = source or Path.cwd()

    console.print(
        f"Updating [bold]{platform}[/bold] plugin (scope: [bold]{scope}[/bold])"
    )

    try:
        installer = Installer(platform=platform)
        instructions = installer.update(
            source_dir=source_dir,
            scope=scope,  # type: ignore[arg-type]
            cwd=Path.cwd(),
        )
    except InstallerError as e:
        _exit_with_error(str(e))
    except Exception as e:
        _exit_with_error(f"Unexpected error during update: {e}")

    console.print(
        Panel(instructions, title="[green]Update complete[/green]", expand=False)
    )


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@app.command()
def validate(
    platform: Annotated[
        str,
        typer.Option("--platform", "-p", help="Target platform (e.g., codex)"),
    ],
    source: Annotated[
        Optional[Path],
        typer.Option(
            "--source",
            "-s",
            help="Converted output directory to validate",
        ),
    ] = None,
) -> None:
    """Validate converted output for a target platform.

    Checks: source patterns removed, TOML valid, agent cross-references intact.
    """
    # Validate platform — DC-8-5
    _validate_platform(platform)

    source_dir = source or Path.cwd()

    if not source_dir.exists():
        _exit_with_error(f"Source directory does not exist: {source_dir}")

    console.print(f"Validating [bold]{platform}[/bold] output in: {source_dir}")

    validator = TargetValidator()
    errors = validator.validate(output_dir=source_dir)

    if errors:
        error_console.print(
            f"[red]Validation failed:[/red] {len(errors)} error(s) found\n"
        )
        for i, error in enumerate(errors, 1):
            error_console.print(f"  {i}. {error}")
        raise typer.Exit(code=1)

    console.print("[green]Validation passed[/green] — no errors found.")


if __name__ == "__main__":
    app()
