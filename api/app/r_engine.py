from __future__ import annotations

import csv
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.parser import ParsedTable


SCRIPT_PATH = Path(__file__).resolve().parent / "r_scripts" / "render_template.R"


@dataclass(frozen=True)
class RCheckResult:
    available: bool
    executable: str | None
    version: str | None
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "executable": self.executable,
            "version": self.version,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class RRenderResult:
    status: str
    artifacts: dict[str, str]
    warnings: list[str]
    errors: list[str]


def check_r_engine(required_packages: Iterable[str] = ()) -> RCheckResult:
    executable, errors = resolve_r_executable()
    if executable is None:
        return RCheckResult(False, None, None, errors)

    try:
        version_run = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RCheckResult(False, executable, None, ["R precheck timed out while reading the version."])
    except OSError as exc:
        return RCheckResult(False, executable, None, [f"R executable could not be started: {exc}."])

    version_text = (version_run.stdout or version_run.stderr or "").splitlines()
    version = version_text[0] if version_text else None
    if version_run.returncode != 0:
        return RCheckResult(False, executable, version, [version_run.stderr.strip() or "R version check failed."])

    packages = [package for package in required_packages if package]
    if packages:
        expression = "; ".join(f"library({package})" for package in packages)
        try:
            package_run = subprocess.run(
                _r_expression_command(executable, expression),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return RCheckResult(False, executable, version, ["R package precheck timed out."])
        if package_run.returncode != 0:
            detail = package_run.stderr.strip() or package_run.stdout.strip() or "R package precheck failed."
            return RCheckResult(False, executable, version, [detail])

    return RCheckResult(True, executable, version, [])


def resolve_r_executable() -> tuple[str | None, list[str]]:
    configured = os.environ.get("HGATCPLOT_RSCRIPT")
    if configured:
        resolved = shutil.which(configured) if not Path(configured).exists() else configured
        if resolved:
            return str(Path(resolved)), []
        return None, [f"HGATCPLOT_RSCRIPT points to '{configured}', but that executable was not found."]

    for candidate in ("R.exe", "Rscript.exe", "R"):
        found = shutil.which(candidate)
        if found:
            return str(Path(found)), []

    windows_roots = [Path("C:/Program Files/R"), Path("C:/Program Files (x86)/R")]
    discovered: list[Path] = []
    for root in windows_roots:
        if root.exists():
            discovered.extend(root.glob("R-*/bin/x64/R.exe"))
            discovered.extend(root.glob("R-*/bin/R.exe"))

    if discovered:
        newest = sorted(discovered, reverse=True)[0]
        return str(newest), []

    return None, [
        "R executable was not found. Set HGATCPLOT_RSCRIPT to R.exe, Rscript.exe, or a full R executable path."
    ]


def run_r_renderer(module: Any, parsed: ParsedTable, options: dict[str, Any], output_dir: Path) -> RRenderResult:
    check = check_r_engine(getattr(module, "r_packages", []))
    if not check.available or check.executable is None:
        return RRenderResult("failed", {}, parsed.warnings, check.errors)

    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = output_dir / "input.tsv"
    _write_parsed_table(input_path, parsed)

    artifacts = {
        "svg": str(output_dir / "plot.svg"),
        "png": str(output_dir / "plot.png"),
        "tiff": str(output_dir / "plot.tiff"),
        "pdf": str(output_dir / "plot.pdf"),
    }
    width = _int_option(options, "width", getattr(module, "default_options", {}).get("width", 900), 520, 1800)
    height = _int_option(options, "height", getattr(module, "default_options", {}).get("height", 620), 360, 1400)
    title = str(options.get("title") or getattr(module, "title", "HGATCplot"))
    timeout = _timeout_seconds()

    args = [
        str(input_path),
        str(output_dir),
        str(getattr(module, "slug", "plot")),
        str(getattr(module, "renderer_family", "bar")),
        str(width),
        str(height),
        title,
    ]

    try:
        completed = subprocess.run(
            _r_script_command(check.executable, SCRIPT_PATH, args),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RRenderResult("failed", {}, parsed.warnings, [f"R render timed out after {timeout} seconds."])
    except OSError as exc:
        return RRenderResult("failed", {}, parsed.warnings, [f"R render failed to start: {exc}."])

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "R render failed."
        return RRenderResult("failed", {}, parsed.warnings, [detail])

    missing = [fmt for fmt, path in artifacts.items() if not Path(path).exists() or Path(path).stat().st_size <= 50]
    if missing:
        return RRenderResult("failed", {}, parsed.warnings, [f"R render did not produce valid artifact(s): {', '.join(missing)}."])

    return RRenderResult("succeeded", artifacts, parsed.warnings, [])


def _write_parsed_table(path: Path, parsed: ParsedTable) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=parsed.headers, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(parsed.rows)


def _r_script_command(executable: str, script_path: Path, args: list[str]) -> list[str]:
    if Path(executable).name.lower().startswith("rscript"):
        return [executable, "--vanilla", str(script_path), *args]
    return [executable, "--slave", "--vanilla", "-f", str(script_path), "--args", *args]


def _r_expression_command(executable: str, expression: str) -> list[str]:
    if Path(executable).name.lower().startswith("rscript"):
        return [executable, "--vanilla", "-e", expression]
    return [executable, "--slave", "--vanilla", "-e", expression]


def _int_option(options: dict[str, Any], key: str, fallback: int, minimum: int, maximum: int) -> int:
    try:
        value = int(float(options.get(key, fallback)))
    except (TypeError, ValueError):
        value = fallback
    return max(minimum, min(maximum, value))


def _timeout_seconds() -> int:
    try:
        return max(5, min(300, int(os.environ.get("HGATCPLOT_R_TIMEOUT_SECONDS", "45"))))
    except ValueError:
        return 45
