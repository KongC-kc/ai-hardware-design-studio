from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


REQUIRED_TOP_LEVEL_KEYS = (
    "meta",
    "requirements",
    "blocks",
    "power_tree",
    "connections",
    "design_rules",
)

REQUIRED_META_KEYS = ("name", "version", "description")
REQUIRED_RULE_KEYS = ("decoupling_required", "power_flags_required", "erc_must_pass")


@dataclass(frozen=True)
class ValidationResult:
    """Result returned by the lightweight V1 IR validator."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    def raise_for_errors(self) -> None:
        if self.errors:
            message = "\n".join(f"- {error}" for error in self.errors)
            raise ValueError(f"Invalid hardware design IR:\n{message}")


def load_ir(path: Path | str) -> dict[str, Any]:
    """Load a hardware design IR JSON file."""

    ir_path = Path(path)
    with ir_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"IR root must be a JSON object: {ir_path}")
    return data


def validate_ir_file(path: Path | str) -> ValidationResult:
    """Load and validate a hardware design IR JSON file."""

    try:
        ir = load_ir(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return ValidationResult(is_valid=False, errors=[str(exc)], warnings=[])
    return validate_ir(ir)


def validate_ir(ir: Mapping[str, Any]) -> ValidationResult:
    """Validate the V1 IR contract without external dependencies."""

    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in ir:
            errors.append(f"Missing top-level key: {key}")

    meta = ir.get("meta")
    if not isinstance(meta, Mapping):
        errors.append("meta must be an object")
    else:
        for key in REQUIRED_META_KEYS:
            if not isinstance(meta.get(key), str) or not meta.get(key):
                errors.append(f"meta.{key} must be a non-empty string")

    requirements = ir.get("requirements")
    if not isinstance(requirements, Mapping):
        errors.append("requirements must be an object")
    else:
        _validate_string_list(requirements, "input", "requirements", errors)
        _validate_string_list(requirements, "output", "requirements", errors)
        _validate_string_list(requirements, "features", "requirements", errors)
        if not isinstance(requirements.get("power_input"), str):
            errors.append("requirements.power_input must be a string")

    block_ids = _validate_blocks(ir.get("blocks"), errors, warnings)
    _validate_power_tree(ir.get("power_tree"), errors)
    _validate_connections(ir.get("connections"), block_ids, errors)
    _validate_design_rules(ir.get("design_rules"), errors)

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)


def _validate_string_list(
    owner: Mapping[str, Any], key: str, path: str, errors: list[str]
) -> None:
    value = owner.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{path}.{key} must be a list of strings")


def _validate_blocks(value: Any, errors: list[str], warnings: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append("blocks must be a non-empty list")
        return set()

    block_ids: set[str] = set()
    for index, block in enumerate(value):
        path = f"blocks[{index}]"
        if not isinstance(block, Mapping):
            errors.append(f"{path} must be an object")
            continue

        block_id = block.get("id")
        block_type = block.get("type")
        if not isinstance(block_id, str) or not block_id:
            errors.append(f"{path}.id must be a non-empty string")
            continue
        if block_id in block_ids:
            errors.append(f"Duplicate block id: {block_id}")
        block_ids.add(block_id)

        if not isinstance(block_type, str) or not block_type:
            errors.append(f"{path}.type must be a non-empty string")

        part = block.get("part")
        if isinstance(part, str) and part.startswith("PLACEHOLDER_"):
            warnings.append(f"{path}.part is a placeholder: {part}")

        if "power_nets" in block and not _is_string_list(block["power_nets"]):
            errors.append(f"{path}.power_nets must be a list of strings")

    return block_ids


def _validate_power_tree(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("power_tree must be a list")
        return

    for index, node in enumerate(value):
        path = f"power_tree[{index}]"
        if not isinstance(node, Mapping):
            errors.append(f"{path} must be an object")
            continue
        if not isinstance(node.get("net"), str):
            errors.append(f"{path}.net must be a string")
        if not isinstance(node.get("source"), str):
            errors.append(f"{path}.source must be a string")
        if not _is_string_list(node.get("children")):
            errors.append(f"{path}.children must be a list of strings")


def _validate_connections(value: Any, block_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("connections must be a list")
        return

    for index, connection in enumerate(value):
        path = f"connections[{index}]"
        if not isinstance(connection, Mapping):
            errors.append(f"{path} must be an object")
            continue
        for endpoint_key in ("from", "to"):
            endpoint = connection.get(endpoint_key)
            if not isinstance(endpoint, str) or "." not in endpoint:
                errors.append(f"{path}.{endpoint_key} must use block.pin format")
                continue
            block_id = endpoint.split(".", 1)[0]
            if block_id not in block_ids:
                errors.append(f"{path}.{endpoint_key} references unknown block: {block_id}")
        if not isinstance(connection.get("net"), str) or not connection.get("net"):
            errors.append(f"{path}.net must be a non-empty string")


def _validate_design_rules(value: Any, errors: list[str]) -> None:
    if not isinstance(value, Mapping):
        errors.append("design_rules must be an object")
        return

    for key in REQUIRED_RULE_KEYS:
        if not isinstance(value.get(key), bool):
            errors.append(f"design_rules.{key} must be a boolean")


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)
