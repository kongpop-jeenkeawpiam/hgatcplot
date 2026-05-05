# Practical SRplot Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade HGATCplot from a 125-template catalog into a practical SRplot-style plotting workbench with stable visual metadata, non-bar renderer routing, priority plot behavior, and grouped frontend controls.

**Architecture:** Keep the current API and 125-module registry as the source of truth. Add non-breaking manifest metadata in the backend, mirror it in the frontend fallback catalog, route rendering by explicit slug first and visual family second, then expose the richer metadata in the workbench UI.

**Tech Stack:** Python FastAPI backend, Python `unittest`, current SVG/matplotlib renderers, React + TypeScript + Vite frontend, Node static UI contract tests.

---

## File Structure

- Modify `api/app/registry.py`: add `VisualKind`, `RendererQuality`, `OptionGroup`, and expose `visualKind`, `rendererQuality`, and `optionGroups` in `module_to_dict()`.
- Modify `api/app/renderers.py`: make renderer routing explicit and ensure non-bar visual kinds cannot fall back to `_render_generic`.
- Modify `api/tests/test_core_contract.py`: add catalog metadata tests and renderer routing tests.
- Modify `api/tests/test_api_contract.py`: assert API responses include the new manifest fields.
- Modify `frontend/src/types.ts`: extend `PlotModule` with the new backend fields.
- Modify `frontend/src/fallbackModules.ts`: mirror the backend visual metadata for offline/frontend fallback mode.
- Modify `frontend/src/App.tsx`: replace hard-coded `BarChart3` module icons, render grouped option controls, and show quality/read-before-use metadata.
- Modify `frontend/src/styles.css`: style grouped controls and visual-kind badges without changing the dense workbench layout.
- Modify `frontend/tests/static-ui-contract.mjs`: assert the UI contract uses visual-kind icons, option groups, and the new fields.

---

### Task 1: Backend Manifest Metadata

**Files:**
- Modify: `api/app/registry.py`
- Test: `api/tests/test_core_contract.py`

- [x] **Step 1: Write failing metadata tests**

Add these assertions to `ModuleRegistryContractTests.test_registry_exposes_all_srplot_templates_with_unique_contracts` in `api/tests/test_core_contract.py`:

```python
        valid_visual_kinds = {
            "pie", "bar", "line", "scatter", "distribution", "density", "heatmap",
            "matrix", "bubble", "enrichment", "forest", "survival", "roc", "pca",
            "set", "network", "hierarchy", "funnel", "genome", "epigenome",
            "pathway", "maf", "sequence", "calendar", "polar", "wordcloud",
            "correlation", "qq", "radar", "area", "dual-axis", "dumbbell",
            "volcano",
        }
        valid_quality = {"practical", "family", "r-only"}
        self.assertTrue(all(module.visual_kind in valid_visual_kinds for module in modules))
        self.assertTrue(all(module.renderer_quality in valid_quality for module in modules))
        self.assertTrue(all(module.option_groups for module in modules))
        self.assertEqual(get_module("volcano").renderer_quality, "practical")
        self.assertEqual(get_module("heatmap").renderer_quality, "practical")
        self.assertEqual(get_module("bubble").renderer_quality, "practical")
        self.assertEqual(get_module("violin").renderer_quality, "practical")
        self.assertEqual(get_module("pie").renderer_quality, "practical")
        self.assertEqual(get_module("line").renderer_quality, "practical")
        self.assertEqual(get_module("scatter").renderer_quality, "practical")
        self.assertEqual(get_module("pca").renderer_quality, "practical")
        self.assertEqual(get_module("roc").renderer_quality, "practical")
        self.assertEqual(get_module("km-survival").renderer_quality, "practical")
        self.assertEqual(get_module("forest-plot").renderer_quality, "practical")
```

- [x] **Step 2: Run the failing backend test**

Run:

```powershell
python -m unittest api.tests.test_core_contract.ModuleRegistryContractTests -v
```

Expected: fail with `AttributeError` for `visual_kind`, `renderer_quality`, or `option_groups`.

- [x] **Step 3: Add backend metadata types**

In `api/app/registry.py`, add this dataclass after `OptionField`:

