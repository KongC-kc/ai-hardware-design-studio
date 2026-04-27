import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from packages.generator.kicad.artifact_generator import generate_kicad_artifacts


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_IR = ROOT / "examples" / "usb_i2s_fpga" / "hardware_design_ir.json"


class GenerateKicadArtifactsTest(unittest.TestCase):
    def test_valid_ir_generates_minimal_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            result = generate_kicad_artifacts(EXAMPLE_IR, project_root)

            self.assertTrue(result.success)
            self.assertEqual(result.mode, "generate_kicad_artifacts")
            self.assertEqual(Path(result.ir_path), EXAMPLE_IR.resolve())
            self.assertEqual(result.validation["is_valid"], True)
            self.assertEqual(
                sorted(Path(path).name for path in result.written_files),
                ["generation_report.json", "usb_i2s_fpga.kicad_pro", "usb_i2s_fpga.kicad_sch"],
            )
            self.assertTrue((project_root / "usb_i2s_fpga.kicad_pro").exists())
            self.assertTrue((project_root / "usb_i2s_fpga.kicad_sch").exists())
            self.assertTrue((project_root / "reports" / "generation_report.json").exists())
            self.assertFalse(any(project_root.rglob("*.kicad_pcb")))

    def test_invalid_ir_does_not_generate_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            ir_path = project_root / "hardware_design_ir.json"
            ir_path.write_text(json.dumps({"meta": {"name": "bad"}}), encoding="utf-8")

            result = generate_kicad_artifacts(ir_path, project_root)

            self.assertFalse(result.success)
            self.assertEqual(result.written_files, [])
            self.assertTrue(result.errors)
            self.assertFalse((project_root / "bad.kicad_pro").exists())
            self.assertFalse((project_root / "reports" / "generation_report.json").exists())

    def test_existing_files_are_not_overwritten_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            existing_project = project_root / "usb_i2s_fpga.kicad_pro"
            existing_project.write_text("existing project\n", encoding="utf-8")

            result = generate_kicad_artifacts(EXAMPLE_IR, project_root)

            self.assertFalse(result.success)
            self.assertEqual(result.written_files, [])
            self.assertIn("already exists", " ".join(result.errors))
            self.assertEqual(existing_project.read_text(encoding="utf-8"), "existing project\n")

    def test_overwrite_allows_existing_files_to_be_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            existing_project = project_root / "usb_i2s_fpga.kicad_pro"
            existing_project.write_text("existing project\n", encoding="utf-8")

            result = generate_kicad_artifacts(EXAMPLE_IR, project_root, overwrite=True)

            self.assertTrue(result.success)
            self.assertNotEqual(existing_project.read_text(encoding="utf-8"), "existing project\n")
            self.assertIn(str(existing_project), result.written_files)

    def test_python_cli_outputs_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "generate_kicad_artifacts.py"),
                    str(EXAMPLE_IR),
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
            self.assertTrue(output["success"])
            self.assertEqual(output["mode"], "generate_kicad_artifacts")
            self.assertFalse(list(Path(temp_dir).rglob("*.kicad_pcb")))


if __name__ == "__main__":
    unittest.main()
