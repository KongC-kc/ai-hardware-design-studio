import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.tools.kicad_cli.erc_diagnostics import parse_erc_diagnostics


class ParseErcDiagnosticsTest(unittest.TestCase):
    def test_empty_report_writes_empty_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_text(json.dumps({"diagnostics": []}), encoding="utf-8")

            result = parse_erc_diagnostics(report_path)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.mode, "parse_erc_diagnostics")
            self.assertEqual(result.summary["error_count"], 0)
            self.assertEqual(result.summary["warning_count"], 0)
            self.assertEqual(result.summary["info_count"], 0)
            self.assertEqual(result.diagnostics, [])
            self.assertTrue(Path(result.diagnostics_path or "").exists())

    def test_mock_report_with_error_and_warning_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            reports_dir = project_root / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "violations": [
                            {
                                "severity": "error",
                                "code": "PIN_NOT_CONNECTED",
                                "description": "Pin is not connected",
                                "file": "project.kicad_sch",
                                "sheet": "/",
                                "symbol": "U1",
                                "pin": "3",
                                "net": "I2S_BCLK",
                                "position": {"x": 12.5, "y": 8.0},
                            },
                            {
                                "severity": "warning",
                                "code": "POWER_INPUT_NOT_DRIVEN",
                                "message": "Power input is not driven",
                                "file": "project.kicad_sch",
                                "sheet": "/power",
                                "symbol": "U2",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = parse_erc_diagnostics(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.summary["error_count"], 1)
            self.assertEqual(result.summary["warning_count"], 1)
            self.assertEqual(result.diagnostics[0]["id"], "erc-001")
            self.assertEqual(result.diagnostics[0]["severity"], "error")
            self.assertEqual(result.diagnostics[0]["code"], "PIN_NOT_CONNECTED")
            self.assertEqual(result.diagnostics[0]["file"], "project.kicad_sch")
            self.assertEqual(result.diagnostics[0]["sheet"], "/")
            self.assertEqual(result.diagnostics[0]["symbol"], "U1")
            self.assertEqual(result.diagnostics[0]["pin"], "3")
            self.assertEqual(result.diagnostics[0]["net"], "I2S_BCLK")
            self.assertEqual(result.diagnostics[0]["location"], {"x": 12.5, "y": 8.0})

    def test_unknown_fields_do_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "future_kicad_shape": [
                            {
                                "level": "info",
                                "text": "Future KiCad diagnostic",
                                "where": {"x": "not-a-number"},
                                "unexpected": {"kept": True},
                            }
                        ],
                        "metadata": {"tool": "kicad-cli"},
                    }
                ),
                encoding="utf-8",
            )

            result = parse_erc_diagnostics(report_path)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.summary["info_count"], 1)
            self.assertEqual(result.diagnostics[0]["message"], "Future KiCad diagnostic")
            self.assertEqual(result.diagnostics[0]["location"], {"x": None, "y": None})

    def test_report_with_utf8_bom_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_bytes(
                b"\xef\xbb\xbf"
                + json.dumps({"diagnostics": [{"severity": "warning", "message": "BOM report"}]}).encode("utf-8")
            )

            result = parse_erc_diagnostics(report_path)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.summary["warning_count"], 1)
            self.assertEqual(result.diagnostics[0]["message"], "BOM report")

    def test_single_bad_diagnostic_does_not_skip_other_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "diagnostics": [
                            ["bad", "record"],
                            {"severity": {"not": "scalar"}, "message": ["bad"]},
                            {"severity": "error", "message": "Valid error", "file": "valid.kicad_sch"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = parse_erc_diagnostics(report_path)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.summary["error_count"], 1)
            self.assertEqual(len(result.diagnostics), 1)
            self.assertEqual(result.diagnostics[0]["message"], "Valid error")
            self.assertTrue(result.warnings)

    def test_current_minimal_erc_report_is_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            reports_dir.mkdir()
            report_path = reports_dir / "erc_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "success": False,
                        "mode": "run_erc",
                        "errors": ["kicad-cli was not found on PATH."],
                        "warnings": ["mock warning"],
                    }
                ),
                encoding="utf-8",
            )

            result = parse_erc_diagnostics(report_path)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.summary["error_count"], 1)
            self.assertEqual(result.summary["warning_count"], 1)
            self.assertEqual(result.diagnostics[0]["code"], "ERC_ERROR")

    def test_missing_report_returns_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            result = parse_erc_diagnostics(project_root)

            self.assertFalse(result.success)
            self.assertIsNone(result.source_report)
            self.assertIn("erc_report.json", " ".join(result.errors))

    def test_parse_does_not_touch_kicad_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            files = {
                project_root / "demo.kicad_pro": "project\n",
                project_root / "demo.kicad_sch": "schematic\n",
                project_root / "demo.kicad_pcb": "pcb\n",
            }
            for path, content in files.items():
                path.write_text(content, encoding="utf-8")
            reports_dir = project_root / "reports"
            reports_dir.mkdir()
            (reports_dir / "erc_report.json").write_text(json.dumps({"diagnostics": []}), encoding="utf-8")

            result = parse_erc_diagnostics(project_root)

            self.assertTrue(result.success, result.errors)
            for path, content in files.items():
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_python_cli_outputs_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            reports_dir = project_root / "reports"
            reports_dir.mkdir()
            (reports_dir / "erc_report.json").write_text(json.dumps({"diagnostics": []}), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "parse_erc_diagnostics.py"),
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
            self.assertEqual(output["mode"], "parse_erc_diagnostics")
            self.assertEqual(output["summary"]["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
