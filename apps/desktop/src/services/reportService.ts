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
  generationReport?: JsonObject | null;
};

export const READ_REPORT_COMMAND = "read_report";

const REPORT_FILES: Record<ReportKind, string> = {
  erc_diagnostics: "erc_diagnostics.json",
  erc_explanation: "erc_explanation.json",
  generation_report: "generation_report.json",
};

const MOCK_KEYS: Record<ReportKind, keyof MockReportReaderData> = {
  erc_diagnostics: "ercDiagnostics",
  erc_explanation: "ercExplanation",
  generation_report: "generationReport",
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
      if (path.endsWith(REPORT_FILES.generation_report)) {
        return data.generationReport ?? null;
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
    [MOCK_KEYS.erc_diagnostics]: data.ercDiagnostics ?? null,
    [MOCK_KEYS.erc_explanation]: data.ercExplanation ?? null,
    [MOCK_KEYS.generation_report]: data.generationReport ?? null,
  });
}

function isReportReader(reader: ReportFileReader | ReportReader): reader is ReportReader {
  return "readReport" in reader;
}

// TODO: When the app adds richer project state, pass a selected project path into
// this service instead of deriving report paths in UI components. GUI callers
// should keep consuming ReportReadResult so this boundary stays stable.
