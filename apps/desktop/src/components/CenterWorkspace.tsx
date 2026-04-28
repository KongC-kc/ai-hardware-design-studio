import { useState } from "react";
import {
  Boxes,
  Braces,
  CircuitBoard,
  FileText,
  LayoutGrid,
  ImageOff,
} from "lucide-react";
import type { CenterTab, JsonObject, ProjectPreview, ReportData, ReportSubTab } from "../types/studio";

type CenterWorkspaceProps = {
  activeTab: CenterTab;
  blocks: { id: string; type: string; part: string; powerNets: string[] }[];
  connections: { from: string; to: string; net: string }[];
  irJson: string;
  reports: ReportData;
  preview: ProjectPreview;
  onTabChange: (tab: CenterTab) => void;
};

export function CenterWorkspace({
  activeTab,
  blocks,
  connections,
  irJson,
  reports,
  preview,
  onTabChange,
}: CenterWorkspaceProps) {
  return (
    <main className="center-workspace">
      <div className="tab-strip">
        <TabButton active={activeTab === "schematic"} icon={<CircuitBoard size={16} />} label="Schematic" onClick={() => onTabChange("schematic")} />
        <TabButton active={activeTab === "pcb"} icon={<LayoutGrid size={16} />} label="PCB" onClick={() => onTabChange("pcb")} />
        <TabButton active={activeTab === "architecture"} icon={<Boxes size={16} />} label="Architecture" onClick={() => onTabChange("architecture")} />
        <TabButton active={activeTab === "ir"} icon={<Braces size={16} />} label="IR JSON" onClick={() => onTabChange("ir")} />
        <TabButton active={activeTab === "reports"} icon={<FileText size={16} />} label="Reports" onClick={() => onTabChange("reports")} />
      </div>
      <div className="center-content">
        {activeTab === "schematic" && <SchematicPreview svgPath={preview.schematicSvgPath} />}
        {activeTab === "pcb" && <PcbPreview svgPath={preview.pcbSvgPath} />}
        {activeTab === "architecture" && (
          <ArchitectureView blocks={blocks} connections={connections} />
        )}
        {activeTab === "ir" && <pre className="ir-viewer">{irJson}</pre>}
        {activeTab === "reports" && <ReportsViewer reports={reports} />}
      </div>
    </main>
  );
}

/* ---- Schematic Preview ---- */

function SchematicPreview({ svgPath }: { svgPath: string | null }) {
  if (!svgPath) {
    return (
      <div className="preview-empty">
        <ImageOff size={48} strokeWidth={1.2} />
        <p>尚未生成原理图预览，请先运行 pipeline / export schematic。</p>
      </div>
    );
  }
  return (
    <div className="preview-frame">
      <img src={svgPath} alt="Schematic preview" className="preview-image" />
    </div>
  );
}

/* ---- PCB Preview ---- */

function PcbPreview({ svgPath }: { svgPath: string | null }) {
  if (!svgPath) {
    return (
      <div className="preview-empty">
        <ImageOff size={48} strokeWidth={1.2} />
        <p>PCB 预览尚未实现。</p>
      </div>
    );
  }
  return (
    <div className="preview-frame">
      <img src={svgPath} alt="PCB preview" className="preview-image" />
    </div>
  );
}

/* ---- Architecture View (kept as auxiliary tab) ---- */

type BlockLike = { id: string; type: string; part: string; powerNets: string[] };
type ConnLike = { from: string; to: string; net: string };

function ArchitectureView({ blocks, connections }: { blocks: BlockLike[]; connections: ConnLike[] }) {
  return (
    <section className="architecture-view">
      <div className="architecture-column">
        <h2>Blocks</h2>
        <div className="block-grid">
          {blocks.map((block) => (
            <article className="block-card" key={block.id}>
              <strong>{block.id}</strong>
              <span>{block.type}</span>
              <small>{block.part}</small>
            </article>
          ))}
        </div>
      </div>
      <div className="architecture-column">
        <h2>Connections</h2>
        <div className="connection-list">
          {connections.map((connection) => (
            <div className="connection-row" key={`${connection.from}-${connection.to}`}>
              <span>{connection.net}</span>
              <small>
                {connection.from} {"->"} {connection.to}
              </small>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ---- Reports Viewer (sub-tabbed) ---- */

function ReportsViewer({ reports }: { reports: ReportData }) {
  const [subTab, setSubTab] = useState<ReportSubTab>("pipeline_report");

  return (
    <div className="reports-viewer">
      <div className="report-sub-tabs">
        <SubTabButton active={subTab === "pipeline_report"} label="Pipeline" onClick={() => setSubTab("pipeline_report")} />
        <SubTabButton active={subTab === "generation_report"} label="Generation" onClick={() => setSubTab("generation_report")} />
        <SubTabButton active={subTab === "erc_diagnostics"} label="ERC Diagnostics" onClick={() => setSubTab("erc_diagnostics")} />
        <SubTabButton active={subTab === "erc_explanation"} label="Explanation" onClick={() => setSubTab("erc_explanation")} />
        <SubTabButton active={subTab === "erc_suggested_fixes"} label="Suggested Fixes" onClick={() => setSubTab("erc_suggested_fixes")} />
      </div>
      <div className="report-content">
        {subTab === "pipeline_report" && <JsonViewer data={reports.pipelineReport as unknown as JsonObject} />}
        {subTab === "generation_report" && <JsonViewer data={reports.generationReport} />}
        {subTab === "erc_diagnostics" && <JsonViewer data={reports.ercDiagnostics} />}
        {subTab === "erc_explanation" && <JsonViewer data={reports.ercExplanation} />}
        {subTab === "erc_suggested_fixes" && <JsonViewer data={reports.ercSuggestedFixes} />}
      </div>
    </div>
  );
}

function JsonViewer({ data }: { data: JsonObject | null }) {
  if (!data) {
    return <div className="preview-empty"><p>No data available.</p></div>;
  }
  return <pre className="ir-viewer">{JSON.stringify(data, null, 2)}</pre>;
}

/* ---- Shared button components ---- */

type TabButtonProps = {
  active: boolean;
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
};

function TabButton({ active, icon, label, onClick }: TabButtonProps) {
  return (
    <button className={`tab-button ${active ? "tab-button-active" : ""}`} onClick={onClick}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

type SubTabButtonProps = {
  active: boolean;
  label: string;
  onClick: () => void;
};

function SubTabButton({ active, label, onClick }: SubTabButtonProps) {
  return (
    <button className={`sub-tab ${active ? "sub-tab-active" : ""}`} onClick={onClick}>
      {label}
    </button>
  );
}
