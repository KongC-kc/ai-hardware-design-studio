from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.generator.kicad.artifact_generator import generate_kicad_artifacts  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate minimal deterministic KiCad artifacts from hardware_design_ir.json."
    )
    parser.add_argument("ir_path", type=Path, help="Path to confirmed hardware_design_ir.json")
    parser.add_argument(
        "--project",
        type=Path,
        required=True,
        help="Project directory that will receive generated KiCad artifacts",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing generated artifact files",
    )
    args = parser.parse_args(argv)

    result = generate_kicad_artifacts(
        ir_path=args.ir_path,
        project_path=args.project,
        overwrite=args.overwrite,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
