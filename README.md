# HGATCplot

HGATCplot is an SRplot-inspired scientific plotting platform with a React/Vite frontend and a FastAPI backend. The first release ships a module registry, tab-delimited input precheck, anonymous session history, and server-generated PNG, TIFF, SVG, and PDF artifacts for twelve seed plot modules.

## Project Layout

- `frontend/` - React + TypeScript workbench UI.
- `api/` - FastAPI service, module registry, parser, job store, and plot renderers.
- `api/tests/` - backend parser, renderer, and API contract tests.

## Local Setup

Install dependencies:

```powershell
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r api\requirements.txt --target api\vendor
cd frontend
npm.cmd install
```

Run the API:

```powershell
$env:PYTHONPATH='api;api\vendor'
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173`.

## Verification

```powershell
$env:PYTHONPATH='api;api\vendor'
C:\Users\Optiplex\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover api\tests -v
cd frontend
npm.cmd run test:ui-contract
npm.cmd run build
```
