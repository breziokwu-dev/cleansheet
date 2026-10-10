
import json
import re
from io import BytesIO

import pandas as pd
import streamlit as st


# -------------------- PAGE CONFIG --------------------

st.set_page_config(
    page_title="CleanSheet",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------- STYLING --------------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .hero {
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        margin-bottom: 0.3rem;
    }

    .muted {
        opacity: 0.7;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.25);
        padding: 1rem;
        border-radius: 12px;
    }

    div.stButton > button {
        border-radius: 9px;
        min-height: 2.7rem;
    }
</style>
""", unsafe_allow_html=True)


# -------------------- HELPERS --------------------

def standardize_columns(columns):
    """Convert column names into consistent snake_case names."""
    result = []
    seen = {}

    for column in columns:
        name = str(column).strip().lower()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^a-z0-9_]", "", name)
        name = name.strip("_") or "column"

        count = seen.get(name, 0) + 1
        seen[name] = count

        if count > 1:
            name = f"{name}_{count}"

        result.append(name)

    return result


def trim_text_values(df):
    """Trim surrounding spaces without changing non-text values."""
    result = df.copy()

    for column in result.select_dtypes(
        include=["object", "string"]
    ).columns:
        result[column] = result[column].map(
            lambda value: value.strip()
            if isinstance(value, str) else value
        )

    return result


def dataframe_to_excel(df):
    """Create an Excel file in memory."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")

    return output.getvalue()


def load_file(uploaded_file):
    """Read CSV or Excel while keeping the upload untouched."""
    uploaded_file.seek(0)

    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.title("🧹 CleanSheet")
    st.caption("Your personal data-cleaning workspace")

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload your dataset",
        type=["csv", "xlsx"],
        help="Supported formats: CSV and Excel (.xlsx).",
    )

    st.divider()

    st.caption("WORKFLOW")
    st.markdown(
        "1. Upload your file\n"
        "2. Inspect data quality\n"
        "3. Choose cleaning rules\n"
        "4. Review and export"
    )

    st.divider()
    st.caption("CleanSheet 2.0 · Local prototype")


# -------------------- MAIN HEADER --------------------

st.markdown("""
<div class="hero">
    <h1>Clean your data with confidence.</h1>
    <p class="muted">
        Inspect, clean, compare and export your dataset in one workspace.
    </p>
</div>
""", unsafe_allow_html=True)


if uploaded_file is None:
    st.info("Upload a CSV or Excel file using the sidebar to get started.")

    st.subheader("What you can do")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("### 🔎 Inspect")
        st.write("Preview your data and find missing values and duplicates.")

    with c2:
        st.markdown("### 🧹 Clean")
        st.write("Choose which cleaning operations to apply.")

    with c3:
        st.markdown("### 📥 Export")
        st.write("Download your cleaned dataset and a change report.")

    st.stop()


# -------------------- LOAD DATA --------------------

try:
    original = load_file(uploaded_file)
except Exception as error:
    st.error(f"Could not read the uploaded file: {error}")
    st.stop()


# Keep a separate copy. Never modify the uploaded DataFrame directly.
original = original.copy(deep=True)

if original.empty:
    st.warning("This file contains no data rows.")
    st.stop()


# -------------------- DATA OVERVIEW --------------------

st.subheader("Dataset overview")

missing_count = int(original.isna().sum().sum())
duplicate_count = int(original.duplicated().sum())

m1, m2, m3, m4 = st.columns(4)

m1.metric("Total rows", f"{len(original):,}")
m2.metric("Total columns", f"{len(original.columns):,}")
m3.metric("Missing cells", f"{missing_count:,}")
m4.metric("Duplicate rows", f"{duplicate_count:,}")

tab_preview, tab_quality, tab_clean = st.tabs(
    ["📋 Data preview", "🔎 Data quality", "🧹 Cleaning workspace"]
)


# -------------------- PREVIEW TAB --------------------

with tab_preview:
    st.subheader("Original dataset")
    st.caption("This is the uploaded data, before any cleaning.")

    st.dataframe(
        original.head(200),
        use_container_width=True,
        height=350,
    )

    st.caption(
        f"Showing up to 200 of {len(original):,} rows."
    )


# -------------------- QUALITY TAB --------------------

with tab_quality:
    st.subheader("Column quality report")

    quality = pd.DataFrame({
        "Column": original.columns.astype(str),
        "Data type": original.dtypes.astype(str).values,
        "Missing values": original.isna().sum().values,
        "Missing (%)": (
            original.isna().mean().mul(100).round(2).values
        ),
        "Unique values": original.nunique(dropna=True).values,
    })

    st.dataframe(quality, use_container_width=True)

    st.subheader("Duplicate rows")
    st.write(f"Found **{duplicate_count:,}** duplicate rows.")

    if duplicate_count:
        st.dataframe(
            original.loc[original.duplicated(keep=False)].head(100),
            use_container_width=True,
        )


# -------------------- CLEANING WORKSPACE --------------------

with tab_clean:
    st.subheader("Choose your cleaning rules")
    st.caption(
        "No changes are applied until you click Apply cleaning."
    )

    with st.form("cleaning_form"):
        st.markdown("#### General cleaning")

        trim_spaces = st.checkbox(
            "Trim surrounding spaces from text",
            value=True,
        )

        normalize_columns = st.checkbox(
            "Standardize column names",
            value=True,
        )

        remove_duplicates = st.checkbox(
            "Remove duplicate rows",
            value=False,
        )

        st.markdown("#### Missing values")

        missing_action = st.selectbox(
            "Apply this rule to missing values",
            [
                "Leave unchanged",
                "Remove rows containing missing values",
                "Fill missing text with 'Unknown'",
                "Fill missing numbers with the column median",
            ],
        )

        st.markdown("#### Optional numeric conversion")

        convert_columns = st.multiselect(
            "Choose columns to convert to numbers",
            options=list(original.columns),
            help=(
                "Only selected columns are converted. "
                "Unconvertible values become missing values."
            ),
        )

        submitted = st.form_submit_button(
            "Apply cleaning",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        cleaned = original.copy(deep=True)
        changes = []

        if trim_spaces:
            cleaned = trim_text_values(cleaned)
            changes.append("Trimmed surrounding spaces in text columns.")

        if normalize_columns:
            cleaned.columns = standardize_columns(cleaned.columns)
            changes.append("Standardized column names.")

        if convert_columns:
            converted = []

            for old_name in convert_columns:
                # Resolve the current column name after standardization.
                if normalize_columns:
                    position = list(original.columns).index(old_name)
                    column_name = cleaned.columns[position]
                else:
                    column_name = old_name

                before_missing = int(cleaned[column_name].isna().sum())

                cleaned[column_name] = pd.to_numeric(
                    cleaned[column_name],
                    errors="coerce",
                )

                after_missing = int(cleaned[column_name].isna().sum())

                converted.append({
                    "column": str(column_name),
                    "newly_missing": max(
                        0, after_missing - before_missing
                    ),
                })

            changes.append({
                "Numeric conversion": converted
            })

        if remove_duplicates:
            before = len(cleaned)
            cleaned = cleaned.drop_duplicates().copy()
            removed = before - len(cleaned)
            changes.append(f"Removed {removed} duplicate rows.")

        if missing_action == "Remove rows containing missing values":
            before = len(cleaned)
            cleaned = cleaned.dropna().copy()
            changes.append(
                f"Removed {before - len(cleaned)} rows with missing values."
            )

        elif missing_action == "Fill missing text with 'Unknown'":
            for column in cleaned.select_dtypes(
                include=["object", "string"]
            ).columns:
                cleaned[column] = cleaned[column].fillna("Unknown")

            changes.append("Filled missing text values with 'Unknown'.")

        elif missing_action == "Fill missing numbers with the column median":
            for column in cleaned.select_dtypes(
                include="number"
            ).columns:
                median = cleaned[column].median()

                if pd.notna(median):
                    cleaned[column] = cleaned[column].fillna(median)

            changes.append("Filled missing numeric values with column medians.")

        report = {
            "file_name": uploaded_file.name,
            "original_rows": int(len(original)),
            "cleaned_rows": int(len(cleaned)),
            "original_columns": int(len(original.columns)),
            "cleaned_columns": int(len(cleaned.columns)),
            "original_missing_cells": int(
                original.isna().sum().sum()
            ),
            "cleaned_missing_cells": int(
                cleaned.isna().sum().sum()
            ),
            "original_duplicate_rows": int(
                original.duplicated().sum()
            ),
            "cleaned_duplicate_rows": int(
                cleaned.duplicated().sum()
            ),
            "changes": changes,
        }

        st.session_state["cleaned_data"] = cleaned
        st.session_state["cleaning_report"] = report
        st.session_state["source_file_name"] = uploaded_file.name

        st.success("Cleaning completed. Review the results below.")


# -------------------- RESULTS AND EXPORT --------------------

if (
    "cleaned_data" in st.session_state
    and st.session_state.get("source_file_name") == uploaded_file.name
):
    cleaned = st.session_state["cleaned_data"]
    report = st.session_state["cleaning_report"]

    st.divider()
    st.subheader("Cleaning results")

    r1, r2, r3 = st.columns(3)
    r1.metric(
        "Rows removed",
        max(0, report["original_rows"] - report["cleaned_rows"]),
    )
    r2.metric(
        "Missing cells remaining",
        report["cleaned_missing_cells"],
    )
    r3.metric(
        "Duplicate rows remaining",
        report["cleaned_duplicate_rows"],
    )

    st.dataframe(
        cleaned.head(200),
        use_container_width=True,
        height=350,
    )

    st.subheader("Download your results")

    try:
        excel_bytes = dataframe_to_excel(cleaned)

        d1, d2, d3 = st.columns(3)

        with d1:
            st.download_button(
                "Download cleaned CSV",
                data=cleaned.to_csv(index=False).encode("utf-8"),
                file_name="cleaned_data.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with d2:
            st.download_button(
                "Download cleaned Excel",
                data=excel_bytes,
                file_name="cleaned_data.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        with d3:
            st.download_button(
                "Download JSON report",
                data=json.dumps(report, indent=2, default=str),
                file_name="cleaning_report.json",
                mime="application/json",
                use_container_width=True,
            )

    except Exception as error:
        st.error(f"Could not prepare downloads: {error}")

    with st.expander("View cleaning report"):
        st.json(report)