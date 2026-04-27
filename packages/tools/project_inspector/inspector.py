from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DetectedSheet:
    name: str
    file: str
    source_schematic: str
    resolved_path: str
    exists: bool


@dataclass(frozen=True)
class ProjectInspectionSummary:
    project_name: str
    project_root: str
    project_files: list[str]
    schematic_files: list[str]
    pcb_files: list[str]
    symbol_library_tables: list[str]
    footprint_library_tables: list[str]
    detected_sheets: list[DetectedSheet]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ProjectInspectorError(ValueError):
    """Raised when a project path cannot be inspected."""


ParsedNode = str | list["ParsedNode"]


def inspect_project(project_path: Path | str) -> ProjectInspectionSummary:
    """Inspect a KiCad project directory without modifying any project files."""

    project_root = Path(project_path).expanduser().resolve()
    if not project_root.exists():
        raise ProjectInspectorError(f"Project path does not exist: {project_root}")
    if not project_root.is_dir():
        raise ProjectInspectorError(f"Project path must be a directory: {project_root}")

    project_files = _find_files(project_root, "*.kicad_pro")
    schematic_files = _find_files(project_root, "*.kicad_sch")
    pcb_files = _find_files(project_root, "*.kicad_pcb")
    symbol_library_tables = _find_named_files(project_root, "sym-lib-table")
    footprint_library_tables = _find_named_files(project_root, "fp-lib-table")

    warnings = _build_project_warnings(project_root, project_files, schematic_files, pcb_files)
    detected_sheets = _detect_sheets(project_root, schematic_files, warnings)
    project_name = _detect_project_name(project_root, project_files)

    return ProjectInspectionSummary(
        project_name=project_name,
        project_root=str(project_root),
        project_files=project_files,
        schematic_files=schematic_files,
        pcb_files=pcb_files,
        symbol_library_tables=symbol_library_tables,
        footprint_library_tables=footprint_library_tables,
        detected_sheets=detected_sheets,
        warnings=warnings,
    )


def _find_files(project_root: Path, pattern: str) -> list[str]:
    return sorted(path.relative_to(project_root).as_posix() for path in project_root.rglob(pattern))


def _find_named_files(project_root: Path, filename: str) -> list[str]:
    return sorted(
        path.relative_to(project_root).as_posix()
        for path in project_root.rglob("*")
        if path.is_file() and path.name == filename
    )


def _detect_project_name(project_root: Path, project_files: list[str]) -> str:
    root_project_files = [Path(path) for path in project_files if len(Path(path).parts) == 1]
    if root_project_files:
        return root_project_files[0].stem
    if project_files:
        return Path(project_files[0]).stem
    return project_root.name


def _build_project_warnings(
    project_root: Path,
    project_files: list[str],
    schematic_files: list[str],
    pcb_files: list[str],
) -> list[str]:
    warnings: list[str] = []
    root_project_files = [path for path in project_files if len(Path(path).parts) == 1]

    if not root_project_files:
        warnings.append("No .kicad_pro file found in project root.")
    if len(root_project_files) > 1:
        joined = ", ".join(root_project_files)
        warnings.append(f"Multiple .kicad_pro files found in project root: {joined}.")
    if not schematic_files:
        warnings.append("No .kicad_sch files found.")
    if not pcb_files:
        warnings.append("No .kicad_pcb files found.")

    if not project_root.exists():
        warnings.append(f"Project root does not exist: {project_root}.")

    return warnings


def _detect_sheets(
    project_root: Path,
    schematic_files: Iterable[str],
    warnings: list[str],
) -> list[DetectedSheet]:
    detected: list[DetectedSheet] = []
    for source_relative in schematic_files:
        source_path = project_root / source_relative
        try:
            content = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.append(f"Could not read schematic as UTF-8: {source_relative}.")
            continue

        try:
            parsed = _parse_s_expression(content)
        except ProjectInspectorError as exc:
            warnings.append(f"Could not parse schematic sheet metadata in {source_relative}: {exc}")
            continue

        for sheet in _find_sheet_nodes(parsed):
            sheet_name = _find_property_value(sheet, "Sheetname")
            sheet_file = _find_property_value(sheet, "Sheetfile")
            if sheet_file is None:
                continue

            resolved_path = (source_path.parent / sheet_file).resolve()
            exists = resolved_path.exists()
            file_value = _relative_path_or_original(resolved_path, project_root, sheet_file)
            name_value = sheet_name or Path(sheet_file).stem
            if not exists:
                warnings.append(
                    f"Sheet file referenced by {source_relative} was not found: {sheet_file}."
                )
            detected.append(
                DetectedSheet(
                    name=name_value,
                    file=file_value,
                    source_schematic=source_relative,
                    resolved_path=str(resolved_path),
                    exists=exists,
                )
            )

    return sorted(
        detected,
        key=lambda sheet: (sheet.source_schematic, sheet.file, sheet.name),
    )


def _relative_path_or_original(path: Path, project_root: Path, original: str) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return original.replace("\\", "/")


def _parse_s_expression(content: str) -> list[ParsedNode]:
    root: list[ParsedNode] = []
    stack: list[list[ParsedNode]] = [root]

    for token in _tokenize_s_expression(content):
        if token == "(":
            node: list[ParsedNode] = []
            stack[-1].append(node)
            stack.append(node)
            continue
        if token == ")":
            if len(stack) == 1:
                raise ProjectInspectorError("unexpected closing parenthesis")
            stack.pop()
            continue
        stack[-1].append(token)

    if len(stack) != 1:
        raise ProjectInspectorError("unclosed parenthesis")
    return root


def _tokenize_s_expression(content: str) -> Iterable[str]:
    index = 0
    length = len(content)
    while index < length:
        char = content[index]
        if char.isspace():
            index += 1
            continue
        if char in "()":
            yield char
            index += 1
            continue
        if char == '"':
            value, index = _read_quoted_string(content, index)
            yield value
            continue

        start = index
        while index < length and not content[index].isspace() and content[index] not in "()":
            index += 1
        yield content[start:index]


def _read_quoted_string(content: str, start_index: int) -> tuple[str, int]:
    index = start_index + 1
    value: list[str] = []
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content):
            value.append(content[index + 1])
            index += 2
            continue
        if char == '"':
            return "".join(value), index + 1
        value.append(char)
        index += 1
    raise ProjectInspectorError("unclosed quoted string")


def _find_sheet_nodes(node: ParsedNode) -> Iterable[list[ParsedNode]]:
    if not isinstance(node, list):
        return
    if node and node[0] == "sheet":
        yield node
    for child in node:
        if isinstance(child, list):
            yield from _find_sheet_nodes(child)


def _find_property_value(node: list[ParsedNode], property_name: str) -> str | None:
    for child in node:
        if (
            isinstance(child, list)
            and len(child) >= 3
            and child[0] == "property"
            and child[1] == property_name
            and isinstance(child[2], str)
        ):
            return child[2]
    return None
