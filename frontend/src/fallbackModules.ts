import type { PlotModule } from "./types";

const citation =
  "Tang D, Chen M, Huang X, Zhang G, Zeng L, Zhang G, Wu S, Wang Y. SRplot: A free online platform for data visualization and graphing. PLoS One. 2023;18(11):e0294236.";

const commonFields = [
  { key: "width", label: "Figure width", kind: "number" as const, default: 900 },
  { key: "height", label: "Figure height", kind: "number" as const, default: 620 },
  { key: "fontFamily", label: "Font family", kind: "select" as const, default: "Arial", choices: ["Arial", "Times New Roman"] },
  { key: "title", label: "Plot title", kind: "text" as const, default: "" }
];

function module(input: Omit<PlotModule, "citation" | "exportFormats" | "optionFields"> & { optionFields?: PlotModule["optionFields"] }): PlotModule {
  return {
    ...input,
    optionFields: input.optionFields ?? commonFields,
    citation,
    exportFormats: ["png", "tiff", "svg", "pdf"]
  };
}

export const fallbackGroups: Record<string, PlotModule[]> = {
  "Basic plot": [
    module({
      slug: "pie",
      title: "2D Pie Plot",
      category: "Basic plot",
      description: "Proportional chart for category/value data.",
      requiredColumns: ["class", "value"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Class composition" },
      demoData: "class\tvalue\nTSS200\t20.93\nTSS1500\t21.68\n5UTR\t21.45\nGene body\t20.86\n"
    }),
    module({
      slug: "up-down-bar",
      title: "Gene Up/Down Bar",
      category: "Basic plot",
      description: "Fold-change bars split above and below the baseline.",
      requiredColumns: ["gene", "log2FC"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Differential fold change" },
      demoData: "gene\tlog2FC\nMIR21\t2.1\nMIR155\t1.4\nCDH1\t-1.6\nPTEN\t-2.3\n"
    }),
    module({
      slug: "line",
      title: "Line Plot",
      category: "Basic plot",
      description: "Trend chart for ordered x/y observations.",
      requiredColumns: ["x", "y"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Time course" },
      demoData: "x\ty\n0\t2.0\n1\t2.8\n2\t3.4\n3\t4.1\n"
    }),
    module({
      slug: "scatter",
      title: "Scatter Plot",
      category: "Basic plot",
      description: "Point cloud for two quantitative columns.",
      requiredColumns: ["x", "y"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Expression correlation" },
      demoData: "x\ty\n1.0\t1.2\n1.4\t1.9\n2.1\t2.8\n2.8\t2.7\n"
    })
  ],
  Transcriptome: [
    module({
      slug: "heatmap",
      title: "Cluster Heatmap",
      category: "Transcriptome",
      description: "Matrix heatmap for expression-like data.",
      requiredColumns: ["gene", "sample1", "sample2"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Expression heatmap" },
      demoData: "gene\tsample1\tsample2\tsample3\nACTB\t1.2\t1.8\t2.2\nMYC\t0.8\t1.1\t2.8\nTP53\t3.1\t2.8\t1.4\n"
    }),
    module({
      slug: "volcano",
      title: "Volcano Plot",
      category: "Transcriptome",
      description: "Differential-expression scatter plot using log2 fold change and p value.",
      requiredColumns: ["gene", "log2FC", "pvalue"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Differential expression", fcCutoff: 1, pCutoff: 0.05 },
      optionFields: [...commonFields, { key: "fcCutoff", label: "Fold-change cutoff", kind: "number", default: 1 }, { key: "pCutoff", label: "P/FDR cutoff", kind: "number", default: 0.05 }],
      demoData: "gene\tlog2FC\tpvalue\nIL6\t2.4\t0.001\nSTAT1\t1.6\t0.02\nACTB\t0.1\t0.71\nCDH1\t-1.8\t0.008\n"
    }),
    module({
      slug: "violin",
      title: "Violin Plot",
      category: "Transcriptome",
      description: "Distribution plot grouped by category.",
      requiredColumns: ["group", "value"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Group distributions" },
      demoData: "group\tvalue\nControl\t2.1\nControl\t2.4\nTreatment\t3.7\nTreatment\t4.0\n"
    }),
    module({
      slug: "bubble",
      title: "Enrichment Bubble",
      category: "Transcriptome",
      description: "Bubble chart for enrichment terms, ratios, and significance.",
      requiredColumns: ["term", "ratio", "pvalue", "count"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "GO enrichment bubble" },
      demoData: "term\tratio\tpvalue\tcount\nimmune response\t0.42\t0.001\t18\ncell cycle\t0.33\t0.004\t14\n"
    })
  ],
  Genome: [
    module({
      slug: "manhattan",
      title: "Manhattan Plot",
      category: "Genome",
      description: "GWAS-style chromosome scatter using genomic position and p value.",
      requiredColumns: ["snp", "chrom", "position", "pvalue"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "GWAS Manhattan plot" },
      demoData: "snp\tchrom\tposition\tpvalue\nrs1\t1\t120\t0.02\nrs2\t1\t220\t0.0003\nrs3\t2\t140\t0.4\nrs4\t2\t360\t0.00001\n"
    })
  ],
  "Clinical plot": [
    module({
      slug: "km-survival",
      title: "Kaplan Meier Survival",
      category: "Clinical plot",
      description: "Stepwise survival curves from time, status, and group columns.",
      requiredColumns: ["time", "status", "group"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "Kaplan Meier survival" },
      demoData: "time\tstatus\tgroup\n2\t1\tLow\n5\t1\tLow\n3\t1\tHigh\n4\t1\tHigh\n"
    }),
    module({
      slug: "roc",
      title: "ROC Curve",
      category: "Clinical plot",
      description: "Receiver operating characteristic curve.",
      requiredColumns: ["fpr", "tpr"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "ROC curve" },
      demoData: "fpr\ttpr\n0.00\t0.00\n0.05\t0.22\n0.12\t0.48\n1.00\t1.00\n"
    })
  ],
  Miscellaneous: [
    module({
      slug: "pca",
      title: "PCA Scatter",
      category: "Miscellaneous",
      description: "Principal component scatter for sample-level coordinates.",
      requiredColumns: ["sample", "pc1", "pc2", "group"],
      defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title: "PCA sample map" },
      demoData: "sample\tpc1\tpc2\tgroup\nS1\t-2.1\t1.2\tControl\nS2\t-1.7\t0.9\tControl\nS4\t1.5\t-1.1\tTreatment\n"
    })
  ]
};

