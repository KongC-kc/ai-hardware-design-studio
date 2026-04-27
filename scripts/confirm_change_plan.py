from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.agent.confirm_change_plan import confirm_change_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Confirm a preview-only change plan and write hardware_design_ir.json."
    )
    parser.add_argument("preview_json_path", type=Path, help="Path to HardwareDesignIRPreview JSON")
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Optional project directory that will receive hardware_design_ir.json",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=ROOT / "workspace",
        help="Workspace root used when --project is not provided",
    )
    args = parser.parse_args(argv)

    try:
        preview = _load_preview(args.preview_json_path)
        result = confirm_change_plan(
            preview,
            project_path=args.project,
            workspace_root=args.workspace,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps(_error_payload(str(exc)), ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


def _load_preview(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Preview JSON root must be an object")
    return data


def _error_payload(message: str) -> dict[str, Any]:
    return {
        "success": False,
        "mode": "confirmed_ir_write",
        "written": False,
        "ir_path": None,
        "validation": {
            "is_valid": False,
            "errors": [message],
            "warnings": [],
        },
        "hardware_design_ir": None,
    }


if __name__ == "__main__":
    raise SystemExit(main())
