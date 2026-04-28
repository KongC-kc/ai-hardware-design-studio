from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from packages.agent.report_explainer import explain_erc_report, suggest_erc_fixes
from packages.generator.kicad import generate_kicad_artifacts
from packages.tools.kicad_cli import parse_erc_diagnostics, run_export_schematic_svg, run_schematic_erc


@dataclass(frozen=True)
class PipelineStepResult:
    step: str
    success: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class PipelineResult:
    success: bool
    ir_path: str
    project_path: str
    completed_steps: list[str]
    failed_step: str | None
    steps: list[PipelineStepResult]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "ir_path": self.ir_path,
            "project_path": self.project_path,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "steps": [asdict(s) for s in self.steps],
            "errors": self.errors,
            "warnings": self.warnings,
        }


StepFn = Callable[[], Any]

_STEPS: list[tuple[str, Callable[[Path, Path, bool], StepFn]]] = [
    ("generate_kicad_artifacts", lambda ir, proj, ow: lambda: generate_kicad_artifacts(ir, proj, ow)),
    ("export_schematic_svg", lambda _ir, proj, _ow: lambda: run_export_schematic_svg(proj)),
    ("run_erc", lambda _ir, proj, _ow: lambda: run_schematic_erc(proj)),
    ("parse_erc_diagnostics", lambda _ir, proj, _ow: lambda: parse_erc_diagnostics(proj)),
    ("explain_erc_report", lambda _ir, proj, _ow: lambda: explain_erc_report(proj)),
    ("suggest_erc_fixes", lambda _ir, proj, _ow: lambda: suggest_erc_fixes(proj)),
]


def run_pipeline(
    project_path: Path | str,
    ir_path: Path | str | None = None,
    overwrite: bool = False,
) -> PipelineResult:
    """Run the full KiCad artifact generation and ERC analysis pipeline.

    Chains: generate → export SVG → erc → diagnostics → explanation → fix suggestions.
    Stops on first failure. Always writes reports/pipeline_report.json.
    """
    resolved_project = Path(project_path).resolve()
    resolved_ir = Path(ir_path).resolve() if ir_path is not None else resolved_project / "hardware_design_ir.json"

    completed_steps: list[str] = []
    step_results: list[PipelineStepResult] = []
    failed_step: str | None = None
    errors: list[str] = []
    warnings: list[str] = []

    for name, make_fn in _STEPS:
        fn = make_fn(resolved_ir, resolved_project, overwrite)
        try:
            result = fn()
        except Exception as exc:  # noqa: BLE001
            step_results.append(PipelineStepResult(step=name, success=False, details={"exception": str(exc)}))
            failed_step = name
            errors.append(f"Step {name} raised an exception: {exc}")
            break

        step_results.append(
            PipelineStepResult(step=name, success=result.success, details=result.to_dict())
        )
        if result.success:
            completed_steps.append(name)
            if hasattr(result, "warnings") and result.warnings:
                warnings.extend(result.warnings)
        else:
            failed_step = name
            if hasattr(result, "errors") and result.errors:
                errors.extend(result.errors)
            if hasattr(result, "warnings") and result.warnings:
                warnings.extend(result.warnings)
            break

    overall_success = failed_step is None and len(completed_steps) == len(_STEPS)
    pipeline_result = PipelineResult(
        success=overall_success,
        ir_path=str(resolved_ir),
        project_path=str(resolved_project),
        completed_steps=completed_steps,
        failed_step=failed_step,
        steps=step_results,
        errors=errors,
        warnings=warnings,
    )
    _write_pipeline_report(resolved_project, pipeline_result)
    return pipeline_result


def _write_pipeline_report(project_path: Path, result: PipelineResult) -> None:
    reports_dir = project_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "pipeline_report.json"
    report_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
