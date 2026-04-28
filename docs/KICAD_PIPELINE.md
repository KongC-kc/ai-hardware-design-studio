# KiCad Pipeline

V1 treats KiCad as the compiler and verification backend. The design source of truth is the IR.

## Pipeline

1. Load `hardware_design_ir.json`.
2. Validate structure and references.
3. Create `workspace/<project_name>/`.
4. Generate `<project_name>.kicad_pro`.
5. Generate `<project_name>.kicad_sch`.
6. Create `reports/`, `exports/`, and `bom/`.
7. Export `exports/schematic.svg` through `packages/tools/kicad_cli/svg_exporter.py` when `kicad-cli` is available.
8. Run schematic ERC through `packages/tools/kicad_cli/erc_runner.py` when `kicad-cli` is available.
9. Parse ERC diagnostics, explain, and suggest fixes.
10. Return machine-readable reports for AI explanation.

### Pipeline Orchestrator

`packages/pipeline/orchestrator.py` chains all steps into a single entry point:

```
generate_kicad_artifacts
→ export_schematic_svg
→ run_erc
→ parse_erc_diagnostics
→ explain_erc_report
→ suggest_erc_fixes
```

Run it:

```powershell
python scripts/run_pipeline.py "E:\ninx_git\projectNinx" --overwrite
```

or:

```powershell
npm run run-pipeline -- "E:\ninx_git\projectNinx" --overwrite
```

The orchestrator stops on first failure and always writes `reports/pipeline_report.json` with `completed_steps`, `failed_step`, per-step `details`, and aggregated `errors`/`warnings`.

## Read-Only Project Inspection

`packages/tools/project_inspector` provides a read-only inspector for existing KiCad project directories. It recursively detects:

- `.kicad_pro`
- `.kicad_sch`
- `.kicad_pcb`
- `sym-lib-table`
- `fp-lib-table`

It also parses schematic sheet metadata enough to report `Sheetname` and `Sheetfile` references. This is intentionally an inspection layer only: it does not invoke `kicad-cli`, write generated artifacts, or modify KiCad project files.

Run it from the repository root:

```powershell
npm run inspect-project -- "E:\ninx_git\projectNinx"
```

The desktop app has a reserved TypeScript API wrapper in `apps/desktop/src/services/projectInspectorApi.ts`. A future Tauri command named `inspect_project` should call the Python inspector through the backend/tool boundary and return the same JSON shape to React.

## Requirement Parsing and Design Planning

`packages/agent/design_request` provides the MVP requirement-structuring layer. It accepts natural-language hardware design text and produces deterministic JSON through two stable functions:

- `parse_design_request(raw_text)`: returns structured design intent with target, MCU, power, interfaces, IO, schematic blocks, assumptions, open questions, and risk notes.
- `create_design_plan(parsed_request, project_inspection_summary=None)`: returns a design plan that can be reviewed before IR generation or KiCad artifact generation.

Run it from the repository root:

```powershell
npm run parse-design -- "做一个 STM32F103 最小系统板，USB 供电，带 8 个 GPIO 排针和一个 I2C 接口。"
```

This phase does not write KiCad files. `files_expected_to_change` in the plan is a future-change forecast for the next confirmed step, not a file-write operation. A later LLM-backed parser should preserve the same JSON shape and function boundary so the GUI and tests can continue to use the deterministic parser as a fallback.

## Preview-Only Change Planning

`packages/agent/change_planner` provides the MVP change-planning layer. It consumes:

- `parsed_request` from `parse_design_request(raw_text)`
- `design_plan` from `create_design_plan(parsed_request, project_inspection_summary=None)`
- optional `projectInspectionSummary` from `packages/tools/project_inspector`

It returns `HardwareDesignIRPreview` JSON with:

- `ir_version`
- `mode: "preview_only"`
- `source`
- `target`
- `proposed_sheets`
- `proposed_modules`
- `proposed_nets`
- `estimated_files_to_modify`
- `risks`
- `confirmation_items`
- `next_action: "confirm_change_plan_before_ir_write"`

Run it from the repository root:

```powershell
npm run plan-changes -- "我要做一个 RP2040 控制板，USB-C 供电，12 个按键输入，4 路 RGB，预留 SWD。" --project "E:\ninx_git\projectNinx"
```

The preview layer is intentionally non-destructive. Missing `.kicad_pro`, `.kicad_sch`, or `.kicad_pcb` files are converted to risks and warnings in the JSON output. The next confirmed step should write or update `hardware_design_ir.json` only; KiCad files still must be emitted by deterministic generator code.

## Confirmed IR Writing

