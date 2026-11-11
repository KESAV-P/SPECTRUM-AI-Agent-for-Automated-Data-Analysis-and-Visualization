import streamlit as st
import pandas as pd


st.set_page_config(page_title="SPECTRUM Data Analyst", page_icon="📊")

st.title("SPECTRUM — AI Data Analyst")
st.write("Explore a dataset by asking questions in plain language.")

st.info("Upload a CSV or Excel (.xlsx) file. Excel uploads use the first worksheet.")

uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

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
            st.dataframe(column_profile, use_container_width=True)

            st.subheader("Missing values")
            missing_profile = dataset.isna().sum().rename("Missing values").to_frame()
            missing_profile.index.name = "Column"
            st.dataframe(missing_profile, use_container_width=True)

            st.dataframe(dataset.head(10), use_container_width=True)
