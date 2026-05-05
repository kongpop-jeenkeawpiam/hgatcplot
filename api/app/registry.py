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
class FamilyProfile:
    required_columns: list[str]
    demo_data: str
    description: str
    defaults: dict[str, Any] = field(default_factory=dict)
    option_fields: list[OptionField] = field(default_factory=list)


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
    source_url: str
    engine: str
    renderer_family: str
    aliases: list[str] = field(default_factory=list)
    r_packages: list[str] = field(default_factory=list)
    export_formats: list[str] = field(default_factory=lambda: EXPORT_FORMATS.copy())


COMMON_OPTIONS = [
    OptionField("width", "Figure width", "number", 900),
    OptionField("height", "Figure height", "number", 620),
    OptionField("fontFamily", "Font family", "select", "Arial", ["Arial", "Times New Roman"]),
    OptionField("title", "Plot title", "text", ""),
]

COLOR_OPTIONS = [
    OptionField("primaryColor", "Primary color", "color", "#2f6f73"),
    OptionField("accentColor", "Accent color", "color", "#d36f45"),
]

FAMILY_PROFILES: dict[str, FamilyProfile] = {
    "pie": FamilyProfile(
        ["class", "value"],
        "class\tvalue\nTSS200\t20.93\nTSS1500\t21.68\n5UTR\t21.45\nGene body\t20.86\n3UTR\t6.36\n1st exon\t8.72\n",
        "Proportional chart for category/value data.",
        option_fields=[OptionField("legend", "Legend", "select", "yes", ["yes", "no"])],
    ),
    "bar": FamilyProfile(
        ["label", "value"],
        "label\tvalue\nA\t12\nB\t18\nC\t9\nD\t24\nE\t15\n",
        "Bar chart for ranked categorical values.",
        option_fields=COLOR_OPTIONS + [OptionField("orientation", "Orientation", "select", "vertical", ["vertical", "horizontal"])],
    ),
    "errorbar": FamilyProfile(
        ["label", "value", "error"],
        "label\tvalue\terror\nA\t12\t1.3\nB\t18\t2.1\nC\t9\t0.9\nD\t24\t2.7\n",
        "Mean-value chart with symmetric error intervals.",
        option_fields=COLOR_OPTIONS,
    ),
    "stacked-bar": FamilyProfile(
        ["category", "series", "value"],
        "category\tseries\tvalue\nA\tUp\t12\nA\tDown\t7\nB\tUp\t18\nB\tDown\t9\nC\tUp\t11\nC\tDown\t13\n",
        "Stacked bar chart for category and series totals.",
        option_fields=COLOR_OPTIONS,
    ),
    "line": FamilyProfile(
        ["x", "y", "group"],
        "x\ty\tgroup\n0\t2.0\tA\n1\t2.8\tA\n2\t3.4\tA\n3\t4.1\tA\n0\t1.5\tB\n1\t2.0\tB\n2\t2.7\tB\n3\t3.2\tB\n",
        "Trend chart for ordered x/y observations.",
        option_fields=COLOR_OPTIONS + [OptionField("smooth", "Smooth", "select", "no", ["yes", "no"])],
    ),
    "area": FamilyProfile(
        ["x", "y", "group"],
        "x\ty\tgroup\n0\t1.8\tA\n1\t2.5\tA\n2\t3.0\tA\n3\t3.9\tA\n0\t0.8\tB\n1\t1.4\tB\n2\t1.9\tB\n3\t2.2\tB\n",
        "Area chart for cumulative or grouped trends.",
        option_fields=COLOR_OPTIONS,
    ),
    "scatter": FamilyProfile(
        ["x", "y", "group"],
        "x\ty\tgroup\n1.0\t1.2\tA\n1.4\t1.9\tA\n2.1\t2.8\tB\n2.8\t2.7\tB\n3.4\t3.9\tC\n4.1\t4.8\tC\n",
        "Point cloud for two quantitative columns.",
        option_fields=COLOR_OPTIONS + [OptionField("pointSize", "Point size", "number", 64)],
    ),
    "bubble": FamilyProfile(
        ["term", "ratio", "pvalue", "count"],
        "term\tratio\tpvalue\tcount\nimmune response\t0.42\t0.001\t18\ncell cycle\t0.33\t0.004\t14\napoptosis\t0.29\t0.015\t11\nangiogenesis\t0.22\t0.03\t8\nmetabolism\t0.18\t0.04\t7\n",
        "Bubble chart for terms, ratios, and significance.",
        defaults={"pCutoff": 0.05},
        option_fields=[OptionField("pCutoff", "P/FDR cutoff", "number", 0.05)],
    ),
    "enrichment": FamilyProfile(
        ["term", "ratio", "pvalue", "count"],
        "term\tratio\tpvalue\tcount\nGO immune response\t0.42\t0.001\t18\nKEGG cell cycle\t0.33\t0.004\t14\nGO apoptosis\t0.29\t0.015\t11\nKEGG angiogenesis\t0.22\t0.03\t8\n",
        "GO, KEGG, or pathway enrichment summary.",
        defaults={"pCutoff": 0.05},
        option_fields=[OptionField("pCutoff", "P/FDR cutoff", "number", 0.05)],
    ),
    "distribution": FamilyProfile(
        ["group", "value"],
        "group\tvalue\nControl\t2.1\nControl\t2.4\nControl\t2.6\nControl\t2.9\nTreatment\t3.1\nTreatment\t3.7\nTreatment\t4.0\nTreatment\t4.2\n",
        "Distribution plot grouped by category.",
        option_fields=COLOR_OPTIONS + [OptionField("showPoints", "Show points", "select", "yes", ["yes", "no"])],
    ),
    "density": FamilyProfile(
        ["group", "value"],
        "group\tvalue\nA\t1.2\nA\t1.4\nA\t1.9\nA\t2.1\nA\t2.4\nB\t2.0\nB\t2.6\nB\t3.0\nB\t3.2\nB\t3.6\n",
        "Density or histogram view of numeric distributions.",
        option_fields=COLOR_OPTIONS,
    ),
    "heatmap": FamilyProfile(
        ["gene", "sample1", "sample2"],
        "gene\tsample1\tsample2\tsample3\tsample4\nACTB\t1.2\t1.8\t2.2\t2.9\nGAPDH\t2.4\t2.1\t1.9\t1.5\nMYC\t0.8\t1.1\t2.8\t3.2\nTP53\t3.1\t2.8\t1.4\t1.2\nVEGFA\t1.0\t1.6\t2.1\t2.7\n",
        "Matrix heatmap for expression-like data.",
        option_fields=[OptionField("lowColor", "Low color", "color", "#3a6ea5"), OptionField("highColor", "High color", "color", "#c94c4c")],
    ),
    "matrix": FamilyProfile(
        ["row", "column", "value"],
        "row\tcolumn\tvalue\nA\tS1\t1.2\nA\tS2\t2.1\nB\tS1\t2.7\nB\tS2\t1.5\nC\tS1\t3.1\nC\tS2\t2.4\n",
        "Long-form matrix heatmap.",
        option_fields=[OptionField("lowColor", "Low color", "color", "#3a6ea5"), OptionField("highColor", "High color", "color", "#c94c4c")],
    ),
    "set": FamilyProfile(
        ["set", "count"],
        "set\tcount\nA only\t18\nB only\t11\nA and B\t7\nC only\t9\nA and C\t5\nB and C\t4\n",
        "Set overlap visualization for list intersections.",
        option_fields=COLOR_OPTIONS + [OptionField("showPercent", "Show percent", "select", "yes", ["yes", "no"])],
    ),
    "network": FamilyProfile(
        ["source", "target", "weight"],
        "source\ttarget\tweight\ncircRNA1\tmiR-21\t3\ncircRNA1\tmiR-155\t2\nmiR-21\tPTEN\t4\nmiR-155\tSOCS1\t3\nlncRNA1\tmiR-21\t2\n",
        "Relationship diagram for source, target, and edge weight data.",
        option_fields=COLOR_OPTIONS,
    ),
    "hierarchy": FamilyProfile(
        ["parent", "child", "value"],
        "parent\tchild\tvalue\nRoot\tImmune\t18\nRoot\tCell cycle\t14\nImmune\tCytokine\t8\nImmune\tT cell\t10\nCell cycle\tG1\t6\nCell cycle\tG2M\t8\n",
        "Hierarchical summary for tree, packing, treemap, or clustering views.",
        option_fields=COLOR_OPTIONS,
    ),
    "funnel": FamilyProfile(
        ["stage", "value"],
        "stage\tvalue\nInput genes\t1200\nFiltered\t820\nMapped\t510\nSignificant\t180\nReported\t64\n",
        "Funnel chart for ordered step reductions.",
        option_fields=COLOR_OPTIONS,
    ),
    "dumbbell": FamilyProfile(
        ["label", "start", "end"],
        "label\tstart\tend\nGene A\t1.2\t2.4\nGene B\t1.6\t2.1\nGene C\t2.3\t1.7\nGene D\t0.9\t1.8\n",
        "Dumbbell chart comparing paired values.",
        option_fields=COLOR_OPTIONS,
    ),
    "correlation": FamilyProfile(
        ["x", "y"],
        "x\ty\n1.0\t1.2\n1.4\t1.9\n2.1\t2.8\n2.8\t2.7\n3.4\t3.9\n4.1\t4.8\n",
        "Correlation scatter or dot summary.",
        option_fields=COLOR_OPTIONS,
    ),
    "qq": FamilyProfile(
        ["expected", "observed"],
        "expected\tobserved\n0.1\t0.12\n0.2\t0.18\n0.3\t0.32\n0.4\t0.47\n0.5\t0.62\n0.6\t0.71\n",
        "Quantile-quantile diagnostic plot.",
        option_fields=COLOR_OPTIONS,
    ),
    "radar": FamilyProfile(
        ["axis", "value", "group"],
        "axis\tvalue\tgroup\nA\t0.8\tSample1\nB\t0.6\tSample1\nC\t0.9\tSample1\nD\t0.5\tSample1\nA\t0.5\tSample2\nB\t0.8\tSample2\nC\t0.6\tSample2\nD\t0.7\tSample2\n",
        "Radar or polar category profile.",
        option_fields=COLOR_OPTIONS,
    ),
    "polar": FamilyProfile(
        ["label", "value"],
        "label\tvalue\nA\t12\nB\t18\nC\t9\nD\t24\nE\t15\n",
        "Polar bar chart for circular category values.",
        option_fields=COLOR_OPTIONS,
    ),
    "calendar": FamilyProfile(
        ["date", "value"],
        "date\tvalue\n2026-01-01\t5\n2026-01-02\t8\n2026-01-03\t4\n2026-01-04\t12\n2026-01-05\t7\n2026-01-06\t10\n",
        "Calendar heatmap for date-indexed values.",
        option_fields=COLOR_OPTIONS,
    ),
    "forest": FamilyProfile(
        ["study", "effect", "low", "high"],
        "study\teffect\tlow\thigh\nCohort A\t1.25\t0.98\t1.56\nCohort B\t0.86\t0.64\t1.12\nCohort C\t1.48\t1.10\t1.92\nCohort D\t1.05\t0.82\t1.31\n",
        "Forest plot for estimates and confidence intervals.",
        defaults={"referenceLine": 1.0},
        option_fields=[OptionField("referenceLine", "Reference line", "number", 1.0)],
    ),
    "genome": FamilyProfile(
        ["chrom", "position", "value"],
        "chrom\tposition\tvalue\n1\t120\t2.4\n1\t220\t4.1\n2\t140\t1.3\n2\t360\t5.0\n3\t180\t2.1\n3\t410\t3.8\n",
        "Genome-position plot for chromosome tracks or densities.",
        defaults={"threshold": 3.0},
        option_fields=[OptionField("threshold", "Threshold", "number", 3.0)],
    ),
    "epigenome": FamilyProfile(
        ["feature", "position", "log2FC"],
        "feature\tposition\tlog2FC\nPeak1\t120\t1.4\nPeak2\t260\t-0.8\nPeak3\t420\t2.1\nPeak4\t620\t-1.6\nPeak5\t880\t0.7\n",
        "Epigenomic summary for peak, methylation, or expression change data.",
        defaults={"threshold": 1.0},
        option_fields=[OptionField("threshold", "Threshold", "number", 1.0)],
    ),
    "pathway": FamilyProfile(
        ["pathway", "gene", "value"],
        "pathway\tgene\tvalue\nApoptosis\tCASP3\t2.1\nApoptosis\tBAX\t1.7\nCell cycle\tCDK1\t2.5\nCell cycle\tCCNB1\t1.9\nMAPK\tMAPK1\t1.4\n",
        "Pathway-centric gene/value summary.",
        option_fields=COLOR_OPTIONS,
    ),
    "sequence": FamilyProfile(
        ["position", "symbol", "score"],
        "position\tsymbol\tscore\n1\tA\t0.8\n2\tC\t1.2\n3\tG\t0.9\n4\tT\t1.4\n5\tA\t1.1\n6\tG\t1.5\n",
        "Sequence-position plot for motifs, alignments, or base scores.",
        defaults={"scoreCutoff": 1.0},
        option_fields=[OptionField("scoreCutoff", "Score cutoff", "number", 1.0)],
    ),
    "wordcloud": FamilyProfile(
        ["word", "weight"],
        "word\tweight\nimmune\t30\ncell\t24\nsignal\t18\npathway\t14\nexpression\t12\ngenome\t10\n",
        "Weighted term cloud.",
        defaults={"maxWords": 60},
        option_fields=[OptionField("maxWords", "Max words", "number", 60)],
    ),
    "maf": FamilyProfile(
        ["gene", "sample", "mutation"],
        "gene\tsample\tmutation\nTP53\tS1\tMissense\nKRAS\tS1\tMissense\nEGFR\tS2\tAmplification\nPIK3CA\tS3\tMissense\nTP53\tS4\tNonsense\n",
        "Mutation annotation format summary.",
        defaults={"topGenes": 20},
        option_fields=[OptionField("topGenes", "Top genes", "number", 20)],
    ),
    "pca": FamilyProfile(
        ["sample", "pc1", "pc2", "group"],
        "sample\tpc1\tpc2\tgroup\nS1\t-2.1\t1.2\tControl\nS2\t-1.7\t0.9\tControl\nS3\t-1.2\t1.5\tControl\nS4\t1.5\t-1.1\tTreatment\nS5\t1.9\t-0.8\tTreatment\nS6\t2.3\t-1.4\tTreatment\n",
        "Principal component scatter for sample coordinates.",
        option_fields=COLOR_OPTIONS,
    ),
    "dual-axis": FamilyProfile(
        ["x", "bar", "line"],
        "x\tbar\tline\nA\t12\t1.2\nB\t18\t1.9\nC\t9\t1.1\nD\t24\t2.4\nE\t15\t1.7\n",
        "Dual-axis chart combining bar and line values.",
        option_fields=COLOR_OPTIONS,
    ),
}


