from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.jobs import artifact_path, create_and_run_job, get_job, history, job_to_dict
from app.parser import parse_tabular_text
from app.r_engine import check_r_engine
from app.registry import get_module, grouped_modules_to_dict, list_modules, module_to_dict


class PrecheckRequest(BaseModel):
    data: str = ""
    source: Literal["paste", "upload", "demo"] = "paste"


class JobRequest(BaseModel):
    moduleSlug: str
    data: str
    options: dict[str, Any] = Field(default_factory=dict)
    sessionId: str = "anonymous"


app = FastAPI(title="HGATCplot API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    r_status = check_r_engine()
    return {
        "status": "ok",
        "templateCount": len(list_modules()),
        "pythonModules": sum(1 for module in list_modules() if module.engine == "python"),
        "rModules": sum(1 for module in list_modules() if module.engine == "r"),
        "r": r_status.to_dict(),
    }


@app.get("/api/modules")
def modules() -> dict[str, Any]:
    return {"groups": grouped_modules_to_dict()}


@app.get("/api/modules/{slug}")
def module(slug: str) -> dict[str, Any]:
    try:
        return module_to_dict(get_module(slug))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/modules/{slug}/precheck")
def precheck(slug: str, payload: PrecheckRequest) -> dict[str, Any]:
    try:
        manifest = get_module(slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    data = manifest.demo_data if payload.source == "demo" and not payload.data else payload.data
    parsed = parse_tabular_text(data)
    missing = [column for column in manifest.required_columns if column not in parsed.headers]
    errors = parsed.errors.copy()
    if missing:
        errors.append(f"Missing required column(s): {', '.join(missing)}.")
    engine_status = None
    if manifest.engine == "r":
        check = check_r_engine(manifest.r_packages)
        engine_status = check.to_dict()
        if not check.available:
            errors.extend(check.errors)
    return {
        "headers": parsed.headers,
        "rowCount": parsed.row_count,
        "columnCount": parsed.column_count,
        "previewRows": parsed.preview_rows,
        "warnings": parsed.warnings,
        "errors": errors,
        "engine": manifest.engine,
        "engineStatus": engine_status,
    }


@app.post("/api/jobs")
def create_job(payload: JobRequest) -> dict[str, Any]:
    try:
        record = create_and_run_job(payload.moduleSlug, payload.data, payload.options, payload.sessionId)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return job_to_dict(record)


@app.get("/api/jobs/{job_id}")
def job(job_id: str) -> dict[str, Any]:
    try:
        return job_to_dict(get_job(job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}/artifacts/{export_format}")
def download_artifact(job_id: str, export_format: Literal["png", "tiff", "svg", "pdf"]) -> FileResponse:
    path = artifact_path(job_id, export_format)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found.")
    media_types = {
        "png": "image/png",
        "tiff": "image/tiff",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }
    return FileResponse(path, media_type=media_types[export_format], filename=f"hgatcplot-{job_id}.{export_format}")


@app.get("/api/history")
def session_history(sessionId: str = Query("anonymous")) -> dict[str, list[dict[str, Any]]]:
    return {"jobs": [job_to_dict(record) for record in history(sessionId)]}


@app.get("/")
def api_root() -> dict[str, str]:
    return {"name": "HGATCplot API", "docs": "/docs"}

