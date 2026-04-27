from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from packages.agent.design_request.parser import ParsedDesignRequest
from packages.agent.design_request.planner import DesignPlan


@dataclass(frozen=True)
class HardwareDesignIRPreview:
    ir_version: str
    mode: str
    source: dict[str, Any]
    target: str
    proposed_sheets: list[dict[str, Any]]
    proposed_modules: list[dict[str, Any]]
    proposed_nets: list[dict[str, Any]]
    estimated_files_to_modify: list[str]
    risks: list[str]
    confirmation_items: list[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_change_plan_preview(
    parsed_request: ParsedDesignRequest,
    design_plan: DesignPlan,
    project_inspection_summary: Mapping[str, Any] | object | None = None,
) -> HardwareDesignIRPreview:
    """Create a preview-only hardware design IR change plan.

    This function forecasts IR/KiCad changes but never writes KiCad files.
    """

    return HardwareDesignIRPreview(
        ir_version="preview.v1",
        mode="preview_only",
        source=_source(parsed_request, design_plan, project_inspection_summary),
        target=parsed_request.target,
        proposed_sheets=_proposed_sheets(parsed_request),
        proposed_modules=_proposed_modules(parsed_request),
        proposed_nets=_proposed_nets(parsed_request),
        estimated_files_to_modify=_estimated_files_to_modify(
            design_plan,
            project_inspection_summary,
        ),
        risks=_risks(parsed_request, project_inspection_summary),
        confirmation_items=_confirmation_items(parsed_request, design_plan),
        next_action="confirm_change_plan_before_ir_write",
    )


def _source(
    parsed_request: ParsedDesignRequest,
    design_plan: DesignPlan,
    project_inspection_summary: Mapping[str, Any] | object | None,
) -> dict[str, Any]:
    source: dict[str, Any] = {
        "raw_request": parsed_request.raw_request,
        "parser": "rules_template_v1",
        "planner": "rules_template_v1",
        "design_plan_title": design_plan.plan_title,
        "project_inspection": "not_provided",
    }
    if project_inspection_summary is not None:
        source["project_inspection"] = {
            "project_name": _summary_value(project_inspection_summary, "project_name"),
            "project_root": _summary_value(project_inspection_summary, "project_root"),
        }
    return source


def _proposed_sheets(parsed_request: ParsedDesignRequest) -> list[dict[str, Any]]:
    sheets = [
        {
            "name": "Root",
            "purpose": "Top-level schematic integration and sheet symbols.",
            "status": "preview",
        },
        {
            "name": "Power",
            "purpose": f"{parsed_request.power['input']} input and 3.3V regulation.",
            "status": "preview",
        },
        {
            "name": "MCU",
            "purpose": f"{parsed_request.mcu['part']} core, clock, reset, and boot circuitry.",
            "status": "preview",
        },
    ]
    if parsed_request.interfaces or parsed_request.io:
        sheets.append(
            {
                "name": "IO",
                "purpose": "External connectors, controls, LEDs, and debug headers.",
                "status": "preview",
            }
        )
    return sheets


def _proposed_modules(parsed_request: ParsedDesignRequest) -> list[dict[str, Any]]:
    modules = [
        _module("power_input", "power", "USB or external power entry and protection."),
        _module("voltage_regulation", "power", "Regulate input power to system rails."),
        _module("decoupling", "power", "Bulk and local decoupling capacitors."),
    ]

    part = parsed_request.mcu["part"]
    if part == "RP2040":
        modules.extend(
            [
                _module("rp2040_core", "mcu", "RP2040 MCU, reset, boot select, and GPIO banks."),
                _module("rp2040_qspi_flash", "memory", "External QSPI flash for RP2040 boot."),
                _module("rp2040_clock", "clock", "RP2040 crystal or clock input."),
            ]
        )
    elif part == "ESP32-S3":
        modules.extend(
            [
                _module("esp32_s3_core", "mcu", "ESP32-S3 module or chip core circuitry."),
                _module(
                    "esp32_rf_antenna",
                    "rf",
                    "Antenna keepout and RF implementation choice.",
                ),
                _module(
                    "usb_to_uart_or_native_usb",
                    "programming",
                    "Programming and USB data path.",
                ),
            ]
        )
    elif part == "STM32F103":
        modules.extend(
            [
                _module(
                    "stm32f103_core",
                    "mcu",
                    "STM32F103 MCU, reset, boot mode, and GPIO banks.",
                ),
                _module("stm32_boot_clock", "clock", "Boot straps and crystal/clock source."),
            ]
        )
    else:
        modules.append(_module("mcu_core", "mcu", "MCU core pending user selection."))

    for interface in parsed_request.interfaces:
        interface_type = str(interface["type"])
        if interface_type == "SWD":
            modules.append(_module("swd_header", "debug", "SWD programming/debug header."))
        elif interface_type == "GPIO header":
            modules.append(_module("gpio_headers", "connector", "GPIO breakout headers."))
        elif interface_type == "I2C":
            modules.append(_module("i2c_connector", "connector", "I2C connector and pull-ups."))
        elif interface_type == "display":
            modules.append(
                _module("display_connector", "connector", "Display connector interface.")
            )

    for io_item in parsed_request.io:
        io_type = str(io_item["type"])
        if io_type == "button_input":
            modules.append(
                _module("button_inputs", "input", "Button GPIO or matrix input network.")
            )
        elif io_type == "rgb_led":
            modules.append(
                _module("rgb_leds", "indicator", "RGB LED chain or discrete RGB drive.")
            )
        elif io_type == "reset_button":
            modules.append(_module("reset_button", "input", "Manual reset button circuit."))

    return _unique_by_id(modules)


def _proposed_nets(parsed_request: ParsedDesignRequest) -> list[dict[str, Any]]:
    nets = [
        _net("VBUS", "power", "USB/external input voltage."),
        _net("+3V3", "power", "Regulated 3.3V system rail."),
        _net("GND", "power", "System ground."),
        _net("RESET_N", "control", "MCU reset line."),
    ]

    if parsed_request.power["input"] in {"USB", "USB-C"}:
        nets.extend(
            [
                _net("USB_D_P", "usb", "USB D+ signal, if data is enabled."),
                _net("USB_D_N", "usb", "USB D- signal, if data is enabled."),
            ]
        )
    if _has_feature(parsed_request.interfaces, "SWD"):
        nets.extend(
            [
                _net("SWDIO", "debug", "SWD data signal."),
                _net("SWCLK", "debug", "SWD clock signal."),
            ]
        )
    if _has_feature(parsed_request.interfaces, "I2C"):
        nets.extend(
            [
                _net("I2C_SCL", "interface", "I2C clock signal."),
                _net("I2C_SDA", "interface", "I2C data signal."),
            ]
        )
    if _has_feature(parsed_request.interfaces, "display"):
        nets.append(
            _net("DISPLAY_IO", "interface", "Display bus signals pending connector choice.")
        )
    if _has_feature(parsed_request.io, "button_input"):
        nets.append(_net("BUTTON_INPUTS", "input", "Button input signals pending topology."))
    if _has_feature(parsed_request.io, "rgb_led"):
        nets.append(_net("RGB_DATA", "output", "RGB LED data or drive signals pending LED choice."))

    return _unique_by_name(nets)


def _estimated_files_to_modify(
    design_plan: DesignPlan,
    project_inspection_summary: Mapping[str, Any] | object | None,
) -> list[str]:
    if project_inspection_summary is None:
        return list(design_plan.files_expected_to_change)

    project_root = _summary_value(project_inspection_summary, "project_root")
    files = ["hardware_design_ir.json"]
    for key in ("project_files", "schematic_files", "pcb_files"):
        for relative_path in _summary_list(project_inspection_summary, key):
            if project_root:
                files.append(f"{project_root}/{relative_path}".replace("\\", "/"))
            else:
                files.append(relative_path)
    if len(files) == 1:
        files.extend(design_plan.files_expected_to_change)
    return _unique(files)


def _risks(
    parsed_request: ParsedDesignRequest,
    project_inspection_summary: Mapping[str, Any] | object | None,
) -> list[str]:
    risks = list(parsed_request.risk_notes)
    if project_inspection_summary is None:
        risks.append("No project inspection summary provided; existing KiCad context is unknown.")
    else:
        risks.extend(
            f"Project warning: {warning}"
            for warning in _summary_list(project_inspection_summary, "warnings")
        )
        if not _summary_list(project_inspection_summary, "project_files"):
            risks.append("No existing .kicad_pro file is available for update planning.")
        if not _summary_list(project_inspection_summary, "schematic_files"):
            risks.append("No existing .kicad_sch file is available for update planning.")
        if not _summary_list(project_inspection_summary, "pcb_files"):
            risks.append("No existing .kicad_pcb file is available for update planning.")
    return _unique(risks)


def _confirmation_items(parsed_request: ParsedDesignRequest, design_plan: DesignPlan) -> list[str]:
    confirmations = list(design_plan.user_confirmations_required)
    confirmations.append("Confirm MCU concrete package before IR write.")
    confirmations.append("Confirm whether ESD, fuse, and power protection are required.")

    if parsed_request.power["input"] == "USB-C":
        confirmations.append("Confirm whether USB-C is power-only or USB2.0 device.")
    elif parsed_request.power["input"] == "USB":
        confirmations.append("Confirm whether USB data is required or power-only.")

    if _has_feature(parsed_request.io, "button_input"):
        confirmations.append("Confirm whether buttons are direct GPIO inputs or a matrix.")
    if _has_feature(parsed_request.io, "rgb_led"):
        confirmations.append(
            "Confirm whether RGB is WS2812/SK6812-style addressable LEDs or discrete RGB."
        )
    if _has_feature(parsed_request.interfaces, "display"):
        confirmations.append("Confirm display connector type and bus.")

    return _unique(confirmations)


def _module(module_id: str, role: str, description: str) -> dict[str, Any]:
    return {
        "id": module_id,
        "role": role,
        "description": description,
        "status": "preview",
    }


def _net(name: str, net_type: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "type": net_type,
        "description": description,
        "status": "preview",
    }


def _has_feature(items: list[dict[str, Any]], feature_type: str) -> bool:
    return any(str(item.get("type")) == feature_type for item in items)


def _summary_value(summary: Mapping[str, Any] | object, key: str) -> Any:
    if isinstance(summary, Mapping):
        return summary.get(key)
    return getattr(summary, key, None)


def _summary_list(summary: Mapping[str, Any] | object, key: str) -> list[str]:
    value = _summary_value(summary, key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _unique_by_id(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        value_id = str(value["id"])
        if value_id not in seen:
            seen.add(value_id)
            result.append(value)
    return result


def _unique_by_name(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for value in values:
        name = str(value["name"])
        if name not in seen:
            seen.add(name)
            result.append(value)
    return result
