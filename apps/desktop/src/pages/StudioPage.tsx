import { useState } from "react";
import { BottomPanel } from "../components/BottomPanel";
import { CenterWorkspace } from "../components/CenterWorkspace";
import { RightPanel } from "../components/RightPanel";
import { Sidebar } from "../components/Sidebar";
import { useMockStudioStore } from "../stores/mockStudioStore";
import type { BottomTab, CenterTab, JsonObject } from "../types/studio";

export function StudioPage() {
  const project = useMockStudioStore();
  const [centerTab, setCenterTab] = useState<CenterTab>("schematic");
  const [bottomTab, setBottomTab] = useState<BottomTab>("pipeline");

  const fixes = (project.reports.ercSuggestedFixes?.fixes ?? []) as unknown as JsonObject[];

  return (
    <div className="studio-shell">
      <header className="topbar">
        <div>
          <strong>AI Hardware Design Studio</strong>
          <span>{project.description}</span>
        </div>
        <div className="topbar-status">
          <span>V1 MVP</span>
          <span>Pipeline OK</span>
          <span>Mock Data</span>
        </div>
      </header>
      <div className="workspace-grid">
        <Sidebar projectName={project.name} files={project.files} />
        <CenterWorkspace
          activeTab={centerTab}
          blocks={project.blocks}
          connections={project.connections}
          irJson={project.irJson}
          reports={project.reports}
          preview={project.preview}
          onTabChange={setCenterTab}
        />
        <RightPanel actions={project.actions} messages={project.chat} suggestedFixes={fixes} />
      </div>
      <BottomPanel
        activeTab={bottomTab}
        logs={project.logs}
        pipelineReport={project.reports.pipelineReport}
        onTabChange={setBottomTab}
      />
    </div>
  );
}
