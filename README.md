# CleanSheet 🧹

CleanSheet is a small Python data-cleaning project for CSV and Excel (`.xlsx`) files. It includes a Streamlit interface for inspecting, cleaning, and exporting datasets, plus a command-line cleaner.

## Features

- Preview uploaded data and inspect row, column, missing-value, and duplicate counts.
- Read UTF-8 CSVs (including Excel-friendly BOM files) and fall back to a common Windows CSV encoding when needed.
- Download outputs with filenames based on the source file.
- Review data quality by column.
- Trim surrounding whitespace and standardize column names.
- Choose cleaning operations before exporting the result.
- Export cleaned data as CSV or Excel, plus a JSON report from the web app.
- Use the command-line tool for a guided cleaning workflow and a separate JSON report.

## Early customer pilot

CleanSheet is being prepared for a small, non-sensitive data-cleaning service pilot before a self-service launch. The current application is still a prototype; customer-facing workflows and data-handling practices must be validated before using it with real or confidential datasets.

See [the first-customer plan](docs/first-customer-plan.md) for the proposed service scope, validation steps, and data-handling checklist.

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

CleanSheet is an early prototype being prepared for real-world testing. It is not yet advertised as production-ready.

Before using it for business-critical data, verify the exported results against the original dataset. Do not upload confidential or personal data to any publicly hosted instance until its deployment, access controls, and data-handling practices have been reviewed. The current app processes uploaded files during a session and does not provide accounts, persistent project storage, or a formal data-retention policy.
