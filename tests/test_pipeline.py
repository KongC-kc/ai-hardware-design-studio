"""Tests for the pipeline orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.pipeline.orchestrator import PipelineResult, run_pipeline
from packages.tools.kicad_cli.runner import detect_kicad_cli

EXAMPLE_IR = Path("examples/usb_i2s_fpga/hardware_design_ir.json")
EXAMPLE_PROJECT = EXAMPLE_IR.parent
IR_META_NAME = "usb_i2s_fpga"

KICAD_CLI_AVAILABLE = detect_kicad_cli().available


@pytest.fixture()
def output_project(tmp_path: Path) -> Path:
    project = tmp_path / "test_project"
    project.mkdir()
    ir_dest = project / "hardware_design_ir.json"
    ir_dest.write_text(EXAMPLE_IR.read_text(encoding="utf-8"), encoding="utf-8")
    return project


class TestRunPipeline:
    def test_writes_pipeline_report(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)

        report_path = output_project / "reports" / "pipeline_report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["ir_path"] == str((output_project / "hardware_design_ir.json").resolve())
        assert report["project_path"] == str(output_project.resolve())

    @pytest.mark.skipif(not KICAD_CLI_AVAILABLE, reason="kicad-cli not on PATH")
    def test_completes_all_steps_when_successful(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)

        assert isinstance(result, PipelineResult)
        assert result.success
        assert len(result.steps) == 6
        step_names = [s.step for s in result.steps]
        assert step_names == [
            "generate_kicad_artifacts",
            "export_schematic_svg",
            "run_erc",
            "parse_erc_diagnostics",
            "explain_erc_report",
            "suggest_erc_fixes",
        ]

    def test_generate_step_produces_kicad_files(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)

        gen_step = result.steps[0]
        assert gen_step.step == "generate_kicad_artifacts"
        assert gen_step.success
        assert (output_project / f"{IR_META_NAME}.kicad_pro").exists()
        assert (output_project / f"{IR_META_NAME}.kicad_sch").exists()

    def test_writes_pipeline_report_on_failure(self, tmp_path: Path) -> None:
        empty_project = tmp_path / "empty"
        empty_project.mkdir()

        result = run_pipeline(empty_project)
        report_path = empty_project / "reports" / "pipeline_report.json"
        assert report_path.exists()

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["success"] is False
        assert report["failed_step"] == "generate_kicad_artifacts"
        assert len(report["errors"]) > 0

    def test_stops_on_first_failure(self, tmp_path: Path) -> None:
        empty_project = tmp_path / "empty"
        empty_project.mkdir()

        result = run_pipeline(empty_project)
        assert not result.success
        assert result.failed_step == "generate_kicad_artifacts"
        assert len(result.completed_steps) == 0

    def test_uses_explicit_ir_path(self, output_project: Path, tmp_path: Path) -> None:
        ir_copy = tmp_path / "custom_ir.json"
        ir_copy.write_text(EXAMPLE_IR.read_text(encoding="utf-8"), encoding="utf-8")

        result = run_pipeline(output_project, ir_path=ir_copy, overwrite=True)
        assert result.steps[0].success
        assert result.ir_path == str(ir_copy.resolve())

    def test_step_details_contain_expected_keys(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)
        gen_details = result.steps[0].details
        assert "success" in gen_details
        assert "mode" in gen_details
        assert "written_files" in gen_details

    def test_default_ir_path_is_project_hardware_design_ir(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)
        assert "hardware_design_ir.json" in result.ir_path

    def test_stops_on_export_svg_failure_without_kicad_cli(self, output_project: Path) -> None:
        if KICAD_CLI_AVAILABLE:
            pytest.skip("This test verifies graceful degradation when kicad-cli is absent.")

        result = run_pipeline(output_project, overwrite=True)
        assert not result.success
        assert result.failed_step == "export_schematic_svg"
        assert result.completed_steps == ["generate_kicad_artifacts"]
        report_path = output_project / "reports" / "pipeline_report.json"
        assert report_path.exists()


class TestPipelineResult:
    def test_to_dict_roundtrip(self, output_project: Path) -> None:
        result = run_pipeline(output_project, overwrite=True)
        d = result.to_dict()
        assert isinstance(d["steps"], list)
        assert len(d["steps"]) >= 1
        for step_dict in d["steps"]:
            assert "step" in step_dict
            assert "success" in step_dict
            assert "details" in step_dict
