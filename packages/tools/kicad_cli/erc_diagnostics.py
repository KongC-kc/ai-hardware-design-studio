from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


Summary = dict[str, int]
Diagnostic = dict[str, Any]


@dataclass(frozen=True)
class ErcDiagnosticsResult:
    success: bool
    mode: str
    source_report: str | None
    diagnostics_path: str | None
    summary: Summary
    diagnostics: list[Diagnostic]
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_erc_diagnostics(input_path: Path, raw_log_path: Path | None = None) -> ErcDiagnosticsResult:
    """Normalize an existing KiCad ERC report into stable diagnostics JSON."""

    report_path, diagnostics_path, resolve_errors = _resolve_report_input(input_path)
    empty_summary = _create_summary([])
    if resolve_errors:
        return ErcDiagnosticsResult(
            success=False,
            mode="parse_erc_diagnostics",
            source_report=str(report_path) if report_path is not None and report_path.exists() else None,
            diagnostics_path=str(diagnostics_path) if diagnostics_path is not None else None,
            summary=empty_summary,
            diagnostics=[],
            errors=resolve_errors,
            warnings=[],
        )

    assert report_path is not None
    assert diagnostics_path is not None

    warnings: list[str] = []
    try:
        report_data = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        errors = [f"Failed to parse ERC report JSON: {exc}"]
        result = ErcDiagnosticsResult(
            success=False,
            mode="parse_erc_diagnostics",
            source_report=str(report_path),
            diagnostics_path=str(diagnostics_path),
            summary=empty_summary,
            diagnostics=[],
            errors=errors,
            warnings=warnings,
        )
        _write_diagnostics(diagnostics_path, result)
        return result

    if raw_log_path is not None and not raw_log_path.exists():
        warnings.append(f"Optional raw ERC log was not found: {raw_log_path}")

    candidates = _collect_candidates(report_data)
    diagnostics: list[Diagnostic] = []
    for candidate, default_severity in candidates:
        diagnostic = _normalize_candidate(candidate, default_severity, len(diagnostics) + 1)
        if diagnostic is None:
            warnings.append("Skipped unparseable ERC diagnostic entry.")
            continue
        diagnostics.append(diagnostic)

    summary = _create_summary(diagnostics)
    result = ErcDiagnosticsResult(
        success=True,
        mode="parse_erc_diagnostics",
        source_report=str(report_path),
        diagnostics_path=str(diagnostics_path),
        summary=summary,
        diagnostics=diagnostics,
        errors=[],
        warnings=_dedupe(warnings),
    )
    _write_diagnostics(diagnostics_path, result)
    return result


def _resolve_report_input(input_path: Path) -> tuple[Path | None, Path | None, list[str]]:
    resolved = input_path.expanduser().resolve()
    if resolved.suffix == ".json":
        diagnostics_path = resolved.parent / "erc_diagnostics.json"
        if not resolved.exists():
            return resolved, diagnostics_path, [f"ERC report not found: {resolved}"]
        if not resolved.is_file():
            return resolved, diagnostics_path, [f"ERC report path is not a file: {resolved}"]
        return resolved, diagnostics_path, []

    if not resolved.exists():
        return None, None, [f"Project path or erc_report.json not found: {resolved}"]
    if not resolved.is_dir():
        return None, None, [f"Input must be a project directory or erc_report.json: {resolved}"]

    reports_dir = resolved if resolved.name == "reports" else resolved / "reports"
    report_path = reports_dir / "erc_report.json"
    diagnostics_path = reports_dir / "erc_diagnostics.json"
    if not report_path.exists():
        return None, diagnostics_path, [f"erc_report.json not found at {report_path}"]
    return report_path, diagnostics_path, []


def _collect_candidates(
    node: Any,
    default_severity: str | None = None,
    force_candidate: bool = False,
) -> list[tuple[Any, str | None]]:
    candidates: list[tuple[Any, str | None]] = []

    if isinstance(node, dict):
        if _looks_like_diagnostic(node) or (force_candidate and _has_diagnostic_marker(node)):
            return [(node, default_severity)]

        for key, value in node.items():
            key_text = str(key)
            next_default = _severity_from_collection_key(key_text) or default_severity
            is_diagnostic_collection = _is_diagnostic_collection_key(key_text)
            if isinstance(value, list):
                if next_default is not None and all(isinstance(item, str) for item in value):
                    candidates.extend(({"message": item}, next_default) for item in value)
                    continue
                for item in value:
                    collected = _collect_candidates(
                        item,
                        next_default,
                        force_candidate=is_diagnostic_collection,
                    )
                    if collected:
                        candidates.extend(collected)
                    elif is_diagnostic_collection:
                        candidates.append((item, next_default))
            elif isinstance(value, dict):
                candidates.extend(_collect_candidates(value, next_default))
            elif next_default is not None and isinstance(value, str):
                candidates.append(({"message": value}, next_default))
        return candidates

    if isinstance(node, list):
        for item in node:
            candidates.extend(_collect_candidates(item, default_severity))
        return candidates

    if default_severity is not None and isinstance(node, str):
        return [({"message": node}, default_severity)]

    return candidates


