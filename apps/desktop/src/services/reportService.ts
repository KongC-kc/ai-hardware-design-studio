import { invoke } from "@tauri-apps/api/core";

import type { JsonObject, ReportKind, ReportReadResult } from "../types/studio";

export type ReportFileReader = {
  readJson: (path: string) => Promise<JsonObject | null>;
};

export type ReportReader = {
  readReport: (projectPath: string, kind: ReportKind) => Promise<ReportReadResult>;
};

export type MockReportReaderData = {
  ercDiagnostics?: JsonObject | null;
  ercExplanation?: JsonObject | null;
  ercSuggestedFixes?: JsonObject | null;
  generationReport?: JsonObject | null;
  pipelineReport?: JsonObject | null;
};

export const READ_REPORT_COMMAND = "read_report";

const REPORT_FILES: Record<ReportKind, string> = {
  erc_diagnostics: "erc_diagnostics.json",
  erc_explanation: "erc_explanation.json",
  erc_suggested_fixes: "erc_suggested_fixes.json",
  generation_report: "generation_report.json",
  pipeline_report: "pipeline_report.json",
};

const MOCK_KEYS: Record<ReportKind, keyof MockReportReaderData> = {
  erc_diagnostics: "ercDiagnostics",
  erc_explanation: "ercExplanation",
  erc_suggested_fixes: "ercSuggestedFixes",
  generation_report: "generationReport",
  pipeline_report: "pipelineReport",
};

export function createMockReportReader(data: MockReportReaderData = {}): ReportFileReader {
  return {
    async readJson(path: string): Promise<JsonObject | null> {
      if (path.endsWith(REPORT_FILES.erc_diagnostics)) {
        return data.ercDiagnostics ?? null;
      }
      if (path.endsWith(REPORT_FILES.erc_explanation)) {
        return data.ercExplanation ?? null;
      }
      if (path.endsWith(REPORT_FILES.erc_suggested_fixes)) {
        return data.ercSuggestedFixes ?? null;
      }
      if (path.endsWith(REPORT_FILES.generation_report)) {
        return data.generationReport ?? null;
      }
      if (path.endsWith(REPORT_FILES.pipeline_report)) {
        return data.pipelineReport ?? null;
      }
      return null;
    },
  };
}

export function createTauriReportReader(fallbackReader?: ReportFileReader): ReportReader {
  return {
    async readReport(projectPath: string, kind: ReportKind): Promise<ReportReadResult> {
      try {
        return await invoke<ReportReadResult>(READ_REPORT_COMMAND, {
          projectPath,
          kind,
        });
      } catch (error) {
        if (fallbackReader !== undefined) {
          return readReport(projectPath, kind, fallbackReader);
        }

        return createEmptyReportResult(kind, getReportPath(projectPath, kind), [
          `Tauri read_report invoke failed: ${error instanceof Error ? error.message : String(error)}`,
        ]);
      }
    },
  };
}

export async function readErcDiagnosticsReport(
  projectPath: string,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  return readReport(projectPath, "erc_diagnostics", reader);
}

export async function readGenerationReport(
  projectPath: string,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  return readReport(projectPath, "generation_report", reader);
}

export async function readErcExplanationReport(
  projectPath: string,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  return readReport(projectPath, "erc_explanation", reader);
}

export async function readErcSuggestedFixesReport(
  projectPath: string,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  return readReport(projectPath, "erc_suggested_fixes", reader);
}

export async function readPipelineReport(
  projectPath: string,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  return readReport(projectPath, "pipeline_report", reader);
}

export async function readReport(
  projectPath: string,
  kind: ReportKind,
  reader: ReportFileReader | ReportReader = createTauriReportReader(createMockReportReader()),
): Promise<ReportReadResult> {
  if (isReportReader(reader)) {
    return reader.readReport(projectPath, kind);
  }

  const path = getReportPath(projectPath, kind);

  try {
    const data = await reader.readJson(path);
    if (data === null) {
      return createEmptyReportResult(kind, path, [`Report file not found or not available in mock reader: ${path}`]);
    }

    return {
      success: true,
      kind,
      path,
      data,
      errors: [],
      warnings: [],
    };
  } catch (error) {
    return createEmptyReportResult(kind, path, [error instanceof Error ? error.message : String(error)]);
  }
}

export function getReportPath(projectPath: string, kind: ReportKind): string {
  const trimmedProjectPath = projectPath.trim();
  const normalizedProjectPath = trimmedProjectPath.replace(/[\\/]+$/, "");
  return `${normalizedProjectPath}/reports/${REPORT_FILES[kind]}`;
}

export function createEmptyReportResult(
  kind: ReportKind,
  path: string | null = null,
  errors: string[] = [],
  warnings: string[] = [],
): ReportReadResult {
  return {
    success: false,
    kind,
    path,
    data: null,
    errors,
    warnings,
  };
}

export function createReportReaderWithMockData(data: MockReportReaderData): ReportFileReader {
  return createMockReportReader({
    ercDiagnostics: data.ercDiagnostics ?? null,
    ercExplanation: data.ercExplanation ?? null,
    ercSuggestedFixes: data.ercSuggestedFixes ?? null,
    generationReport: data.generationReport ?? null,
    pipelineReport: data.pipelineReport ?? null,
  });
}

function isReportReader(reader: ReportFileReader | ReportReader): reader is ReportReader {
  return "readReport" in reader;
}
