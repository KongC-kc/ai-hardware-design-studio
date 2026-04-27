from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from packages.core.validators.validate_ir import validate_ir


@dataclass(frozen=True)
class ConfirmChangePlanResult:
    success: bool
    mode: str
    written: bool
    ir_path: str | None
    validation: dict[str, Any]
    hardware_design_ir: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def confirm_change_plan(
    preview: Mapping[str, Any],
    project_path: Path | str | None = None,
    workspace_root: Path | str = Path("workspace"),
) -> ConfirmChangePlanResult:
    """Validate and write a confirmed hardware design IR from a preview JSON object."""

    ir = build_hardware_design_ir(preview)
    validation = validate_ir(ir)
    validation_payload = _validation_to_dict(validation)
    if not validation.is_valid:
        return ConfirmChangePlanResult(
            success=False,
            mode="confirmed_ir_write",
            written=False,
            ir_path=None,
            validation=validation_payload,
            hardware_design_ir=None,
        )

    output_path = _resolve_output_path(ir, project_path, workspace_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(ir, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ConfirmChangePlanResult(
        success=True,
        mode="confirmed_ir_write",
        written=True,
        ir_path=str(output_path),
        validation=validation_payload,
        hardware_design_ir=ir,
    )


def build_hardware_design_ir(preview: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a preview-only HardwareDesignIRPreview object into the V1 IR shape."""

    target = str(preview.get("target") or "hardware design")
    project_name = _project_name_from_preview(preview, target)
    modules = _list_of_mappings(preview.get("proposed_modules"))
    nets = _list_of_mappings(preview.get("proposed_nets"))

    return {
        "meta": {
            "name": project_name,
            "version": "0.1.0",
            "description": f"Confirmed IR generated from preview for {target}",
        },
        "requirements": {
            "input": _requirement_inputs(preview, nets),
            "output": _requirement_outputs(nets),
            "power_input": _power_input(preview),
            "features": _features(modules, preview),
        },
        "blocks": [_block_from_module(module) for module in modules],
        "power_tree": _power_tree(modules, preview),
        "connections": _connections(modules, nets),
        "design_rules": {
            "decoupling_required": True,
            "power_flags_required": True,
            "erc_must_pass": True,
        },
    }


def _project_name_from_preview(preview: Mapping[str, Any], target: str) -> str:
    estimated_files = preview.get("estimated_files_to_modify")
    if isinstance(estimated_files, list):
        for item in estimated_files:
            if not isinstance(item, str):
                continue
            normalized = item.replace("\\", "/")
            parts = normalized.split("/")
            if len(parts) >= 3 and parts[0] == "workspace":
                return _safe_identifier(parts[1])
    return _safe_identifier(_project_name_from_target(target))


def _project_name_from_target(target: str) -> str:
    upper = target.upper()
    if "RP2040" in upper:
        prefix = "rp2040"
    elif "ESP32-S3" in upper or "ESP32S3" in upper:
        prefix = "esp32_s3"
    elif "STM32F103" in upper:
        prefix = "stm32f103"
    else:
        prefix = "hardware"

    if "控制板" in target or "control" in target.lower():
        suffix = "control_board"
    elif "开发板" in target or "dev" in target.lower():
        suffix = "dev_board"
    elif "最小系统" in target or "minimum" in target.lower():
        suffix = "minimum_system"
    else:
        suffix = "design"
    return f"{prefix}_{suffix}"


def _safe_identifier(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "hardware_design"


def _requirement_inputs(preview: Mapping[str, Any], nets: list[Mapping[str, Any]]) -> list[str]:
    inputs: list[str] = []
    power_input = _power_input(preview)
    if power_input != "TBD":
        inputs.append(power_input)
    for net in nets:
        net_name = str(net.get("name", ""))
        if net_name.startswith("USB_D"):
            inputs.append("USB data")
    return _unique(inputs)


def _requirement_outputs(nets: list[Mapping[str, Any]]) -> list[str]:
    outputs: list[str] = []
    for net in nets:
        net_type = str(net.get("type", ""))
        net_name = str(net.get("name", ""))
        if net_type == "output" or net_name in {"RGB_DATA", "DISPLAY_IO"}:
            outputs.append(net_name)
    return _unique(outputs)


def _power_input(preview: Mapping[str, Any]) -> str:
    for sheet in _list_of_mappings(preview.get("proposed_sheets")):
        if sheet.get("name") != "Power":
            continue
        purpose = str(sheet.get("purpose", ""))
        if "USB-C" in purpose:
            return "USB-C"
        if "USB" in purpose:
            return "USB"
    for net in _list_of_mappings(preview.get("proposed_nets")):
        if net.get("name") == "VBUS":
            return "USB"
    return "TBD"


def _features(modules: list[Mapping[str, Any]], preview: Mapping[str, Any]) -> list[str]:
    features = [str(module.get("id")) for module in modules if module.get("id")]
    features.extend(
        str(item) for item in preview.get("confirmation_items", []) if isinstance(item, str)
    )
    return _unique(features)


def _block_from_module(module: Mapping[str, Any]) -> dict[str, Any]:
    module_id = _safe_identifier(str(module.get("id") or "module"))
    role = str(module.get("role") or module.get("type") or "module")
    block: dict[str, Any] = {
        "id": module_id,
        "type": role,
        "part": f"PLACEHOLDER_{module_id.upper()}",
        "interfaces": [_interface_name(module_id, role)],
    }
    if role in {"mcu", "memory", "clock", "debug", "connector", "input", "indicator"}:
        block["power_nets"] = ["3V3"]
    if module_id == "power_input":
        block["power_nets"] = ["VBUS"]
    if module_id == "voltage_regulation":
        block["input_net"] = "VBUS"
        block["output_net"] = "3V3"
    return block


def _interface_name(module_id: str, role: str) -> str:
    if module_id == "swd_header":
        return "SWD"
    if "usb" in module_id or module_id == "power_input":
        return "USB"
    if "rgb" in module_id:
        return "RGB"
    if "button" in module_id:
        return "GPIO"
    if "display" in module_id:
        return "DISPLAY"
    return role.upper()


def _power_tree(
    modules: list[Mapping[str, Any]],
    preview: Mapping[str, Any],
) -> list[dict[str, Any]]:
    block_ids = [_safe_identifier(str(module.get("id") or "module")) for module in modules]
    powered_children = [
        block_id
        for block_id in block_ids
        if block_id not in {"power_input", "voltage_regulation", "decoupling"}
    ]
    return [
        {
            "net": "VBUS",
            "source": _power_input(preview),
            "children": ["voltage_regulation"] if "voltage_regulation" in block_ids else [],
        },
        {
            "net": "3V3",
            "source": "voltage_regulation",
            "children": powered_children,
        },
    ]


def _connections(
    modules: list[Mapping[str, Any]],
    nets: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    block_ids = {_safe_identifier(str(module.get("id") or "module")) for module in modules}
    if not block_ids:
        return []

    mcu_id = _first_existing(
        block_ids,
        ["rp2040_core", "esp32_s3_core", "stm32f103_core", "mcu_core"],
    )
    if mcu_id is None:
        return []

    connections: list[dict[str, str]] = []
    for net in nets:
        net_name = str(net.get("name") or "")
        source_block = _source_block_for_net(net_name, block_ids)
        if source_block is None or source_block == mcu_id:
            continue
        connections.append(
            {
                "from": f"{source_block}.{_pin_for_net(net_name)}",
                "to": f"{mcu_id}.{_pin_for_net(net_name)}",
                "net": net_name,
            }
        )
    return connections


def _source_block_for_net(net_name: str, block_ids: set[str]) -> str | None:
    candidates_by_net = {
        "SWDIO": ["swd_header"],
        "SWCLK": ["swd_header"],
        "BUTTON_INPUTS": ["button_inputs"],
        "RGB_DATA": ["rgb_leds"],
        "DISPLAY_IO": ["display_connector"],
        "RESET_N": ["reset_button"],
        "USB_D_P": ["power_input", "usb_to_uart_or_native_usb"],
        "USB_D_N": ["power_input", "usb_to_uart_or_native_usb"],
    }
    return _first_existing(block_ids, candidates_by_net.get(net_name, []))


def _first_existing(block_ids: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in block_ids:
            return candidate
    return None


def _pin_for_net(net_name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", net_name).strip("_") or "PIN"


def _resolve_output_path(
    ir: Mapping[str, Any],
    project_path: Path | str | None,
    workspace_root: Path | str,
) -> Path:
    if project_path is not None:
        return Path(project_path) / "hardware_design_ir.json"
    project_name = str(ir["meta"]["name"])
    return Path(workspace_root) / project_name / "hardware_design_ir.json"


def _validation_to_dict(validation: Any) -> dict[str, Any]:
    return {
        "is_valid": validation.is_valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
    }


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
