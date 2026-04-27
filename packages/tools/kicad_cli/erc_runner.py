from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from packages.tools.kicad_cli.runner import detect_kicad_cli


@dataclass(frozen=True)
class ErcRunResult:
    success: bool
    mode: str
    project_path: str
    schematic_path: str | None
    report_path: str | None
    raw_log_path: str | None
    kicad_cli_found: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_schematic_erc(input_path: Path) -> ErcRunResult:
    """Run KiCad schematic ERC in a controlled, report-only workflow."""

    project_path, schematic_path, path_errors, warnings = _resolve_schematic_input(input_path)
    report_path = project_path / "reports" / "erc_report.json" if project_path.is_dir() else None
    raw_log_path = project_path / "reports" / "erc_raw.log" if project_path.is_dir() else None
    status = detect_kicad_cli()

    if path_errors:
        _write_failure_report(report_path, raw_log_path, path_errors, warnings)
        return ErcRunResult(
            success=False,
            mode="run_erc",
            project_path=str(project_path),
            schematic_path=str(schematic_path) if schematic_path is not None else None,
            report_path=str(report_path) if report_path is not None else None,
            raw_log_path=str(raw_log_path) if raw_log_path is not None else None,
            kicad_cli_found=status.available,
            errors=path_errors,
            warnings=warnings,
        )

    if not status.available or status.path is None:
        errors = [status.message]
        _write_failure_report(report_path, raw_log_path, errors, warnings)
        return ErcRunResult(
            success=False,
            mode="run_erc",
            project_path=str(project_path),
            schematic_path=str(schematic_path),
            report_path=str(report_path) if report_path is not None else None,
            raw_log_path=str(raw_log_path) if raw_log_path is not None else None,
            kicad_cli_found=False,
            errors=errors,
            warnings=warnings,
        )

    if report_path is None or raw_log_path is None:
        errors = [f"Cannot write ERC reports because project path is not a directory: {project_path}"]
        return ErcRunResult(
            success=False,
            mode="run_erc",
            project_path=str(project_path),
            schematic_path=str(schematic_path),
            report_path=None,
            raw_log_path=None,
            kicad_cli_found=True,
            errors=errors,
            warnings=warnings,
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        status.path,
        "sch",
        "erc",
        "--format",
        "json",
        "--output",
        str(report_path),
        str(schematic_path),
    ]
    completed = subprocess.run(
        command,
        cwd=project_path,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _write_raw_log(raw_log_path, completed.stdout, completed.stderr)

    errors: list[str] = []
    if completed.returncode != 0:
        errors.append(f"kicad-cli ERC failed with exit code {completed.returncode}.")
    if not report_path.exists():
        errors.append("kicad-cli did not produce reports/erc_report.json.")
        _write_report_json(report_path, success=False, errors=errors, warnings=warnings)

    return ErcRunResult(
        success=not errors,
        mode="run_erc",
        project_path=str(project_path),
        schematic_path=str(schematic_path),
        report_path=str(report_path),
        raw_log_path=str(raw_log_path),
        kicad_cli_found=True,
        errors=errors,
        warnings=warnings,
    )


def _resolve_schematic_input(input_path: Path) -> tuple[Path, Path | None, list[str], list[str]]:
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


def _write_failure_report(
    report_path: Path | None,
    raw_log_path: Path | None,
    errors: list[str],
    warnings: list[str],
) -> None:
    if report_path is None or raw_log_path is None:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _write_report_json(report_path, success=False, errors=errors, warnings=warnings)
    _write_raw_log(raw_log_path, "", "\n".join(errors))


def _write_report_json(report_path: Path, success: bool, errors: list[str], warnings: list[str]) -> None:
    report_path.write_text(
        json.dumps(
            {
                "success": success,
                "mode": "run_erc",
                "errors": errors,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_raw_log(raw_log_path: Path, stdout: str, stderr: str) -> None:
    raw_log_path.parent.mkdir(parents=True, exist_ok=True)
    raw_log_path.write_text(
        "\n".join(
            [
                "[stdout]",
                stdout.rstrip(),
                "",
                "[stderr]",
                stderr.rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
