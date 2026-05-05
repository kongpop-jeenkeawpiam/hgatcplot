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
});

test("stylesheet keeps the interface dense and responsive", () => {
  const css = read("src/styles.css");

  assert.match(css, /grid-template-columns:\s*280px 1fr/);
  assert.match(css, /@media \(max-width: 900px\)/);
  assert.match(css, /--accent/);
  assert.doesNotMatch(css, /border-radius:\s*(2[0-9]|[3-9][0-9])px/);
});
