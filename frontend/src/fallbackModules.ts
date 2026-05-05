import type { PlotModule } from "./types";

const citation =
  "Tang D, Chen M, Huang X, Zhang G, Zeng L, Zhang G, Wu S, Wang Y. SRplot: A free online platform for data visualization and graphing. PLoS One. 2023;18(11):e0294236.";

const commonFields: PlotModule["optionFields"] = [
  { key: "width", label: "Figure width", kind: "number", default: 900 },
  { key: "height", label: "Figure height", kind: "number", default: 620 },
  { key: "fontFamily", label: "Font family", kind: "select", default: "Arial", choices: ["Arial", "Times New Roman"] },
  { key: "title", label: "Plot title", kind: "text", default: "" }
];

type Engine = PlotModule["engine"];
type Profile = {
  requiredColumns: string[];
  demoData: string;
  description: string;
  defaults?: Record<string, string | number>;
  optionFields?: PlotModule["optionFields"];
};
type TemplateSpec = readonly [slug: string, title: string, category: string, page: number, family: keyof typeof profiles, engine?: Engine];

const colorFields: PlotModule["optionFields"] = [
  { key: "primaryColor", label: "Primary color", kind: "color", default: "#2f6f73" },
  { key: "accentColor", label: "Accent color", kind: "color", default: "#d36f45" }
];

