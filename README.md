# CleanSheet 🧹

CleanSheet is a small Python data-cleaning project for CSV and Excel (`.xlsx`) files. It includes a Streamlit interface for inspecting, cleaning, and exporting datasets, plus a command-line cleaner.

## Features

- Preview uploaded data and inspect row, column, missing-value, and duplicate counts.
- Review data quality by column.
- Trim surrounding whitespace and standardize column names.
- Choose cleaning operations before exporting the result.
- Export cleaned data as CSV or Excel, plus a JSON report from the web app.
- Use the command-line tool for a guided cleaning workflow and a separate JSON report.

## Requirements

- Python 3.10 or newer
- pip

## Setup

Clone the repository and move into its directory:

```bash
git clone https://github.com/breziokwu-dev/cleansheet.git
cd cleansheet
```

Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the web app

```bash
python -m streamlit run app.py
```

Streamlit will print a local URL to open in your browser. Upload a CSV or `.xlsx` file in the sidebar, inspect the data, select cleaning options, and review the output before downloading it.

## Run the command-line cleaner

```bash
python data_cleaner.py path/to/file.csv
```

Or use an Excel file:

```bash
python data_cleaner.py path/to/file.xlsx
```

The CLI asks before applying certain changes and writes a separate cleaned file and JSON report by default. You can choose output paths with `--output` and `--report`.

## Supported formats and current limitations

- CSV (`.csv`) and Excel (`.xlsx`) files are supported.
- The CLI currently processes the first worksheet in an Excel workbook.
- Excel formatting and macros are not preserved in exported data.
- Review cleaning choices and exported results before using them in important workflows; automatic type conversion can change how values are interpreted.

## Project status

CleanSheet is an evolving learning project. Features, validation, and automated tests will be improved over time.