def _looks_like_diagnostic(value: dict[Any, Any]) -> bool:
    return _pick_string(value, _message_keys()) is not None or _pick_string(value, _code_keys()) is not None


def _has_diagnostic_marker(value: dict[Any, Any]) -> bool:
    marker_keys = _message_keys() + _code_keys() + _severity_keys()
    return any(_get_case_insensitive(value, key) is not None for key in marker_keys)


def _normalize_candidate(candidate: Any, default_severity: str | None, index: int) -> Diagnostic | None:
    if isinstance(candidate, str):
        candidate = {"message": candidate}
    if not isinstance(candidate, dict):
        return None

    message = _pick_string_deep(candidate, _message_keys())
    code = _pick_string_deep(candidate, _code_keys())
    severity = _normalize_severity(_pick_string(candidate, _severity_keys()) or default_severity)

    if severity is None:
        if message is None and code is None:
            return None
        severity = "info"

    if message is None:
        message = code
    if message is None:
        return None

    if code is None:
        code = f"ERC_{severity.upper()}"

    return {
        "id": f"erc-{index:03d}",
        "severity": severity,
        "code": code,
        "message": message,
        "file": _pick_string_deep(candidate, ["file", "filename", "sheetfile", "source_file", "path"]),
        "sheet": _pick_string_deep(candidate, ["sheet", "sheet_name", "sheetname", "sheet_path"]),
        "symbol": _pick_string_deep(candidate, ["symbol", "symbol_name", "reference", "ref", "component"]),
        "pin": _pick_string_deep(candidate, ["pin", "pin_number", "pin_name"]),
        "net": _pick_string_deep(candidate, ["net", "net_name", "connection"]),
        "location": _extract_location(candidate),
        "raw": candidate,
    }


def _severity_from_collection_key(key: str) -> str | None:
    normalized = key.lower().replace("-", "_")
    if normalized in {"error", "errors"}:
        return "error"
    if normalized in {"warning", "warnings"}:
        return "warning"
    if normalized in {"info", "infos", "information", "notes"}:
        return "info"
    return None


def _is_diagnostic_collection_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {"diagnostic", "diagnostics", "violation", "violations", "issue", "issues", "message", "messages"}


def _normalize_severity(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"error", "err", "fatal", "failure", "failed"}:
        return "error"
    if normalized in {"warning", "warn"}:
        return "warning"
    if normalized in {"info", "information", "notice", "note"}:
        return "info"
    if normalized in {"ok", "pass", "passed", "success", "none"}:
        return None
    return "info"


def _pick_string_deep(value: dict[Any, Any], keys: list[str]) -> str | None:
    direct = _pick_string(value, keys)
    if direct is not None:
        return direct

    for nested_key in ("item", "items", "location", "locations", "source", "sources", "object", "objects"):
        nested = _get_case_insensitive(value, nested_key)
        if isinstance(nested, dict):
            found = _pick_string_deep(nested, keys)
            if found is not None:
                return found
        elif isinstance(nested, list):
            for item in nested:
                if isinstance(item, dict):
                    found = _pick_string_deep(item, keys)
                    if found is not None:
                        return found
    return None


def _pick_string(value: dict[Any, Any], keys: list[str]) -> str | None:
    for key in keys:
        found = _get_case_insensitive(value, key)
        scalar = _stringify_scalar(found)
        if scalar is not None:
            return scalar
    return None


def _get_case_insensitive(value: dict[Any, Any], key: str) -> Any:
    if key in value:
        return value[key]
    key_lower = key.lower()
    for existing_key, existing_value in value.items():
        if isinstance(existing_key, str) and existing_key.lower() == key_lower:
            return existing_value
    return None


def _stringify_scalar(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if isinstance(value, int | float):
        return str(value)
    return None


def _extract_location(value: dict[Any, Any]) -> dict[str, float | None]:
    for key in ("location", "position", "pos", "coordinates", "where"):
        nested = _get_case_insensitive(value, key)
        if isinstance(nested, dict):
            return {
                "x": _coerce_number(_get_case_insensitive(nested, "x")),
                "y": _coerce_number(_get_case_insensitive(nested, "y")),
            }

    return {
        "x": _coerce_number(_get_case_insensitive(value, "x")),
        "y": _coerce_number(_get_case_insensitive(value, "y")),
    }


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _create_summary(diagnostics: list[Diagnostic]) -> Summary:
    return {
        "error_count": sum(1 for item in diagnostics if item.get("severity") == "error"),
        "warning_count": sum(1 for item in diagnostics if item.get("severity") == "warning"),
        "info_count": sum(1 for item in diagnostics if item.get("severity") == "info"),
    }


def _write_diagnostics(path: Path, result: ErcDiagnosticsResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _message_keys() -> list[str]:
    return ["message", "description", "text", "msg", "detail", "details"]


def _code_keys() -> list[str]:
    return ["code", "type", "category", "name", "kind", "test"]


def _severity_keys() -> list[str]:
    return ["severity", "level", "priority"]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
