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

## Inspect an Existing KiCad Project

The project inspector reads an existing KiCad project directory and prints a JSON summary without modifying any KiCad files:

```powershell
npm run inspect-project -- "E:\ninx_git\projectNinx"
```

The summary includes the project name, root path, discovered `.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `sym-lib-table`, `fp-lib-table`, hierarchical sheet references, and warnings for missing project markers or unresolved sheet files.

## Parse a Hardware Design Request

The MVP design request parser turns natural-language hardware requirements into deterministic JSON and a design plan. It is currently a rules/template implementation, not an LLM call:

```powershell
npm run parse-design -- "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。"
```

The output contains:

- `parsed_request`: raw request, target, MCU, power, interfaces, IO, required schematic blocks, assumptions, open questions, and risk notes.
- `design_plan`: schematic blocks, recommended flow, future files expected to change after confirmation, required user confirmations, and the next action.

This stage is read-only. It does not modify KiCad files or generate schematic artifacts. The stable Python boundary is `parse_design_request(raw_text)` and `create_design_plan(parsed_request, project_inspection_summary=None)`. The desktop app also has a reserved TypeScript API wrapper in `apps/desktop/src/services/designRequestApi.ts`.

## Preview a KiCad Change Plan

The MVP change planner combines the parsed request, design plan, and optional project inspection summary into preview-only hardware design IR JSON. It forecasts sheets, modules, nets, risks, confirmation items, and estimated files for a future confirmed step, but it does not modify KiCad files:

```powershell
npm run plan-changes -- "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。" --project "E:\ninx_git\projectNinx"
```

Python entry:

```powershell
python scripts/plan_changes.py "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。" --project "E:\ninx_git\projectNinx"
```

The output has `mode: "preview_only"` and `next_action: "confirm_change_plan_before_ir_write"`. Missing `.kicad_pro`, `.kicad_sch`, or `.kicad_pcb` files are reported as risks instead of hard failures. The desktop app has a reserved TypeScript API wrapper in `apps/desktop/src/services/changePlannerApi.ts`.

## Confirm a Change Plan into IR

After reviewing a preview, confirm it into a validated `hardware_design_ir.json` file:

```powershell
python scripts/confirm_change_plan.py preview.json --project "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run confirm-change-plan -- preview.json --project "E:\ninx_git\projectNinx"
```

This command converts `HardwareDesignIRPreview` into the formal V1 hardware design IR, runs `validate_ir`, and writes only `hardware_design_ir.json` when validation succeeds. If validation fails, it returns structured JSON with `success: false`, does not write the IR file, and never touches `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`.

## Generate Minimal KiCad Artifacts

After `hardware_design_ir.json` is confirmed, generate the minimal deterministic KiCad artifacts:

```powershell
python scripts/generate_kicad_artifacts.py "E:\ninx_git\projectNinx\hardware_design_ir.json" --project "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run generate-kicad-artifacts -- "E:\ninx_git\projectNinx\hardware_design_ir.json" --project "E:\ninx_git\projectNinx"
```

This command runs `validate_ir` before generation and writes only:

- `<project_name>.kicad_pro`
- `<project_name>.kicad_sch`
- `reports/generation_report.json`

It does not generate `.kicad_pcb` and does not run layout. Existing target files are not overwritten unless `--overwrite` is provided. Failures return structured JSON with `success: false`, `written_files: []`, and `errors`.

## Export Schematic SVG

After KiCad artifacts are generated, export a schematic SVG through the controlled tool wrapper:

```powershell
python scripts/export_schematic_svg.py "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run export-schematic-svg -- "E:\ninx_git\projectNinx"
```

The input can be either a project directory or a `.kicad_sch` file. The command detects `kicad-cli`, runs `sch export svg`, and writes:

- `exports/schematic.svg`

If `kicad-cli` is missing or no `.kicad_sch` can be found, the command returns structured JSON with `success: false` and does not crash. This step never modifies `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`, and it never generates `.kicad_pcb`.

## Pipeline Orchestrator

Run the full pipeline in one step:

```powershell
python scripts/run_pipeline.py "E:\ninx_git\projectNinx" --overwrite
```

NPM entry:

```powershell
npm run run-pipeline -- "E:\ninx_git\projectNinx" --overwrite
```

The pipeline chains six steps in order:

1. `generate_kicad_artifacts` — generates `.kicad_pro`, `.kicad_sch`, `reports/generation_report.json`
2. `export_schematic_svg` — exports `exports/schematic.svg`
3. `run_erc` — runs ERC through `kicad-cli`
4. `parse_erc_diagnostics` — normalizes ERC report
5. `explain_erc_report` — generates rule-based explanations
6. `suggest_erc_fixes` — generates proposal-only fix suggestions

Each step calls existing modules without re-implementing logic. The pipeline stops on the first failure and always writes `reports/pipeline_report.json` with the status of every step attempted. The `--ir` flag accepts an explicit IR path; it defaults to `<project_path>/hardware_design_ir.json`.

## Run KiCad Schematic ERC

After a deterministic schematic artifact exists, run schematic ERC through the controlled tool wrapper:

```powershell
python scripts/run_erc.py "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run run-erc -- "E:\ninx_git\projectNinx"
```

The input can be either a project directory or a `.kicad_sch` file. The command detects `kicad-cli`, runs only `sch erc`, and writes:

- `reports/erc_report.json`
- `reports/erc_raw.log`

If `kicad-cli` or a schematic file is missing, the command returns structured JSON with `success: false` and does not crash. This step never modifies `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`, and it does not run PCB DRC.

## Parse ERC Diagnostics

Normalize an existing ERC report into stable diagnostics JSON for GUI display and future report explanation:

```powershell
python scripts/parse_erc_diagnostics.py "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run parse-erc-diagnostics -- "E:\ninx_git\projectNinx"
```

The input can be either a project directory, a `reports` directory, or `reports/erc_report.json`. This command does not run `kicad-cli`; it only reads the existing report and writes `reports/erc_diagnostics.json`. Unknown KiCad JSON shapes are parsed defensively: available fields are preserved, missing fields become `null`, and a malformed item is skipped without failing the whole parse.

## Explain ERC Diagnostics

Create a rule-based explanation report from normalized diagnostics:

```powershell
python scripts/explain_erc_report.py "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run explain-erc-report -- "E:\ninx_git\projectNinx"
```

This command reads only `reports/erc_diagnostics.json` and writes `reports/erc_explanation.json`. It does not read the raw KiCad `erc_report.json`, does not run `kicad-cli`, and does not call a real LLM. The first rule set covers `PIN_NOT_CONNECTED`, `POWER_INPUT_NOT_DRIVEN`, `CONFLICTING_OUTPUTS`, and unknown diagnostics through a fallback explanation.

## Suggest ERC Fixes

Create proposal-only fix suggestions from normalized diagnostics and optional explanation reports:

```powershell
python scripts/suggest_erc_fixes.py "E:\ninx_git\projectNinx"
```

NPM entry:

```powershell
npm run suggest-erc-fixes -- "E:\ninx_git\projectNinx"
```

This command reads `reports/erc_diagnostics.json` and, when present, `reports/erc_explanation.json`. It writes only `reports/erc_suggested_fixes.json`. It does not run `kicad-cli`, does not modify `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, and does not edit `hardware_design_ir.json`.

