from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class AgentActionName(str, Enum):
    CREATE_PROJECT = "create_project"
    ANALYZE_USER_REQUIREMENT = "analyze_user_requirement"
    GENERATE_ARCHITECTURE = "generate_architecture"
    GENERATE_DESIGN_IR = "generate_design_ir"
    UPDATE_DESIGN_IR = "update_design_ir"
    VALIDATE_IR = "validate_ir"
    GENERATE_KICAD_SCHEMATIC = "generate_kicad_schematic"
    RUN_ERC = "run_erc"
    EXPORT_SCHEMATIC_PDF = "export_schematic_pdf"
    EXPORT_SCHEMATIC_SVG = "export_schematic_svg"
    EXPORT_BOM = "export_bom"
    EXPORT_NETLIST = "export_netlist"
    EXPLAIN_ERC_REPORT = "explain_erc_report"
    SUGGEST_DESIGN_FIX = "suggest_design_fix"
    OPEN_IN_KICAD = "open_in_kicad"


SUPPORTED_ACTIONS = tuple(action.value for action in AgentActionName)


@dataclass(frozen=True)
class AgentAction:
    """Declarative action emitted by the agent."""

    action: AgentActionName
    params: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {"action": self.action.value, "params": self.params}


def parse_action(payload: Mapping[str, Any]) -> AgentAction:
    """Parse and validate a raw action payload."""

    action_value = payload.get("action")
    params = payload.get("params", {})
    if not isinstance(action_value, str):
        raise ValueError("action must be a string")
    if action_value not in SUPPORTED_ACTIONS:
        raise ValueError(f"Unsupported action: {action_value}")
    if not isinstance(params, dict):
        raise ValueError("params must be an object")
    return AgentAction(action=AgentActionName(action_value), params=params)


def action_schema_example() -> dict[str, Any]:
    """Return the canonical V1 action example."""

    return {
        "action": AgentActionName.GENERATE_DESIGN_IR.value,
        "params": {
            "project_name": "usb_i2s_fpga",
            "requirement": (
                "USB-C input, I2S output, FPGA processing, "
                "dual low-jitter oscillators"
            ),
        },
    }
