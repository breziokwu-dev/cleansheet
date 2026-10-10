#!/usr/bin/env python3
"""
Clean CSV and Excel files safely.

Features:
- Keeps the original file unchanged.
- Trims leading/trailing whitespace in text cells.
- Standardizes column names.
- Reports duplicate rows and asks before removing them.
- Reports missing values and asks how to handle each affected column.
- Converts text columns to numeric only when every non-empty value converts safely.
- Does not guess ambiguous date formats.
- Writes a separate cleaned file and a JSON cleaning report.

Install:
    python -m pip install pandas openpyxl

Run:
    python data_cleaner.py path/to/file.csv
    python data_cleaner.py path/to/file.xlsx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def ask_choice(prompt: str, choices: dict[str, str], default: str) -> str:
    """Ask until the user enters a supported choice. Enter selects the default."""
    options = "/".join(choices)
    while True:
        answer = input(f"{prompt} [{options}] (default: {default}): ").strip().lower()
        if not answer:
            answer = default
        if answer in choices:
            return answer
        print(f"Please enter one of: {options}")


def standardize_column_name(name: Any) -> str:
    """Convert a column label to lowercase snake_case."""
    text = str(name).strip().lower()
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unnamed_column"


def make_unique_names(names: list[str]) -> list[str]:
    """Make standardized column names unique without discarding any column."""
    result: list[str] = []
    counts: dict[str, int] = {}
    for name in names:
        counts[name] = counts.get(name, 0) + 1
        candidate = name if counts[name] == 1 else f"{name}_{counts[name]}"
        while candidate in result:
            counts[name] += 1
            candidate = f"{name}_{counts[name]}"
        result.append(candidate)
    return result


def read_input(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read a CSV or the first worksheet of an Excel workbook."""
    details: dict[str, Any] = {"input_file": str(path), "input_format": path.suffix.lower()}
    if path.suffix.lower() == ".csv":
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
            try:
                frame = pd.read_csv(path, encoding=encoding)
                details["encoding_used"] = encoding
                return frame, details
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError(f"Could not decode this CSV file: {last_error}")
    if path.suffix.lower() == ".xlsx":
        frame = pd.read_excel(path, sheet_name=0, engine="openpyxl")
        workbook = pd.ExcelFile(path, engine="openpyxl")
        details["worksheet_processed"] = workbook.sheet_names[0] if workbook.sheet_names else None
        if len(workbook.sheet_names) > 1:
            details["note"] = (
                f"This workbook has {len(workbook.sheet_names)} worksheets. "
                "Version 1 processes only the first worksheet."
            )
        return frame, details
    raise ValueError(f"Unsupported file type: {path.suffix}. Use .csv or .xlsx.")


