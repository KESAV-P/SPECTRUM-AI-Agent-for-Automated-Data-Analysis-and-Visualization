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

            analysis_data = dataset
            st.subheader("Filter rows")
            filter_choices = ["No filter", *dataset.columns.tolist()]
            filter_column = st.selectbox("Filter column", filter_choices)
            if filter_column != "No filter":
                if pd.api.types.is_numeric_dtype(dataset[filter_column]):
                    condition = st.selectbox(
                        "Numeric condition", ["equals", "greater than", "less than"]
                    )
                    threshold = st.number_input("Compare with", value=0.0)
                    if condition == "equals":
                        mask = dataset[filter_column] == threshold
                    elif condition == "greater than":
                        mask = dataset[filter_column] > threshold
                    else:
                        mask = dataset[filter_column] < threshold
                    analysis_data = dataset[mask]
                else:
                    values = dataset[filter_column].dropna().unique().tolist()
                    if values:
                        selected_value = st.selectbox("Value", values)
                        analysis_data = dataset[dataset[filter_column] == selected_value]
                    else:
                        analysis_data = dataset.iloc[0:0]
            st.caption(f"Analysis uses {len(analysis_data):,} of {len(dataset):,} rows.")

            st.subheader("Numeric summary")
            numeric_columns = analysis_data.select_dtypes(include="number").columns.tolist()
            if numeric_columns:
                selected_column = st.selectbox("Choose a numeric column", numeric_columns)
                summary = analysis_data[selected_column].agg(["count", "mean", "min", "max"])
                summary.index = ["Count", "Mean", "Minimum", "Maximum"]
                st.dataframe(summary.rename("Value").to_frame(), width="stretch")
            else:
                st.info("No numeric values are available in the current selection.")

            st.subheader("Compare categories")
            category_columns = analysis_data.select_dtypes(exclude="number").columns.tolist()
            if category_columns and numeric_columns:
                category_column = st.selectbox("Group by", category_columns)
                value_column = st.selectbox("Numeric value", numeric_columns)
                aggregation = st.selectbox("Aggregation", ["Sum", "Average"])
                grouped = analysis_data.groupby(category_column, dropna=False)[value_column]
                chart_data = grouped.sum() if aggregation == "Sum" else grouped.mean()
                chart_data = chart_data.sort_values(ascending=False)
                st.dataframe(
                    chart_data.rename("Result").to_frame(), width="stretch"
                )
                st.bar_chart(chart_data)
            else:
                st.info("A category column and a numeric column are needed for this chart.")

            date_columns = []
            parsed_dates = {}
            for column in analysis_data.columns:
                series = analysis_data[column]
                if pd.api.types.is_datetime64_any_dtype(series):
                    parsed = pd.to_datetime(series, errors="coerce")
                elif not pd.api.types.is_numeric_dtype(series) and series.notna().any():
                    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
                else:
                    continue
                non_missing = int(series.notna().sum())
                if non_missing and int(parsed.notna().sum()) / non_missing >= 0.8:
                    date_columns.append(column)
                    parsed_dates[column] = parsed

            st.subheader("Trend over time")
            if date_columns and numeric_columns:
                date_column = st.selectbox("Date column", date_columns)
                trend_value = st.selectbox("Trend value", numeric_columns)
                trend_data = pd.DataFrame(
                    {"date": parsed_dates[date_column], "value": analysis_data[trend_value]}
                ).dropna()
                trend_data = trend_data.groupby("date", as_index=True)["value"].sum().sort_index()
                if trend_data.empty:
                    st.info("No valid date and numeric value pairs are available to chart.")
                else:
                    st.line_chart(trend_data)
            else:
                st.info("A date column and a numeric column are needed for a trend chart.")
