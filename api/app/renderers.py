from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.parser import ParsedTable, numeric_value
from app.registry import get_module, list_modules
from app.r_engine import run_r_renderer


PALETTE = ["#2f6f73", "#d36f45", "#6f5fa8", "#d1a53c", "#4f8f5f", "#b04c6f", "#58798a", "#8a6d3b"]


@dataclass(frozen=True)
class RenderResult:
    status: str
    artifacts: dict[str, str]
    warnings: list[str]
    errors: list[str]


@dataclass(frozen=True)
class RendererSpec:
    backend: str
    family: str
    svg_renderer: Callable[["SVGCanvas", ParsedTable, dict, str], None]


def render_plot(slug: str, parsed: ParsedTable, options: dict, output_dir: Path) -> RenderResult:
    module = get_module(slug)
    missing = [column for column in module.required_columns if column not in parsed.headers]
    if parsed.errors or missing:
        errors = parsed.errors.copy()
        if missing:
            errors.append(f"Missing required column(s): {', '.join(missing)}.")
        return RenderResult("failed", {}, parsed.warnings, errors)

    output_dir.mkdir(parents=True, exist_ok=True)
    width = _int_option(options, "width", module.default_options.get("width", 900), 520, 1800)
    height = _int_option(options, "height", module.default_options.get("height", 620), 360, 1400)
    title = str(options.get("title") or module.default_options.get("title") or module.title)

    if module.engine == "r":
        r_result = run_r_renderer(module, parsed, {**module.default_options, **options}, output_dir)
        return RenderResult(r_result.status, r_result.artifacts, r_result.warnings, r_result.errors)

    svg = SVGCanvas(width, height, title, str(options.get("fontFamily", "Arial")))
    renderer = _select_renderer(module)
    renderer(svg, parsed, {**module.default_options, **options}, title)
    svg_text = svg.finish()

    artifacts = {
        "svg": str(output_dir / "plot.svg"),
        "png": str(output_dir / "plot.png"),
        "tiff": str(output_dir / "plot.tiff"),
        "pdf": str(output_dir / "plot.pdf"),
    }
    if not _write_matplotlib_artifacts(slug, module.renderer_family, parsed, {**module.default_options, **options}, artifacts, width, height, title):
        Path(artifacts["svg"]).write_text(svg_text, encoding="utf-8")
        return RenderResult(
            "failed",
            {},
            parsed.warnings,
            ["Plot-specific export failed. Matplotlib must be available to generate PNG, TIFF, SVG, and PDF artifacts."],
        )
    return RenderResult("succeeded", artifacts, parsed.warnings, [])


class SVGCanvas:
    def __init__(self, width: int, height: int, title: str, font_family: str) -> None:
        self.width = width
        self.height = height
        self.font_family = font_family
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">',
            "<defs><filter id=\"softShadow\" x=\"-20%\" y=\"-20%\" width=\"140%\" height=\"140%\"><feDropShadow dx=\"0\" dy=\"8\" stdDeviation=\"8\" flood-color=\"#244\" flood-opacity=\"0.14\"/></filter></defs>",
            f'<rect width="{width}" height="{height}" fill="#f7faf8"/>',
            f'<text x="32" y="42" fill="#142623" font-size="24" font-weight="700" font-family="{_escape(font_family)}">{_escape(title)}</text>',
        ]

    def rect(self, x: float, y: float, w: float, h: float, fill: str, stroke: str = "none", opacity: float = 1.0, radius: float = 0) -> None:
        self.parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w, 0):.2f}" height="{max(h, 0):.2f}" rx="{radius}" fill="{fill}" stroke="{stroke}" opacity="{opacity}"/>'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = "#60716c", width: float = 1.0, dash: str = "") -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>')

    def circle(self, x: float, y: float, r: float, fill: str, stroke: str = "#ffffff", opacity: float = 0.9) -> None:
        self.parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" opacity="{opacity}"/>')

    def path(self, d: str, fill: str, stroke: str = "none", width: float = 1.0, opacity: float = 1.0) -> None:
        self.parts.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>')

    def polyline(self, points: list[tuple[float, float]], stroke: str, width: float = 3.0, fill: str = "none") -> None:
        encoded = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        self.parts.append(f'<polyline points="{encoded}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')

    def text(self, x: float, y: float, value: str, size: int = 12, fill: str = "#314541", anchor: str = "start", weight: str = "400") -> None:
        self.parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="{_escape(self.font_family)}">{_escape(value)}</text>'
        )

    def plot_area(self) -> tuple[float, float, float, float]:
        return 72, 80, self.width - 112, self.height - 136

    def axes(self, xlabel: str = "", ylabel: str = "") -> tuple[float, float, float, float]:
        x, y, w, h = self.plot_area()
        self.rect(x, y, w, h, "#ffffff", "#d6e0dc", 1, 4)
        self.line(x, y + h, x + w, y + h, "#435a54", 1.4)
        self.line(x, y, x, y + h, "#435a54", 1.4)
        if xlabel:
            self.text(x + w / 2, y + h + 44, xlabel, 13, anchor="middle", weight="600")
        if ylabel:
            self.text(22, y + h / 2, ylabel, 13, weight="600")
        return x, y, w, h

    def finish(self) -> str:
        self.parts.append("</svg>")
        return "\n".join(self.parts)


