"""Robust file input and export helpers for CleanSheet."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def read_tabular_file(file_obj: Any, filename: str) -> pd.DataFrame:
    """Read a CSV or XLSX upload, including common Windows CSV encodings."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a CSV or Excel (.xlsx) file.")

    raw_bytes = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if not raw_bytes:
        raise ValueError("This file is empty. Choose a file that contains a dataset.")

    if suffix == ".csv":
        try:
            return pd.read_csv(BytesIO(raw_bytes), encoding="utf-8-sig")
        except UnicodeDecodeError:
            # Windows-exported CSVs commonly use a legacy Windows encoding.
            try:
                return pd.read_csv(BytesIO(raw_bytes), encoding="cp1252")
            except pd.errors.EmptyDataError as exc:
                raise ValueError("This CSV contains no readable rows or columns.") from exc
        except pd.errors.EmptyDataError as exc:
            raise ValueError("This CSV contains no readable rows or columns.") from exc

    try:
        return pd.read_excel(BytesIO(raw_bytes), engine="openpyxl")
    except (ValueError, OSError) as exc:
        raise ValueError(
            "Could not read this Excel file. Make sure it is a valid .xlsx workbook."
        ) from exc


def cleaned_filename(filename: str, extension: str) -> str:
    """Build a predictable download name from the uploaded file name."""
    if extension not in {".csv", ".xlsx", ".json"}:
        raise ValueError("Unsupported output extension.")
    stem = Path(filename).stem.strip() or "dataset"
    # Avoid path separators and characters that are awkward in download names.
    safe_stem = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in stem
    ).strip("_") or "dataset"
    suffix = "_cleaning_report" if extension == ".json" else "_cleaned"
    return f"{safe_stem}{suffix}{extension}"
