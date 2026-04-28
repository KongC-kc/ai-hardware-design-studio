from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ErcSuggestedFixesResult:
    success: bool
    mode: str
    sources: JsonObject
    output: str | None
    summary: JsonObject
    fixes: list[JsonObject]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FixRule:
    title: str
    proposal_type: str
    patch_op: str
    plain_language: str
    risk_level: str


RULES: dict[str, FixRule] = {
    "PIN_NOT_CONNECTED": FixRule(
        title="Connect unconnected pin",
        proposal_type="ir_change",
        patch_op="add_connection",
        plain_language=(
            "This pin is currently not connected. Confirm the intended destination before applying any change."
        ),
        risk_level="medium",
    ),
    "POWER_INPUT_NOT_DRIVEN": FixRule(
        title="Drive power input",
        proposal_type="ir_change",
        patch_op="add_power_source_or_power_flag",
        plain_language=(
            "This power input is not driven. Confirm the real power source before adding a regulator, connector rail, "
            "or power flag proposal."
        ),
        risk_level="medium",
    ),
    "CONFLICTING_OUTPUTS": FixRule(
        title="Resolve conflicting outputs",
        proposal_type="ir_change",
        patch_op="resolve_conflicting_outputs",
        plain_language=(
            "Multiple outputs may be driving the same net. Confirm the intended single driver, tri-state behavior, "
            "or net split before applying any change."
        ),
        risk_level="high",
    ),
    "GENERIC_UNKNOWN": FixRule(
        title="Review ERC diagnostic",
        proposal_type="manual_review",
        patch_op="review_diagnostic",
        plain_language=(
            "This ERC item is not covered by a specific fix rule yet. Review the diagnostic fields before proposing "
            "an IR change."
        ),
        risk_level="medium",
    ),
}


