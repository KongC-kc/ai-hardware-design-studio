import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.agent.change_planner import create_change_plan_preview
from packages.agent.design_request import create_design_plan, parse_design_request
from packages.tools.project_inspector import inspect_project


ROOT = Path(__file__).resolve().parents[1]


def make_preview(raw_request: str, project_summary: object | None = None) -> object:
    parsed_request = parse_design_request(raw_request)
    design_plan = create_design_plan(parsed_request, project_summary)
    return create_change_plan_preview(parsed_request, design_plan, project_summary)


class ChangePlannerTest(unittest.TestCase):
    def test_rp2040_usb_c_buttons_rgb_swd_preview(self) -> None:
        preview = make_preview(
            "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"
        )

        self.assertEqual(preview.ir_version, "preview.v1")
        self.assertEqual(preview.mode, "preview_only")
        self.assertEqual(preview.target, "RP2040 控制板")
        self.assertEqual(preview.next_action, "confirm_change_plan_before_ir_write")
        self.assertIn("rp2040_core", [module["id"] for module in preview.proposed_modules])
        self.assertIn("swd_header", [module["id"] for module in preview.proposed_modules])
        self.assertIn("BUTTON_INPUTS", [net["name"] for net in preview.proposed_nets])
        self.assertIn("RGB_DATA", [net["name"] for net in preview.proposed_nets])
        self.assertIn(
            "Confirm whether buttons are direct GPIO inputs or a matrix.",
            preview.confirmation_items,
        )
        self.assertIn(
            "Confirm whether RGB is WS2812/SK6812-style addressable LEDs or discrete RGB.",
            preview.confirmation_items,
        )
        self.assertIn(
            "Confirm whether USB-C is power-only or USB2.0 device.",
            preview.confirmation_items,
        )

    def test_esp32s3_type_c_display_reset_preview(self) -> None:
        preview = make_preview("做一个 ESP32-S3 开发板，Type-C 供电，带屏幕接口、RGB 灯和复位按键。")

        module_ids = [module["id"] for module in preview.proposed_modules]
        net_names = [net["name"] for net in preview.proposed_nets]

        self.assertEqual(preview.target, "ESP32-S3 开发板")
        self.assertIn("esp32_s3_core", module_ids)
        self.assertIn("display_connector", module_ids)
        self.assertIn("reset_button", module_ids)
        self.assertIn("DISPLAY_IO", net_names)
        self.assertIn("RESET_N", net_names)
        self.assertIn("Confirm display connector type and bus.", preview.confirmation_items)
        self.assertIn(
            "ESP32-S3 RF layout and antenna keepout can drive PCB constraints.",
            preview.risks,
        )

    def test_stm32f103_usb_swd_preview(self) -> None:
        preview = make_preview("做一个 STM32F103 最小系统板，USB 供电，预留 SWD。")

        module_ids = [module["id"] for module in preview.proposed_modules]
        net_names = [net["name"] for net in preview.proposed_nets]

        self.assertEqual(preview.target, "STM32F103 最小系统板")
        self.assertIn("stm32f103_core", module_ids)
        self.assertIn("stm32_boot_clock", module_ids)
        self.assertIn("swd_header", module_ids)
        self.assertIn("SWDIO", net_names)
        self.assertIn("SWCLK", net_names)
        self.assertIn(
            "Confirm exact STM32F103 package and flash/RAM size.",
            preview.confirmation_items,
        )

    def test_empty_project_inspection_still_outputs_preview_with_risks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_summary = inspect_project(Path(temp_dir))

            preview = make_preview(
                "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。",
                project_summary,
            )

            self.assertEqual(preview.mode, "preview_only")
            self.assertIn(
                "Project warning: No .kicad_pro file found in project root.",
                preview.risks,
            )
            self.assertIn("Project warning: No .kicad_sch files found.", preview.risks)
            self.assertIn("Project warning: No .kicad_pcb files found.", preview.risks)

    def test_preview_without_project_inspection_is_allowed(self) -> None:
        preview = make_preview("做一个 ESP32-S3 开发板，Type-C 供电，带屏幕接口、RGB 灯和复位按键。")

        self.assertEqual(preview.mode, "preview_only")
        self.assertEqual(preview.source["project_inspection"], "not_provided")
        self.assertIn("hardware_design_ir.json", preview.estimated_files_to_modify)

    def test_cli_outputs_preview_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "plan_changes.py"),
                    "做一个 STM32F103 最小系统板，USB 供电，预留 SWD。",
                    "--project",
                    temp_dir,
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(completed.stdout)
            self.assertEqual(output["mode"], "preview_only")
            self.assertEqual(output["next_action"], "confirm_change_plan_before_ir_write")
            self.assertIn("stm32f103_core", [module["id"] for module in output["proposed_modules"]])


if __name__ == "__main__":
    unittest.main()