CITATION = (
    "Tang D, Chen M, Huang X, Zhang G, Zeng L, Zhang G, Wu S, Wang Y. "
    "SRplot: A free online platform for data visualization and graphing. "
    "PLoS One. 2023 Nov 9;18(11):e0294236. doi: 10.1371/journal.pone.0294236."
)


def list_modules() -> list[PlotModule]:
    return list(MODULES)


def grouped_modules() -> dict[str, list[PlotModule]]:
    groups: dict[str, list[PlotModule]] = {}
    for module in MODULES:
        groups.setdefault(module.category, []).append(module)
    return groups


def get_module(slug: str) -> PlotModule:
    normalized = slug.lower()
    for module in MODULES:
        if module.slug == normalized or normalized in module.aliases:
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
        "sourceUrl": module.source_url,
        "engine": module.engine,
        "rendererFamily": module.renderer_family,
        "aliases": module.aliases,
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


def _source_url(page: int, slug: str) -> str:
    return f"https://bioinformatics.com.cn/en?p={page}#{slug}"


def _aliases(title: str, slug: str, extras: list[str] | None = None) -> list[str]:
    values = {slug, title.lower(), title.lower().replace("/", " "), title.lower().replace("-", " ")}
    values.update(alias.lower() for alias in (extras or []))
    return sorted(values)


