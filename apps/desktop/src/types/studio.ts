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
};

export type CenterTab = "schematic" | "architecture" | "ir";

export type BottomTab = "logs" | "erc" | "bom" | "netlist" | "exports";
