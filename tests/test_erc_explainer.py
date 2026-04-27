import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.agent.report_explainer.erc_explainer import explain_erc_report


def _write_diagnostics(project_root: Path, diagnostics: list[dict[str, object]]) -> Path:
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_path = reports_dir / "erc_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "success": True,
                "mode": "parse_erc_diagnostics",
                "source_report": str(reports_dir / "erc_report.json"),
                "diagnostics_path": str(diagnostics_path),
                "summary": {
                    "error_count": sum(1 for item in diagnostics if item.get("severity") == "error"),
                    "warning_count": sum(1 for item in diagnostics if item.get("severity") == "warning"),
                    "info_count": sum(1 for item in diagnostics if item.get("severity") == "info"),
                },
                "diagnostics": diagnostics,
                "errors": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    return diagnostics_path


class ErcExplainerTest(unittest.TestCase):
    def test_explains_error_and_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            diagnostics_path = _write_diagnostics(
                project_root,
                [
                    {
                        "id": "erc-001",
                        "severity": "error",
                        "code": "PIN_NOT_CONNECTED",
                        "message": "Pin is not connected",
                        "file": "project.kicad_sch",
                        "sheet": "/",
                        "symbol": "U1",
                        "pin": "3",
                        "net": "I2S_BCLK",
                        "location": {"x": None, "y": None},
                        "raw": {},
                    },
                    {
                        "id": "erc-002",
                        "severity": "warning",
                        "code": "POWER_INPUT_NOT_DRIVEN",
                        "message": "Power input is not driven",
                        "file": "project.kicad_sch",
                        "sheet": "/power",
                        "symbol": "U2",
                        "pin": "1",
                        "net": "VBUS",
                        "location": {"x": None, "y": None},
                        "raw": {},
                    },
                ],
            )

            result = explain_erc_report(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.mode, "explain_erc_report")
            self.assertEqual(Path(result.source or ""), diagnostics_path.resolve())
            self.assertEqual(result.summary["error_count"], 1)
            self.assertEqual(result.summary["warning_count"], 1)
            self.assertEqual(len(result.explanations), 2)
            self.assertEqual(result.explanations[0]["diagnostic_id"], "erc-001")
            self.assertEqual(result.explanations[0]["severity"], "error")
            self.assertEqual(result.explanations[0]["title"], "Pin is not connected")
            self.assertTrue(result.explanations[0]["requires_user_confirmation"])
            self.assertIn("U1", result.explanations[0]["plain_language"])
            self.assertTrue(result.explanations[0]["likely_causes"])
            self.assertTrue(result.explanations[0]["suggested_fixes"])
            self.assertTrue(Path(result.output or "").exists())

    def test_unknown_code_gets_fallback_explanation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_diagnostics(
                project_root,
                [
                    {
                        "id": "erc-010",
                        "severity": "info",
                        "code": "FUTURE_KICAD_RULE",
                        "message": "Future KiCad rule",
                        "file": "project.kicad_sch",
                        "sheet": "/",
                        "symbol": None,
                        "pin": None,
                        "net": None,
                        "location": {"x": None, "y": None},
                        "raw": {},
                    }
                ],
            )

            result = explain_erc_report(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.explanations[0]["diagnostic_id"], "erc-010")
            self.assertEqual(result.explanations[0]["title"], "Future KiCad rule")
            self.assertIn("unknown ERC diagnostic", result.explanations[0]["plain_language"])

    def test_missing_diagnostics_file_returns_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            result = explain_erc_report(project_root)

            self.assertFalse(result.success)
            self.assertIsNone(result.source)
            self.assertIsNone(result.output)
            self.assertIn("erc_diagnostics.json", " ".join(result.errors))

    def test_explainer_does_not_touch_kicad_project_files_or_raw_erc_report(self) -> None:
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
            raw_report = reports_dir / "erc_report.json"
            raw_report.write_text("{not valid json", encoding="utf-8")
            _write_diagnostics(
                project_root,
                [
                    {
                        "id": "erc-001",
                        "severity": "error",
                        "code": "CONFLICTING_OUTPUTS",
                        "message": "Conflicting outputs",
                        "file": "project.kicad_sch",
                        "sheet": "/",
                        "symbol": "U3",
                        "pin": None,
                        "net": "GPIO0",
                        "location": {"x": None, "y": None},
                        "raw": {},
                    }
                ],
            )

            result = explain_erc_report(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(raw_report.read_text(encoding="utf-8"), "{not valid json")
            for path, content in files.items():
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_python_cli_outputs_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_diagnostics(project_root, [])

            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "explain_erc_report.py"),
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
            self.assertEqual(output["mode"], "explain_erc_report")
            self.assertEqual(output["explanations"], [])


if __name__ == "__main__":
    unittest.main()
