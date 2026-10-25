# CleanSheet 🧹

CleanSheet is a small Python data-cleaning project for CSV and Excel (.xlsx) files. It includes a Streamlit interface for inspecting, cleaning, and exporting datasets, plus a command-line cleaner.

## Features

- Preview uploaded data and inspect row, column, missing-value, and duplicate counts.
- Read UTF-8 CSVs (including Excel-friendly BOM files) and fall back to a common Windows CSV encoding when needed.
- Download outputs with filenames based on the source file.
- Review data quality by column.
- Trim surrounding whitespace and standardize column names.
- Choose cleaning operations before exporting the result.
- Export cleaned data as CSV or Excel, plus a JSON report from the web app.
- Use the command-line tool for a guided cleaning workflow and a separate JSON report.

## Try the demo dataset

A small, **synthetic** sales spreadsheet is included at [examples/demo_sales.csv](examples/demo_sales.csv). It contains intentionally messy examples such as extra spaces, missing values, and duplicate rows.

1. Run CleanSheet using the setup instructions below.
2. Upload examples/demo_sales.csv.
3. Review the overview and data-quality report.
4. Try trimming spaces and standardizing column names.
5. If you choose to remove duplicates or drop rows with missing values, read the confirmation prompt carefully.
6. Download the cleaned file and report, then compare them with the original.

The demo contains invented data only; it is suitable for screenshots or demonstrations without exposing anyone's real records.

## Early customer pilot

CleanSheet is being prepared for a small, non-sensitive data-cleaning service pilot before a self-service launch. The current application is still a prototype; customer-facing workflows and data-handling practices must be validated before using it with real or confidential datasets.

See [the first-customer plan](docs/first-customer-plan.md) for the proposed service scope, validation steps, and data-handling checklist.

## Security and upload limits

The web app has these defensive limits:

- Upload size: 10 MB.
- Worksheet dimensions: at most 100,000 rows, 500 columns, and 2,000,000 populated cells.
- CSV field size: at most 1,000,000 characters.
- XLSX archives are checked for expected workbook structure, excessive expansion, extreme compression ratios, excessive archive entries, and macro project files before parsing.
- Formula-like text in CSV and Excel exports is prefixed with an apostrophe to reduce the risk of spreadsheet formula injection. This intentionally changes risky text values in exported copies; inspect important outputs before using them.
- The app offers a Clear session data control to clear app-owned result state and reset the upload widget.

These are defense-in-depth measures, not a security guarantee. Formula handling differs between spreadsheet applications, and the clear-session control cannot guarantee immediate removal of every copy from hosting infrastructure or browser/runtime memory. Do not upload passwords, payment-card data, government identifiers, health records, confidential customer lists, or other sensitive files to the public demo. Use synthetic or redacted files while validating the product.

For a paid service, verify hosting terms, deployment settings, access control, dependency updates, and data-handling practices before launch. A public app URL is not a paywall, and the current app does not provide user accounts or paid-access enforcement.

## Requirements

- Python 3.10 or newer
- pip

## Setup

Clone the repository and move into its directory:

\`\`\`bash
git clone https://github.com/breziokwu-dev/cleansheet.git
cd cleansheet
\`\`\`

Create and activate a virtual environment (recommended):

\`\`\`bash
python -m venv .venv
\`\`\`

On Windows PowerShell:

\`\`\`powershell
.venv\Scripts\Activate.ps1
\`\`\`

On macOS/Linux:

\`\`\`bash
source .venv/bin/activate
\`\`\`

Install dependencies:

\`\`\`bash
python -m pip install -r requirements.txt
\`\`\`

## Run the web app

\`\`\`bash
python -m streamlit run app.py
\`\`\`

Streamlit will print a local URL to open in your browser. Upload a CSV or .xlsx file in the sidebar, inspect the data, select cleaning options, and review the output before downloading it.

## Run the command-line cleaner

\`\`\`bash
python data_cleaner.py path/to/file.csv
\`\`\`

Or use an Excel file:

\`\`\`bash
python data_cleaner.py path/to/file.xlsx
\`\`\`

The CLI asks before applying certain changes and writes a separate cleaned file and JSON report by default. You can choose output paths with --output and --report.

## Supported formats and current limitations

- CSV (.csv) and Excel (.xlsx) files are supported.
- The CLI currently processes the first worksheet in an Excel workbook.
- Excel formatting and macros are not preserved in exported data.
- Review cleaning choices and exported results before using them in important workflows; automatic type conversion can change how values are interpreted.
- The security checks described above apply to the web app's upload/export path; the command-line tool should only be run on files you trust.

## Project status

CleanSheet is an early prototype being prepared for real-world testing. It is not yet advertised as production-ready. Before using it for business-critical data, verify exported results against the original dataset and complete a deployment and privacy review.