`packages/agent/confirm_change_plan` converts reviewed `HardwareDesignIRPreview` JSON into the formal V1 `hardware_design_ir.json` structure. It keeps a hard boundary between preview and confirmed IR:

- Input: preview-only JSON from the change planner
- Validation: existing `packages/core/validators/validate_ir.py`
- Success output: `hardware_design_ir.json`
- Failure output: structured JSON with validation errors and no file write

Run it from the repository root:

```powershell
python scripts/confirm_change_plan.py preview.json --project "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run confirm-change-plan -- preview.json --project "E:\ninx_git\projectNinx"
```

When `--project` is provided, the IR is written to `<project>/hardware_design_ir.json`. Without `--project`, it is written to `workspace/<project_name>/hardware_design_ir.json`. This step never writes `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`; those remain deterministic generator outputs for a later confirmed stage.

## Controlled KiCad Artifact Generation

`packages/generator/kicad/artifact_generator.py` is the narrow, controlled entry point for generating KiCad artifacts from a confirmed `hardware_design_ir.json`. It always runs `validate_ir` first and only writes files through deterministic generator code.

Run it from the repository root:

```powershell
python scripts/generate_kicad_artifacts.py "E:\ninx_git\projectNinx\hardware_design_ir.json" --project "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run generate-kicad-artifacts -- "E:\ninx_git\projectNinx\hardware_design_ir.json" --project "E:\ninx_git\projectNinx"
```

This stage writes only:

- `<project_name>.kicad_pro`
- `<project_name>.kicad_sch`
- `reports/generation_report.json`

It does not create `.kicad_pcb`, does not run layout, and does not call `kicad-cli`. Existing output files are protected by default; pass `--overwrite` to replace them. The JSON result includes `planned_files` before generation and `written_files` after generation.

## Controlled Schematic SVG Export

`packages/tools/kicad_cli/svg_exporter.py` is the controlled entry point for exporting a schematic SVG. It accepts either a project directory or a `.kicad_sch` file, resolves the schematic path, detects `kicad-cli`, and runs `sch export svg`.

Run it from the repository root:

```powershell
python scripts/export_schematic_svg.py "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run export-schematic-svg -- "E:\ninx_git\projectNinx"
```

The JSON result includes:

- `success`
- `mode: "export_schematic_svg"`
- `project_path`
- `schematic_path`
- `svg_path`
- `kicad_cli_found`
- `errors`
- `warnings`

The command writes `exports/schematic.svg`. If `kicad-cli` is missing or no `.kicad_sch` can be found, it returns `success: false` with structured errors instead of raising an uncaught exception. It does not modify `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`, and it never generates `.kicad_pcb`.

## Controlled Schematic ERC

`packages/tools/kicad_cli/erc_runner.py` is the controlled entry point for running KiCad ERC. It accepts either a project directory or a `.kicad_sch` file, resolves the schematic path, detects `kicad-cli`, and runs only schematic ERC. PCB DRC is intentionally out of scope for this stage.

Run it from the repository root:

```powershell
python scripts/run_erc.py "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run run-erc -- "E:\ninx_git\projectNinx"
```

The JSON result includes:

- `success`
- `mode: "run_erc"`
- `project_path`
- `schematic_path`
- `report_path`
- `raw_log_path`
- `kicad_cli_found`
- `errors`
- `warnings`

The command writes `reports/erc_report.json` and `reports/erc_raw.log`. If `kicad-cli` is missing or no `.kicad_sch` can be found, it returns `success: false` with structured errors instead of raising an uncaught exception. It does not modify `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`, and it never generates `.kicad_pcb`.

## ERC Diagnostics Normalization

`packages/tools/kicad_cli/erc_diagnostics.py` parses an existing `reports/erc_report.json` into a stable diagnostics format for GUI display and future `explain_report` work. It does not call `kicad-cli`; it only reads the report and optional raw log, then writes `reports/erc_diagnostics.json`.

Run it from the repository root:

```powershell
python scripts/parse_erc_diagnostics.py "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run parse-erc-diagnostics -- "E:\ninx_git\projectNinx"
```

The input can be a project directory, a `reports` directory, or the report JSON file itself. The normalized output contains:

- `success`
- `mode: "parse_erc_diagnostics"`
- `source_report`
- `diagnostics_path`
- `summary`
- `diagnostics`
- `errors`
- `warnings`

Each diagnostic receives a stable `erc-###` id plus normalized `severity`, `code`, `message`, schematic context fields, optional `location`, and the original `raw` item. Unknown KiCad JSON shapes are handled defensively: fields are extracted when present, missing fields become `null`, and a malformed single diagnostic creates a warning instead of failing the whole parse.

## Rule-Based ERC Explanation

