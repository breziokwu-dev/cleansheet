from io import BytesIO

import pandas as pd
import pytest

from file_io import cleaned_filename, read_tabular_file


def test_reads_utf8_csv_with_bom():
    upload = BytesIO("\ufeffname,score\nAda,10\n".encode("utf-8"))
    frame = read_tabular_file(upload, "people.csv")

    assert frame.to_dict("records") == [{"name": "Ada", "score": 10}]


def test_reads_common_windows_encoded_csv():
    upload = BytesIO("name,city\nAndré,Montréal\n".encode("cp1252"))
    frame = read_tabular_file(upload, "people.csv")

    assert frame.loc[0, "name"] == "André"
    assert frame.loc[0, "city"] == "Montréal"


def test_rejects_unsupported_file_extension():
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_tabular_file(BytesIO(b"data"), "people.xls")


def test_rejects_empty_file_with_helpful_message():
    with pytest.raises(ValueError, match="file is empty"):
        read_tabular_file(BytesIO(b"\n\n"), "empty.csv")


def test_reports_csv_without_readable_content():
    with pytest.raises(ValueError, match="no readable rows or columns"):
        read_tabular_file(BytesIO(b""), "empty.csv")


def test_download_filename_uses_safe_source_name():
    assert cleaned_filename("March Sales.xlsx", ".xlsx") == "March_Sales_cleaned.xlsx"
    assert cleaned_filename("../private data.csv", ".csv") == "private_data_cleaned.csv"
    assert cleaned_filename("people.csv", ".json") == "people_cleaning_report.json"


def test_rejects_unsupported_download_extension():
    with pytest.raises(ValueError, match="Unsupported output extension"):
        cleaned_filename("people.csv", ".exe")

def test_invalid_excel_file_has_helpful_message():
    with pytest.raises(ValueError, match="valid .xlsx workbook"):
        read_tabular_file(BytesIO(b"not an excel workbook"), "broken.xlsx")
