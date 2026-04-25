import { Activity, FileSpreadsheet, ListChecks, RadioTower, ScrollText } from "lucide-react";
import type { BottomTab, LogEntry } from "../types/studio";

type BottomPanelProps = {
  activeTab: BottomTab;
  logs: LogEntry[];
  onTabChange: (tab: BottomTab) => void;
};

export function BottomPanel({ activeTab, logs, onTabChange }: BottomPanelProps) {
  return (
    <footer className="bottom-panel">
      <div className="bottom-tabs">
        <BottomTabButton
          active={activeTab === "logs"}
          icon={<Activity size={15} />}
          label="Logs"
          onClick={() => onTabChange("logs")}
        />
        <BottomTabButton
          active={activeTab === "erc"}
          icon={<ListChecks size={15} />}
          label="ERC Report"
          onClick={() => onTabChange("erc")}
        />
        <BottomTabButton
          active={activeTab === "bom"}
          icon={<FileSpreadsheet size={15} />}
          label="BOM"
          onClick={() => onTabChange("bom")}
        />
        <BottomTabButton
          active={activeTab === "netlist"}
          icon={<ScrollText size={15} />}
          label="Netlist"
          onClick={() => onTabChange("netlist")}
        />
        <BottomTabButton
          active={activeTab === "exports"}
          icon={<RadioTower size={15} />}
          label="Export Status"
          onClick={() => onTabChange("exports")}
        />
      </div>
      <div className="bottom-content">
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
        {activeTab === "erc" && <p className="bottom-copy">Mock ERC status: pass. Real ERC runs through kicad-cli wrapper.</p>}
        {activeTab === "bom" && <p className="bottom-copy">BOM: 7 logical blocks, placeholder part mapping.</p>}
        {activeTab === "netlist" && <p className="bottom-copy">Netlist: USB, I2S, clocks, 3V3, and 1V2 rails.</p>}
        {activeTab === "exports" && <p className="bottom-copy">SVG, PDF, BOM, and netlist exports are ready in workspace.</p>}
      </div>
    </footer>
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
