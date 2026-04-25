from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.validators.validate_ir import load_ir, validate_ir  # noqa: E402
from packages.generator.kicad.project_writer import write_kicad_project  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a mock KiCad schematic project from hardware_design_ir.json."
    )
    parser.add_argument("ir_path", type=Path, help="Path to hardware_design_ir.json")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=ROOT / "workspace",
        help="Workspace root for generated projects",
    )
    args = parser.parse_args(argv)

    ir = load_ir(args.ir_path)
    validation = validate_ir(ir)
    if not validation.is_valid:
        print("IR validation failed:", file=sys.stderr)
        for error in validation.errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    project_dir = write_kicad_project(ir, args.workspace)
    relative_project_dir = project_dir.relative_to(ROOT) if project_dir.is_relative_to(ROOT) else project_dir
    print(f"Generated project: {relative_project_dir}")
    print(json.dumps({"warnings": validation.warnings}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
