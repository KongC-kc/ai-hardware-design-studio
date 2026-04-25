# Agent Actions

The agent must output action JSON. It must not directly edit complex KiCad files.

## V1 Actions

- `create_project`
- `analyze_user_requirement`
- `generate_architecture`
- `generate_design_ir`
- `update_design_ir`
- `validate_ir`
- `generate_kicad_schematic`
- `run_erc`
- `export_schematic_pdf`
- `export_schematic_svg`
- `export_bom`
- `export_netlist`
- `explain_erc_report`
- `suggest_design_fix`
- `open_in_kicad`

## Example

```json
{
  "action": "generate_design_ir",
  "params": {
    "project_name": "usb_i2s_fpga",
    "requirement": "USB-C input, I2S output, FPGA processing, dual low-jitter oscillators"
  }
}
```

## Execution Contract

Actions are declarative. A runner may validate, approve, and execute them. The tool layer owns external commands. The generator owns KiCad file emission.
