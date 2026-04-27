from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.tools.kicad_cli.erc_diagnostics import parse_erc_diagnostics  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a KiCad ERC report into diagnostics JSON.")
    parser.add_argument("input_path", type=Path, help="Project directory, reports directory, or erc_report.json")
    parser.add_argument("--raw-log", type=Path, default=None, help="Optional reports/erc_raw.log path")
    args = parser.parse_args(argv)

    result = parse_erc_diagnostics(args.input_path, raw_log_path=args.raw_log)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
