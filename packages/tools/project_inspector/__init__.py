"""Read-only KiCad project inspection helpers."""

from packages.tools.project_inspector.inspector import (
    DetectedSheet,
    ProjectInspectionSummary,
    ProjectInspectorError,
    inspect_project,
)

__all__ = [
    "DetectedSheet",
    "ProjectInspectionSummary",
    "ProjectInspectorError",
    "inspect_project",
]
