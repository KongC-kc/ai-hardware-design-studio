from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KicadCliStatus:
    available: bool
    path: str | None
    message: str


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class KicadCliUnavailable(RuntimeError):
    """Raised when kicad-cli is required but not installed."""


def detect_kicad_cli() -> KicadCliStatus:
    """Detect whether kicad-cli is available on PATH."""

    path = shutil.which("kicad-cli")
    if path is None:
        return KicadCliStatus(
            available=False,
            path=None,
            message="kicad-cli was not found on PATH. Install KiCad or run the mock pipeline.",
        )
    return KicadCliStatus(available=True, path=path, message=f"kicad-cli found at {path}")


def run_kicad_cli(args: list[str], cwd: Path | None = None) -> CommandResult:
    """Run kicad-cli with the provided arguments."""

    status = detect_kicad_cli()
    if not status.available or status.path is None:
        raise KicadCliUnavailable(status.message)

    command = [status.path, *args]
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_erc(schematic_path: Path, report_path: Path) -> CommandResult:
    """Run ERC for a schematic file.

    TODO: Confirm KiCad CLI flags for the exact KiCad version used by the user.
    """

    return run_kicad_cli(
        ["sch", "erc", "--format", "json", "--output", str(report_path), str(schematic_path)],
        cwd=schematic_path.parent,
    )


def export_schematic_svg(schematic_path: Path, output_path: Path) -> CommandResult:
    """Export a schematic SVG through kicad-cli."""

    return run_kicad_cli(
        ["sch", "export", "svg", "--output", str(output_path), str(schematic_path)],
        cwd=schematic_path.parent,
    )


def export_schematic_pdf(schematic_path: Path, output_path: Path) -> CommandResult:
    """Export a schematic PDF through kicad-cli."""

    return run_kicad_cli(
        ["sch", "export", "pdf", "--output", str(output_path), str(schematic_path)],
        cwd=schematic_path.parent,
    )


def export_netlist(schematic_path: Path, output_path: Path) -> CommandResult:
    """Export a schematic netlist through kicad-cli."""

    return run_kicad_cli(
        ["sch", "export", "netlist", "--output", str(output_path), str(schematic_path)],
        cwd=schematic_path.parent,
    )