```python
@dataclass(frozen=True)
class OptionGroup:
    key: str
    label: str
    fields: list[str]
```

Extend `PlotModule` with these fields after `renderer_family`:

```python
    visual_kind: str
    renderer_quality: str
    option_groups: list[OptionGroup]
```

- [x] **Step 4: Add shared option grouping helpers**

Add these constants and helpers near the option constants in `api/app/registry.py`:

```python
PRIORITY_PRACTICAL_SLUGS = {
    "volcano", "heatmap", "bubble", "violin", "pie", "up-down-bar", "line",
    "scatter", "pca", "principal-components-analysis", "roc", "km-survival",
    "forest-plot",
}

VISUAL_KIND_BY_FAMILY = {
    "errorbar": "bar",
    "stacked-bar": "bar",
    "enrichment": "bubble",
    "survival": "survival",
}

OPTION_GROUP_LABELS = {
    "figure": "Figure size",
    "text": "Text",
    "font": "Font",
    "colors": "Colors",
    "cutoff": "Cutoff/Scale",
    "labels": "Labels",
    "grid": "Grid",
    "export": "Export",
}

OPTION_FIELD_GROUPS = {
    "width": "figure",
    "height": "figure",
    "title": "text",
    "fontFamily": "font",
    "primaryColor": "colors",
    "accentColor": "colors",
    "upColor": "colors",
    "downColor": "colors",
    "lowColor": "colors",
    "highColor": "colors",
    "fcCutoff": "cutoff",
    "pCutoff": "cutoff",
    "threshold": "cutoff",
    "scoreCutoff": "cutoff",
    "referenceLine": "cutoff",
    "topGenes": "cutoff",
    "maxWords": "cutoff",
    "legend": "labels",
    "showPercent": "labels",
    "showPoints": "labels",
    "confidence": "labels",
    "smooth": "grid",
    "orientation": "grid",
    "pointSize": "grid",
}

def _visual_kind(slug: str, family: str) -> str:
    if slug == "volcano":
        return "volcano"
    return VISUAL_KIND_BY_FAMILY.get(family, family)

def _renderer_quality(slug: str, engine: str) -> str:
    if slug in PRIORITY_PRACTICAL_SLUGS:
        return "practical"
    if engine == "r":
        return "r-only"
    return "family"

def _option_groups(fields: list[OptionField]) -> list[OptionGroup]:
    grouped: dict[str, list[str]] = {}
    for field in fields:
        grouped.setdefault(OPTION_FIELD_GROUPS.get(field.key, "grid"), []).append(field.key)
    grouped.setdefault("export", [])
    return [
        OptionGroup(key=key, label=OPTION_GROUP_LABELS[key], fields=grouped[key])
        for key in OPTION_GROUP_LABELS
        if key in grouped
    ]
```

- [x] **Step 5: Populate metadata in `_template()`**

In `_template()`, create the field list once:

```python
    option_fields = COMMON_OPTIONS + profile.option_fields
```

Then use:

```python
        option_fields=option_fields,
        visual_kind=_visual_kind(slug, family),
        renderer_quality=_renderer_quality(slug, engine),
        option_groups=_option_groups(option_fields),
```

- [x] **Step 6: Populate metadata in explicit `PlotModule(...)` seeds**

For every explicit `PlotModule(...)` in `_seed_modules()`, assign:

```python
            visual_kind=_visual_kind("volcano", "volcano"),
            renderer_quality=_renderer_quality("volcano", "python"),
            option_groups=_option_groups(COMMON_OPTIONS + [OptionField("fcCutoff", "Fold-change cutoff", "number", 1.0), OptionField("pCutoff", "P/FDR cutoff", "number", 0.05)]),
```

Use the matching slug, family, engine, and exact option list for each explicit module. For `km-survival`, keep `renderer_quality` practical even though `engine="r"`.

- [x] **Step 7: Expose metadata through the API dictionary**

In `module_to_dict()`, add:

```python
        "visualKind": module.visual_kind,
        "rendererQuality": module.renderer_quality,
        "optionGroups": [group.__dict__ for group in module.option_groups],
```

