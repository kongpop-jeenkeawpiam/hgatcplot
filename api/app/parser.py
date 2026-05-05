from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SPECIAL_CHARACTERS = set("#<>%()")


@dataclass(frozen=True)
class ParsedTable:
    headers: list[str]
    rows: list[dict[str, str]]
    preview_rows: list[dict[str, str]]
    row_count: int
    column_count: int
    warnings: list[str]
    errors: list[str]


def parse_tabular_text(text: str, max_lines: int = 5000, preview_limit: int = 8) -> ParsedTable:
    normalized = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    warnings: list[str] = []
    errors: list[str] = []

    if not normalized:
        return ParsedTable([], [], [], 0, 0, warnings, ["Input data is required."])

    raw_lines = normalized.split("\n")
    blank_count = sum(1 for line in raw_lines if not line.strip())
    lines = [line.rstrip("\n") for line in raw_lines if line.strip()]

    if blank_count:
        warnings.append(f"Removed {blank_count} empty line(s) before validation.")

    if len(lines) > max_lines + 1:
        errors.append(f"Input has {len(lines) - 1} data lines. Maximum is {max_lines}.")

    if "\t" not in lines[0]:
        errors.append("Input must be tab-delimited. Copy from Excel or upload a tab-separated TXT file.")

    headers = [cell.strip() for cell in lines[0].split("\t")]
    if any(not header for header in headers):
        errors.append("Header names cannot be blank.")

    duplicate_headers = sorted({header for header in headers if headers.count(header) > 1})
    if duplicate_headers:
        errors.append(f"Duplicate header name(s): {', '.join(duplicate_headers)}.")

    if any(_contains_special_characters(cell) for line in lines for cell in line.split("\t")):
        warnings.append("Input contains special characters such as #, <, >, %, or parentheses; plain English labels are safest.")

    if any(_looks_like_comma_decimal(cell) for line in lines[1:] for cell in line.split("\t")):
        warnings.append("Some numeric values look like comma decimals. Use a decimal point, for example 3.14.")

    rows: list[dict[str, str]] = []
    expected_columns = len(headers)
    for line_number, line in enumerate(lines[1:], start=2):
        cells = [cell.strip() for cell in line.split("\t")]
        if len(cells) != expected_columns:
            errors.append(f"Line {line_number} has {len(cells)} column(s); expected {expected_columns}.")
            continue
        rows.append(dict(zip(headers, cells)))

    return ParsedTable(
        headers=headers,
        rows=rows,
        preview_rows=rows[:preview_limit],
        row_count=len(rows),
        column_count=len(headers),
        warnings=warnings,
        errors=errors,
    )


def numeric_value(row: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = row.get(key)
        if value is None or value == "":
            continue
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            continue
    return default


def _contains_special_characters(value: str) -> bool:
    return any(character in SPECIAL_CHARACTERS for character in value)


def _looks_like_comma_decimal(value: str) -> bool:
    if value.count(",") != 1:
        return False
    left, right = value.split(",", 1)
    return left.replace("-", "", 1).isdigit() and right.isdigit()

