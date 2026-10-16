
import hashlib
import json
from io import BytesIO

import pandas as pd
import streamlit as st

from file_io import cleaned_filename, read_tabular_file


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

from cleaning_rules import (
    apply_missing_value_rules,
    standardize_columns,
    trim_text_values,
)
from cleaning_report import build_cleaning_report


def dataframe_to_excel(df):
    """Create an Excel file in memory."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Cleaned Data")

    return output.getvalue()


def load_file(uploaded_file):
    """Read CSV or Excel while keeping the upload untouched."""
    return read_tabular_file(uploaded_file, uploaded_file.name)


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

# A filename alone is not a reliable identity: users can upload a different
# file with the same name. Tie results to the actual uploaded bytes.
uploaded_file_bytes = uploaded_file.getvalue()
source_fingerprint = hashlib.sha256(uploaded_file_bytes).hexdigest()

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
            help="When enabled, later duplicate rows will be excluded from the exported dataset.",
        )

        confirm_row_removal = st.checkbox(
            "I understand that selected rules may remove rows from the exported dataset.",
            value=False,
            help="Required when removing duplicates or dropping rows with missing values.",
        )

        st.markdown("#### Missing values")
        st.caption(
            "Choose a rule separately for each column. Numeric conversion runs "
            "before these rules, so choose a compatible fill method for converted columns."
        )

        missing_rules = []
        for position, column in enumerate(original.columns):
            series = original.iloc[:, position]
            dtype = series.dtype
            options = [
                "Leave unchanged",
                "Drop rows where this column is missing",
                "Fill with most frequent value",
            ]
            if pd.api.types.is_numeric_dtype(dtype):
                options.extend([
                    "Fill with median",
                    "Fill with mean",
                ])
            else:
                options.append("Fill with 'Unknown'")

            action = st.selectbox(
                f"{position + 1}. {str(column)} ({int(series.isna().sum())} missing)",
                options,
                key=f"missing_rule_{position}",
            )
            missing_rules.append((position, action))

        st.markdown("#### Optional numeric conversion")

        # Position-based labels keep columns selectable even when names repeat.
        conversion_options = [
            f"{position + 1}. {str(column)}"
            for position, column in enumerate(original.columns)
        ]
        convert_columns = st.multiselect(
            "Choose columns to convert to numbers",
            options=conversion_options,
            help=(
                "Only selected columns are converted. "
                "Unconvertible values become missing values. "
                "The number identifies the column if names repeat."
            ),
        )

        submitted = st.form_submit_button(
            "Apply cleaning",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        selected_positions = [
            conversion_options.index(option)
            for option in convert_columns
        ]

        row_dropping_rules = [
            position
            for position, action in missing_rules
            if action == "Drop rows where this column is missing"
        ]
        if (remove_duplicates or row_dropping_rules) and not confirm_row_removal:
            st.error(
                "Before applying these rules, confirm that you understand rows "
                "may be excluded from the exported dataset. Review the selected "
                "row-removal settings, tick the confirmation checkbox, and submit again."
            )
            st.stop()

        incompatible_unknown_fills = [
            position + 1
            for position, action in missing_rules
            if position in selected_positions and action == "Fill with 'Unknown'"
        ]

        if incompatible_unknown_fills:
            columns_text = ", ".join(str(position) for position in incompatible_unknown_fills)
            st.error(
                "You selected numeric conversion and 'Fill with Unknown' for "
                f"the same column(s): {columns_text}. Choose 'Leave unchanged' "
                "or another compatible missing-value rule for those columns, "
                "then apply cleaning again."
            )
            st.stop()

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
            for position in selected_positions:
                column_name = str(cleaned.columns[position])
                series = cleaned.iloc[:, position]
                before_missing = int(series.isna().sum())
                numeric_series = pd.to_numeric(series, errors="coerce")
                after_missing = int(numeric_series.isna().sum())

                # Assign by position to support duplicate column names safely.
                cleaned.isetitem(position, numeric_series)

                converted.append({
                    "column": column_name,
                    "position": position + 1,
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

        cleaned, missing_changes = apply_missing_value_rules(
            cleaned,
            missing_rules,
        )
        changes.extend(missing_changes)

        report = build_cleaning_report(
            original=original,
            cleaned=cleaned,
            file_name=uploaded_file.name,
            changes=changes,
        )

        st.session_state["cleaned_data"] = cleaned
        st.session_state["cleaning_report"] = report
        st.session_state["source_file_name"] = uploaded_file.name
        st.session_state["source_fingerprint"] = source_fingerprint

        st.success("Cleaning completed. Review the results below.")


# -------------------- RESULTS AND EXPORT --------------------

if (
    "cleaned_data" in st.session_state
    and st.session_state.get("source_fingerprint") == source_fingerprint
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
                data=cleaned.to_csv(index=False).encode("utf-8-sig"),
                file_name=cleaned_filename(uploaded_file.name, ".csv"),
                mime="text/csv",
                use_container_width=True,
            )

        with d2:
            st.download_button(
                "Download cleaned Excel",
                data=excel_bytes,
                file_name=cleaned_filename(uploaded_file.name, ".xlsx"),
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
                file_name=cleaned_filename(uploaded_file.name, ".json"),
                mime="application/json",
                use_container_width=True,
            )

    except Exception as error:
        st.error(f"Could not prepare downloads: {error}")

    with st.expander("View per-column missing-value changes"):
        column_report = pd.DataFrame(report["column_missing_values"])
        st.dataframe(column_report, use_container_width=True)

    with st.expander("View full cleaning report"):
        st.json(report)