- [x] **Step 8: Run the backend metadata tests**

Run:

```powershell
python -m unittest api.tests.test_core_contract.ModuleRegistryContractTests -v
```

Expected: pass.

---

### Task 2: Renderer Routing Contract

**Files:**
- Modify: `api/app/renderers.py`
- Test: `api/tests/test_core_contract.py`

- [x] **Step 1: Write failing renderer routing tests**

Add this test to `RendererContractTests`:

```python
    def test_non_bar_visual_kinds_do_not_route_to_generic_bar_renderer(self):
        import app.renderers as renderers

        bar_like = {"bar", "errorbar", "stacked-bar"}
        for module in list_modules():
            if module.engine == "r":
                continue
            with self.subTest(module=module.slug):
                renderer = renderers._select_renderer(module)
                if module.renderer_family not in bar_like and module.visual_kind != "bar":
                    self.assertIsNot(renderer, renderers._render_generic)
```

- [x] **Step 2: Run the failing routing test**

Run:

```powershell
python -m unittest api.tests.test_core_contract.RendererContractTests.test_non_bar_visual_kinds_do_not_route_to_generic_bar_renderer -v
```

Expected: fail because `_select_renderer` does not exist.

- [x] **Step 3: Add explicit renderer selection**

In `api/app/renderers.py`, add this function above `render_plot()`:

```python
def _select_renderer(module) -> Callable[[SVGCanvas, ParsedTable, dict, str], None]:
    renderer = RENDERERS.get(module.slug)
    if renderer:
        return renderer
    renderer = FAMILY_RENDERERS.get(module.renderer_family)
    if renderer:
        return renderer
    if module.visual_kind == "bar":
        return _render_generic
    return _render_family_placeholder
```

Then replace:

```python
    renderer = RENDERERS.get(slug) or FAMILY_RENDERERS.get(module.renderer_family, _render_generic)
```

with:

```python
    renderer = _select_renderer(module)
```

- [x] **Step 4: Add a non-bar placeholder renderer**

Add this after `_render_generic()`:

```python
def _render_family_placeholder(svg: SVGCanvas, parsed: ParsedTable, options: dict, title: str) -> None:
    x, y, w, h = svg.axes(parsed.headers[0] if parsed.headers else "x", "value")
    labels = [row.get(parsed.headers[0], f"Row {index + 1}") for index, row in enumerate(parsed.rows)]
    values = [_first_numeric(row, parsed.headers, index + 1) for index, row in enumerate(parsed.rows)]
    points = []
    for index, value in enumerate(values):
        px = x + (index + 0.5) * w / max(len(values), 1)
        py = y + h - _normalize(value, min(values or [0]), max(values or [1])) * h
        points.append((px, py))
        svg.circle(px, py, 6, PALETTE[index % len(PALETTE)])
        svg.text(px, y + h + 20, labels[index][:8], 10, anchor="middle")
    if len(points) > 1:
        svg.polyline(points, PALETTE[0], 2.5)
```

- [x] **Step 5: Run the routing test**

Run:

```powershell
python -m unittest api.tests.test_core_contract.RendererContractTests.test_non_bar_visual_kinds_do_not_route_to_generic_bar_renderer -v
```

Expected: pass.

---

### Task 3: API Contract For New Manifest Fields

**Files:**
- Modify: `api/tests/test_api_contract.py`
- Depends on: Task 1

- [x] **Step 1: Add module list assertions**

In `test_module_precheck_job_artifact_and_history_flow`, after loading `modules.json()`, add:

```python
        volcano_payload = next(
            item
            for items in modules.json()["groups"].values()
            for item in items
            if item["slug"] == "volcano"
        )
        self.assertEqual(volcano_payload["visualKind"], "volcano")
        self.assertEqual(volcano_payload["rendererQuality"], "practical")
        self.assertTrue(volcano_payload["optionGroups"])
```

- [x] **Step 2: Add module detail assertions**

In `test_module_detail_includes_engine_source_and_aliases`, add:

```python
        self.assertIn("visualKind", payload)
        self.assertIn("rendererQuality", payload)
        self.assertIn("optionGroups", payload)
```

