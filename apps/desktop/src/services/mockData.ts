import type { ProjectSnapshot } from "../types/studio";

const ir = {
  meta: {
    name: "usb_i2s_fpga",
    version: "0.1.0",
    description: "USB audio to I2S FPGA board",
  },
  requirements: {
    input: ["USB-C"],
    output: ["I2S"],
    power_input: "USB 5V",
    features: ["FPGA", "dual_oscillator", "low_noise_power"],
  },
  blocks: [
    {
      id: "usb_interface",
      type: "usb_audio_bridge",
      part: "PLACEHOLDER_USB_AUDIO_IC",
      power_nets: ["3V3"],
    },
    {
      id: "fpga",
      type: "fpga",
      part: "PLACEHOLDER_FPGA",
      power_nets: ["3V3", "1V2"],
    },
    {
      id: "clock_44m",
      type: "oscillator",
      part: "PLACEHOLDER_LOW_JITTER_OSCILLATOR",
      power_nets: ["3V3"],
    },
    {
      id: "clock_49m",
      type: "oscillator",
      part: "PLACEHOLDER_LOW_JITTER_OSCILLATOR",
      power_nets: ["3V3"],
    },
  ],
  connections: [
    { from: "usb_interface.I2S_BCLK", to: "fpga.I2S_BCLK", net: "I2S_BCLK" },
    { from: "usb_interface.I2S_LRCK", to: "fpga.I2S_LRCK", net: "I2S_LRCK" },
    { from: "usb_interface.I2S_DATA", to: "fpga.I2S_DATA", net: "I2S_DATA" },
    { from: "clock_44m.OUT", to: "fpga.MCLK_44M", net: "MCLK_44M" },
    { from: "clock_49m.OUT", to: "fpga.MCLK_49M", net: "MCLK_49M" },
  ],
};

const mockGenerationReport = {
  success: true,
  mode: "generate_kicad_artifacts",
  project_name: "usb_i2s_fpga",
  ir_path: "workspace/usb_i2s_fpga/hardware_design_ir.json",
  planned_files: [
    "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_pro",
    "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_sch",
    "workspace/usb_i2s_fpga/reports/generation_report.json",
  ],
  written_files: [
    "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_pro",
    "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_sch",
    "workspace/usb_i2s_fpga/reports/generation_report.json",
  ],
  validation: {
    is_valid: true,
    errors: [],
    warnings: [
      "blocks[0].part is a placeholder: PLACEHOLDER_USB_AUDIO_IC",
      "blocks[1].part is a placeholder: PLACEHOLDER_FPGA",
      "blocks[2].part is a placeholder: PLACEHOLDER_LOW_JITTER_OSCILLATOR",
      "blocks[3].part is a placeholder: PLACEHOLDER_LOW_JITTER_OSCILLATOR",
    ],
  },
  generated_pcb: false,
};

const mockErcDiagnostics = {
  success: true,
  mode: "parse_erc_diagnostics",
  source_report: "workspace/usb_i2s_fpga/reports/erc_report.json",
  diagnostics_path: "workspace/usb_i2s_fpga/reports/erc_diagnostics.json",
  summary: { error_count: 2, warning_count: 1, info_count: 0 },
  diagnostics: [
    {
      id: "erc-001",
      severity: "error",
      code: "PIN_NOT_CONNECTED",
      message: "Pin USB_DP of usb_interface is not connected",
      file: "usb_i2s_fpga.kicad_sch",
      sheet: null,
      symbol: "usb_interface",
      pin: "USB_DP",
      net: null,
    },
    {
      id: "erc-002",
      severity: "error",
      code: "POWER_INPUT_NOT_DRIVEN",
      message: "Power input pin 3V3 of fpga is not driven by any source",
      file: "usb_i2s_fpga.kicad_sch",
      sheet: null,
      symbol: "fpga",
      pin: "3V3",
      net: "3V3",
    },
    {
      id: "erc-003",
      severity: "warning",
      code: "PIN_NOT_CONNECTED",
      message: "Pin MCLK_49M of clock_49m is not connected",
      file: "usb_i2s_fpga.kicad_sch",
      sheet: null,
      symbol: "clock_49m",
      pin: "MCLK_49M",
      net: null,
    },
  ],
  errors: [],
  warnings: [],
};

