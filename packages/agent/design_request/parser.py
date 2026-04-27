from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedDesignRequest:
    raw_request: str
    target: str
    mcu: dict[str, str]
    power: dict[str, str | list[str]]
    interfaces: list[dict[str, Any]]
    io: list[dict[str, Any]]
    required_schematic_blocks: list[str]
    assumptions: list[str]
    open_questions: list[str]
    risk_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_design_request(raw_text: str) -> ParsedDesignRequest:
    """Parse a natural-language hardware request with deterministic MVP rules."""

    request = _repair_common_windows_mojibake(raw_text).strip()
    if not request:
        raise ValueError("raw_text must not be empty")

    mcu = _detect_mcu(request)
    target = _detect_target(request, mcu)
    power = _detect_power(request)
    interfaces = _detect_interfaces(request)
    io = _detect_io(request)
    required_blocks = _required_blocks(mcu, interfaces, io)
    assumptions = _assumptions(mcu, power)
    open_questions = _open_questions(mcu, interfaces, io)
    risk_notes = _risk_notes(mcu, power, interfaces, io)

    return ParsedDesignRequest(
        raw_request=request,
        target=target,
        mcu=mcu,
        power=power,
        interfaces=interfaces,
        io=io,
        required_schematic_blocks=required_blocks,
        assumptions=assumptions,
        open_questions=open_questions,
        risk_notes=risk_notes,
    )


def _detect_mcu(request: str) -> dict[str, str]:
    upper = request.upper()
    if "RP2040" in upper:
        return {
            "part": "RP2040",
            "family": "RP2040",
            "vendor": "Raspberry Pi",
            "confidence": "high",
        }
    if "STM32F103" in upper:
        return {
            "part": "STM32F103",
            "family": "STM32F1",
            "vendor": "STMicroelectronics",
            "confidence": "high",
        }
    if "ESP32-S3" in upper or "ESP32S3" in upper:
        return {
            "part": "ESP32-S3",
            "family": "ESP32-S3",
            "vendor": "Espressif",
            "confidence": "high",
        }
    return {
        "part": "TBD",
        "family": "TBD",
        "vendor": "TBD",
        "confidence": "low",
    }


def _detect_target(request: str, mcu: dict[str, str]) -> str:
    part = mcu["part"]
    for board_kind in ("最小系统板", "开发板", "控制板"):
        if board_kind in request and part != "TBD":
            return f"{part} {board_kind}"
    if part != "TBD":
        return f"{part} hardware design"
    return "hardware design"


def _detect_power(request: str) -> dict[str, str | list[str]]:
    lower = request.lower()
    if "usb-c" in lower or "type-c" in lower or "type c" in lower:
        return {
            "input": "USB-C",
            "connector": "Type-C receptacle",
            "required_rails": ["5V input", "3.3V system rail"],
        }
    if "usb" in lower:
        return {
            "input": "USB",
            "connector": "USB connector type TBD",
            "required_rails": ["5V input", "3.3V system rail"],
        }
    return {
        "input": "TBD",
        "connector": "TBD",
        "required_rails": ["3.3V system rail"],
    }


def _detect_interfaces(request: str) -> list[dict[str, Any]]:
    interfaces: list[dict[str, Any]] = []
    if "SWD" in request.upper():
        interfaces.append({"type": "SWD", "count": 1, "notes": "debug/programming header"})
    if "GPIO" in request.upper() and "排针" in request:
        interfaces.append(
            {
                "type": "GPIO header",
                "count": _count_before_keyword(request, "GPIO", default=1),
                "notes": "pinout TBD",
            }
        )
    if "I2C" in request.upper() or "I²C" in request.upper():
        interfaces.append(
            {
                "type": "I2C",
                "count": _count_before_keyword(request, "I2C", default=1),
                "notes": "voltage and pull-ups TBD",
            }
        )
    if "屏幕接口" in request or "显示接口" in request:
        interfaces.append({"type": "display", "count": 1, "notes": "connector protocol TBD"})
    return interfaces


def _detect_io(request: str) -> list[dict[str, Any]]:
    io: list[dict[str, Any]] = []
    if "按键输入" in request:
        io.append(
            {
                "type": "button_input",
                "count": _count_before_keyword(request, "按键", default=1),
                "notes": "user key inputs",
            }
        )
    if "RGB" in request.upper():
        io.append(
            {
                "type": "rgb_led",
                "count": _count_before_keyword(request, "RGB", default=1),
                "notes": "addressing method TBD",
            }
        )
    if "复位按键" in request or "复位键" in request:
        io.append({"type": "reset_button", "count": 1, "notes": "manual reset input"})
    return io


def _required_blocks(
    mcu: dict[str, str],
    interfaces: list[dict[str, Any]],
    io: list[dict[str, Any]],
) -> list[str]:
    blocks = [
        "mcu_core",
        "power_input",
        "voltage_regulation",
        "decoupling",
        "reset_boot",
    ]
    part = mcu["part"]
    if part == "RP2040":
        blocks.extend(["rp2040_qspi_flash", "rp2040_clock"])
    if part == "STM32F103":
        blocks.append("stm32_boot_and_clock")
    if part == "ESP32-S3":
        blocks.extend(["usb_to_uart_or_native_usb", "esp32_rf_and_antenna"])

    interface_types = {str(item["type"]) for item in interfaces}
    io_types = {str(item["type"]) for item in io}
    if "SWD" in interface_types:
        blocks.append("swd_debug_header")
    if "GPIO header" in interface_types:
        blocks.append("gpio_headers")
    if "I2C" in interface_types:
        blocks.append("i2c_connector")
    if "display" in interface_types:
        blocks.append("display_connector")
    if "button_input" in io_types:
        blocks.append("button_matrix_or_inputs")
    if "rgb_led" in io_types:
        blocks.append("rgb_led_driver_or_chain")
    if "reset_button" in io_types:
        blocks.append("reset_button")
    return _unique(blocks)


