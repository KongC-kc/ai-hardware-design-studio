"""kicad-cli wrapper package."""

from packages.tools.kicad_cli.erc_diagnostics import ErcDiagnosticsResult, parse_erc_diagnostics
from packages.tools.kicad_cli.erc_runner import ErcRunResult, run_schematic_erc
from packages.tools.kicad_cli.runner import CommandResult, KicadCliStatus, detect_kicad_cli
from packages.tools.kicad_cli.svg_exporter import ExportSchematicSvgResult, run_export_schematic_svg

__all__ = [
    "CommandResult",
    "ErcDiagnosticsResult",
    "ErcRunResult",
    "ExportSchematicSvgResult",
    "KicadCliStatus",
    "detect_kicad_cli",
    "parse_erc_diagnostics",
    "run_export_schematic_svg",
    "run_schematic_erc",
]
