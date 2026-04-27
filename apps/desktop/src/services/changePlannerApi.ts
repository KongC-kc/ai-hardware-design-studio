import { invoke } from "@tauri-apps/api/core";

import type {
  DesignPlan,
  HardwareDesignIRPreview,
  ParsedDesignRequest,
  ProjectInspectionSummary,
} from "../types/studio";

export const CREATE_CHANGE_PLAN_PREVIEW_COMMAND = "create_change_plan_preview";

export async function createChangePlanPreview(
  parsedRequest: ParsedDesignRequest,
  designPlan: DesignPlan,
  projectInspectionSummary?: ProjectInspectionSummary,
): Promise<HardwareDesignIRPreview> {
  return invoke<HardwareDesignIRPreview>(CREATE_CHANGE_PLAN_PREVIEW_COMMAND, {
    parsedRequest,
    designPlan,
    projectInspectionSummary,
  });
}
