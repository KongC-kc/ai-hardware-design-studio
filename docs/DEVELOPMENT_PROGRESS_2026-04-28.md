# Development Progress - 2026-04-28

## Current Status

The project now has a guarded MVP pipeline from requirement parsing to deterministic KiCad artifact generation, ERC execution, normalized diagnostics, and rule-based explanation reports.

The important architectural boundary is preserved:

- KiCad files are generated only by deterministic generator code.
- Agent code writes structured IR, previews, plans, diagnostics, and reports.
- No AI code directly edits `.kicad_sch`, `.kicad_pcb`, or `.kicad_pro`.
- External tool execution stays under `packages/tools`.
- `kicad-cli` is optional and detected before use.

## Implemented MVP Steps

1. Read-only KiCad project inspection
   - Module: `packages/tools/project_inspector`
   - CLI: `npm run inspect-project -- "<project_path>"`
   - Detects `.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `sym-lib-table`, `fp-lib-table`, and sheet references.

2. Rule-based design request parsing and planning
   - Module: `packages/agent/design_request`
   - CLI: `npm run parse-design -- "<hardware requirement>"`
   - Supports RP2040, STM32F103, and ESP32-S3 style starter requests.

3. Preview-only KiCad change planning
   - Module: `packages/agent/change_planner`
   - CLI: `npm run plan-changes -- "<request>" --project "<project_path>"`
   - Produces `HardwareDesignIRPreview` with risks and confirmation items.

4. Confirmed IR writing
   - Module: `packages/agent/confirm_change_plan`
   - CLI: `npm run confirm-change-plan -- <preview_json_path> --project <project_path>`
   - Validates before writing `hardware_design_ir.json`.

5. Deterministic minimal KiCad artifact generation
   - Module: `packages/generator/kicad/artifact_generator.py`
   - CLI: `npm run generate-kicad-artifacts -- <hardware_design_ir.json> --project <project_path>`
   - Writes only `<project_name>.kicad_pro`, `<project_name>.kicad_sch`, and `reports/generation_report.json`.
   - Does not generate `.kicad_pcb`.

6. Controlled schematic ERC execution
   - Module: `packages/tools/kicad_cli/erc_runner.py`
   - CLI: `npm run run-erc -- <project_path>`
   - Runs schematic ERC only when `kicad-cli` is available.
   - Writes `reports/erc_report.json` and `reports/erc_raw.log`.

7. ERC diagnostics normalization
   - Module: `packages/tools/kicad_cli/erc_diagnostics.py`
   - CLI: `npm run parse-erc-diagnostics -- <project_path>`
   - Reads `reports/erc_report.json` and writes `reports/erc_diagnostics.json`.
   - Normalizes diagnostics into stable GUI/agent data.

8. Report Service read boundary
   - Frontend service: `apps/desktop/src/services/reportService.ts`
   - Tauri command: `read_report(project_path, kind)`
   - Supported kinds:
     - `erc_diagnostics`
     - `erc_explanation`
     - `generation_report`
   - Whitelisted to `<project_path>/reports/*.json` only.

9. Rule-based ERC report explanation
   - Module: `packages/agent/report_explainer/erc_explainer.py`
   - CLI: `npm run explain-erc-report -- <project_path>`
   - Reads only `reports/erc_diagnostics.json`.
   - Writes `reports/erc_explanation.json`.
   - No real LLM integration yet.

## Current Command Flow

Example end-to-end flow after confirming a design:

```powershell
npm run generate-kicad-artifacts -- "<project_path>\hardware_design_ir.json" --project "<project_path>"
npm run run-erc -- "<project_path>"
npm run parse-erc-diagnostics -- "<project_path>"
npm run explain-erc-report -- "<project_path>"
```

If `kicad-cli` is not installed, `run-erc` returns structured JSON with `success: false` and does not crash.

## Verification Run Today

These passed on 2026-04-28:

```powershell
python -m unittest discover -s tests
npm run build:desktop
```

Current observed result:

- Python tests: 46 tests OK
- Desktop build: TypeScript and Vite build passed

Not verified locally:

```powershell
cargo test --manifest-path apps\desktop\src-tauri\Cargo.toml
```

Reason: `cargo` is not installed or not on `PATH` in the current environment. Rust unit tests for `read_report` are present in `apps/desktop/src-tauri/src/report_service.rs` and should be run once Rust tooling is available.

## Important Boundaries To Keep

- Do not extend the UI until the backend/service pipeline is stable.
- Do not implement real schematic writing from AI output.
- Do not generate `.kicad_pcb` yet.
- Do not run PCB DRC yet.
- Do not read arbitrary files through Tauri.
- Do not let `kind` in `read_report` become a file path.
- Do not connect a real LLM to report explanation until the rule-based shape is stable.

## Suggested Next Steps

1. Install or expose Rust/Cargo, then run Tauri backend tests.
2. Add Tauri commands for existing Python-backed tools only through safe backend wrappers, not directly from React.
3. Add a typed frontend report consumer for `erc_explanation`, without adding a new UI page yet.
4. Expand ERC explanation rules gradually from real KiCad diagnostics.
5. Add a golden sample project under `examples/` for the full artifact -> ERC -> diagnostics -> explanation flow.
6. Later, add an LLM-backed explainer behind the same `erc_explanation` output schema, keeping rule-based fallback.

## Useful Files

- `README.md`
- `docs/KICAD_PIPELINE.md`
- `apps/desktop/src/services/reportService.ts`
- `apps/desktop/src-tauri/src/report_service.rs`
- `packages/tools/kicad_cli/erc_runner.py`
- `packages/tools/kicad_cli/erc_diagnostics.py`
- `packages/agent/report_explainer/erc_explainer.py`
- `packages/generator/kicad/artifact_generator.py`