Every fix is a proposal with `auto_applicable: false` and `requires_user_confirmation: true`. The first rule set covers `PIN_NOT_CONNECTED`, `POWER_INPUT_NOT_DRIVEN`, `CONFLICTING_OUTPUTS`, and `GENERIC_UNKNOWN` fallback proposals. Missing diagnostics return structured failure. Missing explanations produce a warning and fall back to diagnostics-only suggestions.

## Read Reports Through Service Boundary

The desktop app exposes a report-reading boundary in `apps/desktop/src/services/reportService.ts`. It returns a unified `ReportReadResult` for:

- `reports/erc_diagnostics.json`
- `reports/erc_explanation.json`
- `reports/erc_suggested_fixes.json`
- `reports/generation_report.json`
- `reports/pipeline_report.json`

The desktop backend also exposes a read-only Tauri command:

```ts
invoke("read_report", {
  projectPath: "E:\\ninx_git\\projectNinx",
  kind: "erc_diagnostics"
})
```

`kind` is whitelisted to `erc_diagnostics`, `erc_explanation`, `erc_suggested_fixes`, `generation_report`, and `pipeline_report`, which map only to files under `<project_path>/reports/`. The command rejects path-like kinds and `..` traversal, returns a structured empty state when a report is missing, and never reads arbitrary project files. The frontend service keeps a mock reader for tests and non-Tauri fallback.

## V1 Boundary

V1 does not implement a PCB editor, general autorouter, complete PCB layout generator, or complex simulation stack. Those belong to later versions through constraints, templates, and deterministic generation.
