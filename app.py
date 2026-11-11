from pathlib import Path
import os

import streamlit as st
import pandas as pd
import plotly.express as px
from agentic_workflow import run_analysis


st.set_page_config(page_title="SPECTRUM Data Analyst", page_icon="📊")

st.title("SPECTRUM — AI Data Analyst")
st.write("A beginner-friendly prototype for inspecting tabular data.")

st.info("Upload a CSV or Excel (.xlsx) file up to 25 MB. Excel uploads use the first worksheet.")
sample_file = Path(__file__).parent / "data" / "sample_sales.csv"
st.download_button(
    "Download sample sales CSV",
    data=sample_file.read_bytes(),
    file_name="sample_sales.csv",
    mime="text/csv",
)

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

            st.subheader("Personalized visualizations")
            category_columns = [
                column
                for column in analysis_data.select_dtypes(exclude="number").columns
                if column not in date_columns
            ]
            chart_type = st.selectbox(
                "Chart type", ["Bar", "Line", "Pie", "Scatter", "Histogram", "Box"]
            )
            chart_theme = st.selectbox(
                "Chart theme", ["plotly_white", "plotly", "plotly_dark", "ggplot2"]
            )

            if chart_type in {"Bar", "Pie"} and category_columns and numeric_columns:
                group_column = st.selectbox("Category or group", category_columns)
                value_column = st.selectbox("Measure", numeric_columns)
                aggregation = st.selectbox("Aggregation", ["Sum", "Average"])
                grouped = analysis_data.groupby(group_column, dropna=False)[value_column]
                values = grouped.sum() if aggregation == "Sum" else grouped.mean()
                chart_frame = values.rename("Value").reset_index()
                if chart_type == "Bar":
                    figure = px.bar(chart_frame, x=group_column, y="Value", color=group_column, template=chart_theme)
                else:
                    figure = px.pie(chart_frame, names=group_column, values="Value", template=chart_theme)
                st.dataframe(values.sort_values(ascending=False).rename("Result").to_frame(), width="stretch")
                st.plotly_chart(figure, width="stretch")
            elif chart_type == "Line" and date_columns and numeric_columns:
                date_column = st.selectbox("Date column", date_columns)
                value_column = st.selectbox("Trend measure", numeric_columns)
                trend = pd.DataFrame(
                    {"Date": parsed_dates[date_column], "Value": analysis_data[value_column]}
                ).dropna().groupby("Date", as_index=False)["Value"].sum().sort_values("Date")
                if trend.empty:
                    st.info("No valid date and numeric value pairs are available to chart.")
                else:
                    st.plotly_chart(px.line(trend, x="Date", y="Value", markers=True, template=chart_theme), width="stretch")
            elif chart_type == "Scatter" and len(numeric_columns) >= 2:
                x_column = st.selectbox("X axis", numeric_columns)
                y_options = [column for column in numeric_columns if column != x_column]
                y_column = st.selectbox("Y axis", y_options)
                color_options = ["No color grouping", *category_columns]
                color_column = st.selectbox("Color by", color_options)
                figure = px.scatter(
                    analysis_data,
                    x=x_column,
                    y=y_column,
                    color=None if color_column == "No color grouping" else color_column,
                    template=chart_theme,
                )
                st.plotly_chart(figure, width="stretch")
            elif chart_type == "Histogram" and numeric_columns:
                value_column = st.selectbox("Distribution measure", numeric_columns)
                st.plotly_chart(px.histogram(analysis_data, x=value_column, template=chart_theme), width="stretch")
            elif chart_type == "Box" and numeric_columns:
                value_column = st.selectbox("Box plot measure", numeric_columns)
                group_column = st.selectbox("Optional category", ["No grouping", *category_columns])
                figure = px.box(
                    analysis_data,
                    y=value_column,
                    x=None if group_column == "No grouping" else group_column,
                    template=chart_theme,
                )
                st.plotly_chart(figure, width="stretch")
            else:
                st.info("This chart needs more suitable columns. Choose a chart supported by the available data.")

            st.subheader("Autonomous AI analyst")
            st.caption("The planner selects an analysis, Python computes it, a validator checks it, and the reporter explains the result.")
            question = st.text_input("Ask a question about this dataset", key="agent_question")
            api_key = os.environ.get("GROQ_API_KEY", "")
            if not api_key:
                st.info("To enable the Groq analyst, set the GROQ_API_KEY environment variable and restart the app.")
            if st.button("Analyze question", disabled=not api_key or not question.strip()):
                try:
                    with st.spinner("Planner, analyst, validator, and reporter are working…"):
                        agent_result = run_analysis(
                            question,
                            analysis_data,
                            api_key,
                            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"),
                        )
                    st.markdown("#### Agent explanation")
                    st.write(agent_result["explanation"])
                    with st.status("Agent activity", state="complete", expanded=True):
                        for step in agent_result["trace"]:
                            st.write(f"**{step['step']}:** {step['detail']}")
                        st.write("**Plan selected:**")
                        st.json(agent_result["plan"])
                    st.markdown("#### Verified calculation")
                    st.json(agent_result["result"])
                    if agent_result.get("figure") is not None:
                        st.plotly_chart(agent_result["figure"], width="stretch")
                except Exception as error:
                    st.error(f"The analyst could not complete this question: {error}")
