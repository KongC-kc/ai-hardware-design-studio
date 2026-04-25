from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from xml.sax.saxutils import escape


def build_netlist_text(ir: Mapping[str, Any]) -> str:
    """Build a simple XML-like logical netlist from the IR."""

    project_name = str(ir.get("meta", {}).get("name", "unnamed_project"))
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<netlist project="{escape(project_name)}" generator="ai-hardware-design-studio-v1-mock">',
        "  <components>",
    ]
    for block in ir.get("blocks", []):
        if not isinstance(block, Mapping):
            continue
        block_id = escape(str(block.get("id", "")))
        block_type = escape(str(block.get("type", "")))
        part = escape(str(block.get("part", "UNSPECIFIED")))
        lines.append(f'    <component ref="{block_id}" type="{block_type}" part="{part}" />')
    lines.append("  </components>")
    lines.append("  <nets>")
    for connection in ir.get("connections", []):
        if not isinstance(connection, Mapping):
            continue
        net = escape(str(connection.get("net", "")))
        start = escape(str(connection.get("from", "")))
        end = escape(str(connection.get("to", "")))
        lines.append(f'    <net name="{net}">')
        lines.append(f'      <node endpoint="{start}" />')
        lines.append(f'      <node endpoint="{end}" />')
        lines.append("    </net>")
    lines.append("  </nets>")
    lines.append("</netlist>")
    return "\n".join(lines) + "\n"


def write_netlist(ir: Mapping[str, Any], output_path: Path) -> Path:
    """Write the logical mock netlist."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_netlist_text(ir), encoding="utf-8")
    return output_path
