from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def build_schematic_text(ir: Mapping[str, Any]) -> str:
    """Build a deterministic mock KiCad schematic text artifact.

    TODO: Replace the comment-only mock with a real symbol and wire generator.
    """

    meta = ir.get("meta", {})
    project_name = str(meta.get("name", "unnamed_project"))
    description = str(meta.get("description", ""))

    lines = [
        "(kicad_sch",
        "  (version 20240101)",
        "  (generator \"ai-hardware-design-studio-v1-mock\")",
        f"  (paper \"A4\")",
        "  (title_block",
        f"    (title {_sexpr_string(project_name)})",
        f"    (comment 1 {_sexpr_string(description)})",
        "    (comment 2 \"Generated from hardware_design_ir.json\")",
        "  )",
        "  ; Blocks",
    ]

    for block in ir.get("blocks", []):
        if not isinstance(block, Mapping):
            continue
        block_id = str(block.get("id", "unknown"))
        block_type = str(block.get("type", "unknown"))
        part = str(block.get("part", "UNSPECIFIED"))
        lines.append(f"  ; block {block_id}: type={block_type}, part={part}")

    lines.append("  ; Power tree")
    for node in ir.get("power_tree", []):
        if not isinstance(node, Mapping):
            continue
        net = str(node.get("net", ""))
        source = str(node.get("source", ""))
        children = ", ".join(str(child) for child in node.get("children", []))
        lines.append(f"  ; power {net}: source={source}, children={children}")

    lines.append("  ; Logical connections")
    for connection in ir.get("connections", []):
        if not isinstance(connection, Mapping):
            continue
        start = str(connection.get("from", ""))
        end = str(connection.get("to", ""))
        net = str(connection.get("net", ""))
        lines.append(f"  ; net {net}: {start} -> {end}")

    lines.append(")")
    return "\n".join(lines) + "\n"


def write_schematic(ir: Mapping[str, Any], output_path: Path) -> Path:
    """Write the mock schematic artifact."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_schematic_text(ir), encoding="utf-8")
    return output_path


def _sexpr_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