def _template(
    slug: str,
    title: str,
    category: str,
    page: int,
    family: str,
    engine: str = "python",
    description: str | None = None,
    aliases: list[str] | None = None,
    r_packages: list[str] | None = None,
) -> PlotModule:
    profile = FAMILY_PROFILES[family]
    return PlotModule(
        slug=slug,
        title=title,
        category=category,
        description=description or profile.description,
        required_columns=profile.required_columns,
        default_options=_options(title=title, **profile.defaults),
        option_fields=COMMON_OPTIONS + profile.option_fields,
        demo_data=profile.demo_data,
        citation=CITATION,
        source_url=_source_url(page, slug),
        engine=engine,
        renderer_family=family,
        aliases=_aliases(title, slug, aliases),
        r_packages=r_packages or [],
    )


def _seed_modules() -> list[PlotModule]:
    return [
        PlotModule(
            slug="pie",
            title="2D Pie Plot",
            category="Basic plot",
            description=FAMILY_PROFILES["pie"].description,
            required_columns=["class", "value"],
            default_options=_options(title="Class composition"),
            option_fields=COMMON_OPTIONS + [OptionField("legend", "Legend", "select", "yes", ["yes", "no"])],
            demo_data=FAMILY_PROFILES["pie"].demo_data,
            citation=CITATION,
            source_url=_source_url(1, "pie"),
            engine="python",
            renderer_family="pie",
            aliases=_aliases("2D Pie Plot", "pie", ["pie chart"]),
        ),
        PlotModule(
            slug="up-down-bar",
            title="Gene Up/Down Bar",
            category="Basic plot",
            description="Fold-change bars split above and below the baseline.",
            required_columns=["gene", "log2FC"],
            default_options=_options(title="Differential fold change", upColor="#d94b42", downColor="#2f9e6d"),
            option_fields=COMMON_OPTIONS + [OptionField("upColor", "Up color", "color", "#d94b42"), OptionField("downColor", "Down color", "color", "#2f9e6d")],
            demo_data="gene\tlog2FC\nMIR21\t2.1\nMIR155\t1.4\nCDH1\t-1.6\nPTEN\t-2.3\nMYC\t1.9\nTP53\t-1.1\n",
            citation=CITATION,
            source_url=_source_url(1, "up-down-bar"),
            engine="python",
            renderer_family="bar",
            aliases=_aliases("Gene Up/Down Bar", "up-down-bar", ["fold change bar"]),
        ),
        _template("line", "Line Plot", "Basic plot", 1, "line", aliases=["trend line"]),
        _template("scatter", "Scatter Plot", "Basic plot", 1, "scatter"),
        _template("heatmap", "Cluster Heatmap", "Transcriptome", 4, "heatmap", description="Matrix heatmap for expression-like data.", aliases=["cluster heat map"]),
        PlotModule(
            slug="volcano",
            title="Volcano Plot",
            category="Transcriptome",
            description="Differential-expression scatter plot using log2 fold change and p value.",
            required_columns=["gene", "log2FC", "pvalue"],
            default_options=_options(title="Differential expression", fcCutoff=1.0, pCutoff=0.05),
            option_fields=COMMON_OPTIONS + [OptionField("fcCutoff", "Fold-change cutoff", "number", 1.0), OptionField("pCutoff", "P/FDR cutoff", "number", 0.05)],
            demo_data="gene\tlog2FC\tpvalue\nIL6\t2.4\t0.001\nSTAT1\t1.6\t0.02\nACTB\t0.1\t0.71\nCDH1\t-1.8\t0.008\nPTEN\t-2.5\t0.0004\nGAPDH\t0.2\t0.48\nMYC\t1.1\t0.041\n",
            citation=CITATION,
            source_url=_source_url(3, "volcano"),
            engine="python",
            renderer_family="volcano",
            aliases=_aliases("Volcano Plot", "volcano", ["differential expression"]),
        ),
        _template("violin", "Violin Plot", "Transcriptome", 4, "distribution", description="Distribution plot grouped by category."),
        _template("bubble", "Enrichment Bubble", "Transcriptome", 6, "bubble", description="Bubble chart for enrichment terms, ratios, and significance.", aliases=["go bubble"]),
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
            source_url=_source_url(1, "manhattan"),
            engine="python",
            renderer_family="genome",
            aliases=_aliases("Manhattan Plot", "manhattan", ["gwas"]),
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
            source_url=_source_url(6, "km-survival"),
            engine="r",
            renderer_family="survival",
            aliases=_aliases("Kaplan Meier Survival", "km-survival", ["kaplan-meier", "survival"]),
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
            source_url=_source_url(2, "roc"),
            engine="python",
            renderer_family="roc",
            aliases=_aliases("ROC Curve", "roc", ["auc"]),
        ),
        _template("pca", "PCA Scatter", "Miscellaneous", 7, "pca", aliases=["principal component analysis"]),
    ]


