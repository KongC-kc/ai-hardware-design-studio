from __future__ import annotations

from packages.agent.actions.action_schema import AgentAction, AgentActionName


def plan_from_requirement(project_name: str, requirement: str) -> list[AgentAction]:
    """Return a deterministic mock V1 action plan for a user requirement."""

    common_params = {"project_name": project_name, "requirement": requirement}
    return [
        AgentAction(AgentActionName.CREATE_PROJECT, {"project_name": project_name}),
        AgentAction(AgentActionName.ANALYZE_USER_REQUIREMENT, common_params),
        AgentAction(AgentActionName.GENERATE_ARCHITECTURE, common_params),
        AgentAction(AgentActionName.GENERATE_DESIGN_IR, common_params),
        AgentAction(AgentActionName.VALIDATE_IR, {"project_name": project_name}),
        AgentAction(AgentActionName.GENERATE_KICAD_SCHEMATIC, {"project_name": project_name}),
        AgentAction(AgentActionName.RUN_ERC, {"project_name": project_name}),
        AgentAction(AgentActionName.EXPORT_SCHEMATIC_SVG, {"project_name": project_name}),
        AgentAction(AgentActionName.EXPORT_SCHEMATIC_PDF, {"project_name": project_name}),
        AgentAction(AgentActionName.EXPORT_BOM, {"project_name": project_name}),
        AgentAction(AgentActionName.EXPORT_NETLIST, {"project_name": project_name}),
        AgentAction(AgentActionName.EXPLAIN_ERC_REPORT, {"project_name": project_name}),
        AgentAction(AgentActionName.SUGGEST_DESIGN_FIX, {"project_name": project_name}),
    ]


def plan_as_json(project_name: str, requirement: str) -> list[dict[str, object]]:
    """Return the mock action plan as JSON-serializable dictionaries."""

    return [action.to_json() for action in plan_from_requirement(project_name, requirement)]
