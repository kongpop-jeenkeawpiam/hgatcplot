from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.parser import parse_tabular_text
from app.registry import get_module
from app.renderers import render_plot


STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"
JOBS_ROOT = STORAGE_ROOT / "jobs"
DB_PATH = STORAGE_ROOT / "hgatcplot.sqlite3"


@dataclass(frozen=True)
class JobRecord:
    id: str
    module_slug: str
    module_title: str
    session_id: str
    status: str
    created_at: str
    updated_at: str
    warnings: list[str]
    errors: list[str]
    artifacts: dict[str, str]


def init_db() -> None:
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                module_slug TEXT NOT NULL,
                module_title TEXT NOT NULL,
                session_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                warnings_json TEXT NOT NULL,
                errors_json TEXT NOT NULL,
                artifacts_json TEXT NOT NULL
            )
            """
        )


def create_and_run_job(module_slug: str, data: str, options: dict[str, Any], session_id: str) -> JobRecord:
    init_db()
    module = get_module(module_slug)
    job_id = uuid.uuid4().hex
    now = _now()
    _insert_job(job_id, module.slug, module.title, session_id, "running", now, [], [], {})

    parsed = parse_tabular_text(data)
    result = render_plot(module.slug, parsed, options, JOBS_ROOT / job_id)
    _update_job(job_id, result.status, result.warnings, result.errors, _artifact_urls(job_id, result.artifacts))
    return get_job(job_id)


def get_job(job_id: str) -> JobRecord:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown job: {job_id}")
    return _row_to_record(row)


def history(session_id: str, limit: int = 25) -> list[JobRecord]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM jobs WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def artifact_path(job_id: str, export_format: str) -> Path:
    suffix = "tiff" if export_format == "tiff" else export_format
    return JOBS_ROOT / job_id / f"plot.{suffix}"


def job_to_dict(record: JobRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "moduleSlug": record.module_slug,
        "moduleTitle": record.module_title,
        "sessionId": record.session_id,
        "status": record.status,
        "createdAt": record.created_at,
        "updatedAt": record.updated_at,
        "warnings": record.warnings,
        "errors": record.errors,
        "previewUrl": record.artifacts.get("svg"),
        "artifacts": record.artifacts,
    }


def _insert_job(job_id: str, module_slug: str, module_title: str, session_id: str, status: str, now: str, warnings: list[str], errors: list[str], artifacts: dict[str, str]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, module_slug, module_title, session_id, status, created_at, updated_at, warnings_json, errors_json, artifacts_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, module_slug, module_title, session_id, status, now, now, json.dumps(warnings), json.dumps(errors), json.dumps(artifacts)),
        )


def _update_job(job_id: str, status: str, warnings: list[str], errors: list[str], artifacts: dict[str, str]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE jobs SET status = ?, updated_at = ?, warnings_json = ?, errors_json = ?, artifacts_json = ?
            WHERE id = ?
            """,
            (status, _now(), json.dumps(warnings), json.dumps(errors), json.dumps(artifacts), job_id),
        )


def _artifact_urls(job_id: str, artifacts: dict[str, str]) -> dict[str, str]:
    return {export_format: f"/api/jobs/{job_id}/artifacts/{export_format}" for export_format in artifacts}


def _row_to_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        id=row["id"],
        module_slug=row["module_slug"],
        module_title=row["module_title"],
        session_id=row["session_id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        warnings=json.loads(row["warnings_json"]),
        errors=json.loads(row["errors_json"]),
        artifacts=json.loads(row["artifacts_json"]),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

