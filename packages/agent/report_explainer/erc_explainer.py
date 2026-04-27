from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ErcExplanationResult:
    success: bool
    mode: str
    source: str | None
    output: str | None
    summary: JsonObject
    explanations: list[JsonObject]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExplanationRule:
    title: str
    plain_language_template: str
    likely_causes: list[str]
    suggested_fixes: list[str]
    requires_user_confirmation: bool


RULES: dict[str, ExplanationRule] = {
    "PIN_NOT_CONNECTED": ExplanationRule(
        title="Pin is not connected",
        plain_language_template=(
            "{subject} has an unconnected pin{pin_part}{net_part}. This usually means the schematic "
            "is missing an intentional connection, a no-connect marker, or a named net."
        ),
        likely_causes=[
            "The pin was meant to connect to another schematic block but no net was assigned.",
            "The pin is intentionally unused but has no no-connect marker.",
            "A hierarchical sheet or net label did not connect as expected.",
        ],
        suggested_fixes=[
            "Confirm whether the pin should be connected or intentionally unused.",
            "Connect the pin to the intended net if it is required for the design.",
            "Add an explicit no-connect marker only after confirming the pin is intentionally unused.",
        ],
        requires_user_confirmation=True,
    ),
    "POWER_INPUT_NOT_DRIVEN": ExplanationRule(
        title="Power input is not driven",
        plain_language_template=(
            "{subject} is on a power net{net_part}, but ERC did not find a source that drives that "
            "net. The design may need a regulator output, connector power source, or KiCad power flag."
        ),
        likely_causes=[
            "A power rail is labeled but not connected to a regulator, connector, or power source symbol.",
            "KiCad needs a power flag to mark an externally supplied rail as driven.",
            "The intended power source is on another sheet and the net is not connected correctly.",
        ],
        suggested_fixes=[
            "Trace the named rail back to its connector or regulator output.",
            "Add or fix the missing power source connection in the schematic IR/generator input.",
            "Use a power flag only when the rail is truly supplied externally.",
        ],
        requires_user_confirmation=True,
    ),
    "CONFLICTING_OUTPUTS": ExplanationRule(
        title="Conflicting outputs",
        plain_language_template=(
            "{subject} reports multiple outputs driving the same net{net_part}. This can create an "
            "electrical conflict unless the connection is intentionally open-drain, tri-stated, or otherwise protected."
        ),
        likely_causes=[
            "Two push-pull output pins are connected together.",
            "A net label joined signals that were meant to stay separate.",
            "A bidirectional or open-drain interface is missing the correct electrical modeling.",
        ],
        suggested_fixes=[
            "Check every output connected to the net and confirm only one source drives it at a time.",
            "Rename or separate nets that were accidentally joined.",
            "Confirm whether the interface needs open-drain, series resistors, or explicit direction control.",
        ],
        requires_user_confirmation=True,
    ),
    "GENERIC_UNKNOWN": ExplanationRule(
        title="Unknown ERC diagnostic",
        plain_language_template=(
            "{subject} produced an unknown ERC diagnostic{net_part}. Review the original diagnostic "
            "fields before changing the design."
        ),
        likely_causes=[
            "The diagnostic code is not covered by the current rule-based explanation table.",
            "The KiCad ERC output shape or code name may differ from the known templates.",
        ],
        suggested_fixes=[
            "Review the diagnostic message, symbol, pin, sheet, and net fields.",
            "Decide whether this should become a new rule before making schematic changes.",
        ],
        requires_user_confirmation=True,
    ),
}


