import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.tools.project_inspector.inspector import inspect_project


ROOT = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ProjectInspectorTest(unittest.TestCase):
    def test_inspect_project_summarizes_kicad_project_files_and_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_text(project_root / "demo.kicad_pro", "{}\n")
            write_text(project_root / "demo.kicad_pcb", "(kicad_pcb)\n")
            write_text(project_root / "sym-lib-table", "(sym_lib_table)\n")
            write_text(project_root / "libraries" / "fp-lib-table", "(fp_lib_table)\n")
            write_text(
                project_root / "demo.kicad_sch",
                """
(kicad_sch
  (sheet
    (property "Sheetname" "Power")
    (property "Sheetfile" "sheets/power.kicad_sch")
  )
)
""",
            )
            write_text(project_root / "sheets" / "power.kicad_sch", "(kicad_sch)\n")

            summary = inspect_project(project_root)

            self.assertEqual(summary.project_name, "demo")
            self.assertEqual(Path(summary.project_root), project_root.resolve())
            self.assertEqual(summary.schematic_files, ["demo.kicad_sch", "sheets/power.kicad_sch"])
            self.assertEqual(summary.pcb_files, ["demo.kicad_pcb"])
            self.assertEqual(summary.symbol_library_tables, ["sym-lib-table"])
            self.assertEqual(summary.footprint_library_tables, ["libraries/fp-lib-table"])
            self.assertEqual(summary.warnings, [])
            self.assertEqual(len(summary.detected_sheets), 1)
            self.assertEqual(summary.detected_sheets[0].name, "Power")
            self.assertEqual(summary.detected_sheets[0].file, "sheets/power.kicad_sch")
            self.assertEqual(summary.detected_sheets[0].source_schematic, "demo.kicad_sch")
            self.assertTrue(summary.detected_sheets[0].exists)

    def test_inspect_project_warns_when_required_project_markers_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_text(project_root / "only.kicad_sch", "(kicad_sch)\n")

            summary = inspect_project(project_root)

            self.assertEqual(summary.project_name, project_root.name)
            self.assertIn("No .kicad_pro file found in project root.", summary.warnings)
            self.assertIn("No .kicad_pcb files found.", summary.warnings)

    def test_cli_prints_summary_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_text(project_root / "demo.kicad_pro", "{}\n")
            write_text(project_root / "demo.kicad_sch", "(kicad_sch)\n")

            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "inspect_project.py"), str(project_root)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(completed.stdout)
            self.assertEqual(output["project_name"], "demo")
            self.assertEqual(output["schematic_files"], ["demo.kicad_sch"])


if __name__ == "__main__":
    unittest.main()
