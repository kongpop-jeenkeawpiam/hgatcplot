# HGATCplot

HGATCplot is an SRplot-inspired scientific plotting platform with a React/Vite frontend and a FastAPI backend. The current release ships a 125-template SRplot catalog, tab-delimited input precheck, anonymous session history, and server-generated PNG, TIFF, SVG, and PDF artifacts through Python and R renderers.

## Project Layout

- `frontend/` - React + TypeScript workbench UI.
- `api/` - FastAPI service, module registry, parser, job store, and plot renderers.
- `api/tests/` - backend parser, renderer, and API contract tests.

## Local Setup

Install dependencies:

```powershell
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r api\requirements.txt --target api\.deps
cd frontend
npm.cmd install
```

If you already use `api\vendor`, keep it on `PYTHONPATH`; `api\.deps` is an ignored fallback target that is useful when `vendor` is not readable.

R-backed modules use `HGATCPLOT_RSCRIPT` when set. On Windows this can point to `R.exe`, for example:

```powershell
$env:HGATCPLOT_RSCRIPT='C:\Program Files\R\R-4.4.0\bin\x64\R.exe'
```

If the variable is unset, the API tries `R.exe`, `Rscript.exe`, then common `C:\Program Files\R\R-*\bin` locations.

Run the API:

```powershell
$env:PYTHONPATH='api;api\.deps'
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Docker Setup

Build and run both services:

```bash
docker compose up --build
```

Open `http://127.0.0.1:5173`.

The API is exposed at `http://127.0.0.1:8000`, and its health endpoint is `http://127.0.0.1:8000/api/health`. The API image installs R and sets `HGATCPLOT_RSCRIPT=R` so R-backed templates can render inside the container.

Stop the stack:

```bash
docker compose down
```

## Verification

```powershell
$env:PYTHONPATH='api;api\.deps'
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover api\tests -v
cd frontend
npm.cmd run test:ui-contract
npm.cmd run build
```
