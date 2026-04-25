# AI Hardware Design Studio

AI Hardware Design Studio is an AI schematic design agent and deterministic KiCad project compiler. It is not a KiCad replacement. V1 focuses on the schematic design loop:

1. User requirement or `hardware_design_ir.json`
2. AI-assisted architecture explanation
3. Structured schematic IR
4. Deterministic KiCad project generation
5. ERC and report interpretation through a tool wrapper
6. PDF/SVG/BOM/netlist export

The AI layer must edit the IR, schema, rules, templates, or generator inputs. KiCad project files are emitted by deterministic Python generator code.

## Repository Layout

```text
apps/desktop/        Tauri + React + TypeScript mock desktop shell
packages/core/       IR schema and validation
packages/agent/      Agent actions, prompts, and planners
packages/generator/  KiCad project, schematic, BOM, and netlist generators
packages/tools/      External command wrappers such as kicad-cli
packages/parts/      Future part library adapters and databases
packages/rules/      Future electrical and schematic rule packs
workspace/           Generated project workspaces
docs/                Architecture and implementation notes
examples/            Example hardware_design_ir.json inputs
scripts/             CLI entry points
tests/               Python mock pipeline tests
```

## Install Dependencies

Python uses the standard library for the V1 mock pipeline:

```powershell
python -m unittest tests/test_mock_pipeline.py
```

Install desktop dependencies:

```powershell
npm install
```

## Run Mock GUI

```powershell
npm run dev:desktop
```

Open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

Optional Tauri shell:

```powershell
npm run tauri:dev
```

## Run Mock Schematic Generator

```powershell
python scripts/generate_schematic_project.py examples/usb_i2s_fpga/hardware_design_ir.json
```

Expected output:

```text
workspace/usb_i2s_fpga/
  usb_i2s_fpga.kicad_pro
  usb_i2s_fpga.kicad_sch
  reports/
  exports/
  bom/
```

## V1 Boundary

V1 does not implement a PCB editor, general autorouter, complete PCB layout generator, or complex simulation stack. Those belong to later versions through constraints, templates, and deterministic generation.