def explain_erc_report(project_path: Path) -> ErcExplanationResult:
    """Create rule-based explanations from reports/erc_diagnostics.json only."""

    source_path, output_path, errors = _resolve_paths(project_path)
    if errors:
        return ErcExplanationResult(
            success=False,
            mode="explain_erc_report",
            source=str(source_path) if source_path is not None and source_path.exists() else None,
            output=str(output_path) if source_path is not None and source_path.exists() else None,
            summary={},
            explanations=[],
            errors=errors,
            warnings=[],
        )

    assert source_path is not None
    assert output_path is not None

    try:
        diagnostics_data = json.loads(source_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        result = ErcExplanationResult(
            success=False,
            mode="explain_erc_report",
            source=str(source_path),
            output=str(output_path),
            summary={},
            explanations=[],
            errors=[f"Failed to parse ERC diagnostics JSON: {exc}"],
            warnings=[],
        )
        _write_output(output_path, result)
        return result

    diagnostics = diagnostics_data.get("diagnostics", [])
    warnings: list[str] = []
    explanations: list[JsonObject] = []
    if not isinstance(diagnostics, list):
        warnings.append("Diagnostics field is not a list; no explanations were generated.")
        diagnostics = []

    for item in diagnostics:
        if not isinstance(item, dict):
            warnings.append("Skipped non-object diagnostic while explaining ERC report.")
            continue
        explanations.append(_explain_diagnostic(item))

    result = ErcExplanationResult(
        success=True,
        mode="explain_erc_report",
        source=str(source_path),
        output=str(output_path),
        summary=_summary_from_diagnostics(diagnostics_data, explanations),
        explanations=explanations,
        errors=[],
        warnings=_dedupe(warnings),
    )
    _write_output(output_path, result)
    return result


def _resolve_paths(input_path: Path) -> tuple[Path | None, Path | None, list[str]]:
    resolved = input_path.expanduser().resolve()
    if not resolved.exists():
        return None, None, [f"Project path or erc_diagnostics.json not found: {resolved}"]

    if resolved.is_file():
        if resolved.name != "erc_diagnostics.json":
            return None, None, [f"Input file must be erc_diagnostics.json: {resolved}"]
        return resolved, resolved.parent / "erc_explanation.json", []

    if not resolved.is_dir():
        return None, None, [f"Input must be a project directory, reports directory, or erc_diagnostics.json: {resolved}"]

    reports_dir = resolved if resolved.name == "reports" else resolved / "reports"
    source_path = reports_dir / "erc_diagnostics.json"
    output_path = reports_dir / "erc_explanation.json"
    if not source_path.exists():
        return None, None, [f"erc_diagnostics.json not found at {source_path}"]
    return source_path, output_path, []


def _explain_diagnostic(diagnostic: JsonObject) -> JsonObject:
    code = _string_or_default(diagnostic.get("code"), "GENERIC_UNKNOWN").upper()
    rule = RULES.get(code, RULES["GENERIC_UNKNOWN"])
    message = _string_or_default(diagnostic.get("message"), rule.title)

    return {
        "diagnostic_id": _string_or_default(diagnostic.get("id"), "unknown"),
        "severity": _string_or_default(diagnostic.get("severity"), "info"),
        "title": rule.title if code in RULES else message,
        "plain_language": _render_plain_language(rule, diagnostic),
        "likely_causes": rule.likely_causes,
        "suggested_fixes": rule.suggested_fixes,
        "requires_user_confirmation": rule.requires_user_confirmation,
    }


def _render_plain_language(rule: ExplanationRule, diagnostic: JsonObject) -> str:
    return rule.plain_language_template.format(
        subject=_subject(diagnostic),
        pin_part=_pin_part(diagnostic),
        net_part=_net_part(diagnostic),
    )


def _subject(diagnostic: JsonObject) -> str:
    symbol = _string_or_none(diagnostic.get("symbol"))
    file_name = _string_or_none(diagnostic.get("file"))
    sheet = _string_or_none(diagnostic.get("sheet"))

    if symbol is not None:
        return f"{symbol}"
    if sheet is not None:
        return f"Sheet {sheet}"
    if file_name is not None:
        return f"File {file_name}"
    return "This ERC item"


def _pin_part(diagnostic: JsonObject) -> str:
    pin = _string_or_none(diagnostic.get("pin"))
    if pin is None:
        return ""
    return f" ({pin})"


def _net_part(diagnostic: JsonObject) -> str:
    net = _string_or_none(diagnostic.get("net"))
    if net is None:
        return ""
    return f" on net {net}"


def _summary_from_diagnostics(diagnostics_data: JsonObject, explanations: list[JsonObject]) -> JsonObject:
    summary = diagnostics_data.get("summary")
    if isinstance(summary, dict):
        result: JsonObject = dict(summary)
    else:
        result = {}
    result["explanation_count"] = len(explanations)
    return result


def _write_output(path: Path, result: ErcExplanationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if isinstance(value, int | float):
        return str(value)
    return None


def _string_or_default(value: Any, default: str) -> str:
    return _string_or_none(value) or default


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
