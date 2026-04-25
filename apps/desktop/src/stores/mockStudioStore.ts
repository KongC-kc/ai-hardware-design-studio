import { mockProject } from "../services/mockData";
import type { ProjectSnapshot } from "../types/studio";

export function useMockStudioStore(): ProjectSnapshot {
  return mockProject;
}
