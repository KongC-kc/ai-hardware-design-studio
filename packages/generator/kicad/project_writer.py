from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from packages.core.validators.validate_ir import validate_ir
from packages.generator.bom.bom_builder import write_bom
from packages.generator.netlist.netlist_builder import write_netlist
from packages.generator.schematic.schematic_builder import write_schematic
from packages.tools.kicad_cli.runner import detect_kicad_cli


def write_kicad_project(ir: Mapping[str, Any], workspace_root: Path | str = Path("workspace")) -> Path:
    """Write a deterministic V1 mock KiCad project from validated IR."""

    validation = validate_ir(ir)
    validation.raise_for_errors()

    project_name = str(ir["meta"]["name"])
    root = Path(workspace_root)
    project_dir = root / project_name
    reports_dir = project_dir / "reports"
    exports_dir = project_dir / "exports"
    bom_dir = project_dir / "bom"

    for directory in (project_dir, reports_dir, exports_dir, bom_dir):
        directory.mkdir(parents=True, exist_ok=True)

    project_file = project_dir / f"{project_name}.kicad_pro"
    schematic_file = project_dir / f"{project_name}.kicad_sch"
    netlist_file = exports_dir / f"{project_name}.net"
    bom_file = bom_dir / "bom.csv"

    _write_project_file(ir, project_file)
    write_schematic(ir, schematic_file)
    write_netlist(ir, netlist_file)
    write_bom(ir, bom_file)
    _write_mock_svg(ir, exports_dir / f"{project_name}.svg")
    _write_mock_pdf(exports_dir / f"{project_name}.pdf", project_name)
    _write_validation_report(validation.warnings, reports_dir / "validation_report.json")
    _write_mock_erc_report(project_name, reports_dir / "erc_report.json")
    _write_architecture_summary(ir, reports_dir / "architecture.md")

    return project_dir


def _write_project_file(ir: Mapping[str, Any], output_path: Path) -> None:
    project_data = {
        "meta": ir.get("meta", {}),
        "generator": {
            "name": "ai-hardware-design-studio",
            "mode": "v1_mock",
            "note": "This file is generated. Edit hardware_design_ir.json instead.",
        },
        "schematic": {
            "source_ir": "hardware_design_ir.json",
            "deterministic": True,
        },
    }
    output_path.write_text(json.dumps(project_data, indent=2) + "\n", encoding="utf-8")


def _write_validation_report(warnings: list[str], output_path: Path) -> None:
    report = {
        "status": "pass",
        "mode": "mock_validator",
        "warnings": warnings,
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _write_mock_erc_report(project_name: str, output_path: Path) -> None:
    kicad_cli = detect_kicad_cli()
    report = {
        "project": project_name,
        "status": "mock_pass",
        "mode": "mock_erc",
        "kicad_cli_available": kicad_cli.available,
        "kicad_cli_path": kicad_cli.path,
        "messages": [
            {
                "severity": "info",
                "message": "Mock ERC report generated. Run real kicad-cli ERC when available.",
            }
        ],
    }
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _write_architecture_summary(ir: Mapping[str, Any], output_path: Path) -> None:
    meta = ir.get("meta", {})
    requirements = ir.get("requirements", {})
    lines = [
        f"# {meta.get('name', 'Unnamed Project')} Architecture",
        "",
        str(meta.get("description", "")),
        "",
        "## Requirements",
        "",
        f"- Inputs: {', '.join(requirements.get('input', []))}",
        f"- Outputs: {', '.join(requirements.get('output', []))}",
        f"- Power input: {requirements.get('power_input', '')}",
        f"- Features: {', '.join(requirements.get('features', []))}",
        "",
        "## Blocks",
        "",
    ]
    for block in ir.get("blocks", []):
        if isinstance(block, Mapping):
            lines.append(f"- `{block.get('id')}`: {block.get('type')} ({block.get('part', 'UNSPECIFIED')})")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_mock_svg(ir: Mapping[str, Any], output_path: Path) -> None:
    project_name = str(ir.get("meta", {}).get("name", "Project"))
    block_count = len(ir.get("blocks", []))
    connection_count = len(ir.get("connections", []))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <rect width="1200" height="800" fill="#f8fafc"/>
  <text x="48" y="64" font-family="Arial, sans-serif" font-size="28" fill="#0f172a">{project_name}</text>
  <text x="48" y="104" font-family="Arial, sans-serif" font-size="16" fill="#475569">Mock schematic preview generated from IR</text>
  <rect x="48" y="150" width="320" height="120" rx="8" fill="#dbeafe" stroke="#2563eb"/>
  <text x="72" y="215" font-family="Arial, sans-serif" font-size="20" fill="#1e3a8a">Blocks: {block_count}</text>
  <rect x="430" y="150" width="320" height="120" rx="8" fill="#dcfce7" stroke="#16a34a"/>
  <text x="454" y="215" font-family="Arial, sans-serif" font-size="20" fill="#14532d">Connections: {connection_count}</text>
  <rect x="812" y="150" width="320" height="120" rx="8" fill="#fef3c7" stroke="#d97706"/>
  <text x="836" y="215" font-family="Arial, sans-serif" font-size="20" fill="#78350f">ERC: mock pass</text>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")


def _write_mock_pdf(output_path: Path, title: str) -> None:
    text = f"Mock schematic preview for {title}"
    stream = f"BT /F1 24 Tf 72 720 Td ({_escape_pdf_text(text)}) Tj ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, content in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n{content}\nendobj\n".encode("latin-1"))

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )
    output_path.write_bytes(bytes(output))


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
