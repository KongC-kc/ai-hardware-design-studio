import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.agent.change_planner import create_change_plan_preview
from packages.agent.confirm_change_plan import confirm_change_plan
from packages.agent.design_request import create_design_plan, parse_design_request


ROOT = Path(__file__).resolve().parents[1]


def build_preview_dict(raw_request: str = "做一个 STM32F103 最小系统板，USB 供电，预留 SWD。") -> dict:
    parsed_request = parse_design_request(raw_request)
    design_plan = create_design_plan(parsed_request)
    preview = create_change_plan_preview(parsed_request, design_plan)
    return preview.to_dict()


class ConfirmChangePlanTest(unittest.TestCase):
    def test_preview_successfully_writes_valid_hardware_design_ir(self) -> None:
        preview = build_preview_dict(
            "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = confirm_change_plan(preview, project_path=Path(temp_dir))
            ir_path = Path(temp_dir) / "hardware_design_ir.json"

            self.assertTrue(result.success)
            self.assertTrue(result.written)
            self.assertEqual(Path(result.ir_path), ir_path)
            self.assertTrue(ir_path.exists())

            ir = json.loads(ir_path.read_text(encoding="utf-8"))
            self.assertEqual(ir["meta"]["name"], "rp2040_control_board")
            self.assertEqual(ir["requirements"]["power_input"], "USB-C")
            self.assertTrue(ir["blocks"])
            self.assertTrue(result.validation["is_valid"])

    def test_validate_failure_returns_error_and_does_not_write_file(self) -> None:
        invalid_preview = build_preview_dict()
        invalid_preview["proposed_modules"] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            result = confirm_change_plan(invalid_preview, project_path=Path(temp_dir))
            ir_path = Path(temp_dir) / "hardware_design_ir.json"

            self.assertFalse(result.success)
            self.assertFalse(result.written)
            self.assertIsNone(result.ir_path)
            self.assertFalse(ir_path.exists())
            self.assertIn("blocks must be a non-empty list", result.validation["errors"])

    def test_without_project_path_writes_under_workspace_project_name(self) -> None:
        preview = build_preview_dict("做一个 ESP32-S3 开发板，Type-C 供电，带屏幕接口、RGB 灯和复位按键。")

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir) / "workspace"
            result = confirm_change_plan(preview, workspace_root=workspace_root)
            ir_path = workspace_root / "esp32_s3_dev_board" / "hardware_design_ir.json"

            self.assertTrue(result.success)
            self.assertEqual(Path(result.ir_path), ir_path)
            self.assertTrue(ir_path.exists())

    def test_confirm_flow_does_not_touch_kicad_files(self) -> None:
        preview = build_preview_dict()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            kicad_files = [
                project_root / "demo.kicad_pro",
                project_root / "demo.kicad_sch",
                project_root / "demo.kicad_pcb",
            ]
            for index, path in enumerate(kicad_files):
                path.write_text(f"original {index}\n", encoding="utf-8")
            before = {path: path.read_text(encoding="utf-8") for path in kicad_files}

            result = confirm_change_plan(preview, project_path=project_root)

            self.assertTrue(result.success)
            for path in kicad_files:
                self.assertEqual(path.read_text(encoding="utf-8"), before[path])

    def test_python_cli_writes_ir_to_project_path(self) -> None:
        preview = build_preview_dict()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            project_root.mkdir()
            preview_path = Path(temp_dir) / "preview.json"
            preview_path.write_text(json.dumps(preview), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "confirm_change_plan.py"),
                    str(preview_path),
                    "--project",
                    str(project_root),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(completed.stdout)
            self.assertTrue(output["success"])
            self.assertTrue((project_root / "hardware_design_ir.json").exists())


if __name__ == "__main__":
    unittest.main()
