export type ExportFormat = "png" | "tiff" | "svg" | "pdf";

export interface OptionField {
  key: string;
  label: string;
  kind: "number" | "text" | "select" | "color";
  default: string | number;
  choices?: string[];
}

export interface PlotModule {
  slug: string;
  title: string;
  category: string;
  description: string;
  requiredColumns: string[];
  defaultOptions: Record<string, string | number>;
  optionFields: OptionField[];
  demoData: string;
  citation: string;
  exportFormats: ExportFormat[];
}

export interface PrecheckResult {
  headers: string[];
  rowCount: number;
  columnCount: number;
  previewRows: Record<string, string>[];
  warnings: string[];
  errors: string[];
}

export interface JobResult {
  id: string;
  moduleSlug: string;
  moduleTitle: string;
  sessionId: string;
  status: "queued" | "running" | "succeeded" | "failed";
  createdAt: string;
  updatedAt: string;
  warnings: string[];
  errors: string[];
  previewUrl?: string;
  artifacts: Partial<Record<ExportFormat, string>>;
}