def _assumptions(mcu: dict[str, str], power: dict[str, str | list[str]]) -> list[str]:
    assumptions = [
        "Use 3.3V logic unless the user specifies another voltage.",
        "Do not modify KiCad files until the user confirms the design plan.",
        "Generate schematic IR before deterministic KiCad artifact generation.",
    ]
    if power["input"] in {"USB", "USB-C"}:
        assumptions.append(
            "USB input is used for power first; data role is confirmation-dependent."
        )
    if mcu["part"] == "ESP32-S3":
        assumptions.append(
            "ESP32-S3 may be implemented as either module or bare chip after confirmation."
        )
    return assumptions


def _open_questions(
    mcu: dict[str, str],
    interfaces: list[dict[str, Any]],
    io: list[dict[str, Any]],
) -> list[str]:
    questions: list[str] = []
    part = mcu["part"]
    if part == "TBD":
        questions.append("confirm target MCU or module")
    if part == "RP2040":
        questions.append("confirm RP2040 package, crystal choice, and QSPI flash size")
    if part == "STM32F103":
        questions.append("confirm exact STM32F103 package and flash/RAM size")
    if part == "ESP32-S3":
        questions.append("confirm ESP32-S3 module vs bare chip and antenna constraints")

    interface_types = {str(item["type"]) for item in interfaces}
    io_types = {str(item["type"]) for item in io}
    if "display" in interface_types:
        questions.append("confirm display connector type and bus")
    if "I2C" in interface_types:
        questions.append("confirm I2C connector pinout and pull-up voltage")
    if "GPIO header" in interface_types:
        questions.append("confirm GPIO header pinout and connector pitch")
    if "rgb_led" in io_types:
        questions.append("confirm RGB LED type and drive method")
    if "button_input" in io_types:
        questions.append("confirm button wiring style and debounce requirements")
    return _unique(questions)


def _risk_notes(
    mcu: dict[str, str],
    power: dict[str, str | list[str]],
    interfaces: list[dict[str, Any]],
    io: list[dict[str, Any]],
) -> list[str]:
    notes = [
        "Pin allocation must be checked before schematic generation.",
        "Power budget and regulator current margin must be confirmed.",
    ]
    if power["input"] == "USB-C":
        notes.append("USB-C designs need correct CC resistor handling and connector protection.")
    if mcu["part"] == "RP2040":
        notes.append("RP2040 requires external flash and a verified boot/debug circuit.")
    if mcu["part"] == "STM32F103":
        notes.append("STM32 boot mode and clock source choices affect programming workflow.")
    if mcu["part"] == "ESP32-S3":
        notes.append("ESP32-S3 RF layout and antenna keepout can drive PCB constraints.")

    interface_types = {str(item["type"]) for item in interfaces}
    io_types = {str(item["type"]) for item in io}
    if "display" in interface_types:
        notes.append("Display connector choice may consume high-speed or many GPIO pins.")
    if "rgb_led" in io_types:
        notes.append("RGB LEDs may require current budgeting and level/drive checks.")
    return _unique(notes)


def _count_before_keyword(request: str, keyword: str, default: int) -> int:
    escaped = re.escape(keyword)
    patterns = [
        rf"(?P<count>\d+|[一二两三四五六七八九十]+)\s*(?:个|路|组)?\s*{escaped}",
        rf"{escaped}\s*(?P<count>\d+|[一二两三四五六七八九十]+)\s*(?:个|路|组)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if match:
            return _parse_count(match.group("count"), default)
    return default


def _parse_count(value: str, default: int) -> int:
    if value.isdigit():
        return int(value)
    chinese_numbers = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if value in chinese_numbers:
        return chinese_numbers[value]
    if value.startswith("十") and len(value) == 2:
        return 10 + chinese_numbers.get(value[1], 0)
    if "十" in value:
        tens, ones = value.split("十", maxsplit=1)
        return chinese_numbers.get(tens, 1) * 10 + chinese_numbers.get(ones, 0)
    return default


def _repair_common_windows_mojibake(value: str) -> str:
    if _contains_cjk(value) or not any(ord(char) > 127 for char in value):
        return value

    candidates = [value]
    for source_encoding in ("cp1252", "latin-1"):
        for target_encoding in ("gb18030", "gbk"):
            try:
                candidates.append(value.encode(source_encoding).decode(target_encoding))
            except UnicodeError:
                continue

    return max(candidates, key=_cjk_character_count)


def _contains_cjk(value: str) -> bool:
    return _cjk_character_count(value) > 0


def _cjk_character_count(value: str) -> int:
    return sum(1 for char in value if "\u4e00" <= char <= "\u9fff")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
