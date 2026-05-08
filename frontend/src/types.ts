export type ExportFormat = "png" | "tiff" | "svg" | "pdf";

export interface OptionField {
  key: string;
  label: string;
  kind: "number" | "text" | "select" | "color";
  default: string | number;
  choices?: string[];
}

export type VisualKind =
  | "pie" | "bar" | "line" | "scatter" | "distribution" | "density" | "heatmap"
  | "matrix" | "bubble" | "enrichment" | "forest" | "survival" | "roc" | "pca"
  | "set" | "network" | "hierarchy" | "funnel" | "genome" | "epigenome"
  | "pathway" | "maf" | "sequence" | "calendar" | "polar" | "wordcloud"
  | "correlation" | "qq" | "radar" | "area" | "dual-axis" | "dumbbell"
  | "volcano";

export type RendererQuality = "plot-specific-python" | "plot-specific-r" | "plot-specific-hybrid";
export type SRplotParityStatus = "reference-known" | "reference-needed" | "pixel-close" | "exact-match";

export interface OptionGroup {
  key: string;
  label: string;
  fields: string[];
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
  sourceUrl: string;
  srplotReferenceUrl: string;
  srplotParityStatus: SRplotParityStatus;
  styleProfile: string;
  engine: "python" | "r";
  rendererFamily: string;
  visualKind: VisualKind;
  rendererQuality: RendererQuality;
  optionGroups: OptionGroup[];
  aliases: string[];
}

export interface PrecheckResult {
  headers: string[];
  rowCount: number;
  columnCount: number;
  previewRows: Record<string, string>[];
  warnings: string[];
  errors: string[];
  engine?: "python" | "r";
  engineStatus?: {
    available: boolean;
    executable?: string | null;
    version?: string | null;
    errors: string[];
  } | null;
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