- [ ] **Step 3: Run API tests**  
  Blocked locally: FastAPI dependency directories were inaccessible, causing `ModuleNotFoundError: fastapi.testclient`.

Run:

```powershell
python -m unittest api.tests.test_api_contract -v
```

Expected: pass after Task 1 is complete.

---

### Task 4: Frontend Types And Fallback Metadata

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/fallbackModules.ts`
- Test: `frontend/tests/static-ui-contract.mjs`

- [x] **Step 1: Extend TypeScript types**

In `frontend/src/types.ts`, add:

```ts
export type VisualKind =
  | "pie" | "bar" | "line" | "scatter" | "distribution" | "density" | "heatmap"
  | "matrix" | "bubble" | "enrichment" | "forest" | "survival" | "roc" | "pca"
  | "set" | "network" | "hierarchy" | "funnel" | "genome" | "epigenome"
  | "pathway" | "maf" | "sequence" | "calendar" | "polar" | "wordcloud"
  | "correlation" | "qq" | "radar" | "area" | "dual-axis" | "dumbbell"
  | "volcano";

export type RendererQuality = "practical" | "family" | "r-only";

export interface OptionGroup {
  key: string;
  label: string;
  fields: string[];
}
```

Then add to `PlotModule`:

```ts
  visualKind: VisualKind;
  rendererQuality: RendererQuality;
  optionGroups: OptionGroup[];
```

- [x] **Step 2: Mirror metadata in fallback modules**

In `frontend/src/fallbackModules.ts`, add helper constants equivalent to the backend:

```ts
const priorityPracticalSlugs = new Set([
  "volcano", "heatmap", "bubble", "violin", "pie", "up-down-bar", "line",
  "scatter", "pca", "principal-components-analysis", "roc", "km-survival",
  "forest-plot"
]);

const visualKindByFamily: Partial<Record<keyof typeof profiles, PlotModule["visualKind"]>> = {
  errorbar: "bar",
  "stacked-bar": "bar",
  enrichment: "bubble",
  survival: "survival"
};

const optionGroupLabels = {
  figure: "Figure size",
  text: "Text",
  font: "Font",
  colors: "Colors",
  cutoff: "Cutoff/Scale",
  labels: "Labels",
  grid: "Grid",
  export: "Export"
} as const;

const optionFieldGroups: Record<string, keyof typeof optionGroupLabels> = {
  width: "figure",
  height: "figure",
  title: "text",
  fontFamily: "font",
  primaryColor: "colors",
  accentColor: "colors",
  upColor: "colors",
  downColor: "colors",
  lowColor: "colors",
  highColor: "colors",
  fcCutoff: "cutoff",
  pCutoff: "cutoff",
  threshold: "cutoff",
  scoreCutoff: "cutoff",
  referenceLine: "cutoff",
  topGenes: "cutoff",
  maxWords: "cutoff",
  legend: "labels",
  showPercent: "labels",
  showPoints: "labels",
  confidence: "labels",
  smooth: "grid",
  orientation: "grid",
  pointSize: "grid"
};
```

Add these functions:

```ts
function visualKind(slug: string, family: keyof typeof profiles): PlotModule["visualKind"] {
  if (slug === "volcano") return "volcano";
  return visualKindByFamily[family] ?? family;
}

function rendererQuality(slug: string, engine: Engine): PlotModule["rendererQuality"] {
  if (priorityPracticalSlugs.has(slug)) return "practical";
  if (engine === "r") return "r-only";
  return "family";
}

function optionGroups(fields: PlotModule["optionFields"]): PlotModule["optionGroups"] {
  const grouped = new Map<keyof typeof optionGroupLabels, string[]>();
  for (const field of fields) {
    const key = optionFieldGroups[field.key] ?? "grid";
    grouped.set(key, [...(grouped.get(key) ?? []), field.key]);
  }
  if (!grouped.has("export")) grouped.set("export", []);
  return Object.entries(optionGroupLabels)
    .filter(([key]) => grouped.has(key as keyof typeof optionGroupLabels))
    .map(([key, label]) => ({
      key,
      label,
      fields: grouped.get(key as keyof typeof optionGroupLabels) ?? []
    }));
}
```

In `moduleFromSpec()`, create `fields` once and return the new fields:

```ts
  const fields = [...commonFields, ...(profile.optionFields ?? [])];
