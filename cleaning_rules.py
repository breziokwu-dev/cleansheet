"""Reusable, testable data-cleaning rules for CleanSheet."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def standardize_columns(
    columns: list[Any],
    case_style: str = "lower",
    separator: str = "underscore",
    custom_names: list[str] | None = None,
) -> list[str]:
    """Apply user-selected casing and separators, preserving unique labels."""
    if case_style not in {"keep", "lower", "upper", "title"}:
        raise ValueError(f"Unsupported column case style: {case_style}")
    if separator not in {"space", "underscore", "hyphen"}:
        raise ValueError(f"Unsupported column separator: {separator}")
    if custom_names is not None and len(custom_names) != len(columns):
        raise ValueError("Custom names must match the number of columns.")

    joiner = {"space": " ", "underscore": "_", "hyphen": "-"}[separator]
    result: list[str] = []
    used: set[str] = set()

    for position, column in enumerate(columns):
        raw = str(custom_names[position] if custom_names is not None else column).strip()
        words = re.sub(r"[\\s_-]+", " ", raw).strip()
        if case_style == "lower":
            words = words.lower()
        elif case_style == "upper":
            words = words.upper()
        elif case_style == "title":
            words = words.title()
        name = re.sub(r"\\s+", joiner, words).strip(" _-")
        if not name:
            name = f"Column{position + 1}" if case_style in {"keep", "title"} else f"column{position + 1}"

        candidate = name
        suffix = 2
        while candidate.casefold() in used:
            candidate = f"{name}{joiner}{suffix}"
            suffix += 1
        result.append(candidate)
        used.add(candidate.casefold())
    return result


def detect_date_columns(df: pd.DataFrame) -> list[int]:
    """Suggest likely date columns without changing the original data."""
    candidates: list[int] = []
    pattern = re.compile(
        r"[-/.:]|\\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\\b",
        re.IGNORECASE,
    )
    for position in range(len(df.columns)):
        series = df.iloc[:, position]
        values = series.dropna()
        if values.empty:
            continue
        if pd.api.types.is_datetime64_any_dtype(series.dtype):
            candidates.append(position)
            continue
        if not (
            pd.api.types.is_object_dtype(series.dtype)
            or pd.api.types.is_string_dtype(series.dtype)
        ):
            continue
        strings = values.astype(str).str.strip()
        if not strings.map(lambda value: bool(pattern.search(value))).any():
            continue
        parsed = pd.to_datetime(strings, errors="coerce", format="mixed", dayfirst=False)
        if float(parsed.notna().mean()) >= 0.7:
            candidates.append(position)
    return candidates


def format_date_column(
    series: pd.Series,
    output_format: str,
    day_first: bool = True,
) -> tuple[pd.Series, int]:
    """Format parseable dates; retain invalid values and report their count."""
    allowed = {
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d-%m-%Y", "%d %b %Y", "%B %d, %Y",
    }
    if output_format not in allowed:
        raise ValueError("Unsupported output date format.")
    original = series.copy()
    parsed = pd.to_datetime(
        series, errors="coerce", format="mixed", dayfirst=day_first
    )
    formatted = original.astype("object").copy()
    valid = parsed.notna()
    formatted.loc[valid] = parsed.loc[valid].dt.strftime(output_format)
    failures = int((original.notna() & ~valid).sum())
    return formatted, failures


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
    """Apply missing-value rules by column position, so duplicate labels are safe."""
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
            result = result.loc[result.iloc[:, position].notna()].copy()
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
            if not (pd.api.types.is_object_dtype(series.dtype) or pd.api.types.is_string_dtype(series.dtype)):
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
