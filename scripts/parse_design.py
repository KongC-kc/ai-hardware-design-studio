from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.agent.design_request import create_design_plan, parse_design_request  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse a hardware design request and create a deterministic design plan."
    )
    parser.add_argument("request", help="Natural-language hardware design request")
    args = parser.parse_args(argv)

    try:
        parsed_request = parse_design_request(args.request)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    design_plan = create_design_plan(parsed_request)
    print(
        json.dumps(
            {
                "parsed_request": parsed_request.to_dict(),
                "design_plan": design_plan.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
