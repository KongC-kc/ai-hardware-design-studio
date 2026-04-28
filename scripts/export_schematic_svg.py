from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.tools.kicad_cli.svg_exporter import run_export_schematic_svg  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export schematic SVG through kicad-cli.")
    parser.add_argument("input_path", type=Path, help="Project directory or .kicad_sch file")
    args = parser.parse_args(argv)

    result = run_export_schematic_svg(args.input_path)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
