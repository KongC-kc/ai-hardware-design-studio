from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping


def build_bom_rows(ir: Mapping[str, Any]) -> list[dict[str, str]]:
    """Build simple V1 BOM rows from IR blocks."""

    rows: list[dict[str, str]] = []
    for block in ir.get("blocks", []):
        if not isinstance(block, Mapping):
            continue
        rows.append(
            {
                "reference": str(block.get("id", "")),
                "block_type": str(block.get("type", "")),
                "part": str(block.get("part", "UNSPECIFIED")),
                "quantity": "1",
                "notes": "mock V1 BOM row",
            }
        )
    return rows


def write_bom(ir: Mapping[str, Any], output_path: Path) -> Path:
    """Write a CSV BOM for the mock project."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_bom_rows(ir)
    fieldnames = ["reference", "block_type", "part", "quantity", "notes"]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path