```

Then:

```ts
    optionFields: fields,
    visualKind: visualKind(slug, family),
    rendererQuality: rendererQuality(slug, engine),
    optionGroups: optionGroups(fields),
```

- [x] **Step 3: Add fallback contract tests**

In `frontend/tests/static-ui-contract.mjs`, add:

```js
  assert.match(fallback, /visualKind/);
  assert.match(fallback, /rendererQuality/);
  assert.match(fallback, /optionGroups/);
  assert.match(fallback, /priorityPracticalSlugs/);
```

- [x] **Step 4: Run frontend static contract**

Run:

```powershell
cd frontend
npm.cmd run test:ui-contract
```

Expected: pass.

---

### Task 5: Visual-Kind Icons And Grouped Controls

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/tests/static-ui-contract.mjs`

- [x] **Step 1: Update imports**

In `frontend/src/App.tsx`, import visual icons:

```tsx
  Activity,
  AreaChart,
  BarChart3,
  Binary,
  Boxes,
  CircleDot,
  Clock3,
  GitFork,
  Grid3X3,
  LineChart,
  Network,
  PieChart,
  Radar,
  ScatterChart,
  Table2,
  Trees,
```

Keep existing imports that are still used.

- [x] **Step 2: Add icon map and grouped option helper**

Add after `exportLabels`:

```tsx
const visualKindIcons = {
  pie: PieChart,
  bar: BarChart3,
  line: LineChart,
  scatter: ScatterChart,
  distribution: Activity,
  density: Activity,
  heatmap: Grid3X3,
  matrix: Table2,
  bubble: CircleDot,
  enrichment: CircleDot,
  forest: GitFork,
  survival: Clock3,
  roc: Activity,
  pca: ScatterChart,
  set: Boxes,
  network: Network,
  hierarchy: Trees,
  funnel: BarChart3,
  genome: Binary,
  epigenome: Binary,
  pathway: GitFork,
  maf: Grid3X3,
  sequence: Binary,
  calendar: Grid3X3,
  polar: Radar,
  wordcloud: Activity,
  correlation: ScatterChart,
  qq: ScatterChart,
  radar: Radar,
  area: AreaChart,
  "dual-axis": LineChart,
  dumbbell: Activity,
  volcano: ScatterChart
} satisfies Record<PlotModule["visualKind"], typeof BarChart3>;

function ModuleIcon({ module, size = 16 }: { module: PlotModule; size?: number }) {
  const Icon = visualKindIcons[module.visualKind] ?? BarChart3;
  return <Icon size={size} aria-hidden="true" />;
}

function fieldsForGroup(module: PlotModule, groupFields: string[]) {
  const wanted = new Set(groupFields);
  return module.optionFields.filter((field) => wanted.has(field.key));
}
```

- [x] **Step 3: Replace module list hard-coded icons**

Replace:

```tsx
                  <BarChart3 size={16} />
```

with:

```tsx
                  <ModuleIcon module={module} />
```

- [x] **Step 4: Add visual and quality metadata to the header**

In the status strip, add:

```tsx
            <span><ModuleIcon module={activeModule} size={15} /> {activeModule.visualKind}</span>
            <span><CheckCircle2 size={15} /> {activeModule.rendererQuality}</span>
```

- [x] **Step 5: Render option groups**

Replace the existing `.option-grid` mapping with:

