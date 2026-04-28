import { Activity, CheckCircle2, CircleSlash, ListChecks, ScrollText, XCircle } from "lucide-react";
import type { BottomTab, LogEntry, PipelineReport } from "../types/studio";

type BottomPanelProps = {
  activeTab: BottomTab;
  logs: LogEntry[];
  pipelineReport: PipelineReport | null;
  onTabChange: (tab: BottomTab) => void;
};

export function BottomPanel({ activeTab, logs, pipelineReport, onTabChange }: BottomPanelProps) {
  return (
    <footer className="bottom-panel">
      <div className="bottom-tabs">
        <BottomTabButton
          active={activeTab === "pipeline"}
          icon={<ListChecks size={15} />}
          label="Pipeline"
          onClick={() => onTabChange("pipeline")}
        />
        <BottomTabButton
          active={activeTab === "logs"}
          icon={<Activity size={15} />}
          label="Logs"
          onClick={() => onTabChange("logs")}
        />
        <BottomTabButton
          active={activeTab === "erc"}
          icon={<XCircle size={15} />}
          label="ERC"
          onClick={() => onTabChange("erc")}
        />
        <BottomTabButton
          active={activeTab === "bom"}
          icon={<ScrollText size={15} />}
          label="BOM"
          onClick={() => onTabChange("bom")}
        />
        <BottomTabButton
          active={activeTab === "netlist"}
          icon={<ScrollText size={15} />}
          label="Netlist"
          onClick={() => onTabChange("netlist")}
        />
      </div>
      <div className="bottom-content">
        {activeTab === "pipeline" && <PipelineView report={pipelineReport} />}
        {activeTab === "logs" && (
          <div className="log-list">
            {logs.map((log) => (
              <div className={`log-row log-${log.level}`} key={log.id}>
                <span>{log.level}</span>
                <p>{log.message}</p>
              </div>
            ))}
          </div>
        )}
        {activeTab === "erc" && <ErcSummary pipelineReport={pipelineReport} />}
        {activeTab === "bom" && <p className="bottom-copy">BOM: 4 logical blocks, placeholder part mapping.</p>}
        {activeTab === "netlist" && <p className="bottom-copy">Netlist: USB, I2S, clocks, and power rails.</p>}
      </div>
    </footer>
  );
}

function PipelineView({ report }: { report: PipelineReport | null }) {
  if (!report) {
    return <p className="bottom-copy">No pipeline report available.</p>;
  }
  return (
    <div className="pipeline-steps">
      {report.steps.map((step) => (
        <div className={`pipeline-step ${step.success ? "step-success" : "step-failed"}`} key={step.step}>
          {step.success ? <CheckCircle2 size={16} /> : <CircleSlash size={16} />}
          <span className="step-name">{step.step}</span>
          <span className="step-status">{step.success ? "OK" : "FAILED"}</span>
        </div>
      ))}
      {report.failed_step && (
        <div className="pipeline-errors">
          <strong>Failed at: {report.failed_step}</strong>
          {report.errors.map((err, i) => (
            <p key={i} className="error-text">{err}</p>
          ))}
        </div>
      )}
      {report.warnings.length > 0 && (
        <div className="pipeline-warnings">
          <strong>Warnings:</strong>
          {report.warnings.map((w, i) => (
            <p key={i} className="warn-text">{w}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function ErcSummary({ pipelineReport }: { pipelineReport: PipelineReport | null }) {
  const diagStep = pipelineReport?.steps.find((s) => s.step === "parse_erc_diagnostics");
  const details = diagStep?.details as { summary?: { error_count?: number; warning_count?: number; info_count?: number } } | undefined;
  if (!details?.summary) {
    return <p className="bottom-copy">ERC diagnostics not available.</p>;
  }
  const s = details.summary;
  return (
    <div className="erc-summary-grid">
      <div className="erc-stat erc-error"><XCircle size={16} /><span>{s.error_count ?? 0} errors</span></div>
      <div className="erc-stat erc-warn"><Activity size={16} /><span>{s.warning_count ?? 0} warnings</span></div>
      <div className="erc-stat erc-info"><CheckCircle2 size={16} /><span>{s.info_count ?? 0} info</span></div>
    </div>
  );
}

type BottomTabButtonProps = {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
};

function BottomTabButton({ active, icon, label, onClick }: BottomTabButtonProps) {
  return (
    <button className={`bottom-tab ${active ? "bottom-tab-active" : ""}`} onClick={onClick}>
      {icon}
      <span>{label}</span>
    </button>
  );
}