def suggest_erc_fixes(project_path: Path) -> ErcSuggestedFixesResult:
    """Create proposal-only ERC fix suggestions from normalized diagnostics and optional explanations."""

    diagnostics_path, explanation_path, output_path, path_errors = _resolve_paths(project_path)
    if path_errors:
        return _failure(errors=path_errors)

    assert diagnostics_path is not None
    assert explanation_path is not None
    assert output_path is not None

    try:
        diagnostics_data = json.loads(diagnostics_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return _failure(
            sources={"diagnostics": str(diagnostics_path), "explanation": None},
            output=str(output_path),
            errors=[f"Failed to parse ERC diagnostics JSON: {exc}"],
        )

    diagnostics = diagnostics_data.get("diagnostics", [])
    warnings: list[str] = []
    if not isinstance(diagnostics, list):
        diagnostics = []
        warnings.append("Diagnostics field is not a list; no fix proposals were generated.")

    explanation_source, explanation_lookup, explanation_warnings = _load_explanations(explanation_path)
    warnings.extend(explanation_warnings)

    fixes: list[JsonObject] = []
    for item in diagnostics:
        if not isinstance(item, dict):
            warnings.append("Skipped non-object diagnostic while suggesting ERC fixes.")
            continue
        fixes.append(_suggest_fix(len(fixes) + 1, item, explanation_lookup))

    result = ErcSuggestedFixesResult(
        success=True,
        mode="suggest_erc_fixes",
        sources={
            "diagnostics": str(diagnostics_path),
            "explanation": explanation_source,
        },
        output=str(output_path),
        summary={
            "fix_count": len(fixes),
            "auto_applicable_count": 0,
            "requires_confirmation_count": len(fixes),
        },
        fixes=fixes,
        errors=[],
        warnings=_dedupe(warnings),
    )
    _write_output(output_path, result)
    return result


def _resolve_paths(input_path: Path) -> tuple[Path | None, Path | None, Path | None, list[str]]:
    resolved = input_path.expanduser().resolve()
    if not resolved.exists():
        return None, None, None, [f"Project path, reports directory, or erc_diagnostics.json not found: {resolved}"]

    if resolved.is_file():
        if resolved.name != "erc_diagnostics.json":
            return None, None, None, [f"Input file must be erc_diagnostics.json: {resolved}"]
        reports_dir = resolved.parent
    elif resolved.is_dir():
        reports_dir = resolved if resolved.name == "reports" else resolved / "reports"
    else:
        return None, None, None, [f"Input must be a project directory, reports directory, or erc_diagnostics.json: {resolved}"]

    diagnostics_path = reports_dir / "erc_diagnostics.json"
    explanation_path = reports_dir / "erc_explanation.json"
    output_path = reports_dir / "erc_suggested_fixes.json"
    if not diagnostics_path.exists():
        return None, None, None, [f"erc_diagnostics.json not found at {diagnostics_path}"]
    return diagnostics_path.resolve(), explanation_path.resolve(), output_path.resolve(), []


def _load_explanations(explanation_path: Path) -> tuple[str | None, dict[str, JsonObject], list[str]]:
    if not explanation_path.exists():
        return None, {}, [f"erc_explanation.json not found at {explanation_path}; generated fixes from diagnostics only."]

    try:
        explanation_data = json.loads(explanation_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return (
            str(explanation_path),
            {},
            [f"Failed to parse ERC explanation JSON; generated fixes from diagnostics only: {exc}"],
        )

    explanations = explanation_data.get("explanations", [])
    if not isinstance(explanations, list):
        return str(explanation_path), {}, ["Explanation field is not a list; generated fixes from diagnostics only."]

    lookup: dict[str, JsonObject] = {}
    warnings: list[str] = []
    for item in explanations:
        if not isinstance(item, dict):
            warnings.append("Skipped non-object ERC explanation while suggesting fixes.")
            continue
        diagnostic_id = _string_or_none(item.get("diagnostic_id"))
        if diagnostic_id is not None:
            lookup[diagnostic_id] = item
    return str(explanation_path), lookup, warnings


def _suggest_fix(index: int, diagnostic: JsonObject, explanation_lookup: dict[str, JsonObject]) -> JsonObject:
    diagnostic_id = _string_or_default(diagnostic.get("id"), "unknown")
    code = _string_or_default(diagnostic.get("code"), "GENERIC_UNKNOWN").upper()
    rule = RULES.get(code, RULES["GENERIC_UNKNOWN"])
    explanation = explanation_lookup.get(diagnostic_id, {})

    return {
        "id": f"fix-{index:03d}",
        "diagnostic_id": diagnostic_id,
        "severity": _string_or_default(diagnostic.get("severity"), "info"),
        "title": rule.title,
        "target": _target_from_diagnostic(diagnostic),
        "proposal_type": rule.proposal_type,
        "proposed_ir_patch": _proposed_ir_patch(rule.patch_op, diagnostic, code),
        "plain_language": _plain_language(rule, explanation),
        "risk_level": rule.risk_level,
        "auto_applicable": False,
        "requires_user_confirmation": True,
    }


def _target_from_diagnostic(diagnostic: JsonObject) -> JsonObject:
    return {
        "file": _string_or_none(diagnostic.get("file")),
        "symbol": _string_or_none(diagnostic.get("symbol")),
        "pin": _string_or_none(diagnostic.get("pin")),
        "net": _string_or_none(diagnostic.get("net")),
    }


def _proposed_ir_patch(op: str, diagnostic: JsonObject, code: str) -> JsonObject:
    symbol = _string_or_none(diagnostic.get("symbol"))
    pin = _string_or_none(diagnostic.get("pin"))
    net = _string_or_default(diagnostic.get("net"), "TODO_CONFIRM_NET")
    endpoint = f"{symbol}.{pin}" if symbol is not None and pin is not None else "TODO_CONFIRM_SOURCE"

    if op == "add_connection":
        return {
            "op": op,
            "from": endpoint,
            "to": "TODO_CONFIRM_TARGET",
            "net": net,
        }
    if op == "add_power_source_or_power_flag":
        return {
            "op": op,
            "target": endpoint,
            "net": net,
            "source": "TODO_CONFIRM_POWER_SOURCE",
        }
    if op == "resolve_conflicting_outputs":
        return {
            "op": op,
            "net": net,
            "preferred_driver": "TODO_CONFIRM_DRIVER",
            "resolution": "TODO_CONFIRM_SPLIT_OR_DIRECTION_CONTROL",
        }
    return {
        "op": "review_diagnostic",
        "diagnostic_id": _string_or_default(diagnostic.get("id"), "unknown"),
        "code": code,
    }


def _plain_language(rule: FixRule, explanation: JsonObject) -> str:
    suggested_fixes = explanation.get("suggested_fixes")
    if isinstance(suggested_fixes, list) and suggested_fixes:
        first_fix = _string_or_none(suggested_fixes[0])
        if first_fix is not None:
            return f"{rule.plain_language} Related explanation suggestion: {first_fix}"
    return rule.plain_language


def _failure(
    errors: list[str],
    sources: JsonObject | None = None,
    output: str | None = None,
    warnings: list[str] | None = None,
) -> ErcSuggestedFixesResult:
    return ErcSuggestedFixesResult(
        success=False,
        mode="suggest_erc_fixes",
        sources=sources or {"diagnostics": None, "explanation": None},
        output=output,
        summary={
            "fix_count": 0,
            "auto_applicable_count": 0,
            "requires_confirmation_count": 0,
        },
        fixes=[],
        errors=errors,
        warnings=warnings or [],
    )


def _write_output(path: Path, result: ErcSuggestedFixesResult) -> None:
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
