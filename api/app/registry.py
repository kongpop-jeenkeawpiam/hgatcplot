from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EXPORT_FORMATS = ["png", "tiff", "svg", "pdf"]


@dataclass(frozen=True)
class OptionField:
    key: str
    label: str
    kind: str
    default: Any
    choices: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlotModule:
    slug: str
    title: str
    category: str
    description: str
    required_columns: list[str]
    default_options: dict[str, Any]
    option_fields: list[OptionField]
    demo_data: str
    citation: str
    export_formats: list[str] = field(default_factory=lambda: EXPORT_FORMATS.copy())


COMMON_OPTIONS = [
    OptionField("width", "Figure width", "number", 900),
    OptionField("height", "Figure height", "number", 620),
    OptionField("fontFamily", "Font family", "select", "Arial", ["Arial", "Times New Roman"]),
    OptionField("title", "Plot title", "text", ""),
]


def list_modules() -> list[PlotModule]:
    return list(MODULES)


def grouped_modules() -> dict[str, list[PlotModule]]:
    groups: dict[str, list[PlotModule]] = {}
    for module in MODULES:
        groups.setdefault(module.category, []).append(module)
    return groups


def get_module(slug: str) -> PlotModule:
    for module in MODULES:
        if module.slug == slug:
            return module
    raise KeyError(f"Unknown plot module: {slug}")


def module_to_dict(module: PlotModule) -> dict[str, Any]:
    return {
        "slug": module.slug,
        "title": module.title,
        "category": module.category,
        "description": module.description,
        "requiredColumns": module.required_columns,
        "defaultOptions": module.default_options,
        "optionFields": [field.__dict__ for field in module.option_fields],
        "demoData": module.demo_data,
        "citation": module.citation,
        "exportFormats": module.export_formats,
    }


def grouped_modules_to_dict() -> dict[str, list[dict[str, Any]]]:
    return {
        category: [module_to_dict(module) for module in modules]
        for category, modules in grouped_modules().items()
    }


def _options(**overrides: Any) -> dict[str, Any]:
    values = {field.key: field.default for field in COMMON_OPTIONS}
    values.update(overrides)
    return values


CITATION = (
    "Tang D, Chen M, Huang X, Zhang G, Zeng L, Zhang G, Wu S, Wang Y. "
    "SRplot: A free online platform for data visualization and graphing. "
    "PLoS One. 2023 Nov 9;18(11):e0294236. doi: 10.1371/journal.pone.0294236."
)


