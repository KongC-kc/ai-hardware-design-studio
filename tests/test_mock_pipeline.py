import json
import tempfile
import unittest
from pathlib import Path

from packages.core.validators.validate_ir import validate_ir_file
from packages.generator.kicad.project_writer import write_kicad_project


class MockPipelineTest(unittest.TestCase):
    def test_example_ir_validates(self) -> None:
        result = validate_ir_file(Path("examples/usb_i2s_fpga/hardware_design_ir.json"))

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_mock_project_writer_creates_expected_outputs(self) -> None:
        ir_path = Path("examples/usb_i2s_fpga/hardware_design_ir.json")
        ir = json.loads(ir_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = write_kicad_project(ir, Path(temp_dir))

            self.assertEqual(output_dir.name, "usb_i2s_fpga")
            self.assertTrue((output_dir / "usb_i2s_fpga.kicad_pro").exists())
            self.assertTrue((output_dir / "usb_i2s_fpga.kicad_sch").exists())
            self.assertTrue((output_dir / "reports" / "erc_report.json").exists())
            self.assertTrue((output_dir / "bom" / "bom.csv").exists())
            self.assertTrue((output_dir / "exports" / "usb_i2s_fpga.net").exists())


if __name__ == "__main__":
    unittest.main()
