import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from packages.tools.kicad_cli.erc_runner import run_schematic_erc


def _create_mock_kicad_cli(bin_dir: Path) -> None:
    if os.name == "nt":
        mock_path = bin_dir / "kicad-cli.cmd"
        mock_path.write_text(
            "\n".join(
                [
                    "@echo off",
                    "setlocal",
                    "echo mock kicad-cli stdout",
                    "echo mock kicad-cli stderr 1>&2",
                    'set "OUT="',
                    ":loop",
                    'if "%~1"=="" goto done',
                    'if "%~1"=="--output" (',
                    '  set "OUT=%~2"',
                    ")",
                    "shift",
                    "goto loop",
                    ":done",
                    'if "%OUT%"=="" exit /b 2',
                    '> "%OUT%" echo {"source":"mock-kicad-cli","severity":"ok"}',
                    "exit /b 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    else:
        mock_path = bin_dir / "kicad-cli"
        mock_path.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'echo "mock kicad-cli stdout"',
                    'echo "mock kicad-cli stderr" >&2',
                    'out=""',
                    'while [ "$#" -gt 0 ]; do',
                    '  if [ "$1" = "--output" ]; then',
                    "    shift",
                    '    out="$1"',
                    "  fi",
                    "  shift",
                    "done",
                    'if [ -z "$out" ]; then exit 2; fi',
                    'printf \'{"source":"mock-kicad-cli","severity":"ok"}\\n\' > "$out"',
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        mock_path.chmod(mock_path.stat().st_mode | stat.S_IEXEC)


class RunErcTest(unittest.TestCase):
    def test_missing_kicad_cli_fails_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            (project_root / "demo.kicad_sch").write_text("(kicad_sch)\n", encoding="utf-8")

            with patch.dict(os.environ, {"PATH": ""}):
                result = run_schematic_erc(project_root)

            self.assertFalse(result.success)
            self.assertFalse(result.kicad_cli_found)
            self.assertEqual(result.mode, "run_erc")
            self.assertIn("kicad-cli", " ".join(result.errors))

    def test_missing_schematic_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            result = run_schematic_erc(project_root)

            self.assertFalse(result.success)
            self.assertIsNone(result.schematic_path)
            self.assertIn(".kicad_sch", " ".join(result.errors))

    def test_mock_kicad_cli_success_writes_report_and_raw_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            project_root.mkdir()
            schematic_path = project_root / "demo.kicad_sch"
            schematic_path.write_text("(kicad_sch)\n", encoding="utf-8")
            bin_dir = Path(temp_dir) / "bin"
            bin_dir.mkdir()
            _create_mock_kicad_cli(bin_dir)

            with patch.dict(os.environ, {"PATH": str(bin_dir)}):
                result = run_schematic_erc(schematic_path)

            self.assertTrue(result.success, result.errors)
            self.assertTrue(result.kicad_cli_found)
            self.assertEqual(Path(result.project_path), project_root.resolve())
            self.assertEqual(Path(result.schematic_path or ""), schematic_path.resolve())
            self.assertTrue(result.report_path)
            self.assertTrue(result.raw_log_path)

            report_path = Path(result.report_path)
            raw_log_path = Path(result.raw_log_path)
            self.assertEqual(report_path.name, "erc_report.json")
            self.assertEqual(raw_log_path.name, "erc_raw.log")
            self.assertTrue(report_path.exists())
            self.assertTrue(raw_log_path.exists())
            self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["source"], "mock-kicad-cli")
            raw_log = raw_log_path.read_text(encoding="utf-8")
            self.assertIn("mock kicad-cli stdout", raw_log)
            self.assertIn("mock kicad-cli stderr", raw_log)
            self.assertFalse(list(project_root.rglob("*.kicad_pcb")))

    def test_run_erc_does_not_touch_kicad_project_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            project_root.mkdir()
            files = {
                project_root / "demo.kicad_pro": "project\n",
                project_root / "demo.kicad_sch": "schematic\n",
                project_root / "demo.kicad_pcb": "pcb\n",
            }
            for path, content in files.items():
                path.write_text(content, encoding="utf-8")
            bin_dir = Path(temp_dir) / "bin"
            bin_dir.mkdir()
            _create_mock_kicad_cli(bin_dir)

            with patch.dict(os.environ, {"PATH": str(bin_dir)}):
                result = run_schematic_erc(project_root)

            self.assertTrue(result.success, result.errors)
            for path, content in files.items():
                self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_python_cli_outputs_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "project"
            project_root.mkdir()
            (project_root / "demo.kicad_sch").write_text("(kicad_sch)\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "run_erc.py"),
                    str(project_root),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "PATH": ""},
            )

            self.assertEqual(completed.returncode, 1)
            output = json.loads(completed.stdout)
            self.assertFalse(output["success"])
            self.assertEqual(output["mode"], "run_erc")
            self.assertFalse(output["kicad_cli_found"])


if __name__ == "__main__":
    unittest.main()