`packages/agent/report_explainer/erc_explainer.py` is the first `explain_report` boundary. It reads only `reports/erc_diagnostics.json` and writes `reports/erc_explanation.json`; it does not read the raw KiCad `erc_report.json`, does not invoke `kicad-cli`, and does not call a real LLM.

Run it from the repository root:

```powershell
python scripts/explain_erc_report.py "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run explain-erc-report -- "E:\ninx_git\projectNinx"
```

The output contains:

- `success`
- `mode: "explain_erc_report"`
- `source`
- `output`
- `summary`
- `explanations`
- `errors`
- `warnings`

The MVP rule set covers `PIN_NOT_CONNECTED`, `POWER_INPUT_NOT_DRIVEN`, `CONFLICTING_OUTPUTS`, and `GENERIC_UNKNOWN`. Unknown diagnostic codes use the fallback rule and still produce plain-language context, likely causes, suggested fixes, and a `requires_user_confirmation` flag.

## Rule-Based ERC Fix Suggestions

`packages/agent/report_explainer/erc_fix_suggester.py` is the first `suggest_erc_fixes` boundary. It reads `reports/erc_diagnostics.json` and optionally reads `reports/erc_explanation.json`, then writes `reports/erc_suggested_fixes.json`.

Run it from the repository root:

```powershell
python scripts/suggest_erc_fixes.py "E:\ninx_git\projectNinx"
```

or:

```powershell
npm run suggest-erc-fixes -- "E:\ninx_git\projectNinx"
```

This stage is proposal-only. It does not run `kicad-cli`, does not modify `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, and does not write `hardware_design_ir.json`. Every generated fix has `auto_applicable: false` and `requires_user_confirmation: true`.

The output contains:

- `success`
- `mode: "suggest_erc_fixes"`
- `sources`
- `output`
- `summary`
- `fixes`
- `errors`
- `warnings`

The MVP rule set covers:

- `PIN_NOT_CONNECTED` -> an `add_connection` IR-change proposal with a `TODO_CONFIRM_TARGET`
- `POWER_INPUT_NOT_DRIVEN` -> an `add_power_source_or_power_flag` IR-change proposal
- `CONFLICTING_OUTPUTS` -> a conflict-resolution IR-change proposal
- `GENERIC_UNKNOWN` and unknown codes -> a manual review proposal

Missing `erc_diagnostics.json` returns structured failure and writes no suggestion file. Missing `erc_explanation.json` returns success with a warning and falls back to diagnostics-only suggestions.

## Report Service Boundary

`apps/desktop/src/services/reportService.ts` is the GUI/Agent boundary for reading generated reports. Consumers should use `ReportReadResult` instead of directly binding UI state to individual report file shapes.

Supported report kinds:

- `erc_diagnostics`: reads `reports/erc_diagnostics.json`
- `erc_explanation`: reads `reports/erc_explanation.json`
- `erc_suggested_fixes`: reads `reports/erc_suggested_fixes.json`
- `generation_report`: reads `reports/generation_report.json`
- `pipeline_report`: reads `reports/pipeline_report.json`

The service currently provides a mock `ReportFileReader` and returns structured empty states when a report is missing:

```json
{
  "success": false,
  "kind": "erc_diagnostics",
  "path": ".../reports/erc_diagnostics.json",
  "data": null,
  "errors": ["Report file not found or not available in mock reader: ..."],
  "warnings": []
}
```

The Tauri backend exposes the same boundary through:

```ts
invoke("read_report", {
  projectPath: "E:\\ninx_git\\projectNinx",
  kind: "erc_diagnostics"
})
```

`kind` is a strict whitelist:

- `erc_diagnostics` -> `<project_path>/reports/erc_diagnostics.json`
- `erc_explanation` -> `<project_path>/reports/erc_explanation.json`
- `erc_suggested_fixes` -> `<project_path>/reports/erc_suggested_fixes.json`
- `generation_report` -> `<project_path>/reports/generation_report.json`
- `pipeline_report` -> `<project_path>/reports/pipeline_report.json`

The backend rejects path-like `kind` values, rejects `..` traversal, canonicalizes existing report paths, and verifies the resolved file stays inside the project `reports` directory before reading. Missing reports return `success: false` with `data: null` and structured errors. This layer does not invoke `kicad-cli`, does not read KiCad project files directly, and does not call a real LLM.

## kicad-cli Policy

- Never assume `kicad-cli` exists.
- Detect it with `shutil.which`.
- Return clear command metadata.
- In mock mode, generate placeholder reports and exports.
- Keep all shell command execution inside `packages/tools`.

## Generated Artifacts

Generated files live under `workspace/`. They can be regenerated from IR and should not be edited by the AI directly.