const profiles = {
  pie: {
    requiredColumns: ["class", "value"],
    description: "Proportional chart for category/value data.",
    demoData: "class\tvalue\nTSS200\t20.93\nTSS1500\t21.68\n5UTR\t21.45\nGene body\t20.86\n3UTR\t6.36\n"
  },
  bar: {
    requiredColumns: ["label", "value"],
    description: "Bar chart for ranked categorical values.",
    demoData: "label\tvalue\nA\t12\nB\t18\nC\t9\nD\t24\nE\t15\n",
    optionFields: colorFields
  },
  errorbar: {
    requiredColumns: ["label", "value", "error"],
    description: "Mean-value chart with symmetric error intervals.",
    demoData: "label\tvalue\terror\nA\t12\t1.3\nB\t18\t2.1\nC\t9\t0.9\nD\t24\t2.7\n",
    optionFields: colorFields
  },
  "stacked-bar": {
    requiredColumns: ["category", "series", "value"],
    description: "Stacked bar chart for category and series totals.",
    demoData: "category\tseries\tvalue\nA\tUp\t12\nA\tDown\t7\nB\tUp\t18\nB\tDown\t9\nC\tUp\t11\nC\tDown\t13\n",
    optionFields: colorFields
  },
  line: {
    requiredColumns: ["x", "y", "group"],
    description: "Trend chart for ordered x/y observations.",
    demoData: "x\ty\tgroup\n0\t2.0\tA\n1\t2.8\tA\n2\t3.4\tA\n3\t4.1\tA\n0\t1.5\tB\n1\t2.0\tB\n2\t2.7\tB\n3\t3.2\tB\n",
    optionFields: colorFields
  },
  area: {
    requiredColumns: ["x", "y", "group"],
    description: "Area chart for cumulative or grouped trends.",
    demoData: "x\ty\tgroup\n0\t1.8\tA\n1\t2.5\tA\n2\t3.0\tA\n3\t3.9\tA\n0\t0.8\tB\n1\t1.4\tB\n2\t1.9\tB\n3\t2.2\tB\n",
    optionFields: colorFields
  },
  scatter: {
    requiredColumns: ["x", "y", "group"],
    description: "Point cloud for two quantitative columns.",
    demoData: "x\ty\tgroup\n1.0\t1.2\tA\n1.4\t1.9\tA\n2.1\t2.8\tB\n2.8\t2.7\tB\n3.4\t3.9\tC\n4.1\t4.8\tC\n",
    optionFields: [...colorFields, { key: "pointSize", label: "Point size", kind: "number", default: 64 }]
  },
  bubble: {
    requiredColumns: ["term", "ratio", "pvalue", "count"],
    description: "Bubble chart for terms, ratios, and significance.",
    demoData: "term\tratio\tpvalue\tcount\nimmune response\t0.42\t0.001\t18\ncell cycle\t0.33\t0.004\t14\napoptosis\t0.29\t0.015\t11\nangiogenesis\t0.22\t0.03\t8\n",
    defaults: { pCutoff: 0.05 },
    optionFields: [{ key: "pCutoff", label: "P/FDR cutoff", kind: "number", default: 0.05 }]
  },
  enrichment: {
    requiredColumns: ["term", "ratio", "pvalue", "count"],
    description: "GO, KEGG, or pathway enrichment summary.",
    demoData: "term\tratio\tpvalue\tcount\nGO immune response\t0.42\t0.001\t18\nKEGG cell cycle\t0.33\t0.004\t14\nGO apoptosis\t0.29\t0.015\t11\nKEGG angiogenesis\t0.22\t0.03\t8\n",
    defaults: { pCutoff: 0.05 },
    optionFields: [{ key: "pCutoff", label: "P/FDR cutoff", kind: "number", default: 0.05 }]
  },
  distribution: {
    requiredColumns: ["group", "value"],
    description: "Distribution plot grouped by category.",
    demoData: "group\tvalue\nControl\t2.1\nControl\t2.4\nControl\t2.6\nControl\t2.9\nTreatment\t3.1\nTreatment\t3.7\nTreatment\t4.0\nTreatment\t4.2\n",
    optionFields: colorFields
  },
  density: {
    requiredColumns: ["group", "value"],
    description: "Density or histogram view of numeric distributions.",
    demoData: "group\tvalue\nA\t1.2\nA\t1.4\nA\t1.9\nA\t2.1\nA\t2.4\nB\t2.0\nB\t2.6\nB\t3.0\nB\t3.2\nB\t3.6\n",
    optionFields: colorFields
  },
  heatmap: {
    requiredColumns: ["gene", "sample1", "sample2"],
    description: "Matrix heatmap for expression-like data.",
    demoData: "gene\tsample1\tsample2\tsample3\tsample4\nACTB\t1.2\t1.8\t2.2\t2.9\nGAPDH\t2.4\t2.1\t1.9\t1.5\nMYC\t0.8\t1.1\t2.8\t3.2\nTP53\t3.1\t2.8\t1.4\t1.2\n"
  },
  matrix: {
    requiredColumns: ["row", "column", "value"],
    description: "Long-form matrix heatmap.",
    demoData: "row\tcolumn\tvalue\nA\tS1\t1.2\nA\tS2\t2.1\nB\tS1\t2.7\nB\tS2\t1.5\nC\tS1\t3.1\nC\tS2\t2.4\n"
  },
  set: {
    requiredColumns: ["set", "count"],
    description: "Set overlap visualization for list intersections.",
    demoData: "set\tcount\nA only\t18\nB only\t11\nA and B\t7\nC only\t9\nA and C\t5\n"
  },
  network: {
    requiredColumns: ["source", "target", "weight"],
    description: "Relationship diagram for source, target, and edge weight data.",
    demoData: "source\ttarget\tweight\ncircRNA1\tmiR-21\t3\ncircRNA1\tmiR-155\t2\nmiR-21\tPTEN\t4\nmiR-155\tSOCS1\t3\n"
  },
  hierarchy: {
    requiredColumns: ["parent", "child", "value"],
    description: "Hierarchical summary for tree, packing, treemap, or clustering views.",
    demoData: "parent\tchild\tvalue\nRoot\tImmune\t18\nRoot\tCell cycle\t14\nImmune\tCytokine\t8\nImmune\tT cell\t10\n"
  },
  funnel: {
    requiredColumns: ["stage", "value"],
    description: "Funnel chart for ordered step reductions.",
    demoData: "stage\tvalue\nInput genes\t1200\nFiltered\t820\nMapped\t510\nSignificant\t180\nReported\t64\n"
  },
  dumbbell: {
    requiredColumns: ["label", "start", "end"],
    description: "Dumbbell chart comparing paired values.",
    demoData: "label\tstart\tend\nGene A\t1.2\t2.4\nGene B\t1.6\t2.1\nGene C\t2.3\t1.7\nGene D\t0.9\t1.8\n"
  },
  correlation: {
    requiredColumns: ["x", "y"],
    description: "Correlation scatter or dot summary.",
    demoData: "x\ty\n1.0\t1.2\n1.4\t1.9\n2.1\t2.8\n2.8\t2.7\n3.4\t3.9\n"
  },
  qq: {
    requiredColumns: ["expected", "observed"],
    description: "Quantile-quantile diagnostic plot.",
    demoData: "expected\tobserved\n0.1\t0.12\n0.2\t0.18\n0.3\t0.32\n0.4\t0.47\n0.5\t0.62\n"
  },
  radar: {
    requiredColumns: ["axis", "value", "group"],
    description: "Radar or polar category profile.",
    demoData: "axis\tvalue\tgroup\nA\t0.8\tSample1\nB\t0.6\tSample1\nC\t0.9\tSample1\nD\t0.5\tSample1\nA\t0.5\tSample2\n"
  },
  polar: {
    requiredColumns: ["label", "value"],
    description: "Polar bar chart for circular category values.",
    demoData: "label\tvalue\nA\t12\nB\t18\nC\t9\nD\t24\nE\t15\n"
  },
  calendar: {
    requiredColumns: ["date", "value"],
    description: "Calendar heatmap for date-indexed values.",
    demoData: "date\tvalue\n2026-01-01\t5\n2026-01-02\t8\n2026-01-03\t4\n2026-01-04\t12\n"
  },
  forest: {
    requiredColumns: ["study", "effect", "low", "high"],
    description: "Forest plot for estimates and confidence intervals.",
    demoData: "study\teffect\tlow\thigh\nCohort A\t1.25\t0.98\t1.56\nCohort B\t0.86\t0.64\t1.12\nCohort C\t1.48\t1.10\t1.92\n",
    defaults: { referenceLine: 1 }
  },
  genome: {
    requiredColumns: ["chrom", "position", "value"],
    description: "Genome-position plot for chromosome tracks or densities.",
    demoData: "chrom\tposition\tvalue\n1\t120\t2.4\n1\t220\t4.1\n2\t140\t1.3\n2\t360\t5.0\n3\t180\t2.1\n",
    defaults: { threshold: 3 }
  },
  epigenome: {
    requiredColumns: ["feature", "position", "log2FC"],
    description: "Epigenomic summary for peak, methylation, or expression change data.",
    demoData: "feature\tposition\tlog2FC\nPeak1\t120\t1.4\nPeak2\t260\t-0.8\nPeak3\t420\t2.1\nPeak4\t620\t-1.6\n"
  },
  pathway: {
    requiredColumns: ["pathway", "gene", "value"],
    description: "Pathway-centric gene/value summary.",
    demoData: "pathway\tgene\tvalue\nApoptosis\tCASP3\t2.1\nApoptosis\tBAX\t1.7\nCell cycle\tCDK1\t2.5\nCell cycle\tCCNB1\t1.9\n"
  },
  sequence: {
    requiredColumns: ["position", "symbol", "score"],
    description: "Sequence-position plot for motifs, alignments, or base scores.",
    demoData: "position\tsymbol\tscore\n1\tA\t0.8\n2\tC\t1.2\n3\tG\t0.9\n4\tT\t1.4\n5\tA\t1.1\n"
  },
  wordcloud: {
    requiredColumns: ["word", "weight"],
    description: "Weighted term cloud.",
    demoData: "word\tweight\nimmune\t30\ncell\t24\nsignal\t18\npathway\t14\nexpression\t12\n"
  },
  maf: {
    requiredColumns: ["gene", "sample", "mutation"],
    description: "Mutation annotation format summary.",
    demoData: "gene\tsample\tmutation\nTP53\tS1\tMissense\nKRAS\tS1\tMissense\nEGFR\tS2\tAmplification\nPIK3CA\tS3\tMissense\n"
  },
  pca: {
    requiredColumns: ["sample", "pc1", "pc2", "group"],
    description: "Principal component scatter for sample coordinates.",
    demoData: "sample\tpc1\tpc2\tgroup\nS1\t-2.1\t1.2\tControl\nS2\t-1.7\t0.9\tControl\nS4\t1.5\t-1.1\tTreatment\nS5\t1.9\t-0.8\tTreatment\n"
  },
  "dual-axis": {
    requiredColumns: ["x", "bar", "line"],
    description: "Dual-axis chart combining bar and line values.",
    demoData: "x\tbar\tline\nA\t12\t1.2\nB\t18\t1.9\nC\t9\t1.1\nD\t24\t2.4\n"
  },
  volcano: {
    requiredColumns: ["gene", "log2FC", "pvalue"],
    description: "Differential-expression scatter plot using log2 fold change and p value.",
    demoData: "gene\tlog2FC\tpvalue\nIL6\t2.4\t0.001\nSTAT1\t1.6\t0.02\nACTB\t0.1\t0.71\nCDH1\t-1.8\t0.008\n",
    defaults: { fcCutoff: 1, pCutoff: 0.05 }
  },
  manhattan: {
    requiredColumns: ["snp", "chrom", "position", "pvalue"],
    description: "GWAS-style chromosome scatter using genomic position and p value.",
    demoData: "snp\tchrom\tposition\tpvalue\nrs1\t1\t120\t0.02\nrs2\t1\t220\t0.0003\nrs3\t2\t140\t0.4\nrs4\t2\t360\t0.00001\n"
  },
  survival: {
    requiredColumns: ["time", "status", "group"],
    description: "Stepwise survival curves from time, status, and optional group columns.",
    demoData: "time\tstatus\tgroup\n2\t1\tLow\n5\t1\tLow\n7\t0\tLow\n3\t1\tHigh\n4\t1\tHigh\n6\t1\tHigh\n"
  },
  roc: {
    requiredColumns: ["fpr", "tpr"],
    description: "Receiver operating characteristic curve.",
    demoData: "fpr\ttpr\n0.00\t0.00\n0.05\t0.22\n0.12\t0.48\n0.25\t0.67\n1.00\t1.00\n"
  }
} satisfies Record<string, Profile>;

