from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.agent.report_explainer.erc_fix_suggester import suggest_erc_fixes  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest proposal-only ERC fixes from normalized reports.")
    parser.add_argument("project_path", type=Path, help="Project directory, reports directory, or erc_diagnostics.json")
    args = parser.parse_args(argv)

    result = suggest_erc_fixes(args.project_path)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