EXTRA_TEMPLATES: tuple[tuple[str, str, str, int, str, str], ...] = (
    ("bp-cc-mf-3-in-1", "BP CC MF 3 in 1", "Enrichment", 1, "enrichment", "r"),
    ("circrna-mirna-ring", "circRNA-miRNA Ring", "Network and Set", 1, "network", "r"),
    ("alluvial-plot", "Alluvial Plot", "Network and Set", 1, "network", "python"),
    ("cerna", "ceRNA", "Network and Set", 1, "network", "r"),
    ("proportional-venn", "Proportional Venn", "Network and Set", 1, "set", "r"),
    ("upsetr", "UpSetR", "Network and Set", 1, "set", "r"),
    ("quadrant-scatter", "Quadrant Scatter", "Basic plot", 1, "scatter", "python"),
    ("waterfall-chart", "Waterfall Chart", "Basic plot", 1, "bar", "python"),
    ("ridgeline-joyplot", "Ridgeline Joyplot", "Statistical plot", 1, "density", "python"),
    ("smooth-line", "Smooth Line", "Basic plot", 1, "line", "python"),
    ("three-d-pie", "3D Pie", "Basic plot", 1, "pie", "python"),
    ("rectangle-funnel", "Rectangle Funnel", "Basic plot", 1, "funnel", "python"),
    ("dendrogram", "Dendrogram", "Statistical plot", 1, "hierarchy", "r"),
    ("element-statistics", "Element Statistics", "Basic plot", 1, "bar", "python"),
    ("box-with-jetter", "Box with Jetter", "Statistical plot", 2, "distribution", "python"),
    ("circle-square-area", "Circle Square Area", "Basic plot", 2, "bubble", "python"),
    ("half-circle-area", "Half Circle Area", "Basic plot", 2, "bubble", "python"),
    ("bar-with-errorbar", "Bar with Errorbar", "Basic plot", 2, "errorbar", "python"),
    ("pie-matrix", "Pie Matrix", "Basic plot", 2, "matrix", "python"),
    ("standalone-errorbar", "Standalone Errorbar", "Basic plot", 2, "errorbar", "python"),
    ("genomic-peak-venn", "Genomic Peak Venn", "Genome", 2, "set", "r"),
    ("beeswarm-box", "Beeswarm Box", "Statistical plot", 2, "distribution", "python"),
    ("expression-connection-lines", "Expression Connection Lines", "Transcriptome", 2, "line", "python"),
    ("x4-square-area", "x4 Square Area", "Basic plot", 2, "bubble", "python"),
    ("two-tracks-circos", "Two Tracks Circos", "Genome", 2, "genome", "r"),
    ("dumbbell-chart", "Dumbbell Chart", "Basic plot", 2, "dumbbell", "python"),
    ("m6a-expression-log2fc", "m6A and Expression log2FC", "Epigenome", 2, "epigenome", "r"),
    ("kernel-density", "Kernel Density", "Statistical plot", 2, "density", "python"),
    ("dual-y-bar", "Dual Y Bar", "Basic plot", 2, "dual-axis", "python"),
    ("filled-stackbar", "Filled Stackbar", "Basic plot", 2, "stacked-bar", "python"),
    ("flower-plot", "Flower Plot", "Network and Set", 2, "set", "r"),
    ("regression-scatter", "Regression Scatter", "Statistical plot", 3, "correlation", "python"),
    ("qqplot", "QQplot", "Statistical plot", 3, "qq", "python"),
    ("motif-logo", "Motif Logo", "Genome", 3, "sequence", "r"),
    ("scatter-plot-fold-change", "Scatter Plot Fold Change", "Transcriptome", 3, "scatter", "python"),
    ("three-d-scatter", "3D Scatter", "Basic plot", 3, "scatter", "python"),
    ("circular-cluster-heatmap", "Circular Cluster Heatmap", "Transcriptome", 3, "heatmap", "r"),
    ("boxplot-with-lines", "Boxplot with Lines", "Statistical plot", 3, "distribution", "python"),
    ("balloon-plot", "Balloon Plot", "Basic plot", 3, "bubble", "python"),
    ("pearson-spearman-scatter", "Pearson Spearman Scatter", "Statistical plot", 3, "correlation", "python"),
    ("waffle-chart", "Waffle Chart", "Basic plot", 3, "pie", "python"),
    ("funnel-plot", "Funnel Plot", "Basic plot", 3, "funnel", "python"),
    ("radar", "Radar", "Basic plot", 3, "radar", "python"),
    ("scatter-marginal-histograms", "Scatter with Marginal Histograms", "Statistical plot", 3, "scatter", "python"),
    ("butterfly-bar", "Butterfly Bar", "Basic plot", 3, "bar", "python"),
    ("area-plot", "Area Plot", "Basic plot", 3, "area", "python"),
    ("three-d-area-plot", "3D Area Plot", "Basic plot", 4, "area", "python"),
    ("area-stack", "Area Stack", "Basic plot", 4, "area", "python"),
    ("line-stack", "Line Stack", "Basic plot", 4, "line", "python"),
    ("vertical-bar-trend", "Vertical Bar with Trend", "Basic plot", 4, "dual-axis", "python"),
    ("horizontal-bar", "Horizontal Bar", "Basic plot", 4, "bar", "python"),
    ("treemap", "Treemap", "Basic plot", 4, "hierarchy", "python"),
    ("matrix-heatmap", "Matrix Heatmap", "Transcriptome", 4, "heatmap", "python"),
    ("vertical-lollipop", "Vertical Lollipop", "Basic plot", 4, "bar", "python"),
    ("horizontal-lollipop", "Horizontal Lollipop", "Basic plot", 4, "bar", "python"),
    ("horizontal-box-plot", "Horizontal Box Plot", "Statistical plot", 4, "distribution", "python"),
    ("violin-srplot-endpoint-2", "Violin Plot SRplot Endpoint 2", "Transcriptome", 4, "distribution", "python"),
    ("histogram-with-fit", "Histogram with Fit", "Statistical plot", 4, "density", "python"),
    ("correlation-dot", "Correlation Dot", "Statistical plot", 4, "correlation", "python"),
    ("stem-plot", "Stem Plot", "Basic plot", 4, "bar", "python"),
    ("polar-bar", "Polar Bar", "Basic plot", 4, "polar", "python"),
    ("vertical-bars", "Vertical Bars", "Basic plot", 4, "bar", "python"),
    ("dot-bars", "Dot Bars", "Basic plot", 4, "bar", "python"),
    ("vertical-stack-bars", "Vertical Stack Bars", "Basic plot", 4, "stacked-bar", "python"),
    ("horizontal-stack-bars", "Horizontal Stack Bars", "Basic plot", 5, "stacked-bar", "python"),
    ("dot-bar-plot", "Dot Bar Plot", "Basic plot", 5, "bar", "python"),
    ("bullet-chart", "Bullet Chart", "Basic plot", 5, "dual-axis", "python"),
    ("pathway-map-add-color", "Pathway Map Add Color", "Pathway and MAF", 5, "pathway", "r"),
    ("vertical-3d-bars", "Vertical 3D Bars", "Basic plot", 5, "bar", "python"),
    ("venn-diagram", "Venn Diagram", "Network and Set", 5, "set", "r"),
    ("correlation", "Correlation", "Statistical plot", 5, "correlation", "python"),
    ("donut-chart", "Donut Chart", "Basic plot", 5, "pie", "python"),
    ("pcr-rnaseq-dual-y", "PCR RNAseq Dual Y", "Transcriptome", 5, "dual-axis", "python"),
    ("go-chord", "GO Chord", "Enrichment", 5, "enrichment", "r"),
    ("peak-chromosome-distribution", "Peak Chromosome Distribution", "Genome", 5, "genome", "r"),
    ("two-layer-pie", "Two Layer Pie", "Basic plot", 5, "pie", "python"),
    ("circle-waffle", "Circle Waffle", "Basic plot", 5, "pie", "python"),
    ("two-layer-donut", "Two Layer Donut", "Basic plot", 5, "pie", "python"),
    ("trapezoid-funnel", "Trapezoid Funnel", "Basic plot", 5, "funnel", "python"),
    ("raincloud", "Raincloud", "Statistical plot", 5, "distribution", "python"),
    ("snp-likelihood", "SNP Likelihood", "Genome", 5, "genome", "python"),
    ("enrichment-bar-with-color", "Enrichment Bar with Color", "Enrichment", 6, "enrichment", "r"),
    ("triplex-dna", "Triplex DNA", "Genome", 6, "sequence", "r"),
    ("half-violin", "Half Violin", "Statistical plot", 6, "distribution", "python"),
    ("calendar-heatmap", "Calendar Heatmap", "Statistical plot", 6, "calendar", "python"),
    ("forest-plot", "Forest Plot", "Clinical plot", 6, "forest", "r"),
    ("two-directional-bars", "Two Directional Bars", "Basic plot", 6, "bar", "python"),
    ("expression-trend", "Expression Trend", "Transcriptome", 6, "line", "python"),
    ("upgma-cluster", "UPGMA Cluster", "Statistical plot", 6, "hierarchy", "r"),
    ("m6a-metaplot", "m6A Metaplot", "Epigenome", 6, "epigenome", "r"),
    ("multi-groups-bubble", "Multi Groups Bubble", "Transcriptome", 6, "bubble", "python"),
    ("violin-with-statistics", "Violin with Statistics", "Statistical plot", 6, "distribution", "python"),
    ("snp-density", "SNP Density", "Genome", 6, "genome", "python"),
    ("peak-chromosome-distribution-centromere", "Peak Chromosome Distribution with Centromere", "Genome", 6, "genome", "r"),
    ("go-kegg-bar-dot", "GO KEGG Bar Dot", "Enrichment", 6, "enrichment", "r"),
    ("voronoi-treemaps", "Voronoi Treemaps", "Basic plot", 6, "hierarchy", "python"),
    ("cerebro-colormap", "Cerebro Colormap", "Transcriptome", 7, "heatmap", "python"),
    ("bars-with-truncation", "Bars with Truncation", "Basic plot", 7, "bar", "python"),
    ("wordcloud", "Wordcloud", "Miscellaneous", 7, "wordcloud", "python"),
    ("wenxiang-diagram", "Wenxiang Diagram", "Network and Set", 7, "network", "python"),
    ("miranda-mirna-targets-prediction", "miRanda miRNA Targets Prediction", "Network and Set", 7, "network", "r"),
    ("sankey-and-dot", "Sankey and Dot", "Network and Set", 7, "network", "r"),
    ("go-pathway-enrichment-analysis", "GO Pathway Enrichment Analysis", "Enrichment", 7, "enrichment", "r"),
    ("eccdna-chromosome-distribution", "eccDNA Chromosome Distribution", "Genome", 7, "genome", "r"),
    ("pathway-summary", "Pathway Summary", "Pathway and MAF", 7, "pathway", "r"),
    ("paired-sequence-alignment-spirals", "Paired Sequence Alignment Spirals", "Genome", 7, "sequence", "r"),
    ("species-accumulation-curves", "Species Accumulation Curves", "Statistical plot", 7, "line", "python"),
    ("multi-types-pie", "Multi Types Pie", "Basic plot", 7, "pie", "python"),
    ("circle-packing", "Circle Packing", "Basic plot", 7, "hierarchy", "python"),
    ("maf-summary-plot", "MAF Summary Plot", "Pathway and MAF", 7, "maf", "r"),
    ("maf-oncoplot", "MAF Oncoplot", "Pathway and MAF", 7, "maf", "r"),
    ("two-three-category", "Two Three Category", "Basic plot", 7, "pie", "python"),
    ("principal-components-analysis", "Principal Components Analysis", "Miscellaneous", 7, "pca", "python"),
)


def _build_modules() -> tuple[PlotModule, ...]:
    modules = _seed_modules()
    modules.extend(
        _template(slug, title, category, page, family, engine)
        for slug, title, category, page, family, engine in EXTRA_TEMPLATES
    )
    return tuple(modules)


MODULES: tuple[PlotModule, ...] = _build_modules()
