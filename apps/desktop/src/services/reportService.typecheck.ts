import type { ReportReadResult } from "../types/studio";

import {
  createMockReportReader,
  readErcDiagnosticsReport,
  readErcExplanationReport,
  readErcSuggestedFixesReport,
  readGenerationReport,
  readPipelineReport,
} from "./reportService";

export async function reportServiceTypecheck(projectPath: string): Promise<ReportReadResult[]> {
  const mockReader = createMockReportReader({
    ercDiagnostics: {
      success: true,
      mode: "parse_erc_diagnostics",
      summary: { error_count: 0, warning_count: 0, info_count: 0 },
      diagnostics: [],
    },
    generationReport: {
      success: true,
      mode: "generate_kicad_artifacts",
      written_files: [],
    },
    ercExplanation: {
      success: true,
      mode: "explain_erc_report",
      explanations: [],
    },
    ercSuggestedFixes: {
      success: true,
      mode: "suggest_erc_fixes",
      fixes: [],
    },
    pipelineReport: {
      success: true,
      completed_steps: [],
      steps: [],
      errors: [],
      warnings: [],
    },
  });

  const ercDiagnostics = await readErcDiagnosticsReport(projectPath, mockReader);
  const generationReport = await readGenerationReport(projectPath, mockReader);
  const ercExplanation = await readErcExplanationReport(projectPath, mockReader);
  const ercSuggestedFixes = await readErcSuggestedFixesReport(projectPath, mockReader);
  const pipelineReport = await readPipelineReport(projectPath, mockReader);

  return [ercDiagnostics, generationReport, ercExplanation, ercSuggestedFixes, pipelineReport];
}
