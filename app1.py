
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="CleanSheet",
    page_icon="🧹",
    layout="wide"
)

st.title("🧹 CleanSheet")
st.caption("A simple tool for cleaning messy CSV and Excel files.")

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully!")

        # Dataset overview
        st.subheader("Dataset overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Rows", df.shape[0])

        with col2:
            st.metric("Columns", df.shape[1])

        with col3:
            st.metric("Missing cells", int(df.isna().sum().sum()))

        with col4:
            st.metric("Duplicate rows", int(df.duplicated().sum()))

        # Preview original data
        st.subheader("Data preview")
        st.dataframe(df.head(100), use_container_width=True)

        # Cleaning options
        st.subheader("Cleaning options")

        trim_text = st.checkbox(
            "Remove unnecessary spaces from text",
            value=True
        )

        standardize_columns = st.checkbox(
            "Standardize column names",
            value=True
        )

        remove_duplicates = st.checkbox(
            "Remove duplicate rows",
            value=False
        )

        missing_action = st.selectbox(
            "How should missing values be handled?",
            [
                "Leave unchanged",
                "Remove rows with missing values",
                "Fill missing text with 'Unknown'",
                "Fill missing numeric values with the column median"
            ]
        )

        if st.button("Clean dataset", type="primary"):
            cleaned = df.copy()

            if trim_text:
                for column in cleaned.select_dtypes(
                    include=["object", "string"]
                ).columns:
                    cleaned[column] = cleaned[column].map(
                        lambda value: value.strip()
                        if isinstance(value, str) else value
                    )

            if standardize_columns:
                cleaned.columns = (
                    cleaned.columns.astype(str)
                    .str.strip()
                    .str.lower()
                    .str.replace(r"\s+", "_", regex=True)
                    .str.replace(r"[^a-z0-9_]", "", regex=True)
                )

            if remove_duplicates:
                cleaned = cleaned.drop_duplicates()

            if missing_action == "Remove rows with missing values":
                cleaned = cleaned.dropna()

            elif missing_action == "Fill missing text with 'Unknown'":
                for column in cleaned.select_dtypes(
                    include=["object", "string"]
                ).columns:
                    cleaned[column] = cleaned[column].fillna("Unknown")

            elif missing_action == (
                "Fill missing numeric values with the column median"
            ):
                for column in cleaned.select_dtypes(
                    include="number"
                ).columns:
                    median = cleaned[column].median()
                    if pd.notna(median):
                        cleaned[column] = cleaned[column].fillna(median)

            st.session_state["cleaned_data"] = cleaned

        # Results
        if "cleaned_data" in st.session_state:
            cleaned = st.session_state["cleaned_data"]

            st.subheader("Cleaning results")

            left, right = st.columns(2)

            with left:
                st.write("**Original data**")
                st.dataframe(df.head(100), use_container_width=True)

            with right:
                st.write("**Cleaned data**")
                st.dataframe(cleaned.head(100), use_container_width=True)

            st.metric("Rows after cleaning", cleaned.shape[0])

            csv_bytes = cleaned.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download cleaned CSV",
                data=csv_bytes,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )

            report = {
                "original_rows": int(df.shape[0]),
                "cleaned_rows": int(cleaned.shape[0]),
                "original_columns": int(df.shape[1]),
                "cleaned_columns": int(cleaned.shape[1]),
                "original_missing_cells": int(df.isna().sum().sum()),
                "cleaned_missing_cells": int(cleaned.isna().sum().sum()),
                "original_duplicate_rows": int(df.duplicated().sum()),
                "cleaned_duplicate_rows": int(cleaned.duplicated().sum())
            }

            st.download_button(
                "Download cleaning report",
                data=pd.Series(report).to_json(indent=2),
                file_name="cleaning_report.json",
                mime="application/json"
            )

    except Exception as error:
        st.error(f"Could not read or process this file: {error}")