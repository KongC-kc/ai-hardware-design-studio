export type FileKind = "ir" | "generated" | "report";

export type FileItem = {
  id: string;
  label: string;
  path: string;
  kind: FileKind;
  status: "ready" | "mock" | "warning";
};

export type HardwareBlock = {
  id: string;
  type: string;
  part: string;
  powerNets: string[];
};

export type LogicalConnection = {
  from: string;
  to: string;
  net: string;
};

export type AgentAction = {
  id: string;
  action: string;
  status: "queued" | "running" | "done" | "blocked";
  params: Record<string, string>;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  body: string;
};

export type LogEntry = {
  id: string;
  level: "info" | "warn" | "error";
  message: string;
};

export type PipelineStepSnapshot = {
  step: string;
  success: boolean;
  details: Record<string, unknown>;
};

export type PipelineReport = {
  success: boolean;
  ir_path: string;
  project_path: string;
  completed_steps: string[];
  failed_step: string | null;
  steps: PipelineStepSnapshot[];
  errors: string[];
  warnings: string[];
};

export type ProjectPreview = {
  schematicSvgPath: string | null;
  pcbSvgPath: string | null;
};

export type ProjectSnapshot = {
  name: string;
  description: string;
  files: FileItem[];
  blocks: HardwareBlock[];
  connections: LogicalConnection[];
  actions: AgentAction[];
  chat: ChatMessage[];
  logs: LogEntry[];
  irJson: string;
  reports: ReportData;
  preview: ProjectPreview;
};

export type ReportData = {
  generationReport: JsonObject | null;
  ercDiagnostics: JsonObject | null;
  ercExplanation: JsonObject | null;
  ercSuggestedFixes: JsonObject | null;
  pipelineReport: PipelineReport | null;
};

export type DetectedSheet = {
  name: string;
  file: string;
  source_schematic: string;
  resolved_path: string;
  exists: boolean;
};

export type ProjectInspectionSummary = {
  project_name: string;
  project_root: string;
  project_files: string[];
  schematic_files: string[];
  pcb_files: string[];
  symbol_library_tables: string[];
  footprint_library_tables: string[];
  detected_sheets: DetectedSheet[];
  warnings: string[];
};

export type DesignRequestFeature = {
  type: string;
  count: number;
  notes: string;
};

export type ParsedDesignRequest = {
  raw_request: string;
  target: string;
  mcu: Record<string, string>;
  power: {
    input: string;
    connector: string;
    required_rails: string[];
  };
  interfaces: DesignRequestFeature[];
  io: DesignRequestFeature[];
  required_schematic_blocks: string[];
  assumptions: string[];
  open_questions: string[];
  risk_notes: string[];
};

export type DesignPlan = {
  plan_title: string;
  schematic_blocks: string[];
  recommended_flow: string[];
  files_expected_to_change: string[];
  user_confirmations_required: string[];
  next_action: string;
};

export type DesignParseResult = {
  parsed_request: ParsedDesignRequest;
  design_plan: DesignPlan;
};

export type HardwareDesignIRPreviewSource = {
  raw_request: string;
  parser: string;
  planner: string;
  design_plan_title: string;
  project_inspection:
    | "not_provided"
    | {
        project_name?: string;
        project_root?: string;
      };
};

export type ProposedSheet = {
  name: string;
  purpose: string;
  status: "preview";
};

export type ProposedModule = {
  id: string;
  role: string;
  description: string;
  status: "preview";
};

export type ProposedNet = {
  name: string;
  type: string;
  description: string;
  status: "preview";
};

export type HardwareDesignIRPreview = {
  ir_version: string;
  mode: "preview_only";
  source: HardwareDesignIRPreviewSource;
  target: string;
  proposed_sheets: ProposedSheet[];
  proposed_modules: ProposedModule[];
  proposed_nets: ProposedNet[];
  estimated_files_to_modify: string[];
  risks: string[];
  confirmation_items: string[];
  next_action: "confirm_change_plan_before_ir_write";
};

export type ReportKind =
  | "erc_diagnostics"
  | "erc_explanation"
  | "erc_suggested_fixes"
  | "generation_report"
  | "pipeline_report";

export type JsonObject = Record<string, unknown>;

export type ReportReadResult = {
  success: boolean;
  kind: ReportKind;
  path: string | null;
  data: JsonObject | null;
  errors: string[];
  warnings: string[];
};

export type CenterTab =
  | "schematic"
  | "pcb"
  | "architecture"
  | "ir"
  | "reports";

export type ReportSubTab =
  | "generation_report"
  | "erc_diagnostics"
  | "erc_explanation"
  | "erc_suggested_fixes"
  | "pipeline_report";

export type BottomTab = "logs" | "pipeline" | "erc" | "bom" | "netlist";