const mockErcExplanation = {
  success: true,
  mode: "explain_erc_report",
  source: "workspace/usb_i2s_fpga/reports/erc_diagnostics.json",
  output: "workspace/usb_i2s_fpga/reports/erc_explanation.json",
  summary: { error_count: 2, warning_count: 1, info_count: 0, explanation_count: 3 },
  explanations: [
    {
      diagnostic_id: "erc-001",
      severity: "error",
      title: "Pin is not connected",
      plain_language:
        "usb_interface has an unconnected pin (USB_DP). This usually means the schematic is missing an intentional connection, a no-connect marker, or a named net.",
      likely_causes: [
        "The pin was meant to connect to another schematic block but no net was assigned.",
        "The pin is intentionally unused but has no no-connect marker.",
      ],
      suggested_fixes: [
        "Confirm whether the pin should be connected or intentionally unused.",
        "Connect the pin to the intended net if it is required for the design.",
      ],
      requires_user_confirmation: true,
    },
    {
      diagnostic_id: "erc-002",
      severity: "error",
      title: "Power input is not driven",
      plain_language:
        "fpga is on a power net on net 3V3, but ERC did not find a source that drives that net. The design may need a regulator output, connector power source, or KiCad power flag.",
      likely_causes: [
        "A power rail is labeled but not connected to a regulator, connector, or power source symbol.",
        "KiCad needs a power flag to mark an externally supplied rail as driven.",
      ],
      suggested_fixes: [
        "Trace the named rail back to its connector or regulator output.",
        "Add or fix the missing power source connection in the schematic IR/generator input.",
      ],
      requires_user_confirmation: true,
    },
    {
      diagnostic_id: "erc-003",
      severity: "warning",
      title: "Pin is not connected",
      plain_language:
        "clock_49m has an unconnected pin (MCLK_49M). This usually means the schematic is missing an intentional connection, a no-connect marker, or a named net.",
      likely_causes: [
        "The pin was meant to connect to another schematic block but no net was assigned.",
        "The pin is intentionally unused but has no no-connect marker.",
      ],
      suggested_fixes: [
        "Confirm whether the pin should be connected or intentionally unused.",
        "Connect the pin to the intended net if it is required for the design.",
      ],
      requires_user_confirmation: true,
    },
  ],
  errors: [],
  warnings: [],
};

const mockErcSuggestedFixes = {
  success: true,
  mode: "suggest_erc_fixes",
  sources: {
    diagnostics: "workspace/usb_i2s_fpga/reports/erc_diagnostics.json",
    explanation: "workspace/usb_i2s_fpga/reports/erc_explanation.json",
  },
  output: "workspace/usb_i2s_fpga/reports/erc_suggested_fixes.json",
  summary: {
    fix_count: 3,
    auto_applicable_count: 0,
    requires_confirmation_count: 3,
  },
  fixes: [
    {
      id: "fix-001",
      diagnostic_id: "erc-001",
      severity: "error",
      title: "Connect unconnected pin",
      target: { file: "usb_i2s_fpga.kicad_sch", symbol: "usb_interface", pin: "USB_DP", net: null },
      proposal_type: "ir_change",
      proposed_ir_patch: {
        op: "add_connection",
        from: "usb_interface.USB_DP",
        to: "TODO_CONFIRM_TARGET",
        net: "TODO_CONFIRM_NET",
      },
      plain_language:
        "This pin is currently not connected. Confirm the intended destination before applying any change.",
      risk_level: "medium",
      auto_applicable: false,
      requires_user_confirmation: true,
    },
    {
      id: "fix-002",
      diagnostic_id: "erc-002",
      severity: "error",
      title: "Drive power input",
      target: { file: "usb_i2s_fpga.kicad_sch", symbol: "fpga", pin: "3V3", net: "3V3" },
      proposal_type: "ir_change",
      proposed_ir_patch: {
        op: "add_power_source_or_power_flag",
        target: "fpga.3V3",
        net: "3V3",
        source: "TODO_CONFIRM_POWER_SOURCE",
      },
      plain_language:
        "This power input is not driven. Confirm the real power source before adding a regulator, connector rail, or power flag proposal.",
      risk_level: "medium",
      auto_applicable: false,
      requires_user_confirmation: true,
    },
    {
      id: "fix-003",
      diagnostic_id: "erc-003",
      severity: "warning",
      title: "Connect unconnected pin",
      target: { file: "usb_i2s_fpga.kicad_sch", symbol: "clock_49m", pin: "MCLK_49M", net: null },
      proposal_type: "ir_change",
      proposed_ir_patch: {
        op: "add_connection",
        from: "clock_49m.MCLK_49M",
        to: "TODO_CONFIRM_TARGET",
        net: "TODO_CONFIRM_NET",
      },
      plain_language:
        "This pin is currently not connected. Confirm the intended destination before applying any change. Related explanation suggestion: Confirm whether the pin should be connected or intentionally unused.",
      risk_level: "medium",
      auto_applicable: false,
      requires_user_confirmation: true,
    },
  ],
  errors: [],
  warnings: [],
};

const mockPipelineReport = {
  success: true,
  ir_path: "workspace/usb_i2s_fpga/hardware_design_ir.json",
  project_path: "workspace/usb_i2s_fpga",
  completed_steps: [
    "generate_kicad_artifacts",
    "run_erc",
    "parse_erc_diagnostics",
    "explain_erc_report",
    "suggest_erc_fixes",
  ],
  failed_step: null,
  steps: [
    {
      step: "generate_kicad_artifacts",
      success: true,
      details: mockGenerationReport,
    },
    {
      step: "run_erc",
      success: true,
      details: {
        success: true,
        mode: "run_erc",
        project_path: "workspace/usb_i2s_fpga",
        schematic_path: "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_sch",
        report_path: "workspace/usb_i2s_fpga/reports/erc_report.json",
        raw_log_path: "workspace/usb_i2s_fpga/reports/erc_raw.log",
        kicad_cli_found: true,
        errors: [],
        warnings: [],
      },
    },
    {
      step: "parse_erc_diagnostics",
      success: true,
      details: mockErcDiagnostics,
    },
    {
      step: "explain_erc_report",
      success: true,
      details: mockErcExplanation,
    },
    {
      step: "suggest_erc_fixes",
      success: true,
      details: mockErcSuggestedFixes,
    },
  ],
  errors: [],
  warnings: [],
};

export const mockProject: ProjectSnapshot = {
  name: "usb_i2s_fpga",
  description: "USB audio bridge, FPGA processing, dual low-jitter oscillators",
  files: [
    {
      id: "ir",
      label: "hardware_design_ir.json",
      path: "workspace/usb_i2s_fpga/hardware_design_ir.json",
      kind: "ir",
      status: "ready",
    },
    {
      id: "pro",
      label: "usb_i2s_fpga.kicad_pro",
      path: "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_pro",
      kind: "generated",
      status: "ready",
    },
    {
      id: "sch",
      label: "usb_i2s_fpga.kicad_sch",
      path: "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_sch",
      kind: "generated",
      status: "ready",
    },
    {
      id: "gen-report",
      label: "generation_report.json",
      path: "workspace/usb_i2s_fpga/reports/generation_report.json",
      kind: "report",
      status: "ready",
    },
    {
      id: "erc-report",
      label: "erc_report.json",
      path: "workspace/usb_i2s_fpga/reports/erc_report.json",
      kind: "report",
      status: "ready",
    },
    {
      id: "erc-diag",
      label: "erc_diagnostics.json",
      path: "workspace/usb_i2s_fpga/reports/erc_diagnostics.json",
      kind: "report",
      status: "ready",
    },
    {
      id: "erc-expl",
      label: "erc_explanation.json",
      path: "workspace/usb_i2s_fpga/reports/erc_explanation.json",
      kind: "report",
      status: "ready",
    },
    {
      id: "erc-fix",
      label: "erc_suggested_fixes.json",
      path: "workspace/usb_i2s_fpga/reports/erc_suggested_fixes.json",
      kind: "report",
      status: "ready",
    },
    {
      id: "pipeline",
      label: "pipeline_report.json",
      path: "workspace/usb_i2s_fpga/reports/pipeline_report.json",
      kind: "report",
      status: "ready",
    },
  ],
  blocks: ir.blocks.map((block) => ({
    id: block.id,
    type: block.type,
    part: block.part,
    powerNets: block.power_nets,
  })),
  connections: ir.connections,
  actions: [
    {
      id: "a1",
      action: "generate_kicad_artifacts",
      status: "done",
      params: { mode: "generate_kicad_artifacts" },
    },
    {
      id: "a2",
      action: "run_erc",
      status: "done",
      params: { mode: "run_erc" },
    },
    {
      id: "a3",
      action: "parse_erc_diagnostics",
      status: "done",
      params: { mode: "parse_erc_diagnostics" },
    },
    {
      id: "a4",
      action: "explain_erc_report",
      status: "done",
      params: { mode: "explain_erc_report" },
    },
    {
      id: "a5",
      action: "suggest_erc_fixes",
      status: "done",
      params: { mode: "suggest_erc_fixes" },
    },
  ],
  chat: [
    {
      id: "c1",
      role: "user",
      body: "USB-C input, I2S output, FPGA processing, dual low-jitter oscillators.",
    },
    {
      id: "c2",
      role: "assistant",
      body: "Pipeline complete. Generated KiCad artifacts, ran ERC, found 2 errors and 1 warning. Suggested fixes are ready for your review.",
    },
  ],
  logs: [
    { id: "l1", level: "info", message: "[generate_kicad_artifacts] Generated usb_i2s_fpga.kicad_pro, usb_i2s_fpga.kicad_sch" },
    { id: "l2", level: "info", message: "[generate_kicad_artifacts] IR validation passed (4 placeholder warnings)" },
    { id: "l3", level: "info", message: "[run_erc] kicad-cli sch erc completed" },
    { id: "l4", level: "info", message: "[parse_erc_diagnostics] 3 diagnostics found (2 errors, 1 warning)" },
    { id: "l5", level: "info", message: "[explain_erc_report] 3 explanations generated" },
    { id: "l6", level: "info", message: "[suggest_erc_fixes] 3 fix proposals generated" },
    { id: "l7", level: "info", message: "[pipeline] All 5 steps completed successfully" },
  ],
  irJson: JSON.stringify(ir, null, 2),
  reports: {
    generationReport: mockGenerationReport as unknown as Record<string, unknown>,
    ercDiagnostics: mockErcDiagnostics as unknown as Record<string, unknown>,
    ercExplanation: mockErcExplanation as unknown as Record<string, unknown>,
    ercSuggestedFixes: mockErcSuggestedFixes as unknown as Record<string, unknown>,
    pipelineReport: mockPipelineReport,
  },
  preview: {
    schematicSvgPath: null,
    pcbSvgPath: null,
  },
};
