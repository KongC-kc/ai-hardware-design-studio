# Hardware Design IR Schema

The hardware design IR is the source of truth for V1. It is stored as JSON and validated before generation.

Schema path:

```text
packages/core/schema/hardware_design_ir.schema.json
```

Example path:

```text
examples/usb_i2s_fpga/hardware_design_ir.json
```

## Top-level Fields

- `meta`: project name, version, and description.
- `requirements`: user-facing requirements captured by the agent.
- `blocks`: logical schematic blocks such as connectors, regulators, bridge ICs, FPGA, and oscillators.
- `power_tree`: named supply rails and their sources and loads.
- `connections`: point-to-point logical nets using `block.pin` endpoints.
- `design_rules`: generation and validation requirements.

## Endpoint Format

Connections use `block_id.pin_name`:

```json
{
  "from": "usb_interface.I2S_BCLK",
  "to": "fpga.I2S_BCLK",
  "net": "I2S_BCLK"
}
```

The validator checks that `usb_interface` and `fpga` exist in `blocks`.

## V1 Rules

V1 validation is deliberately lightweight:

- Required top-level sections must exist.
- Block IDs must be unique.
- Connection endpoints must refer to known block IDs.
- Design rules must include `decoupling_required`, `power_flags_required`, and `erc_must_pass`.

Future schema versions should add pin maps, symbol aliases, package references, electrical types, constraints, and rule severities.
