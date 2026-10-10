"""Validation helpers for user-uploaded synthetic or real CSV files."""

import csv
from io import StringIO
import math
import re
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_DATA_ROWS = 5_000
REQUIRED_COLUMNS = (
    "segment",
    "quarter",
    "market_size_usd_billions",
    "growth_percent",
)
TEMPLATE_CSV = (
    "segment,quarter,market_size_usd_billions,growth_percent\n"
    "Example segment,Q1 '25,12.5,4.2\n"
)
_QUARTER_PATTERN = re.compile(r"^Q[1-4] '\d{2}$")


def validate_csv_upload(filename: str, content: bytes) -> dict[str, Any]:
    """Parse and validate a bounded UTF-8 CSV without trusting its contents."""
    if not filename.lower().endswith(".csv"):
        return _failure("Choose a file with the .csv extension.", status_code=415)
    if len(content) > MAX_UPLOAD_BYTES:
        return _failure(
            f"The file exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.",
            status_code=413,
        )
    if not content:
        return _failure("The uploaded file is empty.")
    if b"\x00" in content:
        return _failure("The file contains invalid binary data; upload a UTF-8 CSV.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _failure("The file must use UTF-8 text encoding.")

    try:
        reader = csv.reader(StringIO(text), strict=True)
        headers = next(reader, None)
    except csv.Error:
        return _failure("The CSV header is malformed. Check quoting and delimiters.")
    if not headers or not any(header.strip() for header in headers):
        return _failure("The CSV has no header row.")

    columns = [header.strip() for header in headers]
    if len(columns) != len(set(columns)):
        return _failure("The CSV contains duplicate column names.")
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_columns:
        return _failure(
            "Missing required columns: " + ", ".join(missing_columns) + ".",
            columns=columns,
        )

    try:
        frame = pd.read_csv(
            StringIO(text),
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=False,
            on_bad_lines="error",
        )
    except (EmptyDataError, ParserError, ValueError, csv.Error):
        return _failure(
            "The CSV rows could not be parsed. Check quoting and that each row has the same number of columns.",
            columns=columns,
        )

    if len(frame) > MAX_DATA_ROWS:
        return _failure(
            f"The file contains more than the {MAX_DATA_ROWS:,}-row limit.",
            columns=columns,
        )
    if frame.empty:
        return _failure("The CSV contains a header but no data rows.", columns=columns)

    frame.columns = columns
    valid_records: list[dict[str, Any]] = []
    errors: list[str] = []
    for csv_row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        row_errors: list[str] = []
        segment = str(row["segment"]).strip()
        quarter = str(row["quarter"]).strip()
        market_size_text = str(row["market_size_usd_billions"]).strip()
        growth_text = str(row["growth_percent"]).strip()

        if not segment:
            row_errors.append("segment is required")
        if not _QUARTER_PATTERN.fullmatch(quarter):
            row_errors.append("quarter must look like Q1 '25")

        market_size = _parse_finite_number(market_size_text)
        if market_size is None:
            row_errors.append("market_size_usd_billions must be a number")
        elif market_size <= 0:
            row_errors.append("market_size_usd_billions must be greater than zero")

        growth = _parse_finite_number(growth_text)
        if growth is None:
            row_errors.append("growth_percent must be a number")

        if row_errors:
            errors.append(f"Row {csv_row_number}: " + "; ".join(row_errors) + ".")
            continue

        assert market_size is not None and growth is not None
        record: dict[str, Any] = {
            column: str(row[column]).strip() for column in columns
        }
        record.update(
            {
                "segment": segment,
                "quarter": quarter,
                "market_size_usd_billions": market_size,
                "growth_percent": growth,
            }
        )
        valid_records.append(record)

    return {
        "ok": True,
        "filename": filename,
        "columns": columns,
        "total_rows": len(frame),
        "valid_rows": len(valid_records),
        "invalid_rows": len(frame) - len(valid_records),
        "errors": errors[:100],
        "errors_truncated": len(errors) > 100,
        "preview": valid_records[:20],
        "valid_records": valid_records,
        "max_rows": MAX_DATA_ROWS,
    }


def _parse_finite_number(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _failure(
    message: str,
    *,
    status_code: int = 422,
    columns: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "message": message,
        "columns": columns or [],
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "errors": [message],
        "preview": [],
        "valid_records": [],
        "status_code": status_code,
    }
