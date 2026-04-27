from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.agent.change_planner import create_change_plan_preview  # noqa: E402
from packages.agent.design_request import create_design_plan, parse_design_request  # noqa: E402
from packages.tools.project_inspector import (  # noqa: E402
    ProjectInspectorError,
    inspect_project,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a preview-only KiCad hardware design change plan."
    )
    parser.add_argument("request", help="Natural-language hardware design request")
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Optional KiCad project directory to inspect before planning",
    )
    args = parser.parse_args(argv)

    try:
        parsed_request = parse_design_request(args.request)
        project_summary = _inspect_project_if_requested(args.project)
        design_plan = create_design_plan(parsed_request, project_summary)
        preview = create_change_plan_preview(parsed_request, design_plan, project_summary)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(preview.to_dict(), ensure_ascii=False, indent=2))
    return 0


def _inspect_project_if_requested(project_path: Path | None) -> object | None:
    if project_path is None:
        return None
    try:
        return inspect_project(project_path)
    except ProjectInspectorError as exc:
        return {
            "project_name": project_path.name,
            "project_root": str(project_path),
            "project_files": [],
            "schematic_files": [],
            "pcb_files": [],
            "symbol_library_tables": [],
            "footprint_library_tables": [],
            "detected_sheets": [],
            "warnings": [f"Project inspection failed: {exc}"],
        }


if __name__ == "__main__":
    raise SystemExit(main())
