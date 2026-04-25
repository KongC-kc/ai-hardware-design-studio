import { FileJson, Files, FolderTree, ScrollText } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { FileItem } from "../types/studio";

type SidebarProps = {
  projectName: string;
  files: FileItem[];
};

export function Sidebar({ projectName, files }: SidebarProps) {
  const irFiles = files.filter((file) => file.kind === "ir");
  const generatedFiles = files.filter((file) => file.kind === "generated");
  const reports = files.filter((file) => file.kind === "report");

  return (
    <aside className="sidebar">
      <div className="project-title">
        <FolderTree size={18} aria-hidden="true" />
        <span>{projectName}</span>
      </div>
      <SidebarSection title="Project Explorer" icon={<Files size={16} />} files={files} />
      <SidebarSection title="IR Files" icon={<FileJson size={16} />} files={irFiles} />
      <SidebarSection title="Generated Files" icon={<Files size={16} />} files={generatedFiles} />
      <SidebarSection title="Reports" icon={<ScrollText size={16} />} files={reports} />
    </aside>
  );
}

type SidebarSectionProps = {
  title: string;
  icon: React.ReactNode;
  files: FileItem[];
};

function SidebarSection({ title, icon, files }: SidebarSectionProps) {
  return (
    <section className="sidebar-section">
      <div className="section-title">
        {icon}
        <span>{title}</span>
      </div>
      <div className="file-list">
        {files.map((file) => (
          <button className="file-row" key={file.id} title={file.path}>
            <span>{file.label}</span>
            <StatusBadge status={file.status} />
          </button>
        ))}
      </div>
    </section>
  );
}
