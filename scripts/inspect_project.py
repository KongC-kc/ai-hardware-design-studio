from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.tools.project_inspector import ProjectInspectorError, inspect_project  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a KiCad project directory without writing it."
    )
    parser.add_argument("project_path", type=Path, help="Path to a KiCad project directory")
    args = parser.parse_args(argv)

    try:
        summary = inspect_project(args.project_path)
    except ProjectInspectorError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(summary.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