def json_safe(value: Any) -> Any:
    """Convert common pandas/numpy values into JSON-safe values."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely clean a CSV or Excel file and create a change report."
    )
    parser.add_argument("file", help="Path to the .csv or .xlsx file to clean")
    parser.add_argument(
        "--output",
        help="Optional output path. Default: inputname_cleaned.csv or .xlsx",
    )
    parser.add_argument(
        "--report",
        help="Optional report path. Default: inputname_cleaning_report.json",
    )
    args = parser.parse_args()

    source = Path(args.file).expanduser().resolve()
    if not source.exists() or not source.is_file():
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print("Error: use a .csv or .xlsx file.", file=sys.stderr)
        return 1

    output_suffix = source.suffix.lower()
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.with_name(f"{source.stem}_cleaned{output_suffix}")
    )
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else source.with_name(f"{source.stem}_cleaning_report.json")
    )

    # Prevent accidental replacement of the input, report, or one another.
    if output == source:
        print("Error: output path must not be the same as the original file.", file=sys.stderr)
        return 1
    if report_path == source or report_path == output:
        print("Error: report path must be different from the input and output paths.", file=sys.stderr)
        return 1
    if output.exists():
        choice = ask_choice(
            f"Output file already exists: {output}. Replace it?",
            {"y": "replace", "n": "cancel"},
            "n",
        )
        if choice == "n":
            print("Cancelled; no files were changed.")
            return 0
    if report_path.exists():
        choice = ask_choice(
            f"Report file already exists: {report_path}. Replace it?",
            {"y": "replace", "n": "cancel"},
            "n",
        )
        if choice == "n":
            print("Cancelled; no files were changed.")
            return 0

    try:
        df, details = read_input(source)
    except Exception as exc:
        print(f"Could not read the file: {exc}", file=sys.stderr)
        return 1

    original_rows, original_columns = df.shape
    report: dict[str, Any] = {
        **details,
        "started_at": datetime.now().astimezone().isoformat(),
        "original_shape": {"rows": original_rows, "columns": original_columns},
        "actions": [],
        "warnings": [],
        "unresolved_issues": [],
    }

    print("\n=== Data Cleaner ===")
    print(f"Input: {source}")
    print(f"Rows: {original_rows:,} | Columns: {original_columns:,}")
    if details.get("note"):
        print(f"Note: {details['note']}")

    # Standardize column names. If labels collide after normalization, add suffixes.
    old_columns = [str(col) for col in df.columns]
    new_columns = make_unique_names([standardize_column_name(col) for col in old_columns])
    if old_columns != new_columns:
        df.columns = new_columns
        report["actions"].append({
            "action": "standardized_column_names",
            "changed": [
                {"from": old, "to": new}
                for old, new in zip(old_columns, new_columns)
                if old != new
            ],
        })
        print("\nStandardized column names.")

    # Trim whitespace from text cells without changing missing values.
    trimmed_cells = 0
    for column in df.columns:
        if pd.api.types.is_object_dtype(df[column].dtype) or pd.api.types.is_string_dtype(df[column].dtype):
            def trim_value(value: Any) -> Any:
                nonlocal trimmed_cells
                if isinstance(value, str):
                    cleaned = value.strip()
                    if cleaned != value:
                        trimmed_cells += 1
                    return cleaned
                return value
            df[column] = df[column].map(trim_value)
    report["actions"].append({"action": "trimmed_text_whitespace", "cells_changed": trimmed_cells})
    print(f"Trimmed surrounding whitespace in {trimmed_cells:,} cell(s).")

    # Detect duplicate rows and ask before removing.
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        print(f"\nDetected {duplicate_count:,} fully duplicated row(s).")
        choice = ask_choice(
            "Remove duplicate rows? The first occurrence will be kept.",
            {"y": "remove", "n": "keep"},
            "n",
        )
        if choice == "y":
            before = len(df)
            df = df.drop_duplicates(keep="first").reset_index(drop=True)
            report["actions"].append({
                "action": "removed_duplicate_rows",
                "rows_removed": before - len(df),
                "policy": "kept first occurrence",
            })
        else:
            report["unresolved_issues"].append({
                "issue": "duplicate_rows",
                "count": duplicate_count,
                "decision": "kept; user declined removal",
            })
    else:
        print("\nNo fully duplicated rows detected.")

    # Report and optionally handle missing values, one column at a time.
    missing_by_column = df.isna().sum()
    missing_columns = [(str(col), int(count)) for col, count in missing_by_column.items() if count > 0]
    if missing_columns:
        print("\nMissing values detected:")
        for column, count in missing_columns:
            print(f"  - {column}: {count:,} missing value(s)")
        for column, count in missing_columns:
            print(f"\nColumn '{column}' has {count:,} missing value(s).")
            choice = ask_choice(
                "Choose how to handle them",
                {"k": "keep missing", "f": "fill with a value", "d": "drop rows missing this column"},
                "k",
            )
            if choice == "f":
                fill_value = input("Enter the exact value to use (e.g. Unknown, 0, or N/A): ")
                # Keep the user's entered value as text; do not guess numeric/date meaning.
                df[column] = df[column].fillna(fill_value)
                report["actions"].append({
                    "action": "filled_missing_values",
                    "column": column,
                    "count": count,
                    "fill_value": fill_value,
                    "value_treated_as": "text",
                })
            elif choice == "d":
                before = len(df)
                df = df.dropna(subset=[column]).reset_index(drop=True)
                report["actions"].append({
                    "action": "dropped_rows_with_missing_values",
                    "column": column,
                    "rows_removed": before - len(df),
                })
            else:
                report["unresolved_issues"].append({
                    "issue": "missing_values",
                    "column": column,
                    "count": count,
                    "decision": "kept missing",
                })
    else:
        print("No missing values detected.")

    # Safe numeric conversion: only convert when every non-empty value parses as a number.
    for column in list(df.columns):
        series = df[column]
        if not (
            pd.api.types.is_object_dtype(series.dtype)
            or pd.api.types.is_string_dtype(series.dtype)
        ):
            continue
        non_missing = series.dropna()
        if non_missing.empty:
            continue
        # Do not reinterpret identifiers that commonly contain leading zeroes.
        name = str(column).lower()
        identifier_like = any(word in name for word in ("id", "code", "zip", "postal", "phone", "telephone"))
        if identifier_like:
            report["unresolved_issues"].append({
                "issue": "possible_numeric_text",
                "column": str(column),
                "decision": "not converted because the column name suggests an identifier",
            })
            continue
        converted = pd.to_numeric(non_missing, errors="coerce")
        if converted.notna().all():
            choice = ask_choice(
                f"Column '{column}' contains text values that all look numeric. Convert to numbers?",
                {"y": "convert", "n": "leave as text"},
                "y",
            )
            if choice == "y":
                df[column] = pd.to_numeric(df[column], errors="coerce")
                report["actions"].append({
                    "action": "converted_text_to_numeric",
                    "column": str(column),
                    "non_missing_values_checked": int(len(non_missing)),
                })
            else:
                report["unresolved_issues"].append({
                    "issue": "numeric_text",
                    "column": str(column),
                    "decision": "left as text",
                })

    # Flag possible date columns instead of guessing ambiguous formats.
    for column in df.columns:
        name = str(column).lower()
        if any(token in name for token in ("date", "time", "dob", "birth")):
            if not pd.api.types.is_datetime64_any_dtype(df[column].dtype):
                report["unresolved_issues"].append({
                    "issue": "possible_date_column",
                    "column": str(column),
                    "decision": "not converted automatically; date formats may be ambiguous",
                })

    report["final_shape"] = {"rows": int(len(df)), "columns": int(len(df.columns))}
    report["finished_at"] = datetime.now().astimezone().isoformat()
    report["output_file"] = str(output)
    report["report_file"] = str(report_path)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".csv":
            df.to_csv(output, index=False, encoding="utf-8-sig")
        elif output.suffix.lower() == ".xlsx":
            df.to_excel(output, index=False, engine="openpyxl")

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=json_safe), encoding="utf-8")
    except Exception as exc:
        print(f"Error saving output/report: {exc}", file=sys.stderr)
        return 1

    print("\n=== Finished ===")
    print(f"Cleaned file: {output}")
    print(f"Report:       {report_path}")
    print(f"Rows:         {original_rows:,} -> {len(df):,}")
    print(f"Columns:      {original_columns:,} -> {len(df.columns):,}")
    if report["unresolved_issues"]:
        print(f"Items needing review: {len(report['unresolved_issues'])}")
        print("See the JSON report for details.")
    else:
        print("No unresolved issues were recorded.")
    print("The original file was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