```tsx
            <div className="option-groups">
              {activeModule.optionGroups.map((group) => {
                const fields = fieldsForGroup(activeModule, group.fields);
                return (
                  <section className="option-group" key={group.key}>
                    <h3>{group.label}</h3>
                    {fields.length ? (
                      <div className="option-grid">
                        {fields.map((field) => (
                          <label key={field.key} className="option-field">
                            <span>{field.label}</span>
                            {field.kind === "select" ? (
                              <select value={String(options[field.key] ?? field.default)} onChange={(event) => setOptions({ ...options, [field.key]: event.target.value })}>
                                {(field.choices ?? []).map((choice) => (
                                  <option value={choice} key={choice}>{choice}</option>
                                ))}
                              </select>
                            ) : (
                              <input
                                type={field.kind === "number" ? "number" : field.kind === "color" ? "color" : "text"}
                                value={String(options[field.key] ?? field.default)}
                                onChange={(event) => setOptions({ ...options, [field.key]: field.kind === "number" ? Number(event.target.value) : event.target.value })}
                              />
                            )}
                          </label>
                        ))}
                      </div>
                    ) : (
                      <div className="export-note">Exports are generated as PNG, TIFF, SVG, and PDF.</div>
                    )}
                  </section>
                );
              })}
            </div>
```

- [x] **Step 6: Replace empty preview icon**

Replace:

```tsx
                  <BarChart3 size={42} />
```

with:

```tsx
                  <ModuleIcon module={activeModule} size={42} />
```

- [x] **Step 7: Add CSS for option groups**

In `frontend/src/styles.css`, add:

```css
.option-groups {
  display: grid;
  gap: 12px;
}

.option-group {
  display: grid;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}

.option-group:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.option-group h3 {
  margin: 0;
  color: #405852;
  font-size: 13px;
}

.export-note {
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #f7faf8;
  color: var(--muted);
  padding: 9px;
  font-size: 12px;
}
```

- [x] **Step 8: Update static UI contract tests**

In `frontend/tests/static-ui-contract.mjs`, add:

```js
  assert.match(app, /visualKindIcons/);
  assert.match(app, /ModuleIcon/);
  assert.match(app, /activeModule\.optionGroups/);
  assert.doesNotMatch(app, /<BarChart3 size=\{16\}/);
```

Add CSS assertions:

```js
  assert.match(css, /\.option-groups/);
  assert.match(css, /\.option-group/);
```

- [x] **Step 9: Run frontend tests and build**

Run:

```powershell
cd frontend
npm.cmd run test:ui-contract
npm.cmd run build
```

Expected: both pass.

---

### Task 6: Final End-To-End Verification

**Files:**
- No source edits unless verification fails.

- [ ] **Step 1: Run full backend tests**  
  Blocked locally: API dependency import failed, and Python temporary directories created with inaccessible ACLs caused `PermissionError`.

Run:

```powershell
python -m unittest discover api\tests -v
```

Expected: all non-R tests pass; R-specific smoke tests may skip when R is unavailable.

- [x] **Step 2: Run frontend verification**

Run:

```powershell
cd frontend
npm.cmd run test:ui-contract
npm.cmd run build
```

Expected: static contract and Vite build pass.

- [ ] **Step 3: Manually inspect the API payload**  
  Blocked locally by the same FastAPI dependency access issue as the API contract tests.

Run:

```powershell
python -m unittest api.tests.test_api_contract.ApiContractTests.test_module_detail_includes_engine_source_and_aliases -v
```

Expected: detail payload has `engine`, `sourceUrl`, `aliases`, `visualKind`, `rendererQuality`, and `optionGroups`.

- [x] **Step 4: Record any residual R limitation**

If R is unavailable, final notes must say:

```text
R-backed modules were not rendered locally because R is unavailable; Python-backed modules and API diagnostics were verified.
```

---

## Self-Review

Spec coverage:
- Preserves 125 modules and current endpoints: Tasks 1, 3, and 6.
- Adds `visualKind`, `optionGroups`, `rendererQuality`: Tasks 1, 3, and 4.
- Replaces generic non-bar fallback routing: Task 2.
- Priority practical plots marked and tested: Task 1.
- Frontend icon routing from `visualKind`: Task 5.
- SRplot-like grouped options/workbench: Task 5, building on existing workbench UI.
- Verification commands from PLAN3: Task 6.

Placeholder scan:
- No `TBD`, `TODO`, `implement later`, or unspecified “write tests” steps remain.

Type consistency:
- Backend snake_case fields are `visual_kind`, `renderer_quality`, `option_groups`.
- API/TypeScript camelCase fields are `visualKind`, `rendererQuality`, `optionGroups`.
- `rendererQuality` values are `practical`, `family`, and `r-only`.
