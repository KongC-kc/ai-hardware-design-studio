from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from packages.tools.kicad_cli.runner import detect_kicad_cli, export_schematic_svg


@dataclass(frozen=True)
class ExportSchematicSvgResult:
    success: bool
    mode: str
    project_path: str
    schematic_path: str | None
    svg_path: str | None
    kicad_cli_found: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_export_schematic_svg(input_path: Path) -> ExportSchematicSvgResult:
    """Export schematic SVG through kicad-cli.

    Accepts a project directory or a .kicad_sch file path.
    Writes to exports/schematic.svg under the project directory.
    """

    project_path, schematic_path, path_errors, warnings = _resolve_schematic_input(input_path)
    svg_path = project_path / "exports" / "schematic.svg" if project_path.is_dir() else None
    status = detect_kicad_cli()

    if path_errors:
        return ExportSchematicSvgResult(
            success=False,
            mode="export_schematic_svg",
            project_path=str(project_path),
            schematic_path=str(schematic_path) if schematic_path is not None else None,
            svg_path=str(svg_path) if svg_path is not None else None,
            kicad_cli_found=status.available,
            errors=path_errors,
            warnings=warnings,
        )

    if not status.available or status.path is None:
        return ExportSchematicSvgResult(
            success=False,
            mode="export_schematic_svg",
            project_path=str(project_path),
            schematic_path=str(schematic_path),
            svg_path=str(svg_path) if svg_path is not None else None,
            kicad_cli_found=False,
            errors=[status.message],
            warnings=warnings,
        )

    if svg_path is None:
        return ExportSchematicSvgResult(
            success=False,
            mode="export_schematic_svg",
            project_path=str(project_path),
            schematic_path=str(schematic_path),
            svg_path=None,
            kicad_cli_found=True,
            errors=[f"Cannot write SVG because project path is not a directory: {project_path}"],
            warnings=warnings,
        )

    svg_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_result = export_schematic_svg(schematic_path, svg_path)

    errors: list[str] = []
    if cmd_result.returncode != 0:
        errors.append(f"kicad-cli SVG export failed with exit code {cmd_result.returncode}.")
    if not svg_path.exists():
        errors.append(f"kicad-cli did not produce {svg_path}.")

    if errors:
        _write_failure_report(project_path, errors, warnings)

    return ExportSchematicSvgResult(
        success=not errors,
        mode="export_schematic_svg",
        project_path=str(project_path),
        schematic_path=str(schematic_path),
        svg_path=str(svg_path) if svg_path.exists() else None,
        kicad_cli_found=True,
        errors=errors,
        warnings=warnings,
    )


def _resolve_schematic_input(
    input_path: Path,
) -> tuple[Path, Path | None, list[str], list[str]]:
    resolved = input_path.expanduser().resolve()
    warnings: list[str] = []

    if resolved.suffix == ".kicad_sch":
        if not resolved.exists():
            return resolved.parent, None, [f"Schematic file not found: {resolved}"], warnings
        if not resolved.is_file():
            return resolved.parent, None, [f"Schematic path is not a file: {resolved}"], warnings
        return resolved.parent, resolved, [], warnings

    project_path = resolved
    if not project_path.exists():
        return project_path, None, [f"Project path not found: {project_path}"], warnings
    if not project_path.is_dir():
        return project_path.parent, None, [f"Input must be a project directory or .kicad_sch file: {resolved}"], warnings

    schematic_files = sorted(project_path.glob("*.kicad_sch"))
    if not schematic_files:
        schematic_files = sorted(project_path.rglob("*.kicad_sch"))
    if not schematic_files:
        return project_path, None, [f"No .kicad_sch file found under project path: {project_path}"], warnings

    if len(schematic_files) > 1:
        warnings.append(f"Multiple .kicad_sch files found; using {schematic_files[0]}.")
    return project_path, schematic_files[0].resolve(), [], warnings


def _write_failure_report(project_path: Path, errors: list[str], warnings: list[str]) -> None:
    reports_dir = project_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "export_schematic_svg_report.json"
    report_path.write_text(
        json.dumps(
            {
                "success": False,
                "mode": "export_schematic_svg",
                "errors": errors,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
