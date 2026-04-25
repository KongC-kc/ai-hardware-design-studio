# Roadmap

## V1: AI Schematic Design Loop

Goal: run the complete schematic intent loop with deterministic mock generation.

- Accept natural language requirement or `hardware_design_ir.json`.
- Produce hardware architecture notes.
- Produce and validate structured schematic IR.
- Generate KiCad project directory, `.kicad_pro`, and `.kicad_sch`.
- Run ERC through a `kicad-cli` wrapper when available.
- Export PDF, SVG, BOM, and netlist through tool wrappers.
- Let AI explain ERC and design issues.
- Provide a desktop GUI for project management, preview, IR viewing, chat, and reports.

## V2: Better Schematic Generation

- Add symbol library mapping.
- Add pin-aware connection generation.
- Add deterministic sheet placement.
- Add design rule packs for common power, clock, and connector checks.
- Add part library adapters.

## V3: Constraint-driven PCB Preparation

- Generate PCB constraints and placement templates.
- Support board templates for known design families.
- Produce layout starting points, not general autorouting.

## Later

- Rich part database integration.
- Optional simulation hooks.
- Collaborative project history.
- Deeper KiCad round-trip inspection.