MODULES: tuple[PlotModule, ...] = (
    PlotModule(
        slug="pie",
        title="2D Pie Plot",
        category="Basic plot",
        description="Proportional chart for category/value data.",
        required_columns=["class", "value"],
        default_options=_options(title="Class composition"),
        option_fields=COMMON_OPTIONS + [OptionField("legend", "Legend", "select", "yes", ["yes", "no"])],
        demo_data="class\tvalue\nTSS200\t20.93\nTSS1500\t21.68\n5UTR\t21.45\nGene body\t20.86\n3UTR\t6.36\n1st exon\t8.72\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="up-down-bar",
        title="Gene Up/Down Bar",
        category="Basic plot",
        description="Fold-change bars split above and below the baseline.",
        required_columns=["gene", "log2FC"],
        default_options=_options(title="Differential fold change", upColor="#d94b42", downColor="#2f9e6d"),
        option_fields=COMMON_OPTIONS
        + [
            OptionField("upColor", "Up color", "color", "#d94b42"),
            OptionField("downColor", "Down color", "color", "#2f9e6d"),
        ],
        demo_data="gene\tlog2FC\nMIR21\t2.1\nMIR155\t1.4\nCDH1\t-1.6\nPTEN\t-2.3\nMYC\t1.9\nTP53\t-1.1\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="line",
        title="Line Plot",
        category="Basic plot",
        description="Trend chart for ordered x/y observations.",
        required_columns=["x", "y"],
        default_options=_options(title="Time course"),
        option_fields=COMMON_OPTIONS,
        demo_data="x\ty\n0\t2.0\n1\t2.8\n2\t3.4\n3\t4.1\n4\t4.8\n5\t5.5\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="scatter",
        title="Scatter Plot",
        category="Basic plot",
        description="Point cloud for two quantitative columns.",
        required_columns=["x", "y"],
        default_options=_options(title="Expression correlation"),
        option_fields=COMMON_OPTIONS,
        demo_data="x\ty\n1.0\t1.2\n1.4\t1.9\n2.1\t2.8\n2.8\t2.7\n3.4\t3.9\n4.1\t4.8\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="heatmap",
        title="Cluster Heatmap",
        category="Transcriptome",
        description="Matrix heatmap for expression-like data.",
        required_columns=["gene", "sample1", "sample2"],
        default_options=_options(title="Expression heatmap", lowColor="#3a6ea5", highColor="#c94c4c"),
        option_fields=COMMON_OPTIONS
        + [
            OptionField("lowColor", "Low color", "color", "#3a6ea5"),
            OptionField("highColor", "High color", "color", "#c94c4c"),
        ],
        demo_data="gene\tsample1\tsample2\tsample3\tsample4\nACTB\t1.2\t1.8\t2.2\t2.9\nGAPDH\t2.4\t2.1\t1.9\t1.5\nMYC\t0.8\t1.1\t2.8\t3.2\nTP53\t3.1\t2.8\t1.4\t1.2\nVEGFA\t1.0\t1.6\t2.1\t2.7\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="volcano",
        title="Volcano Plot",
        category="Transcriptome",
        description="Differential-expression scatter plot using log2 fold change and p value.",
        required_columns=["gene", "log2FC", "pvalue"],
        default_options=_options(title="Differential expression", fcCutoff=1.0, pCutoff=0.05),
        option_fields=COMMON_OPTIONS
        + [
            OptionField("fcCutoff", "Fold-change cutoff", "number", 1.0),
            OptionField("pCutoff", "P/FDR cutoff", "number", 0.05),
        ],
        demo_data="gene\tlog2FC\tpvalue\nIL6\t2.4\t0.001\nSTAT1\t1.6\t0.02\nACTB\t0.1\t0.71\nCDH1\t-1.8\t0.008\nPTEN\t-2.5\t0.0004\nGAPDH\t0.2\t0.48\nMYC\t1.1\t0.041\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="violin",
        title="Violin Plot",
        category="Transcriptome",
        description="Distribution plot grouped by category.",
        required_columns=["group", "value"],
        default_options=_options(title="Group distributions"),
        option_fields=COMMON_OPTIONS,
        demo_data="group\tvalue\nControl\t2.1\nControl\t2.4\nControl\t2.6\nControl\t2.9\nTreatment\t3.1\nTreatment\t3.7\nTreatment\t4.0\nTreatment\t4.2\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="bubble",
        title="Enrichment Bubble",
        category="Transcriptome",
        description="Bubble chart for enrichment terms, ratios, and significance.",
        required_columns=["term", "ratio", "pvalue", "count"],
        default_options=_options(title="GO enrichment bubble"),
        option_fields=COMMON_OPTIONS,
        demo_data="term\tratio\tpvalue\tcount\nimmune response\t0.42\t0.001\t18\ncell cycle\t0.33\t0.004\t14\napoptosis\t0.29\t0.015\t11\nangiogenesis\t0.22\t0.03\t8\nmetabolism\t0.18\t0.04\t7\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="manhattan",
        title="Manhattan Plot",
        category="Genome",
        description="GWAS-style chromosome scatter using genomic position and p value.",
        required_columns=["snp", "chrom", "position", "pvalue"],
        default_options=_options(title="GWAS Manhattan plot", threshold=0.00001),
        option_fields=COMMON_OPTIONS + [OptionField("threshold", "Significance threshold", "number", 0.00001)],
        demo_data="snp\tchrom\tposition\tpvalue\nrs1\t1\t120\t0.02\nrs2\t1\t220\t0.0003\nrs3\t2\t140\t0.4\nrs4\t2\t360\t0.00001\nrs5\t3\t180\t0.07\nrs6\t3\t410\t0.0008\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="km-survival",
        title="Kaplan Meier Survival",
        category="Clinical plot",
        description="Stepwise survival curves from time, status, and optional group columns.",
        required_columns=["time", "status", "group"],
        default_options=_options(title="Kaplan Meier survival", confidence="show"),
        option_fields=COMMON_OPTIONS + [OptionField("confidence", "Confidence band", "select", "show", ["show", "hide"])],
        demo_data="time\tstatus\tgroup\n2\t1\tLow\n5\t1\tLow\n7\t0\tLow\n9\t1\tLow\n3\t1\tHigh\n4\t1\tHigh\n6\t1\tHigh\n8\t0\tHigh\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="roc",
        title="ROC Curve",
        category="Clinical plot",
        description="Receiver operating characteristic curve with AUC-like visual summary.",
        required_columns=["fpr", "tpr"],
        default_options=_options(title="ROC curve"),
        option_fields=COMMON_OPTIONS,
        demo_data="fpr\ttpr\n0.00\t0.00\n0.05\t0.22\n0.12\t0.48\n0.25\t0.67\n0.40\t0.81\n0.65\t0.92\n1.00\t1.00\n",
        citation=CITATION,
    ),
    PlotModule(
        slug="pca",
        title="PCA Scatter",
        category="Miscellaneous",
        description="Principal component scatter for sample-level coordinates.",
        required_columns=["sample", "pc1", "pc2", "group"],
        default_options=_options(title="PCA sample map"),
        option_fields=COMMON_OPTIONS,
        demo_data="sample\tpc1\tpc2\tgroup\nS1\t-2.1\t1.2\tControl\nS2\t-1.7\t0.9\tControl\nS3\t-1.2\t1.5\tControl\nS4\t1.5\t-1.1\tTreatment\nS5\t1.9\t-0.8\tTreatment\nS6\t2.3\t-1.4\tTreatment\n",
        citation=CITATION,
    ),
)

