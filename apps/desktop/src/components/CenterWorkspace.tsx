import { Boxes, Braces, CircuitBoard } from "lucide-react";
import type { CenterTab, HardwareBlock, LogicalConnection } from "../types/studio";

type CenterWorkspaceProps = {
  activeTab: CenterTab;
  blocks: HardwareBlock[];
  connections: LogicalConnection[];
  irJson: string;
  onTabChange: (tab: CenterTab) => void;
};

export function CenterWorkspace({
  activeTab,
  blocks,
  connections,
  irJson,
  onTabChange,
}: CenterWorkspaceProps) {
  return (
    <main className="center-workspace">
      <div className="tab-strip">
        <TabButton
          active={activeTab === "schematic"}
          icon={<CircuitBoard size={16} />}
          label="Schematic Viewer"
          onClick={() => onTabChange("schematic")}
        />
        <TabButton
          active={activeTab === "architecture"}
          icon={<Boxes size={16} />}
          label="Architecture View"
          onClick={() => onTabChange("architecture")}
        />
        <TabButton
          active={activeTab === "ir"}
          icon={<Braces size={16} />}
          label="IR JSON Viewer"
          onClick={() => onTabChange("ir")}
        />
      </div>
      {activeTab === "schematic" && <SchematicPreview blocks={blocks} connections={connections} />}
      {activeTab === "architecture" && <ArchitectureView blocks={blocks} connections={connections} />}
      {activeTab === "ir" && <pre className="ir-viewer">{irJson}</pre>}
    </main>
  );
}

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

type SchematicPreviewProps = {
  blocks: HardwareBlock[];
  connections: LogicalConnection[];
};

function SchematicPreview({ blocks, connections }: SchematicPreviewProps) {
  return (
    <section className="schematic-view">
      <svg className="schematic-canvas" viewBox="0 0 1000 620" role="img" aria-label="Mock schematic">
        <rect x="0" y="0" width="1000" height="620" fill="#fbfdff" />
        <line x1="110" y1="310" x2="860" y2="310" stroke="#cbd5e1" strokeWidth="2" />
        {blocks.map((block, index) => {
          const x = 80 + (index % 3) * 310;
          const y = 90 + Math.floor(index / 3) * 250;
          return (
            <g key={block.id}>
              <rect x={x} y={y} width="220" height="112" rx="6" fill="#e0f2fe" stroke="#0284c7" />
              <text x={x + 18} y={y + 38} fontSize="18" fill="#0f172a" fontFamily="Inter, Arial">
                {block.id}
              </text>
              <text x={x + 18} y={y + 68} fontSize="13" fill="#475569" fontFamily="Inter, Arial">
                {block.type}
              </text>
              <text x={x + 18} y={y + 92} fontSize="12" fill="#0369a1" fontFamily="Inter, Arial">
                {block.powerNets.join(" / ") || "signal"}
              </text>
            </g>
          );
        })}
        <text x="80" y="560" fontSize="15" fill="#475569" fontFamily="Inter, Arial">
          {connections.length} logical nets in mock preview
        </text>
      </svg>
    </section>
  );
}

type ArchitectureViewProps = {
  blocks: HardwareBlock[];
  connections: LogicalConnection[];
};

function ArchitectureView({ blocks, connections }: ArchitectureViewProps) {
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
