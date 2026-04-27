import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from packages.agent.design_request import create_design_plan, parse_design_request


ROOT = Path(__file__).resolve().parents[1]


class DesignRequestTest(unittest.TestCase):
    def test_parse_rp2040_control_board_request(self) -> None:
        raw_request = "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"

        parsed = parse_design_request(raw_request)
        plan = create_design_plan(parsed)

        self.assertEqual(parsed.raw_request, raw_request)
        self.assertEqual(parsed.target, "RP2040 控制板")
        self.assertEqual(parsed.mcu["part"], "RP2040")
        self.assertEqual(parsed.power["input"], "USB-C")
        self.assertIn(
            {"type": "SWD", "count": 1, "notes": "debug/programming header"},
            parsed.interfaces,
        )
        self.assertIn({"type": "button_input", "count": 12, "notes": "user key inputs"}, parsed.io)
        self.assertIn({"type": "rgb_led", "count": 4, "notes": "addressing method TBD"}, parsed.io)
        self.assertIn("mcu_core", parsed.required_schematic_blocks)
        self.assertIn("button_matrix_or_inputs", parsed.required_schematic_blocks)
        self.assertIn("confirm RGB LED type and drive method", parsed.open_questions)
        self.assertEqual(plan.plan_title, "RP2040 控制板 Design Plan")
        self.assertIn("confirm_design_plan_before_ir_generation", plan.next_action)

    def test_parse_stm32f103_minimum_system_request(self) -> None:
        raw_request = "做一个 STM32F103 最小系统板，USB 供电，带 8 个 GPIO 排针和一个 I2C 接口。"

        parsed = parse_design_request(raw_request)
        plan = create_design_plan(parsed)

        self.assertEqual(parsed.target, "STM32F103 最小系统板")
        self.assertEqual(parsed.mcu["part"], "STM32F103")
        self.assertEqual(parsed.power["input"], "USB")
        self.assertIn({"type": "GPIO header", "count": 8, "notes": "pinout TBD"}, parsed.interfaces)
        self.assertIn(
            {"type": "I2C", "count": 1, "notes": "voltage and pull-ups TBD"},
            parsed.interfaces,
        )
        self.assertIn("stm32_boot_and_clock", parsed.required_schematic_blocks)
        self.assertIn("confirm exact STM32F103 package and flash/RAM size", parsed.open_questions)
        self.assertIn("pinout_assignment", plan.schematic_blocks)

    def test_parse_esp32s3_development_board_request(self) -> None:
        raw_request = "做一个 ESP32-S3 开发板，Type-C 供电，带屏幕接口、RGB 灯和复位按键。"

        parsed = parse_design_request(raw_request)
        plan = create_design_plan(parsed)

        self.assertEqual(parsed.target, "ESP32-S3 开发板")
        self.assertEqual(parsed.mcu["part"], "ESP32-S3")
        self.assertEqual(parsed.power["input"], "USB-C")
        self.assertIn(
            {"type": "display", "count": 1, "notes": "connector protocol TBD"},
            parsed.interfaces,
        )
        self.assertIn({"type": "rgb_led", "count": 1, "notes": "addressing method TBD"}, parsed.io)
        self.assertIn(
            {"type": "reset_button", "count": 1, "notes": "manual reset input"},
            parsed.io,
        )
        self.assertIn("usb_to_uart_or_native_usb", parsed.required_schematic_blocks)
        self.assertIn("confirm display connector type and bus", parsed.open_questions)
        self.assertIn(
            "Confirm RF module/chip choice and antenna constraints.",
            plan.user_confirmations_required,
        )

    def test_cli_outputs_parse_and_plan_json(self) -> None:
        raw_request = "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"

        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "parse_design.py"), raw_request],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["parsed_request"]["mcu"]["part"], "RP2040")
        self.assertEqual(
            output["design_plan"]["next_action"],
            "confirm_design_plan_before_ir_generation",
        )

    def test_parser_repairs_common_windows_cli_mojibake(self) -> None:
        raw_request = "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"
        mojibake_request = raw_request.encode("gbk").decode("cp1252")

        parsed = parse_design_request(mojibake_request)

        self.assertEqual(parsed.raw_request, raw_request)
        self.assertEqual(parsed.target, "RP2040 控制板")
        self.assertIn({"type": "button_input", "count": 12, "notes": "user key inputs"}, parsed.io)

    def test_npm_script_preserves_unicode_request_text(self) -> None:
        npm = shutil.which("npm.cmd") or shutil.which("npm")
        if npm is None:
            self.skipTest("npm is not available")
        raw_request = "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"

        completed = subprocess.run(
            [npm, "run", "--silent", "parse-design", "--", raw_request],
            check=False,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual(output["parsed_request"]["raw_request"], raw_request)
        self.assertEqual(output["parsed_request"]["target"], "RP2040 控制板")


if __name__ == "__main__":
    unittest.main()
