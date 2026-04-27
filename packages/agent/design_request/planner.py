from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from packages.agent.design_request.parser import ParsedDesignRequest


@dataclass(frozen=True)
class DesignPlan:
    plan_title: str
    schematic_blocks: list[str]
    recommended_flow: list[str]
    files_expected_to_change: list[str]
    user_confirmations_required: list[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_design_plan(
    parsed_request: ParsedDesignRequest,
    project_inspection_summary: Mapping[str, Any] | None = None,
) -> DesignPlan:
    """Create a deterministic design plan from a parsed request.

    The optional project inspection summary is reserved for the next MVP step, where the plan
    can compare requested design intent with an existing KiCad project before any file writes.
    """

    schematic_blocks = _schematic_blocks(parsed_request)
    confirmations = _confirmations(parsed_request, project_inspection_summary)
    project_slug = _project_slug(parsed_request)

    return DesignPlan(
        plan_title=f"{parsed_request.target} Design Plan",
        schematic_blocks=schematic_blocks,
        recommended_flow=[
            "review_structured_request",
            "confirm_open_questions",
            "create_or_update_hardware_design_ir",
            "validate_hardware_design_ir",
            "generate_kicad_artifacts_with_deterministic_generator",
            "run_erc_or_mock_report",
        ],
        files_expected_to_change=[
            "hardware_design_ir.json",
            f"workspace/{project_slug}/{project_slug}.kicad_pro",
            f"workspace/{project_slug}/{project_slug}.kicad_sch",
            f"workspace/{project_slug}/reports/validation_report.json",
            f"workspace/{project_slug}/reports/erc_report.json",
        ],
        user_confirmations_required=confirmations,
        next_action="confirm_design_plan_before_ir_generation",
    )


def _schematic_blocks(parsed_request: ParsedDesignRequest) -> list[str]:
    blocks = list(parsed_request.required_schematic_blocks)
    if parsed_request.interfaces or parsed_request.io:
        blocks.append("pinout_assignment")
    blocks.append("erc_review_notes")
    return _unique(blocks)


def _confirmations(
    parsed_request: ParsedDesignRequest,
    project_inspection_summary: Mapping[str, Any] | None,
) -> list[str]:
    confirmations = [
        "Confirm target MCU/package and board purpose.",
        "Confirm power input, regulator current, and connector choice.",
    ]
    confirmations.extend(_humanize_question(question) for question in parsed_request.open_questions)

    if parsed_request.mcu["part"] == "ESP32-S3":
        confirmations.append("Confirm RF module/chip choice and antenna constraints.")
    if project_inspection_summary is not None:
        confirmations.append(
            "Confirm whether to update the inspected project or create a new workspace."
        )

    return _unique(confirmations)


def _humanize_question(question: str) -> str:
    if not question:
        return question
    return question[0].upper() + question[1:] + "."


def _project_slug(parsed_request: ParsedDesignRequest) -> str:
    part = parsed_request.mcu["part"].lower().replace("-", "_")
    if part == "tbd":
        return "hardware_design"
    if "最小系统板" in parsed_request.target:
        suffix = "minimum_system"
    elif "开发板" in parsed_request.target:
        suffix = "dev_board"
    elif "控制板" in parsed_request.target:
        suffix = "control_board"
    else:
        suffix = "design"
    return f"{part}_{suffix}"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
