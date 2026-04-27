import { invoke } from "@tauri-apps/api/core";

import type { ProjectInspectionSummary } from "../types/studio";

export const INSPECT_PROJECT_COMMAND = "inspect_project";

export async function inspectProject(projectPath: string): Promise<ProjectInspectionSummary> {
  return invoke<ProjectInspectionSummary>(INSPECT_PROJECT_COMMAND, {
    projectPath,
  });
}
