# KiCad Pipeline

V1 treats KiCad as the compiler and verification backend. The design source of truth is the IR.

## Pipeline

1. Load `hardware_design_ir.json`.
2. Validate structure and references.
3. Create `workspace/<project_name>/`.
4. Generate `<project_name>.kicad_pro`.
5. Generate `<project_name>.kicad_sch`.
6. Create `reports/`, `exports/`, and `bom/`.
7. Run ERC through `packages/tools/kicad_cli/runner.py` when `kicad-cli` is available.
8. Export PDF, SVG, BOM, and netlist when the toolchain supports it.
9. Return machine-readable reports for AI explanation.

## kicad-cli Policy

- Never assume `kicad-cli` exists.
- Detect it with `shutil.which`.
- Return clear command metadata.
- In mock mode, generate placeholder reports and exports.
- Keep all shell command execution inside `packages/tools`.

## Generated Artifacts

Generated files live under `workspace/`. They can be regenerated from IR and should not be edited by the AI directly.
