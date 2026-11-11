import streamlit as st
import pandas as pd


st.set_page_config(page_title="SPECTRUM Data Analyst", page_icon="📊")

st.title("SPECTRUM — AI Data Analyst")
st.write("A beginner-friendly prototype for inspecting tabular data.")

st.info("Upload a CSV or Excel (.xlsx) file up to 25 MB. Excel uploads use the first worksheet.")

uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx"],
    max_upload_size=25,
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".xlsx"):
            dataset = pd.read_excel(uploaded_file, sheet_name=0)
        else:
            dataset = pd.read_csv(uploaded_file)
    except Exception:
        st.error("Could not read this file. Check that it is a valid CSV or .xlsx workbook.")
    else:
        if dataset.empty or len(dataset.columns) == 0:
            st.error("This file does not contain any data rows to preview.")
        else:
            st.success(f"Loaded {len(dataset):,} rows and {len(dataset.columns):,} columns.")

            st.subheader("Columns")
            column_profile = dataset.dtypes.astype(str).rename("Detected type").to_frame()
            column_profile.index.name = "Column"
            st.dataframe(column_profile, width="stretch")

            st.subheader("Missing values")
            missing_profile = dataset.isna().sum().rename("Missing values").to_frame()
            missing_profile.index.name = "Column"
            st.dataframe(missing_profile, width="stretch")

            st.dataframe(dataset.head(10), width="stretch")

            st.subheader("Numeric summary")
            numeric_columns = dataset.select_dtypes(include="number").columns.tolist()
            if numeric_columns:
                selected_column = st.selectbox("Choose a numeric column", numeric_columns)
                summary = dataset[selected_column].agg(["count", "mean", "min", "max"])
                summary.index = ["Count", "Mean", "Minimum", "Maximum"]
                st.dataframe(summary.rename("Value").to_frame(), width="stretch")
            else:
                st.info("This dataset has no numeric columns to summarize.")
