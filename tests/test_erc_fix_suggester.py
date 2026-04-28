import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.agent.report_explainer.erc_fix_suggester import suggest_erc_fixes


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


def _write_explanation(project_root: Path, explanations: list[dict[str, object]]) -> Path:
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    explanation_path = reports_dir / "erc_explanation.json"
    explanation_path.write_text(
        json.dumps(
            {
                "success": True,
                "mode": "explain_erc_report",
                "summary": {"explanation_count": len(explanations)},
                "explanations": explanations,
                "errors": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    return explanation_path


class ErcFixSuggesterTest(unittest.TestCase):
    def test_generates_suggested_fixes_from_diagnostics_and_explanation(self) -> None:
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
                    }
                ],
            )
            explanation_path = _write_explanation(
                project_root,
                [
                    {
                        "diagnostic_id": "erc-001",
                        "plain_language": "Explanation plain text.",
                        "suggested_fixes": ["Confirm the intended net destination."],
                    }
                ],
            )

            result = suggest_erc_fixes(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.mode, "suggest_erc_fixes")
            self.assertEqual(result.sources["diagnostics"], str(diagnostics_path.resolve()))
            self.assertEqual(result.sources["explanation"], str(explanation_path.resolve()))
            self.assertEqual(result.summary["fix_count"], 1)
            self.assertEqual(result.summary["auto_applicable_count"], 0)
            self.assertEqual(result.summary["requires_confirmation_count"], 1)
            self.assertEqual(len(result.fixes), 1)
            fix = result.fixes[0]
            self.assertEqual(fix["id"], "fix-001")
            self.assertEqual(fix["diagnostic_id"], "erc-001")
            self.assertEqual(fix["severity"], "error")
            self.assertEqual(fix["title"], "Connect unconnected pin")
            self.assertEqual(fix["target"]["file"], "project.kicad_sch")
            self.assertEqual(fix["target"]["symbol"], "U1")
            self.assertEqual(fix["target"]["pin"], "3")
            self.assertEqual(fix["target"]["net"], "I2S_BCLK")
            self.assertEqual(fix["proposal_type"], "ir_change")
            self.assertEqual(
                fix["proposed_ir_patch"],
                {
                    "op": "add_connection",
                    "from": "U1.3",
                    "to": "TODO_CONFIRM_TARGET",
                    "net": "I2S_BCLK",
                },
            )
            self.assertFalse(fix["auto_applicable"])
            self.assertTrue(fix["requires_user_confirmation"])
            output_path = Path(result.output or "")
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["mode"], "suggest_erc_fixes")

    def test_missing_diagnostics_returns_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            result = suggest_erc_fixes(project_root)

            self.assertFalse(result.success)
            self.assertEqual(result.mode, "suggest_erc_fixes")
            self.assertIsNone(result.sources["diagnostics"])
            self.assertIsNone(result.output)
            self.assertEqual(result.fixes, [])
            self.assertIn("erc_diagnostics.json", " ".join(result.errors))

    def test_missing_explanation_falls_back_to_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_diagnostics(
                project_root,
                [
                    {
                        "id": "erc-002",
                        "severity": "warning",
                        "code": "POWER_INPUT_NOT_DRIVEN",
                        "message": "Power input is not driven",
                        "file": "project.kicad_sch",
                        "symbol": "J1",
                        "pin": "1",
                        "net": "VBUS",
                    }
                ],
            )

            result = suggest_erc_fixes(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertIsNone(result.sources["explanation"])
            self.assertIn("erc_explanation.json", " ".join(result.warnings))
            self.assertEqual(result.fixes[0]["diagnostic_id"], "erc-002")
            self.assertEqual(result.fixes[0]["title"], "Drive power input")
            self.assertTrue(result.fixes[0]["requires_user_confirmation"])

    def test_unknown_code_generates_fallback_fix(self) -> None:
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
                    }
                ],
            )

            result = suggest_erc_fixes(project_root)

            self.assertTrue(result.success, result.errors)
            self.assertEqual(result.fixes[0]["diagnostic_id"], "erc-010")
            self.assertEqual(result.fixes[0]["title"], "Review ERC diagnostic")
            self.assertEqual(result.fixes[0]["proposal_type"], "manual_review")
            self.assertEqual(result.fixes[0]["proposed_ir_patch"]["op"], "review_diagnostic")
            self.assertFalse(result.fixes[0]["auto_applicable"])
            self.assertTrue(result.fixes[0]["requires_user_confirmation"])

    def test_suggester_does_not_touch_kicad_project_files_or_ir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            files = {
                project_root / "demo.kicad_pro": "project\n",
                project_root / "demo.kicad_sch": "schematic\n",
                project_root / "demo.kicad_pcb": "pcb\n",
                project_root / "hardware_design_ir.json": '{"meta": {"name": "demo"}}\n',
            }
            for path, content in files.items():
                path.write_text(content, encoding="utf-8")
            _write_diagnostics(
                project_root,
                [
                    {
                        "id": "erc-003",
                        "severity": "error",
                        "code": "CONFLICTING_OUTPUTS",
                        "message": "Conflicting outputs",
                        "file": "project.kicad_sch",
                        "symbol": "U3",
                        "net": "GPIO0",
                    }
                ],
            )

            result = suggest_erc_fixes(project_root)

            self.assertTrue(result.success, result.errors)
            for path, content in files.items():
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_python_cli_outputs_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_diagnostics(project_root, [])

            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "suggest_erc_fixes.py"),
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
            self.assertEqual(output["mode"], "suggest_erc_fixes")
            self.assertEqual(output["summary"]["fix_count"], 0)


if __name__ == "__main__":
    unittest.main()