const seedTemplates: TemplateSpec[] = [
  ["pie", "2D Pie Plot", "Basic plot", 1, "pie", "python"],
  ["up-down-bar", "Gene Up/Down Bar", "Basic plot", 1, "bar", "python"],
  ["line", "Line Plot", "Basic plot", 1, "line", "python"],
  ["scatter", "Scatter Plot", "Basic plot", 1, "scatter", "python"],
  ["heatmap", "Cluster Heatmap", "Transcriptome", 4, "heatmap", "python"],
  ["volcano", "Volcano Plot", "Transcriptome", 3, "volcano", "python"],
  ["violin", "Violin Plot", "Transcriptome", 4, "distribution", "python"],
  ["bubble", "Enrichment Bubble", "Transcriptome", 6, "bubble", "python"],
  ["manhattan", "Manhattan Plot", "Genome", 1, "manhattan", "python"],
  ["km-survival", "Kaplan Meier Survival", "Clinical plot", 6, "survival", "r"],
  ["roc", "ROC Curve", "Clinical plot", 2, "roc", "python"],
  ["pca", "PCA Scatter", "Miscellaneous", 7, "pca", "python"]
];

const extraTemplates: TemplateSpec[] = [
  ["bp-cc-mf-3-in-1", "BP CC MF 3 in 1", "Enrichment", 1, "enrichment", "r"],
  ["circrna-mirna-ring", "circRNA-miRNA Ring", "Network and Set", 1, "network", "r"],
  ["alluvial-plot", "Alluvial Plot", "Network and Set", 1, "network", "python"],
  ["cerna", "ceRNA", "Network and Set", 1, "network", "r"],
  ["proportional-venn", "Proportional Venn", "Network and Set", 1, "set", "r"],
  ["upsetr", "UpSetR", "Network and Set", 1, "set", "r"],
  ["quadrant-scatter", "Quadrant Scatter", "Basic plot", 1, "scatter", "python"],
  ["waterfall-chart", "Waterfall Chart", "Basic plot", 1, "bar", "python"],
  ["ridgeline-joyplot", "Ridgeline Joyplot", "Statistical plot", 1, "density", "python"],
  ["smooth-line", "Smooth Line", "Basic plot", 1, "line", "python"],
  ["three-d-pie", "3D Pie", "Basic plot", 1, "pie", "python"],
  ["rectangle-funnel", "Rectangle Funnel", "Basic plot", 1, "funnel", "python"],
  ["dendrogram", "Dendrogram", "Statistical plot", 1, "hierarchy", "r"],
  ["element-statistics", "Element Statistics", "Basic plot", 1, "bar", "python"],
  ["box-with-jetter", "Box with Jetter", "Statistical plot", 2, "distribution", "python"],
  ["circle-square-area", "Circle Square Area", "Basic plot", 2, "bubble", "python"],
  ["half-circle-area", "Half Circle Area", "Basic plot", 2, "bubble", "python"],
  ["bar-with-errorbar", "Bar with Errorbar", "Basic plot", 2, "errorbar", "python"],
  ["pie-matrix", "Pie Matrix", "Basic plot", 2, "matrix", "python"],
  ["standalone-errorbar", "Standalone Errorbar", "Basic plot", 2, "errorbar", "python"],
  ["genomic-peak-venn", "Genomic Peak Venn", "Genome", 2, "set", "r"],
  ["beeswarm-box", "Beeswarm Box", "Statistical plot", 2, "distribution", "python"],
  ["expression-connection-lines", "Expression Connection Lines", "Transcriptome", 2, "line", "python"],
  ["x4-square-area", "x4 Square Area", "Basic plot", 2, "bubble", "python"],
  ["two-tracks-circos", "Two Tracks Circos", "Genome", 2, "genome", "r"],
  ["dumbbell-chart", "Dumbbell Chart", "Basic plot", 2, "dumbbell", "python"],
  ["m6a-expression-log2fc", "m6A and Expression log2FC", "Epigenome", 2, "epigenome", "r"],
  ["kernel-density", "Kernel Density", "Statistical plot", 2, "density", "python"],
  ["dual-y-bar", "Dual Y Bar", "Basic plot", 2, "dual-axis", "python"],
  ["filled-stackbar", "Filled Stackbar", "Basic plot", 2, "stacked-bar", "python"],
  ["flower-plot", "Flower Plot", "Network and Set", 2, "set", "r"],
  ["regression-scatter", "Regression Scatter", "Statistical plot", 3, "correlation", "python"],
  ["qqplot", "QQplot", "Statistical plot", 3, "qq", "python"],
  ["motif-logo", "Motif Logo", "Genome", 3, "sequence", "r"],
  ["scatter-plot-fold-change", "Scatter Plot Fold Change", "Transcriptome", 3, "scatter", "python"],
  ["three-d-scatter", "3D Scatter", "Basic plot", 3, "scatter", "python"],
  ["circular-cluster-heatmap", "Circular Cluster Heatmap", "Transcriptome", 3, "heatmap", "r"],
  ["boxplot-with-lines", "Boxplot with Lines", "Statistical plot", 3, "distribution", "python"],
  ["balloon-plot", "Balloon Plot", "Basic plot", 3, "bubble", "python"],
  ["pearson-spearman-scatter", "Pearson Spearman Scatter", "Statistical plot", 3, "correlation", "python"],
  ["waffle-chart", "Waffle Chart", "Basic plot", 3, "pie", "python"],
  ["funnel-plot", "Funnel Plot", "Basic plot", 3, "funnel", "python"],
  ["radar", "Radar", "Basic plot", 3, "radar", "python"],
  ["scatter-marginal-histograms", "Scatter with Marginal Histograms", "Statistical plot", 3, "scatter", "python"],
  ["butterfly-bar", "Butterfly Bar", "Basic plot", 3, "bar", "python"],
  ["area-plot", "Area Plot", "Basic plot", 3, "area", "python"],
  ["three-d-area-plot", "3D Area Plot", "Basic plot", 4, "area", "python"],
  ["area-stack", "Area Stack", "Basic plot", 4, "area", "python"],
  ["line-stack", "Line Stack", "Basic plot", 4, "line", "python"],
  ["vertical-bar-trend", "Vertical Bar with Trend", "Basic plot", 4, "dual-axis", "python"],
  ["horizontal-bar", "Horizontal Bar", "Basic plot", 4, "bar", "python"],
  ["treemap", "Treemap", "Basic plot", 4, "hierarchy", "python"],
  ["matrix-heatmap", "Matrix Heatmap", "Transcriptome", 4, "heatmap", "python"],
  ["vertical-lollipop", "Vertical Lollipop", "Basic plot", 4, "bar", "python"],
  ["horizontal-lollipop", "Horizontal Lollipop", "Basic plot", 4, "bar", "python"],
  ["horizontal-box-plot", "Horizontal Box Plot", "Statistical plot", 4, "distribution", "python"],
  ["violin-srplot-endpoint-2", "Violin Plot SRplot Endpoint 2", "Transcriptome", 4, "distribution", "python"],
  ["histogram-with-fit", "Histogram with Fit", "Statistical plot", 4, "density", "python"],
  ["correlation-dot", "Correlation Dot", "Statistical plot", 4, "correlation", "python"],
  ["stem-plot", "Stem Plot", "Basic plot", 4, "bar", "python"],
  ["polar-bar", "Polar Bar", "Basic plot", 4, "polar", "python"],
  ["vertical-bars", "Vertical Bars", "Basic plot", 4, "bar", "python"],
  ["dot-bars", "Dot Bars", "Basic plot", 4, "bar", "python"],
  ["vertical-stack-bars", "Vertical Stack Bars", "Basic plot", 4, "stacked-bar", "python"],
  ["horizontal-stack-bars", "Horizontal Stack Bars", "Basic plot", 5, "stacked-bar", "python"],
  ["dot-bar-plot", "Dot Bar Plot", "Basic plot", 5, "bar", "python"],
  ["bullet-chart", "Bullet Chart", "Basic plot", 5, "dual-axis", "python"],
  ["pathway-map-add-color", "Pathway Map Add Color", "Pathway and MAF", 5, "pathway", "r"],
  ["vertical-3d-bars", "Vertical 3D Bars", "Basic plot", 5, "bar", "python"],
  ["venn-diagram", "Venn Diagram", "Network and Set", 5, "set", "r"],
  ["correlation", "Correlation", "Statistical plot", 5, "correlation", "python"],
  ["donut-chart", "Donut Chart", "Basic plot", 5, "pie", "python"],
  ["pcr-rnaseq-dual-y", "PCR RNAseq Dual Y", "Transcriptome", 5, "dual-axis", "python"],
  ["go-chord", "GO Chord", "Enrichment", 5, "enrichment", "r"],
  ["peak-chromosome-distribution", "Peak Chromosome Distribution", "Genome", 5, "genome", "r"],
  ["two-layer-pie", "Two Layer Pie", "Basic plot", 5, "pie", "python"],
  ["circle-waffle", "Circle Waffle", "Basic plot", 5, "pie", "python"],
  ["two-layer-donut", "Two Layer Donut", "Basic plot", 5, "pie", "python"],
  ["trapezoid-funnel", "Trapezoid Funnel", "Basic plot", 5, "funnel", "python"],
  ["raincloud", "Raincloud", "Statistical plot", 5, "distribution", "python"],
  ["snp-likelihood", "SNP Likelihood", "Genome", 5, "genome", "python"],
  ["enrichment-bar-with-color", "Enrichment Bar with Color", "Enrichment", 6, "enrichment", "r"],
  ["triplex-dna", "Triplex DNA", "Genome", 6, "sequence", "r"],
  ["half-violin", "Half Violin", "Statistical plot", 6, "distribution", "python"],
  ["calendar-heatmap", "Calendar Heatmap", "Statistical plot", 6, "calendar", "python"],
  ["forest-plot", "Forest Plot", "Clinical plot", 6, "forest", "r"],
  ["two-directional-bars", "Two Directional Bars", "Basic plot", 6, "bar", "python"],
  ["expression-trend", "Expression Trend", "Transcriptome", 6, "line", "python"],
  ["upgma-cluster", "UPGMA Cluster", "Statistical plot", 6, "hierarchy", "r"],
  ["m6a-metaplot", "m6A Metaplot", "Epigenome", 6, "epigenome", "r"],
  ["multi-groups-bubble", "Multi Groups Bubble", "Transcriptome", 6, "bubble", "python"],
  ["violin-with-statistics", "Violin with Statistics", "Statistical plot", 6, "distribution", "python"],
  ["snp-density", "SNP Density", "Genome", 6, "genome", "python"],
  ["peak-chromosome-distribution-centromere", "Peak Chromosome Distribution with Centromere", "Genome", 6, "genome", "r"],
  ["go-kegg-bar-dot", "GO KEGG Bar Dot", "Enrichment", 6, "enrichment", "r"],
  ["voronoi-treemaps", "Voronoi Treemaps", "Basic plot", 6, "hierarchy", "python"],
  ["cerebro-colormap", "Cerebro Colormap", "Transcriptome", 7, "heatmap", "python"],
  ["bars-with-truncation", "Bars with Truncation", "Basic plot", 7, "bar", "python"],
  ["wordcloud", "Wordcloud", "Miscellaneous", 7, "wordcloud", "python"],
  ["wenxiang-diagram", "Wenxiang Diagram", "Network and Set", 7, "network", "python"],
  ["miranda-mirna-targets-prediction", "miRanda miRNA Targets Prediction", "Network and Set", 7, "network", "r"],
  ["sankey-and-dot", "Sankey and Dot", "Network and Set", 7, "network", "r"],
  ["go-pathway-enrichment-analysis", "GO Pathway Enrichment Analysis", "Enrichment", 7, "enrichment", "r"],
  ["eccdna-chromosome-distribution", "eccDNA Chromosome Distribution", "Genome", 7, "genome", "r"],
  ["pathway-summary", "Pathway Summary", "Pathway and MAF", 7, "pathway", "r"],
  ["paired-sequence-alignment-spirals", "Paired Sequence Alignment Spirals", "Genome", 7, "sequence", "r"],
  ["species-accumulation-curves", "Species Accumulation Curves", "Statistical plot", 7, "line", "python"],
  ["multi-types-pie", "Multi Types Pie", "Basic plot", 7, "pie", "python"],
  ["circle-packing", "Circle Packing", "Basic plot", 7, "hierarchy", "python"],
  ["maf-summary-plot", "MAF Summary Plot", "Pathway and MAF", 7, "maf", "r"],
  ["maf-oncoplot", "MAF Oncoplot", "Pathway and MAF", 7, "maf", "r"],
  ["two-three-category", "Two Three Category", "Basic plot", 7, "pie", "python"],
  ["principal-components-analysis", "Principal Components Analysis", "Miscellaneous", 7, "pca", "python"]
];

