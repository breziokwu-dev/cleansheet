"""Reusable, testable data-cleaning rules for CleanSheet."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def standardize_columns(columns: list[Any]) -> list[str]:
    """Convert labels to unique lowercase snake_case names.

    The uniqueness check handles collisions such as columns named "a", "a",
    and "a_2" without overwriting or merging any columns.
    """
    result: list[str] = []
    used: set[str] = set()

    for column in columns:
        name = str(column).strip().lower()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^a-z0-9_]", "", name)
        name = name.strip("_") or "column"

        candidate = name
        suffix = 2
        while candidate in used:
            candidate = f"{name}_{suffix}"
            suffix += 1

        result.append(candidate)
        used.add(candidate)

    return result


def trim_text_values(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace around strings without changing other values."""
    result = df.copy(deep=True)

    for position in range(len(result.columns)):
        series = result.iloc[:, position]
        if pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype):
            trimmed = series.map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            result.isetitem(position, trimmed)

    return result


def apply_missing_value_rules(
    df: pd.DataFrame,
    rules: list[tuple[int, str]],
) -> tuple[pd.DataFrame, list[str]]:
    """Apply missing-value rules by column position, so duplicate labels are safe.

    Supported actions are: leave unchanged, drop rows missing in that column,
    fill with mode, fill with median/mean for numeric columns, and fill text
    values with 'Unknown'.
    """
    result = df.copy(deep=True)
    changes: list[str] = []

    for position, action in rules:
        if position < 0 or position >= len(result.columns):
            raise IndexError(f"Column position out of range: {position}")

        if action == "Leave unchanged":
            continue

        column_label = str(result.columns[position])
        series = result.iloc[:, position]
        before_missing = int(series.isna().sum())

        if action == "Drop rows where this column is missing":
            before_rows = len(result)
            keep_mask = result.iloc[:, position].notna()
            result = result.loc[keep_mask].copy()
            removed = before_rows - len(result)
            changes.append(f"Column '{column_label}': removed {removed} rows with missing values.")
            continue

        if action == "Fill with most frequent value":
            modes = series.mode(dropna=True)
            if modes.empty:
                changes.append(f"Column '{column_label}': no non-missing value available for mode fill; left unchanged.")
                continue
            fill_value = modes.iloc[0]
        elif action == "Fill with median":
            if not pd.api.types.is_numeric_dtype(series.dtype):
                raise TypeError(f"Median fill requires a numeric column: {column_label}")
            fill_value = series.median()
            if pd.isna(fill_value):
                changes.append(f"Column '{column_label}': no median available; left unchanged.")
                continue
        elif action == "Fill with mean":
            if not pd.api.types.is_numeric_dtype(series.dtype):
                raise TypeError(f"Mean fill requires a numeric column: {column_label}")
            fill_value = series.mean()
            if pd.isna(fill_value):
                changes.append(f"Column '{column_label}': no mean available; left unchanged.")
                continue
        elif action == "Fill with 'Unknown'":
            if not (
                pd.api.types.is_object_dtype(series.dtype)
                or pd.api.types.is_string_dtype(series.dtype)
            ):
                raise TypeError(f"'Unknown' fill requires a text column: {column_label}")
            fill_value = "Unknown"
        else:
            raise ValueError(f"Unsupported missing-value action: {action}")

        result.isetitem(position, series.fillna(fill_value))
        after_missing = int(result.iloc[:, position].isna().sum())
        changes.append(
            f"Column '{column_label}': filled {before_missing - after_missing} missing values using {action.lower()}."
        )

    return result, changes
