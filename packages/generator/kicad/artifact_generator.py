from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from packages.core.validators.validate_ir import load_ir, validate_ir
from packages.generator.schematic.schematic_builder import write_schematic


@dataclass(frozen=True)
class GenerateKicadArtifactsResult:
    success: bool
    mode: str
    ir_path: str
    project_path: str
    planned_files: list[str]
    written_files: list[str]
    validation: dict[str, Any]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_kicad_artifacts(
    ir_path: Path | str,
    project_path: Path | str,
    overwrite: bool = False,
) -> GenerateKicadArtifactsResult:
    """Generate minimal deterministic KiCad artifacts from a validated IR file."""

    resolved_ir_path = Path(ir_path).resolve()
    resolved_project_path = Path(project_path).resolve()

    try:
        ir = load_ir(resolved_ir_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _failure(
            ir_path=resolved_ir_path,
            project_path=resolved_project_path,
            planned_files=[],
            validation={"is_valid": False, "errors": [str(exc)], "warnings": []},
            errors=[str(exc)],
        )

    validation = validate_ir(ir)
    validation_payload = _validation_to_dict(validation)
    if not validation.is_valid:
        return _failure(
            ir_path=resolved_ir_path,
            project_path=resolved_project_path,
            planned_files=[],
            validation=validation_payload,
            errors=validation.errors,
        )

    planned_paths = _planned_paths(ir, resolved_project_path)
    planned_files = [str(path) for path in planned_paths]
    existing_paths = [path for path in planned_paths if path.exists()]
    if existing_paths and not overwrite:
        return _failure(
            ir_path=resolved_ir_path,
            project_path=resolved_project_path,
            planned_files=planned_files,
            validation=validation_payload,
            errors=[
                "Target file already exists; pass --overwrite to replace it: "
                f"{existing_path}"
                for existing_path in existing_paths
            ],
        )

    written_files = _write_artifacts(
        ir=ir,
        ir_path=resolved_ir_path,
        project_path=resolved_project_path,
        planned_paths=planned_paths,
        validation=validation_payload,
    )

    return GenerateKicadArtifactsResult(
        success=True,
        mode="generate_kicad_artifacts",
        ir_path=str(resolved_ir_path),
        project_path=str(resolved_project_path),
        planned_files=planned_files,
        written_files=written_files,
        validation=validation_payload,
        errors=[],
    )


def _planned_paths(ir: Mapping[str, Any], project_path: Path) -> list[Path]:
    project_name = str(ir["meta"]["name"])
    return [
        project_path / f"{project_name}.kicad_pro",
        project_path / f"{project_name}.kicad_sch",
        project_path / "reports" / "generation_report.json",
    ]


def _write_artifacts(
    ir: Mapping[str, Any],
    ir_path: Path,
    project_path: Path,
    planned_paths: list[Path],
    validation: dict[str, Any],
) -> list[str]:
    project_path.mkdir(parents=True, exist_ok=True)
    reports_dir = project_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    project_file, schematic_file, report_file = planned_paths
    _write_project_file(ir, project_file)
    write_schematic(ir, schematic_file)
    written_files = [str(project_file), str(schematic_file), str(report_file)]
    _write_generation_report(
        ir=ir,
        ir_path=ir_path,
        report_path=report_file,
        planned_files=[str(path) for path in planned_paths],
        written_files=written_files,
        validation=validation,
    )
    return written_files


def _write_project_file(ir: Mapping[str, Any], output_path: Path) -> None:
    project_data = {
        "meta": ir.get("meta", {}),
        "generator": {
            "name": "ai-hardware-design-studio",
            "mode": "generate_kicad_artifacts",
            "deterministic": True,
            "note": "Generated from hardware_design_ir.json. Do not edit by hand.",
        },
        "artifacts": {
            "schematic": f"{ir['meta']['name']}.kicad_sch",
            "pcb": None,
        },
    }
    output_path.write_text(
        json.dumps(project_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_generation_report(
    ir: Mapping[str, Any],
    ir_path: Path,
    report_path: Path,
    planned_files: list[str],
    written_files: list[str],
    validation: dict[str, Any],
) -> None:
    report = {
        "success": True,
        "mode": "generate_kicad_artifacts",
        "project_name": ir["meta"]["name"],
        "ir_path": str(ir_path),
        "planned_files": planned_files,
        "written_files": written_files,
        "validation": validation,
        "generated_pcb": False,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _failure(
    ir_path: Path,
    project_path: Path,
    planned_files: list[str],
    validation: dict[str, Any],
    errors: list[str],
) -> GenerateKicadArtifactsResult:
    return GenerateKicadArtifactsResult(
        success=False,
        mode="generate_kicad_artifacts",
        ir_path=str(ir_path),
        project_path=str(project_path),
        planned_files=planned_files,
        written_files=[],
        validation=validation,
        errors=errors,
    )


def _validation_to_dict(validation: Any) -> dict[str, Any]:
    return {
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }
