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

export const mockProject: ProjectSnapshot = {
  name: "usb_i2s_fpga",
  description: "USB audio bridge, FPGA processing, dual low-jitter oscillators",
  files: [
    {
      id: "ir",
      label: "hardware_design_ir.json",
      path: "examples/usb_i2s_fpga/hardware_design_ir.json",
      kind: "ir",
      status: "ready",
    },
    {
      id: "pro",
      label: "usb_i2s_fpga.kicad_pro",
      path: "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_pro",
      kind: "generated",
      status: "mock",
    },
    {
      id: "sch",
      label: "usb_i2s_fpga.kicad_sch",
      path: "workspace/usb_i2s_fpga/usb_i2s_fpga.kicad_sch",
      kind: "generated",
      status: "mock",
    },
    {
      id: "erc",
      label: "erc_report.json",
      path: "workspace/usb_i2s_fpga/reports/erc_report.json",
      kind: "report",
      status: "mock",
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
      action: "analyze_user_requirement",
      status: "done",
      params: { project_name: "usb_i2s_fpga" },
    },
    {
      id: "a2",
      action: "generate_design_ir",
      status: "done",
      params: { project_name: "usb_i2s_fpga" },
    },
    {
      id: "a3",
      action: "generate_kicad_schematic",
      status: "done",
      params: { project_name: "usb_i2s_fpga" },
    },
    {
      id: "a4",
      action: "run_erc",
      status: "queued",
      params: { project_name: "usb_i2s_fpga" },
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
      body: "Proposed a USB audio bridge feeding an FPGA over I2S, with 45.1584 MHz and 49.152 MHz oscillator domains.",
    },
  ],
  logs: [
    { id: "l1", level: "info", message: "Loaded hardware_design_ir.json" },
    { id: "l2", level: "info", message: "Mock KiCad project generated" },
    { id: "l3", level: "warn", message: "kicad-cli not required for mock preview" },
  ],
  irJson: JSON.stringify(ir, null, 2),
};