def _render_pie(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    values = [max(numeric_value(row, "value", "percent"), 0.0) for row in parsed.rows]
    labels = [row.get("class", row.get(parsed.headers[0], "")) for row in parsed.rows]
    total = sum(values) or 1.0
    cx, cy = svg.width * 0.43, svg.height * 0.54
    radius = min(svg.width, svg.height) * 0.28
    angle = -math.pi / 2
    for index, value in enumerate(values):
        span = value / total * math.tau
        end = angle + span
        x1, y1 = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        x2, y2 = cx + radius * math.cos(end), cy + radius * math.sin(end)
        large = 1 if span > math.pi else 0
        svg.path(f"M {cx:.2f} {cy:.2f} L {x1:.2f} {y1:.2f} A {radius:.2f} {radius:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} Z", PALETTE[index % len(PALETTE)])
        angle = end
    for index, label in enumerate(labels[:8]):
        y = 108 + index * 24
        svg.rect(svg.width - 250, y - 12, 14, 14, PALETTE[index % len(PALETTE)], radius=2)
        svg.text(svg.width - 228, y, f"{label} ({values[index] / total * 100:.1f}%)", 13)


def _render_bar(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Gene", "log2FC")
    values = [numeric_value(row, "log2FC", "value") for row in parsed.rows]
    labels = [row.get("gene", row.get(parsed.headers[0], "")) for row in parsed.rows]
    max_abs = max([abs(value) for value in values] + [1.0])
    baseline = y + h / 2
    bar_width = w / max(len(values), 1) * 0.62
    for index, value in enumerate(values):
        px = x + (index + 0.2) * (w / max(len(values), 1))
        bar_height = abs(value) / max_abs * (h / 2 - 14)
        py = baseline - bar_height if value >= 0 else baseline
        color = options.get("upColor", "#d94b42") if value >= 0 else options.get("downColor", "#2f9e6d")
        svg.rect(px, py, bar_width, bar_height, color, radius=3)
        svg.text(px + bar_width / 2, y + h + 20, labels[index][:8], 10, anchor="middle")
    svg.line(x, baseline, x + w, baseline, "#203a35", 1.5)


def _render_line(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("x", "y")
    xs = [numeric_value(row, "x", "time") for row in parsed.rows]
    ys = [numeric_value(row, "y", "value") for row in parsed.rows]
    points = [_scale_pair(xs[i], ys[i], xs, ys, x, y, w, h) for i in range(len(xs))]
    svg.polyline(points, "#2f6f73", 3.5)
    for px, py in points:
        svg.circle(px, py, 4.2, "#d36f45")


def _render_scatter(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("x", "y")
    xs = [numeric_value(row, "x", "pc1", "ratio", "fpr") for row in parsed.rows]
    ys = [numeric_value(row, "y", "pc2", "tpr", "value") for row in parsed.rows]
    for index, (raw_x, raw_y) in enumerate(zip(xs, ys)):
        px, py = _scale_pair(raw_x, raw_y, xs, ys, x, y, w, h)
        svg.circle(px, py, 7, PALETTE[index % len(PALETTE)])


def _render_heatmap(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    label_column = parsed.headers[0]
    sample_columns = parsed.headers[1:]
    values = [numeric_value(row, column) for row in parsed.rows for column in sample_columns]
    low, high = min(values or [0]), max(values or [1])
    x, y, w, h = svg.plot_area()
    cell_w = w / max(len(sample_columns), 1)
    cell_h = h / max(len(parsed.rows), 1)
    for row_index, row in enumerate(parsed.rows):
        svg.text(x - 10, y + row_index * cell_h + cell_h * 0.62, row.get(label_column, "")[:12], 11, anchor="end")
        for column_index, column in enumerate(sample_columns):
            ratio = _normalize(numeric_value(row, column), low, high)
            color = _blend("#3a6ea5", "#f2f1e8", "#c94c4c", ratio)
            svg.rect(x + column_index * cell_w, y + row_index * cell_h, cell_w - 2, cell_h - 2, color)
    for column_index, column in enumerate(sample_columns):
        svg.text(x + column_index * cell_w + cell_w / 2, y + h + 20, column[:10], 11, anchor="middle")


def _render_volcano(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("log2FC", "-log10(p)")
    fc = [numeric_value(row, "log2FC") for row in parsed.rows]
    neg_log = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
    fc_cutoff = float(options.get("fcCutoff", 1.0))
    p_cutoff = -math.log10(max(float(options.get("pCutoff", 0.05)), 1e-300))
    tx1, _ = _scale_pair(-fc_cutoff, min(neg_log), fc + [-fc_cutoff, fc_cutoff], neg_log, x, y, w, h)
    tx2, _ = _scale_pair(fc_cutoff, min(neg_log), fc + [-fc_cutoff, fc_cutoff], neg_log, x, y, w, h)
    _, ty = _scale_pair(0, p_cutoff, fc, neg_log + [p_cutoff], x, y, w, h)
    svg.line(tx1, y, tx1, y + h, "#9ca9a5", 1, "5 5")
    svg.line(tx2, y, tx2, y + h, "#9ca9a5", 1, "5 5")
    svg.line(x, ty, x + w, ty, "#9ca9a5", 1, "5 5")
    for index, row in enumerate(parsed.rows):
        raw_x, raw_y = fc[index], neg_log[index]
        px, py = _scale_pair(raw_x, raw_y, fc, neg_log, x, y, w, h)
        color = "#d94b42" if raw_x >= fc_cutoff and raw_y >= p_cutoff else "#2f6fbd" if raw_x <= -fc_cutoff and raw_y >= p_cutoff else "#87938f"
        svg.circle(px, py, 6, color)
        if raw_y >= p_cutoff and abs(raw_x) >= fc_cutoff:
            svg.text(px + 7, py - 6, row.get("gene", ""), 10)


def _render_violin(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Group", "Value")
    groups = sorted({row.get("group", "") for row in parsed.rows})
    values = [numeric_value(row, "value") for row in parsed.rows]
    for index, group in enumerate(groups):
        group_values = [numeric_value(row, "value") for row in parsed.rows if row.get("group") == group]
        gx = x + (index + 0.5) * w / max(len(groups), 1)
        for offset, value in enumerate(group_values):
            _, gy = _scale_pair(0, value, [0], values, x, y, w, h)
            jitter = (offset - len(group_values) / 2) * 8
            svg.circle(gx + jitter, gy, 5, PALETTE[index % len(PALETTE)], opacity=0.72)
        if group_values:
            q1, q3 = min(group_values), max(group_values)
            _, y1 = _scale_pair(0, q1, [0], values, x, y, w, h)
            _, y3 = _scale_pair(0, q3, [0], values, x, y, w, h)
            svg.path(f"M {gx-36:.2f} {(y1+y3)/2:.2f} C {gx-18:.2f} {y3:.2f}, {gx+18:.2f} {y3:.2f}, {gx+36:.2f} {(y1+y3)/2:.2f} C {gx+18:.2f} {y1:.2f}, {gx-18:.2f} {y1:.2f}, {gx-36:.2f} {(y1+y3)/2:.2f} Z", PALETTE[index % len(PALETTE)], opacity=0.2)
        svg.text(gx, y + h + 22, group, 12, anchor="middle")


def _render_bubble(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Gene ratio", "-log10(p)")
    ratios = [numeric_value(row, "ratio") for row in parsed.rows]
    sigs = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
    counts = [numeric_value(row, "count", default=1.0) for row in parsed.rows]
    for index, row in enumerate(parsed.rows):
        px, py = _scale_pair(ratios[index], sigs[index], ratios, sigs, x, y, w, h)
        radius = 5 + _normalize(counts[index], min(counts), max(counts)) * 16
        svg.circle(px, py, radius, PALETTE[index % len(PALETTE)], opacity=0.76)
        svg.text(px + radius + 4, py + 4, row.get("term", "")[:22], 10)


def _render_manhattan(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Chromosome", "-log10(p)")
    chroms = [row.get("chrom", "") for row in parsed.rows]
    positions = [index + numeric_value(row, "position") / 1000 for index, row in enumerate(parsed.rows)]
    sigs = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
    for index, row in enumerate(parsed.rows):
        px, py = _scale_pair(positions[index], sigs[index], positions, sigs, x, y, w, h)
        svg.circle(px, py, 5, PALETTE[index % 2])
    threshold = -math.log10(max(float(options.get("threshold", 0.00001)), 1e-300))
    _, ty = _scale_pair(0, threshold, positions, sigs + [threshold], x, y, w, h)
    svg.line(x, ty, x + w, ty, "#c94c4c", 1.4, "6 4")
    for index, chrom in enumerate(chroms):
        if index == 0 or chrom != chroms[index - 1]:
            px, _ = _scale_pair(positions[index], min(sigs), positions, sigs, x, y, w, h)
            svg.text(px, y + h + 20, chrom, 11, anchor="middle")


def _render_km(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Time", "Survival probability")
    groups = sorted({row.get("group", "All") or "All" for row in parsed.rows})
    all_times = [numeric_value(row, "time") for row in parsed.rows]
    for index, group in enumerate(groups):
        rows = sorted([row for row in parsed.rows if (row.get("group", "All") or "All") == group], key=lambda item: numeric_value(item, "time"))
        at_risk = len(rows)
        survival = 1.0
        points = []
        previous_time = 0.0
        points.append(_scale_pair(previous_time, survival, all_times + [0], [0, 1], x, y, w, h))
        for row in rows:
            time = numeric_value(row, "time")
            points.append(_scale_pair(time, survival, all_times + [0], [0, 1], x, y, w, h))
            if row.get("status") in {"1", "2"} and at_risk > 0:
                survival *= (at_risk - 1) / at_risk
            at_risk = max(at_risk - 1, 1)
            points.append(_scale_pair(time, survival, all_times + [0], [0, 1], x, y, w, h))
        svg.polyline(points, PALETTE[index % len(PALETTE)], 3)
        svg.text(x + w - 120, y + 24 + index * 22, group, 12, PALETTE[index % len(PALETTE)], weight="700")


def _render_roc(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("False positive rate", "True positive rate")
    xs = [numeric_value(row, "fpr") for row in parsed.rows]
    ys = [numeric_value(row, "tpr") for row in parsed.rows]
    svg.line(x, y + h, x + w, y, "#b5bfba", 1.6, "6 5")
    svg.polyline([_scale_pair(xs[i], ys[i], [0, 1], [0, 1], x, y, w, h) for i in range(len(xs))], "#2f6f73", 4)


def _render_pca(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("PC1", "PC2")
    xs = [numeric_value(row, "pc1") for row in parsed.rows]
    ys = [numeric_value(row, "pc2") for row in parsed.rows]
    groups = sorted({row.get("group", "") for row in parsed.rows})
    color_by_group = {group: PALETTE[index % len(PALETTE)] for index, group in enumerate(groups)}
    for row, raw_x, raw_y in zip(parsed.rows, xs, ys):
        px, py = _scale_pair(raw_x, raw_y, xs, ys, x, y, w, h)
        svg.circle(px, py, 8, color_by_group[row.get("group", "")])
        svg.text(px + 8, py - 8, row.get("sample", ""), 10)


def _render_generic(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes(parsed.headers[0] if parsed.headers else "x", "value")
    labels = [row.get(parsed.headers[0], f"Row {index + 1}") for index, row in enumerate(parsed.rows)]
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    max_value = max([abs(value) for value in values] + [1.0])
    bar_width = w / max(len(values), 1) * 0.58
    for index, value in enumerate(values):
        px = x + (index + 0.22) * (w / max(len(values), 1))
        bar_height = abs(value) / max_value * (h - 22)
        svg.rect(px, y + h - bar_height, bar_width, bar_height, PALETTE[index % len(PALETTE)], radius=3, opacity=0.82)
        svg.text(px + bar_width / 2, y + h + 20, labels[index][:8], 10, anchor="middle")


def _render_bar_family(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes(parsed.headers[0] if parsed.headers else "label", "value")
    labels = [row.get(parsed.headers[0], f"Row {index + 1}") for index, row in enumerate(parsed.rows)]
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    max_abs = max([abs(value) for value in values] + [1.0])
    baseline = y + h if min(values or [0]) >= 0 else y + h / 2
    bar_width = w / max(len(values), 1) * 0.58
    for index, value in enumerate(values):
        px = x + (index + 0.22) * (w / max(len(values), 1))
        bar_height = abs(value) / max_abs * (h - 22 if baseline == y + h else h / 2 - 12)
        py = baseline - bar_height if value >= 0 else baseline
        svg.rect(px, py, bar_width, bar_height, PALETTE[index % len(PALETTE)], radius=3, opacity=0.86)
        svg.text(px + bar_width / 2, y + h + 20, labels[index][:8], 10, anchor="middle")
    svg.line(x, baseline, x + w, baseline, "#435a54", 1.2)


def _render_set_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    _render_pie(svg, parsed, options, title)


def _render_hierarchy_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    labels = [row.get("child", row.get(parsed.headers[0], f"Node {index + 1}")) for index, row in enumerate(parsed.rows)]
    values = [max(_first_numeric(row, parsed.headers, index + 1), 0.0) for index, row in enumerate(parsed.rows)]
    total = sum(values) or 1.0
    cursor = x
    for index, value in enumerate(values):
        cell_w = w * value / total
        svg.rect(cursor, y, cell_w - 2, h, PALETTE[index % len(PALETTE)], opacity=0.72, radius=4)
        if cell_w > 44:
            svg.text(cursor + 8, y + 28, labels[index][:16], 11, "#ffffff", weight="700")
        cursor += cell_w


def _render_funnel_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("stage", "value")
    labels = [row.get("stage", row.get(parsed.headers[0], f"Stage {index + 1}")) for index, row in enumerate(parsed.rows)]
    values = [max(_first_numeric(row, parsed.headers, index + 1), 0.0) for index, row in enumerate(parsed.rows)]
    max_value = max(values or [1.0])
    row_h = h / max(len(values), 1) * 0.64
    for index, value in enumerate(values):
        bar_w = w * value / max_value
        px = x + (w - bar_w) / 2
        py = y + index * h / max(len(values), 1) + 8
        svg.rect(px, py, bar_w, row_h, PALETTE[index % len(PALETTE)], opacity=0.82, radius=4)
        svg.text(x + w / 2, py + row_h * 0.62, labels[index][:18], 11, "#ffffff", anchor="middle", weight="700")


def _render_calendar_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    low, high = min(values or [0]), max(values or [1])
    columns = min(14, max(len(values), 1))
    cell = min(w / columns, h / max(math.ceil(len(values) / columns), 1)) - 3
    for index, row in enumerate(parsed.rows):
        px = x + (index % columns) * (cell + 3)
        py = y + (index // columns) * (cell + 3)
        color = _blend("#eaf2ee", "#9fc3b5", "#2f6f73", _normalize(values[index], low, high))
        svg.rect(px, py, cell, cell, color, radius=3)
        if cell > 28:
            svg.text(px + cell / 2, py + cell / 2 + 4, row.get(parsed.headers[0], "")[-2:], 9, "#172623", anchor="middle")


def _render_polar_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    _render_pie(svg, parsed, options, title)


def _render_pathway_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    _render_bar_family(svg, parsed, options, title)


def _render_sequence_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("position", "score")
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    labels = [row.get("symbol", row.get(parsed.headers[0], "")) for row in parsed.rows]
    max_value = max(values or [1.0])
    for index, value in enumerate(values):
        px = x + (index + 0.5) * w / max(len(values), 1)
        bar_h = value / max_value * (h - 24)
        svg.rect(px - 12, y + h - bar_h, 24, bar_h, PALETTE[index % len(PALETTE)], radius=2)
        svg.text(px, y + h - bar_h - 8, labels[index][:1], 13, anchor="middle", weight="700")


def _render_maf_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    genes = sorted({row.get("gene", "") for row in parsed.rows})
    samples = sorted({row.get("sample", "") for row in parsed.rows})
    cell_w = w / max(len(samples), 1)
    cell_h = h / max(len(genes), 1)
    for row in parsed.rows:
        if row.get("gene", "") in genes and row.get("sample", "") in samples:
            gx = samples.index(row.get("sample", ""))
            gy = genes.index(row.get("gene", ""))
            svg.rect(x + gx * cell_w, y + gy * cell_h, cell_w - 2, cell_h - 2, PALETTE[gy % len(PALETTE)], radius=2)
    for index, gene in enumerate(genes):
        svg.text(x - 8, y + index * cell_h + cell_h * 0.62, gene[:10], 10, anchor="end")


def _render_wordcloud_plot(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    low, high = min(values or [0]), max(values or [1])
    for index, row in enumerate(parsed.rows[:24]):
        size = int(12 + _normalize(values[index], low, high) * 22)
        px = x + (index % 4) * w / 4 + 18
        py = y + (index // 4) * 42 + 30
        svg.text(px, min(py, y + h - 10), row.get(parsed.headers[0], "")[:14], size, PALETTE[index % len(PALETTE)], weight="700")


def _render_family_placeholder(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes(parsed.headers[0] if parsed.headers else "x", "value")
    labels = [row.get(parsed.headers[0], f"Row {index + 1}") for index, row in enumerate(parsed.rows)]
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    points = []
    low, high = min(values or [0]), max(values or [1])
    for index, value in enumerate(values):
        px = x + (index + 0.5) * w / max(len(values), 1)
        py = y + h - _normalize(value, low, high) * h
        points.append((px, py))
        svg.circle(px, py, 6, PALETTE[index % len(PALETTE)])
        svg.text(px, y + h + 20, labels[index][:8], 10, anchor="middle")
    if len(points) > 1:
        svg.polyline(points, PALETTE[0], 2.5)


def _render_generic_line(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("x", "value")
    xs = [_first_numeric(row, parsed.headers, index) for index, row in enumerate(parsed.rows)]
    ys = [_second_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    points = [_scale_pair(xs[i], ys[i], xs, ys, x, y, w, h) for i in range(len(xs))]
    svg.polyline(points, PALETTE[0], 3)
    for point in points:
        svg.circle(point[0], point[1], 4.5, PALETTE[1])


def _render_generic_scatter(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("x", "y")
    xs = [_first_numeric(row, parsed.headers, index) for index, row in enumerate(parsed.rows)]
    ys = [_second_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    for index, (raw_x, raw_y) in enumerate(zip(xs, ys)):
        px, py = _scale_pair(raw_x, raw_y, xs, ys, x, y, w, h)
        radius = _int_option(options, "pointSize", 64, 16, 240) ** 0.5
        svg.circle(px, py, radius, PALETTE[index % len(PALETTE)])


def _render_generic_distribution(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes("Group", "Value")
    group_key = "group" if "group" in parsed.headers else parsed.headers[0]
    groups = sorted({row.get(group_key, "") for row in parsed.rows})
    values = [_first_numeric(row, parsed.headers, 0) for row in parsed.rows]
    for index, group in enumerate(groups):
        group_values = [_first_numeric(row, parsed.headers, 0) for row in parsed.rows if row.get(group_key) == group]
        gx = x + (index + 0.5) * w / max(len(groups), 1)
        for offset, value in enumerate(group_values):
            _, gy = _scale_pair(0, value, [0], values, x, y, w, h)
            svg.circle(gx + (offset - len(group_values) / 2) * 7, gy, 4.5, PALETTE[index % len(PALETTE)], opacity=0.7)
        if group_values:
            low, high = min(group_values), max(group_values)
            _, y_low = _scale_pair(0, low, [0], values, x, y, w, h)
            _, y_high = _scale_pair(0, high, [0], values, x, y, w, h)
            svg.rect(gx - 18, y_high, 36, y_low - y_high, PALETTE[index % len(PALETTE)], opacity=0.25, radius=6)
        svg.text(gx, y + h + 20, group[:10], 11, anchor="middle")


def _render_generic_network(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    nodes = sorted({row.get("source", "") for row in parsed.rows} | {row.get("target", "") for row in parsed.rows})
    cx, cy = x + w / 2, y + h / 2
    radius = min(w, h) * 0.38
    positions = {}
    for index, node in enumerate(nodes):
        angle = math.tau * index / max(len(nodes), 1)
        positions[node] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
    for row in parsed.rows:
        source, target = row.get("source", ""), row.get("target", "")
        if source in positions and target in positions:
            svg.line(*positions[source], *positions[target], "#9aa8a3", 1.4)
    for index, node in enumerate(nodes):
        px, py = positions[node]
        svg.circle(px, py, 15, PALETTE[index % len(PALETTE)])
        svg.text(px, py + 4, node[:10], 9, "#ffffff", anchor="middle", weight="700")


def _render_generic_heatmap(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    if len(parsed.headers) >= 3 and parsed.headers[1] == "column":
        _render_long_matrix(svg, parsed, options, title)
    else:
        _render_heatmap(svg, parsed, options, title)


def _render_long_matrix(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.plot_area()
    rows = sorted({row.get("row", "") for row in parsed.rows})
    columns = sorted({row.get("column", "") for row in parsed.rows})
    values = [numeric_value(row, "value") for row in parsed.rows]
    low, high = min(values or [0]), max(values or [1])
    cell_w = w / max(len(columns), 1)
    cell_h = h / max(len(rows), 1)
    for row_index, row_label in enumerate(rows):
        svg.text(x - 8, y + row_index * cell_h + cell_h * 0.62, row_label[:10], 11, anchor="end")
        for column_index, column_label in enumerate(columns):
            match = next((item for item in parsed.rows if item.get("row") == row_label and item.get("column") == column_label), {})
            ratio = _normalize(numeric_value(match, "value"), low, high)
            svg.rect(x + column_index * cell_w, y + row_index * cell_h, cell_w - 2, cell_h - 2, _blend("#3a6ea5", "#f2f1e8", "#c94c4c", ratio))
    for column_index, column_label in enumerate(columns):
        svg.text(x + column_index * cell_w + cell_w / 2, y + h + 18, column_label[:10], 11, anchor="middle")


def _first_numeric(row: dict[str, Any], headers: list[str], default: float = 0.0) -> float:
    for header in headers:
        value = numeric_value(row, header, default=math.nan)
        if not math.isnan(value):
            return value
    return default


def _second_numeric(row: dict[str, Any], headers: list[str], default: float = 0.0) -> float:
    seen_first = False
    for header in headers:
        value = numeric_value(row, header, default=math.nan)
        if math.isnan(value):
            continue
        if seen_first:
            return value
        seen_first = True
    return default


RENDERERS: dict[str, Callable[[SVGCanvas, ParsedTable, dict, str], None]] = {
    "pie": _render_pie,
    "up-down-bar": _render_bar,
    "line": _render_line,
    "scatter": _render_scatter,
    "heatmap": _render_heatmap,
    "volcano": _render_volcano,
    "violin": _render_violin,
    "bubble": _render_bubble,
    "manhattan": _render_manhattan,
    "km-survival": _render_km,
    "roc": _render_roc,
    "pca": _render_pca,
}


FAMILY_RENDERERS: dict[str, Callable[[SVGCanvas, ParsedTable, dict, str], None]] = {
    "pie": _render_pie,
    "bar": _render_bar_family,
    "errorbar": _render_bar_family,
    "stacked-bar": _render_bar_family,
    "line": _render_generic_line,
    "area": _render_generic_line,
    "dual-axis": _render_generic_line,
    "scatter": _render_generic_scatter,
    "correlation": _render_generic_scatter,
    "qq": _render_generic_scatter,
    "distribution": _render_generic_distribution,
    "density": _render_generic_distribution,
    "bubble": _render_bubble,
    "enrichment": _render_bubble,
    "heatmap": _render_generic_heatmap,
    "matrix": _render_long_matrix,
    "set": _render_set_plot,
    "network": _render_generic_network,
    "hierarchy": _render_hierarchy_plot,
    "funnel": _render_funnel_plot,
    "dumbbell": _render_generic_line,
    "radar": _render_generic_line,
    "polar": _render_polar_plot,
    "calendar": _render_calendar_plot,
    "forest": _render_generic_line,
    "genome": _render_generic_scatter,
    "epigenome": _render_generic_scatter,
    "pathway": _render_pathway_plot,
    "sequence": _render_sequence_plot,
    "wordcloud": _render_wordcloud_plot,
    "maf": _render_maf_plot,
    "pca": _render_pca,
}


def _build_renderer_specs() -> dict[str, RendererSpec]:
    specs: dict[str, RendererSpec] = {}
    for module in list_modules():
        renderer = RENDERERS.get(module.slug) or FAMILY_RENDERERS.get(module.renderer_family)
        if renderer is None:
            renderer = _render_bar_family if module.visual_kind == "bar" else _render_generic_scatter
        specs[module.slug] = RendererSpec(
            backend=module.engine,
            family=module.renderer_family,
            svg_renderer=renderer,
        )
    return specs


RENDERER_SPECS = _build_renderer_specs()


def _select_renderer(module) -> Callable[[SVGCanvas, ParsedTable, dict, str], None]:
    try:
        return RENDERER_SPECS[module.slug].svg_renderer
    except KeyError:
        renderer = FAMILY_RENDERERS.get(module.renderer_family)
        if renderer is None:
            raise KeyError(f"No renderer is registered for {module.slug}.")
        return renderer


def _scale_pair(raw_x: float, raw_y: float, xs: list[float], ys: list[float], x: float, y: float, w: float, h: float) -> tuple[float, float]:
    min_x, max_x = min(xs or [0]), max(xs or [1])
    min_y, max_y = min(ys or [0]), max(ys or [1])
    nx = _normalize(raw_x, min_x, max_x)
    ny = _normalize(raw_y, min_y, max_y)
    return x + nx * w, y + h - ny * h


def _normalize(value: float, low: float, high: float) -> float:
    if math.isclose(low, high):
        return 0.5
    return min(max((value - low) / (high - low), 0.0), 1.0)


def _int_option(options: dict, key: str, fallback: int, minimum: int, maximum: int) -> int:
    try:
        value = int(float(options.get(key, fallback)))
    except (TypeError, ValueError):
        value = fallback
    return max(minimum, min(maximum, value))


def _blend(low_color: str, mid_color: str, high_color: str, ratio: float) -> str:
    start, end, local = (low_color, mid_color, ratio * 2) if ratio < 0.5 else (mid_color, high_color, (ratio - 0.5) * 2)
    sr, sg, sb = _hex_to_rgb(start)
    er, eg, eb = _hex_to_rgb(end)
    return f"#{int(sr + (er - sr) * local):02x}{int(sg + (eg - sg) * local):02x}{int(sb + (eb - sb) * local):02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _escape(value: str) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _write_matplotlib_artifacts(slug: str, family: str, parsed: ParsedTable, options: dict, artifacts: dict[str, str], width: int, height: int, title: str) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
    except Exception:
        return False

    fig_width = max(width / 140, 4.8)
    fig_height = max(height / 140, 3.6)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    fig.patch.set_facecolor("#f7faf8")
    ax.set_facecolor("#ffffff")
    try:
        if slug == "pie":
            values = [max(numeric_value(row, "value", "percent"), 0.0) for row in parsed.rows]
            labels = [row.get("class", row.get(parsed.headers[0], "")) for row in parsed.rows]
            ax.pie(values, labels=labels, autopct="%1.1f%%", colors=PALETTE[: len(values)], textprops={"fontsize": 8})
            ax.axis("equal")
        elif slug == "up-down-bar":
            labels = [row.get("gene", row.get(parsed.headers[0], "")) for row in parsed.rows]
            values = [numeric_value(row, "log2FC", "value") for row in parsed.rows]
            colors = [options.get("upColor", "#d94b42") if value >= 0 else options.get("downColor", "#2f9e6d") for value in values]
            ax.bar(labels, values, color=colors)
            ax.axhline(0, color="#172623", linewidth=0.9)
            ax.set_ylabel("log2FC")
        elif slug == "line":
            xs = [numeric_value(row, "x", "time") for row in parsed.rows]
            ys = [numeric_value(row, "y", "value") for row in parsed.rows]
            ax.plot(xs, ys, marker="o", color="#2f6f73", linewidth=2.2)
            ax.set_xlabel("x")
            ax.set_ylabel("y")
        elif slug == "scatter":
            _matplotlib_scatter(ax, parsed, "x", "y")
        elif slug == "heatmap":
            sample_columns = parsed.headers[1:]
            matrix = [[numeric_value(row, column) for column in sample_columns] for row in parsed.rows]
            cmap = LinearSegmentedColormap.from_list("hgatc_heat", ["#3a6ea5", "#f2f1e8", "#c94c4c"])
            image = ax.imshow(matrix, cmap=cmap, aspect="auto")
            ax.set_xticks(range(len(sample_columns)), sample_columns, rotation=35, ha="right")
            ax.set_yticks(range(len(parsed.rows)), [row.get(parsed.headers[0], "") for row in parsed.rows])
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        elif slug == "volcano":
            fc = [numeric_value(row, "log2FC") for row in parsed.rows]
            neg_log = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
            cutoff = float(options.get("fcCutoff", 1.0))
            p_cutoff = -math.log10(max(float(options.get("pCutoff", 0.05)), 1e-300))
            colors = ["#d94b42" if x >= cutoff and y >= p_cutoff else "#2f6fbd" if x <= -cutoff and y >= p_cutoff else "#87938f" for x, y in zip(fc, neg_log)]
            ax.scatter(fc, neg_log, c=colors, s=58, alpha=0.86, edgecolors="white", linewidths=0.6)
            ax.axvline(cutoff, color="#98a5a0", linestyle="--", linewidth=0.9)
            ax.axvline(-cutoff, color="#98a5a0", linestyle="--", linewidth=0.9)
            ax.axhline(p_cutoff, color="#98a5a0", linestyle="--", linewidth=0.9)
            ax.set_xlabel("log2FC")
            ax.set_ylabel("-log10(p)")
        elif slug == "violin":
            groups = sorted({row.get("group", "") for row in parsed.rows})
            series = [[numeric_value(row, "value") for row in parsed.rows if row.get("group", "") == group] for group in groups]
            ax.violinplot(series, showmeans=True)
            ax.set_xticks(range(1, len(groups) + 1), groups)
            ax.set_ylabel("Value")
        elif slug == "bubble":
            ratios = [numeric_value(row, "ratio") for row in parsed.rows]
            sigs = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
            counts = [numeric_value(row, "count", default=1.0) for row in parsed.rows]
            ax.scatter(ratios, sigs, s=[count * 22 for count in counts], c=PALETTE[: len(ratios)], alpha=0.74, edgecolors="white")
            for row, x_value, y_value in zip(parsed.rows, ratios, sigs):
                ax.annotate(row.get("term", "")[:18], (x_value, y_value), fontsize=7, xytext=(5, 2), textcoords="offset points")
            ax.set_xlabel("Gene ratio")
            ax.set_ylabel("-log10(p)")
        elif slug == "manhattan":
            positions = [index + numeric_value(row, "position") / 1000 for index, row in enumerate(parsed.rows)]
            sigs = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
            colors = [PALETTE[index % 2] for index in range(len(positions))]
            ax.scatter(positions, sigs, c=colors, s=50, alpha=0.86)
            ax.axhline(-math.log10(max(float(options.get("threshold", 0.00001)), 1e-300)), color="#c94c4c", linestyle="--")
            ax.set_xlabel("Chromosome position")
            ax.set_ylabel("-log10(p)")
        elif slug == "km-survival":
            _matplotlib_km(ax, parsed)
        elif slug == "roc":
            xs = [numeric_value(row, "fpr") for row in parsed.rows]
            ys = [numeric_value(row, "tpr") for row in parsed.rows]
            ax.plot([0, 1], [0, 1], color="#b5bfba", linestyle="--")
            ax.plot(xs, ys, marker="o", color="#2f6f73", linewidth=2.4)
            ax.set_xlabel("False positive rate")
            ax.set_ylabel("True positive rate")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        elif slug == "pca":
            _matplotlib_grouped_scatter(ax, parsed, "pc1", "pc2", "group", "sample")
        else:
            _matplotlib_family_plot(ax, fig, parsed, family, options, LinearSegmentedColormap)

        ax.set_title(title, fontsize=14, fontweight="bold", color="#172623")
        if family not in {"pie", "set"}:
            ax.grid(True, color="#dde6e2", linewidth=0.7, alpha=0.7)
        ax.tick_params(axis="both", labelsize=8, colors="#314541")
        for spine in ax.spines.values():
            spine.set_color("#d6e0dc")
        fig.tight_layout()
        fig.savefig(artifacts["svg"], format="svg")
        fig.savefig(artifacts["png"], format="png", dpi=180)
        fig.savefig(artifacts["tiff"], format="tiff", dpi=180)
        fig.savefig(artifacts["pdf"], format="pdf")
        return True
    except Exception:
        return False
    finally:
        try:
            plt.close(fig)
        except Exception:
            pass


def _matplotlib_family_plot(ax, fig, parsed: ParsedTable, family: str, options: dict, cmap_factory) -> None:
    labels = [row.get(parsed.headers[0], f"Row {index + 1}") for index, row in enumerate(parsed.rows)]
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]

    if family in {"pie", "set", "polar"}:
        ax.pie([abs(value) for value in values], labels=labels, colors=PALETTE[: len(values)], textprops={"fontsize": 8})
        ax.axis("equal")
    elif family in {"bar", "hierarchy", "funnel", "calendar", "wordcloud", "pathway", "sequence", "maf"}:
        orientation = str(options.get("orientation", "vertical"))
        if orientation == "horizontal" or family == "funnel":
            order = list(range(len(values)))[::-1]
            ax.barh([labels[index] for index in order], [abs(values[index]) for index in order], color=[PALETTE[index % len(PALETTE)] for index in order])
        else:
            ax.bar(labels, values, color=[PALETTE[index % len(PALETTE)] for index in range(len(values))])
            ax.tick_params(axis="x", rotation=35)
        ax.set_ylabel("value")
    elif family == "errorbar":
        errors = [numeric_value(row, "error", default=0.0) for row in parsed.rows]
        ax.bar(labels, values, yerr=errors, color=PALETTE[: len(values)], capsize=4)
        ax.tick_params(axis="x", rotation=35)
        ax.set_ylabel("value")
    elif family == "stacked-bar":
        categories = sorted({row.get("category", "") for row in parsed.rows})
        series = sorted({row.get("series", "") for row in parsed.rows})
        bottoms = [0.0] * len(categories)
        for series_index, series_name in enumerate(series):
            series_values = [
                sum(numeric_value(row, "value") for row in parsed.rows if row.get("category") == category and row.get("series") == series_name)
                for category in categories
            ]
            ax.bar(categories, series_values, bottom=bottoms, label=series_name, color=PALETTE[series_index % len(PALETTE)])
            bottoms = [bottom + value for bottom, value in zip(bottoms, series_values)]
        ax.legend(frameon=False, fontsize=8)
    elif family in {"line", "area", "dual-axis", "dumbbell", "radar"}:
        xs = [numeric_value(row, "x", default=index) for index, row in enumerate(parsed.rows)]
        ys = [_second_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
        ax.plot(xs, ys, marker="o", color=PALETTE[0], linewidth=2.2)
        if family == "area":
            ax.fill_between(xs, ys, min(ys or [0]), color=PALETTE[0], alpha=0.22)
        if family == "dual-axis" and "line" in parsed.headers:
            ax.plot(xs, [numeric_value(row, "line") for row in parsed.rows], marker="s", color=PALETTE[1], linewidth=2.0)
        ax.set_xlabel("x")
        ax.set_ylabel("value")
    elif family in {"scatter", "correlation", "qq", "genome", "epigenome"}:
        xs = [_first_numeric(row, parsed.headers, index) for index, row in enumerate(parsed.rows)]
        ys = [_second_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
        ax.scatter(xs, ys, c=PALETTE[: len(xs)], s=float(options.get("pointSize", 64)), alpha=0.82, edgecolors="white")
        if family in {"correlation", "qq"} and len(xs) > 1:
            ax.plot([min(xs), max(xs)], [min(ys), max(ys)], color=PALETTE[1], linewidth=1.4, linestyle="--")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
    elif family in {"distribution", "density"}:
        if "group" in parsed.headers and "value" in parsed.headers:
            groups = sorted({row.get("group", "") for row in parsed.rows})
            series = [[numeric_value(row, "value") for row in parsed.rows if row.get("group", "") == group] for group in groups]
            ax.violinplot(series, showmeans=True)
            ax.set_xticks(range(1, len(groups) + 1), groups)
        else:
            ax.hist(values, color=PALETTE[0], alpha=0.72, edgecolor="white")
        ax.set_ylabel("value")
    elif family in {"bubble", "enrichment"}:
        ratios = [numeric_value(row, "ratio", default=index + 1) for index, row in enumerate(parsed.rows)]
        sigs = [-math.log10(max(numeric_value(row, "pvalue", default=1.0), 1e-300)) for row in parsed.rows]
        counts = [numeric_value(row, "count", default=1.0) for row in parsed.rows]
        ax.scatter(ratios, sigs, s=[max(count, 1) * 22 for count in counts], c=PALETTE[: len(ratios)], alpha=0.74, edgecolors="white")
        for row, x_value, y_value in zip(parsed.rows, ratios, sigs):
            ax.annotate(row.get("term", "")[:18], (x_value, y_value), fontsize=7, xytext=(5, 2), textcoords="offset points")
        ax.set_xlabel("ratio")
        ax.set_ylabel("-log10(p)")
    elif family in {"heatmap", "matrix"}:
        if "row" in parsed.headers and "column" in parsed.headers:
            rows = sorted({row.get("row", "") for row in parsed.rows})
            columns = sorted({row.get("column", "") for row in parsed.rows})
            matrix = [
                [next((numeric_value(item, "value") for item in parsed.rows if item.get("row") == row and item.get("column") == column), 0.0) for column in columns]
                for row in rows
            ]
        else:
            columns = parsed.headers[1:]
            rows = [row.get(parsed.headers[0], "") for row in parsed.rows]
            matrix = [[numeric_value(row, column) for column in columns] for row in parsed.rows]
        cmap = cmap_factory.from_list("hgatc_heat", ["#3a6ea5", "#f2f1e8", "#c94c4c"])
        image = ax.imshow(matrix, cmap=cmap, aspect="auto")
        ax.set_xticks(range(len(columns)), columns, rotation=35, ha="right")
        ax.set_yticks(range(len(rows)), rows)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    elif family == "network":
        nodes = sorted({row.get("source", "") for row in parsed.rows} | {row.get("target", "") for row in parsed.rows})
        positions = {
            node: (math.cos(math.tau * index / max(len(nodes), 1)), math.sin(math.tau * index / max(len(nodes), 1)))
            for index, node in enumerate(nodes)
        }
        for row in parsed.rows:
            source, target = row.get("source", ""), row.get("target", "")
            if source in positions and target in positions:
                ax.plot([positions[source][0], positions[target][0]], [positions[source][1], positions[target][1]], color="#9aa8a3", linewidth=1.2)
        for index, node in enumerate(nodes):
            ax.scatter([positions[node][0]], [positions[node][1]], s=360, color=PALETTE[index % len(PALETTE)], edgecolors="white")
            ax.annotate(node[:10], positions[node], ha="center", va="center", fontsize=7, color="white", weight="bold")
        ax.axis("off")
    elif family == "forest":
        effects = [numeric_value(row, "effect") for row in parsed.rows]
        lows = [numeric_value(row, "low", default=effect * 0.85) for row, effect in zip(parsed.rows, effects)]
        highs = [numeric_value(row, "high", default=effect * 1.15) for row, effect in zip(parsed.rows, effects)]
        y_values = list(range(len(effects)))
        ax.errorbar(effects, y_values, xerr=[[effect - low for effect, low in zip(effects, lows)], [high - effect for effect, high in zip(effects, highs)]], fmt="o", color=PALETTE[0], ecolor=PALETTE[0], capsize=4)
        ax.axvline(float(options.get("referenceLine", 1.0)), color=PALETTE[1], linestyle="--")
        ax.set_yticks(y_values, labels)
        ax.set_xlabel("effect")
    else:
        ax.bar(labels, values, color=PALETTE[: len(values)])


def _matplotlib_scatter(ax, parsed: ParsedTable, x_key: str, y_key: str) -> None:
    xs = [numeric_value(row, x_key, "x") for row in parsed.rows]
    ys = [numeric_value(row, y_key, "y") for row in parsed.rows]
    ax.scatter(xs, ys, c="#2f6f73", s=64, alpha=0.82, edgecolors="white")
    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)


def _matplotlib_grouped_scatter(ax, parsed: ParsedTable, x_key: str, y_key: str, group_key: str, label_key: str) -> None:
    groups = sorted({row.get(group_key, "") for row in parsed.rows})
    for index, group in enumerate(groups):
        rows = [row for row in parsed.rows if row.get(group_key, "") == group]
        xs = [numeric_value(row, x_key) for row in rows]
        ys = [numeric_value(row, y_key) for row in rows]
        ax.scatter(xs, ys, label=group, c=PALETTE[index % len(PALETTE)], s=70, alpha=0.84, edgecolors="white")
        for row, x_value, y_value in zip(rows, xs, ys):
            ax.annotate(row.get(label_key, "")[:10], (x_value, y_value), fontsize=7, xytext=(5, 2), textcoords="offset points")
    ax.set_xlabel(x_key.upper())
    ax.set_ylabel(y_key.upper())
    ax.legend(frameon=False, fontsize=8)


def _matplotlib_km(ax, parsed: ParsedTable) -> None:
    groups = sorted({row.get("group", "All") or "All" for row in parsed.rows})
    for index, group in enumerate(groups):
        rows = sorted([row for row in parsed.rows if (row.get("group", "All") or "All") == group], key=lambda item: numeric_value(item, "time"))
        at_risk = len(rows)
        survival = 1.0
        times = [0.0]
        probs = [1.0]
        for row in rows:
            time = numeric_value(row, "time")
            times.append(time)
            probs.append(survival)
            if row.get("status") in {"1", "2"} and at_risk > 0:
                survival *= (at_risk - 1) / at_risk
            at_risk = max(at_risk - 1, 1)
            times.append(time)
            probs.append(survival)
        ax.step(times, probs, where="post", label=group, color=PALETTE[index % len(PALETTE)], linewidth=2.2)
    ax.set_xlabel("Time")
    ax.set_ylabel("Survival probability")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=8)
