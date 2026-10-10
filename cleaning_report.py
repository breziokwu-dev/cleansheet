"""Build a machine-readable summary of CleanSheet's before/after changes."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_cleaning_report(
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    file_name: str,
    changes: list[Any],
) -> dict[str, Any]:
    """Summarize dataset-level and per-column quality before and after cleaning.

    Column comparisons use position rather than labels because cleaning may
    standardize names, and input data can contain duplicate column labels.
    """
    original_missing = original.isna().sum()
    cleaned_missing = cleaned.isna().sum()

    column_count = max(len(original.columns), len(cleaned.columns))
    column_missing_values: list[dict[str, Any]] = []

    for position in range(column_count):
        original_name = (
            str(original.columns[position])
            if position < len(original.columns)
            else None
        )
        cleaned_name = (
            str(cleaned.columns[position])
            if position < len(cleaned.columns)
            else None
        )
        missing_before = (
            int(original_missing.iloc[position])
            if position < len(original.columns)
            else None
        )
        missing_after = (
            int(cleaned_missing.iloc[position])
            if position < len(cleaned.columns)
            else None
        )

        column_missing_values.append(
            {
                "position": position,
                "original_column": original_name,
                "cleaned_column": cleaned_name,
                "missing_before": missing_before,
                "missing_after": missing_after,
                "missing_change": (
                    missing_after - missing_before
                    if missing_before is not None and missing_after is not None
                    else None
                ),
            }
        )

    original_missing_cells = int(original.isna().sum().sum())
    cleaned_missing_cells = int(cleaned.isna().sum().sum())

    return {
        "file_name": file_name,
        "original_rows": int(len(original)),
        "cleaned_rows": int(len(cleaned)),
        "rows_removed": max(0, int(len(original) - len(cleaned))),
        "original_columns": int(len(original.columns)),
        "cleaned_columns": int(len(cleaned.columns)),
        "original_missing_cells": original_missing_cells,
        "cleaned_missing_cells": cleaned_missing_cells,
        "missing_cells_change": cleaned_missing_cells - original_missing_cells,
        "original_duplicate_rows": int(original.duplicated().sum()),
        "cleaned_duplicate_rows": int(cleaned.duplicated().sum()),
        "column_missing_values": column_missing_values,
        "changes": changes,
    }
