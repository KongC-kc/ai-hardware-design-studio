import { invoke } from "@tauri-apps/api/core";

import type { DesignParseResult, DesignPlan, ParsedDesignRequest } from "../types/studio";

export const PARSE_DESIGN_REQUEST_COMMAND = "parse_design_request";
export const CREATE_DESIGN_PLAN_COMMAND = "create_design_plan";

export async function parseDesignRequest(rawText: string): Promise<DesignParseResult> {
  return invoke<DesignParseResult>(PARSE_DESIGN_REQUEST_COMMAND, {
    rawText,
  });
}

export async function createDesignPlan(
  parsedRequest: ParsedDesignRequest,
): Promise<DesignPlan> {
  return invoke<DesignPlan>(CREATE_DESIGN_PLAN_COMMAND, {
    parsedRequest,
  });
}
