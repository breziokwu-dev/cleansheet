import pandas as pd

from cleaning_report import build_cleaning_report


def test_report_summarizes_row_and_missing_value_changes():
    original = pd.DataFrame(
        {"Name": ["Ada", None, "Lin"], "Score": [10, 20, None]}
    )
    cleaned = pd.DataFrame(
        {"name": ["Ada", "Lin"], "score": [10.0, 0.0]}
    )
    changes = ["Removed 1 row.", "Filled 1 missing score."]

    report = build_cleaning_report(original, cleaned, "people.csv", changes)

    assert report["file_name"] == "people.csv"
    assert report["original_rows"] == 3
    assert report["cleaned_rows"] == 2
    assert report["rows_removed"] == 1
    assert report["original_missing_cells"] == 2
    assert report["cleaned_missing_cells"] == 0
    assert report["missing_cells_change"] == -2
    assert report["changes"] == changes


def test_report_compares_columns_by_position_after_renaming():
    original = pd.DataFrame(
        {"Full Name": ["Ada", None], "Age": [None, 12]}
    )
    cleaned = pd.DataFrame(
        {"full_name": ["Ada", "Unknown"], "age": [12.0, 12.0]}
    )

    report = build_cleaning_report(original, cleaned, "people.csv", [])

    assert report["column_missing_values"] == [
        {
            "position": 0,
            "original_column": "Full Name",
            "cleaned_column": "full_name",
            "missing_before": 1,
            "missing_after": 0,
            "missing_change": -1,
        },
        {
            "position": 1,
            "original_column": "Age",
            "cleaned_column": "age",
            "missing_before": 1,
            "missing_after": 0,
            "missing_change": -1,
        },
    ]


def test_report_handles_duplicate_column_names():
    original = pd.DataFrame([[None, "x"]], columns=["value", "value"])
    cleaned = pd.DataFrame([["Unknown", "x"]], columns=["value", "value"])

    report = build_cleaning_report(original, cleaned, "duplicate.csv", [])

    assert report["column_missing_values"][0]["missing_before"] == 1
    assert report["column_missing_values"][1]["missing_before"] == 0
    assert report["column_missing_values"][0]["missing_after"] == 0


def test_report_does_not_claim_negative_rows_removed():
    original = pd.DataFrame({"value": [1]})
    cleaned = pd.DataFrame({"value": [1, 2]})

    report = build_cleaning_report(original, cleaned, "data.csv", [])

    assert report["rows_removed"] == 0
