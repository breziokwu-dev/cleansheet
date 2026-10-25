"""Safe, bounded file input and spreadsheet export helpers for CleanSheet."""

from __future__ import annotations

import csv
from io import BytesIO, TextIOWrapper
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd
from openpyxl import load_workbook


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 500
MAX_FIELD_CHARS = 1_000_000
MAX_XLSX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_XLSX_ENTRIES = 2_000
MAX_COMPRESSION_RATIO = 100


def _read_bytes(file_obj) -> bytes:
    raw_bytes = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if not isinstance(raw_bytes, bytes):
        raise ValueError("The uploaded file could not be read.")
    if not raw_bytes:
        raise ValueError("This file is empty. Choose a file that contains a dataset.")
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 10 MB upload limit.")
    return raw_bytes


def _validate_csv_structure(raw_bytes: bytes, encoding: str) -> None:
    """Bound CSV dimensions and field sizes before loading into pandas."""
    csv.field_size_limit(MAX_FIELD_CHARS)
    row_count = 0
    try:
        with TextIOWrapper(BytesIO(raw_bytes), encoding=encoding, newline="") as text:
            reader = csv.reader(text, strict=True)
            for row in reader:
                if not row:
                    continue
                row_count += 1
                if row_count > MAX_ROWS + 1:  # allow one header row
                    raise ValueError("CSV exceeds the 100,000-row limit.")
                if len(row) > MAX_COLUMNS:
                    raise ValueError("CSV exceeds the 500-column limit.")
    except UnicodeDecodeError:
        raise
    except csv.Error as exc:
        raise ValueError("This CSV is malformed or contains a field that is too large.") from exc


def _validate_xlsx(raw_bytes: bytes) -> None:
    """Reject suspicious archives and oversized worksheets before pandas loads them."""
    try:
        with ZipFile(BytesIO(raw_bytes)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_XLSX_ENTRIES:
                raise ValueError("Excel workbook contains too many internal files.")
            total_uncompressed = sum(entry.file_size for entry in entries)
            if total_uncompressed > MAX_XLSX_UNCOMPRESSED_BYTES:
                raise ValueError("Excel workbook expands beyond the 100 MB processing limit.")
            for entry in entries:
                if entry.file_size > 1_000_000 and (
                    entry.compress_size == 0
                    or entry.file_size / entry.compress_size > MAX_COMPRESSION_RATIO
                ):
                    raise ValueError("Excel workbook has a suspicious compression ratio.")
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
                raise ValueError("This is not a valid .xlsx workbook.")
            if "xl/vbaProject.bin" in names:
                raise ValueError("Macro-enabled workbooks are not accepted.")
    except BadZipFile as exc:
        raise ValueError("This is not a valid .xlsx workbook.") from exc

    workbook = None
    try:
        workbook = load_workbook(BytesIO(raw_bytes), read_only=True, data_only=True)
        if not workbook.worksheets:
            raise ValueError("Excel workbook contains no worksheets.")
        sheet = workbook.worksheets[0]
        # Ignore potentially inaccurate worksheet dimension metadata.
        sheet.reset_dimensions()
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if row_number > MAX_ROWS + 1:
                raise ValueError("Excel workbook exceeds the 100,000-row limit.")
            if len(row) > MAX_COLUMNS:
                raise ValueError("Excel workbook exceeds the 500-column limit.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Could not safely inspect this Excel workbook.") from exc
    finally:
        if workbook is not None:
            workbook.close()


def read_tabular_file(file_obj, filename: str) -> pd.DataFrame:
    """Read a bounded CSV or XLSX upload with structural validation."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a CSV or Excel (.xlsx) file.")

    raw_bytes = _read_bytes(file_obj)

    if suffix == ".csv":
        encoding = "utf-8-sig"
        try:
            _validate_csv_structure(raw_bytes, encoding)
        except UnicodeDecodeError:
            encoding = "cp1252"
            _validate_csv_structure(raw_bytes, encoding)

        try:
            return pd.read_csv(BytesIO(raw_bytes), encoding=encoding)
        except pd.errors.EmptyDataError as exc:
            raise ValueError("This CSV contains no readable rows or columns.") from exc
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise ValueError("This CSV is malformed or could not be decoded.") from exc

    _validate_xlsx(raw_bytes)
    try:
        return pd.read_excel(BytesIO(raw_bytes), engine="openpyxl")
    except Exception as exc:
        raise ValueError("Could not read this Excel file. Make sure it is a valid .xlsx workbook.") from exc


def _is_formula_like(value: str) -> bool:
    """Detect text that spreadsheet software may interpret as a formula."""
    stripped = value.lstrip(" \t\r\n\u0000\uFEFF")
    if value.startswith(("\t", "\r", "\n")):
        return True
    return stripped.startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠"))


def spreadsheet_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Copy a frame and neutralize formula-like text for spreadsheet exports.

    Numeric cells remain numeric. A leading apostrophe is deliberately added
    to risky text values and headers; this changes the exported text slightly
    but helps prevent spreadsheet formula evaluation.
    """
    safe = df.copy(deep=True)
    safe.columns = [
        "'" + column if isinstance(column, str) and _is_formula_like(column) else column
        for column in safe.columns
    ]
    for position in range(len(safe.columns)):
        series = safe.iloc[:, position]
        if (
            pd.api.types.is_object_dtype(series.dtype)
            or pd.api.types.is_string_dtype(series.dtype)
        ):
            safe.isetitem(
                position,
                series.map(
                    lambda value: "'" + value
                    if isinstance(value, str) and _is_formula_like(value)
                    else value
                ),
            )
    return safe


def cleaned_filename(filename: str, extension: str) -> str:
    """Build a predictable, length-limited download name from the source name."""
    if extension not in {".csv", ".xlsx", ".json"}:
        raise ValueError("Unsupported output extension.")
    stem = Path(filename).stem.strip() or "dataset"
    safe_stem = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in stem
    ).strip("_") or "dataset"
    safe_stem = safe_stem[:100].rstrip("_") or "dataset"
    suffix = "_cleaning_report" if extension == ".json" else "_cleaned"
    return f"{safe_stem}{suffix}{extension}"
