import json
from pathlib import Path

import pandas as pd
import pytest

from data_cleaner_v2 import (
    ask_choice,
    json_safe,
    make_unique_names,
    read_input,
    standardize_column_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Customer Name", "customer_name"),
        ("  City / Region  ", "city_region"),
        ("Age!!!", "age"),
        ("", "unnamed_column"),
        ("   ", "unnamed_column"),
        ("first__last", "first_last"),
    ],
)
def test_standardize_column_name(raw, expected):
    assert standardize_column_name(raw) == expected


def test_make_unique_names_adds_suffixes():
    assert make_unique_names(["name", "name", "city", "name"]) == [
        "name",
        "name_2",
        "city",
        "name_3",
    ]


def test_make_unique_names_handles_existing_suffix():
    assert make_unique_names(["name", "name", "name_2"]) == [
        "name",
        "name_2",
        "name_2_2",
    ]


def test_read_input_reads_csv_and_records_encoding(tmp_path):
    path = tmp_path / "people.csv"
    path.write_text("name,age\nAda,17\nJohn,18\n", encoding="utf-8")

    frame, details = read_input(path)

    assert list(frame.columns) == ["name", "age"]
    assert frame.to_dict(orient="records") == [
        {"name": "Ada", "age": 17},
        {"name": "John", "age": 18},
    ]
    assert details["input_format"] == ".csv"
    assert details["encoding_used"] in {"utf-8-sig", "utf-8"}


def test_read_input_reads_first_worksheet_of_xlsx(tmp_path):
    path = tmp_path / "people.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"name": ["Ada"], "age": [17]}).to_excel(
            writer, sheet_name="People", index=False
        )
        pd.DataFrame({"name": ["John"], "age": [18]}).to_excel(
            writer, sheet_name="Other", index=False
        )

    frame, details = read_input(path)

    assert frame.to_dict(orient="records") == [{"name": "Ada", "age": 17}]
    assert details["worksheet_processed"] == "People"
    assert "first worksheet" in details["note"]


def test_read_input_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "people.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        read_input(path)


def test_json_safe_converts_missing_values_and_timestamps():
    assert json_safe(float("nan")) is None
    assert json_safe(pd.NaT) is None
    assert json_safe(pd.Timestamp("2026-10-10")) == "2026-10-10T00:00:00"


def test_ask_choice_uses_default_when_user_hits_enter(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ask_choice("Remove duplicates?", {"y": "yes", "n": "no"}, "n") == "n"


def test_ask_choice_retries_invalid_input(monkeypatch):
    answers = iter(["maybe", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert ask_choice("Remove duplicates?", {"y": "yes", "n": "no"}, "n") == "y"