function sourceUrl(page: number, slug: string) {
  return `https://bioinformatics.com.cn/en?p=${page}#${slug}`;
}

function aliases(title: string, slug: string) {
  return Array.from(new Set([slug, title.toLowerCase(), title.toLowerCase().replace(/[/-]/g, " ")]));
}

function moduleFromSpec([slug, title, category, page, family, engine = "python"]: TemplateSpec): PlotModule {
  const profile: Profile = profiles[family];
  return {
    slug,
    title,
    category,
    description: profile.description,
    requiredColumns: profile.requiredColumns,
    defaultOptions: { width: 900, height: 620, fontFamily: "Arial", title, ...(profile.defaults ?? {}) },
    optionFields: [...commonFields, ...(profile.optionFields ?? [])],
    demoData: profile.demoData,
    citation,
    exportFormats: ["png", "tiff", "svg", "pdf"],
    sourceUrl: sourceUrl(page, slug),
    engine,
    rendererFamily: family,
    aliases: aliases(title, slug)
  };
}

const fallbackModules = [...seedTemplates, ...extraTemplates].map(moduleFromSpec);

export const fallbackGroups: Record<string, PlotModule[]> = fallbackModules.reduce<Record<string, PlotModule[]>>((groups, item) => {
  groups[item.category] = [...(groups[item.category] ?? []), item];
  return groups;
}, {});
