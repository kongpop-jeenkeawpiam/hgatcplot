# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HGATCplot is a scientific plotting platform with 125 plot templates, inspired by SRplot. React/Vite frontend + FastAPI backend. Supports Python and R rendering engines.

## Essential Commands

### Backend (`api/`)
```bash
# Install deps
pip install -r api/requirements.txt --target api/.deps

# Run dev server (set PYTHONPATH)
$env:PYTHONPATH='api;api\.deps'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Run tests (with vendor or .deps)
$env:PYTHONPATH='api;api\.deps'
python -m unittest discover api/tests -v
```

### Frontend (`frontend/`)
```bash
cd frontend
npm install

# Dev server (proxies /api -> 127.0.0.1:8000)
npm run dev           # http://127.0.0.1:5173

# Build
npm run build

# UI contract tests (static checks)
npm run test:ui-contract
```

### Docker
```bash
docker compose up --build   # API on :8000, frontend on :5173
docker compose down
```

## R Engine
R-rendered modules (25+) use `HGATCPLOT_RSCRIPT` env var. Docker sets `HGATCPLOT_RSCRIPT=R`. Locally, falls back to `R.exe` / `Rscript.exe` / common Windows paths. Timeout default: 45s (override with `HGATCPLOT_R_TIMEOUT_SECONDS`). R scripts live in `api/app/r_scripts/render_template.R`.

## Architecture

### Backend (`api/app/`)

| File | Role |
|---|---|
| `main.py` | FastAPI app. Endpoints: `/api/health`, `/api/modules`, `/api/modules/{slug}`, `/api/modules/{slug}/precheck`, `/api/jobs` (POST), `/api/jobs/{job_id}` (GET), `/api/jobs/{job_id}/artifacts/{format}` (GET), `/api/history`, `/` |
| `jobs.py` | Job lifecycle: `create_and_run_job` (sync), SQLite persistence (`storage/hgatcplot.sqlite3`), artifact storage under `storage/jobs/{job_id}/`, session history |
| `registry.py` | 125 module definitions. Each has: slug, title, category, description, required_columns, default_options, option_fields, demo_data, engine (python/r), renderer_family, visual_kind, option_groups, aliases |
| `parser.py` | Tab-delimited text parser. Returns `ParsedTable(headers, rows, preview_rows, warnings, errors)`. Max 5000 data lines. `numeric_value()` helper extracts floats from row dicts |
| `r_engine.py` | R process management: `check_r_engine()` (availability + package check), `run_r_renderer()` (writes input.tsv, invokes `render_template.R`, collects artifacts). `RCheckResult` and `RRenderResult` dataclasses |
| `renderers.py` | `render_plot()` — central dispatch. Two paths: (1) **R**: calls `run_r_renderer` for R modules; (2) **Python**: uses `SVGCanvas` class to build SVG natively, then matplotlib to generate PNG/TIFF/SVG/PDF artifacts (when available) |

### Rendering Pipeline

```
Request -> get_module => parse_tabular_text => render_plot
  => R module? -> run_r_renderer (spawns R process, writes input.tsv, reads back artifacts)
  => Python? -> SVGCanvas + renderer function (SVG) + matplotlib (PNG/TIFF/SVG/PDF)
```

Named renderers are in `RENDERERS` dict (slug-keyed: pie, up-down-bar, line, scatter, volcano, violin, bubble, manhattan, km-survival, roc, pca). All other types route through `FAMILY_RENDERERS` by `renderer_family` (bar, line, scatter, heatmap, distribution, network, forest, etc.).

### Frontend (`frontend/src/`)

| File | Role |
|---|---|
| `App.tsx` | Single-page app. Module list (left rail), input data textarea, option fields, plot preview (SVG img), download links, session history |
| `api.ts` | `fetchModules()`, `precheck()`, `createJob()`, `fetchHistory()`, `artifactHref()`. Falls back to `fallbackModules.ts` if API unavailable |
| `types.ts` | TypeScript types: `PlotModule`, `PrecheckResult`, `JobResult`, `VisualKind`, `ExportFormat`, `RendererQuality`, `OptionField` |

State is entirely React `useState`. Session ID stored in `localStorage` (`hgatcplot-session-id`). No router — single page.

## Tests

**Backend**: Two test files in `api/tests/`:
- `test_api_contract.py` — HTTP-level: health check, module list (125), precheck, job creation, artifact download, history, unknown module 404, R module flow
- `test_core_contract.py` — Unit-level: parser, registry (125 unique slugs, valid visual_kinds, demo_data valid), renderer (all exports generated, no wrong routing), R engine (missing executable, bad packages, timeout)

**Frontend**: `frontend/tests/static-ui-contract.mjs` — Static assertions on source files: UI labels present, fallback module contract, CSS layout rules

## Key Directories

- `api/app/` — Backend Python code
- `api/tests/` — Backend tests
- `api/storage/` — SQLite DB and job artifacts (created at runtime)
- `frontend/src/` — React source
- `frontend/tests/` — Frontend static tests
- `docs/superpowers/` — Design documents
- `structure/` — Old planning notes

## Notes

- Job `id`s are `uuid4().hex` (32 hex chars, no dashes)
- `JobRequest.sessionId` defaults to `"anonymous"` on API
- CORS is fully open (`allow_origins=["*"]`)
- Artifacts served directly via `FileResponse` at `/api/jobs/{job_id}/artifacts/{format}`
- Vite dev server proxies `/api` to `http://127.0.0.1:8000` — use relative API calls in dev
