import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";

const root = resolve(import.meta.dirname, "..");

function read(path) {
  return readFileSync(resolve(root, path), "utf8");
}

test("app shell exposes the scientific plotting workflow", () => {
  const app = read("src/App.tsx");

  assert.match(app, /Module Library/);
  assert.match(app, /Precheck/);
  assert.match(app, /Generate Plot/);
  assert.match(app, /Session History/);
  assert.match(app, /PNG/);
  assert.match(app, /TIFF/);
  assert.match(app, /SVG/);
  assert.match(app, /PDF/);
  assert.match(app, /activeModule\.engine\.toUpperCase/);
  assert.match(app, /activeModule\.sourceUrl/);
  assert.match(app, /visualKindIcons/);
  assert.match(app, /ModuleIcon/);
  assert.match(app, /activeModule\.optionGroups/);
  assert.doesNotMatch(app, /<BarChart3 size=\{16\}/);
});

test("fallback catalog mirrors the expanded SRplot module contract", () => {
  const fallback = read("src/fallbackModules.ts");

  assert.match(fallback, /extraTemplates/);
  assert.match(fallback, /motif-logo/);
  assert.match(fallback, /maf-oncoplot/);
  assert.match(fallback, /sourceUrl/);
  assert.match(fallback, /Engine = PlotModule/);
  assert.match(fallback, /"r"\]/);
  assert.match(fallback, /aliases:/);
  assert.match(fallback, /visualKind/);
  assert.match(fallback, /rendererQuality/);
  assert.match(fallback, /optionGroups/);
  assert.match(fallback, /plot-specific-python/);
  assert.match(fallback, /plot-specific-r/);
});

test("stylesheet keeps the interface dense and responsive", () => {
  const css = read("src/styles.css");

  assert.match(css, /grid-template-columns:\s*280px 1fr/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /--accent/);
  assert.match(css, /\.option-groups/);
  assert.match(css, /\.option-group/);
  assert.doesNotMatch(css, /border-radius:\s*(2[0-9]|[3-9][0-9])px/);
});
