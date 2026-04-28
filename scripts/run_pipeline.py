from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.pipeline.orchestrator import run_pipeline  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full KiCad artifact generation and ERC analysis pipeline."
    )
    parser.add_argument("project_path", type=Path, help="Project directory")
    parser.add_argument("--ir", type=Path, default=None, help="Path to hardware_design_ir.json (default: <project_path>/hardware_design_ir.json)")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing generated artifact files")
    args = parser.parse_args(argv)

    result = run_pipeline(
        project_path=args.project_path,
        ir_path=args.ir,
        overwrite=args.overwrite,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
