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

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from samsara_cli.converter.engine import ConversionEngine, EngineError
from samsara_cli.installer.detect import PlatformDetector
from samsara_cli.installer.install import Installer, InstallerError
from samsara_cli.release.version_metadata import (
    PartialSyncError,
    SyncResult,
    VersionDriftError,
    VersionMetadata,
    VersionMetadataError,
)
from samsara_cli.validators.target import TargetValidator

app = typer.Typer(
    name="samsara-cli",
    help="Convert samsara Claude Code plugins to other platform formats.",
    no_args_is_help=True,
)
release_app = typer.Typer(
    help="Inspect and synchronize release version metadata.",
    no_args_is_help=True,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exit_with_error(message: str, exit_code: int = 1) -> None:
    """Print error message and exit with given code."""
    typer.echo(f"Error: {message}", err=True)
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


def _format_sync_result(result: SyncResult) -> str:
    changed = ", ".join(path.name for path in result.changed_paths) or "none"
    mode = "check-only" if result.check_only else "written"
    return (
        f"marketplace version: {result.version}\n"
        f"release tag: {result.tag}\n"
        f"changed files ({mode}): {changed}"
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


@release_app.command("check-version")
def release_check_version(
    root: Annotated[
        Path,
        typer.Option("--root", help="Repository root containing version metadata"),
    ] = Path.cwd(),
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit machine-readable JSON"),
    ] = False,
) -> None:
    """Check whether marketplace, plugin, and pyproject versions are synchronized."""
    try:
        metadata = VersionMetadata.load(root)
    except VersionDriftError as exc:
        mismatch_lines = [
            {
                "path": str(mismatch.path),
                "field": mismatch.field,
                "expected": mismatch.expected,
                "actual": mismatch.actual,
            }
            for mismatch in exc.mismatches
        ]
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "status": "failure",
                        "error": "version_drift",
                        "mismatches": mismatch_lines,
                    }
                )
            )
            raise typer.Exit(code=1)
        detail = "\n".join(
            f"  - {item['path']} ({item['field']}): expected {item['expected']}, got {item['actual']}"
            for item in mismatch_lines
        )
        _exit_with_error(f"Version drift detected:\n{detail}")
    except VersionMetadataError as exc:
        if json_output:
            typer.echo(json.dumps({"status": "failure", "error": str(exc)}))
            raise typer.Exit(code=1)
        _exit_with_error(str(exc))

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "status": "success",
                    "version": metadata.marketplace_version,
                    "tag": metadata.tag,
                    "is_synced": metadata.is_synced,
                }
            )
        )
        return

    typer.echo(
        f"Versions synchronized: {metadata.marketplace_version} ({metadata.tag})"
    )


@release_app.command("sync-version")
def release_sync_version(
    root: Annotated[
        Path,
        typer.Option("--root", help="Repository root containing version metadata"),
    ] = Path.cwd(),
    check_only: Annotated[
        bool,
        typer.Option("--check", help="Report required changes without writing files"),
    ] = False,
) -> None:
    """Synchronize plugin and pyproject versions to marketplace metadata.version."""
    try:
        result = VersionMetadata.sync_from_marketplace(root, check_only=check_only)
    except PartialSyncError as exc:
        _exit_with_error(str(exc))
    except VersionMetadataError as exc:
        _exit_with_error(str(exc))

    typer.echo(_format_sync_result(result))


@release_app.command("print-tag")
def release_print_tag(
    root: Annotated[
        Path,
        typer.Option("--root", help="Repository root containing version metadata"),
    ] = Path.cwd(),
) -> None:
    """Print the release tag derived from marketplace metadata.version."""
    try:
        metadata = VersionMetadata.load(root)
    except VersionMetadataError as exc:
        _exit_with_error(str(exc))

    typer.echo(metadata.tag)


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
    errors = validator.validate(output_dir=source_dir, platform=platform)

    if errors:
        typer.echo(f"Validation failed: {len(errors)} error(s) found\n", err=True)
        for i, error in enumerate(errors, 1):
            typer.echo(f"  {i}. {error}", err=True)
        raise typer.Exit(code=1)

    console.print("[green]Validation passed[/green] — no errors found.")


app.add_typer(release_app, name="release")


if __name__ == "__main__":
    app()
