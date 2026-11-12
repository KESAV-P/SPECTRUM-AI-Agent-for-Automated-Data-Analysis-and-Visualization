# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is a Streamlit data analysis app with a multi-page layout. It uploads and profiles tabular data, runs deterministic analyses, creates interactive charts, and includes a Groq-powered (or offline rule-based) agent workflow with a planner, analyst, validator, and reporter.

## Pages

| Page | Description |
|---|---|
| 📊 **Explore Data** | Upload, profile, filter, group, and visualize your dataset manually |
| 🤖 **AI Analyst** | Ask a natural-language question; the agent plans and runs the analysis |
| 📖 **About** | Renders this README and DEMO guide inline |

## Features

- **Upload CSV or Excel (.xlsx)** files up to 25 MB
- **Data profile**: column types, missing values, 10-row preview, and descriptive statistics (`describe()`)
- **Filter rows**: numeric conditions (`equals`, `greater than`, `less than`) or category match
- **Numeric summary**: count, mean, minimum, maximum for any numeric column
- **Group analysis** with aggregations: **Sum**, **Average**, **Median**, **Std**
- **Correlation heatmap** (auto-shown when ≥ 2 numeric columns)
- **Visualizations**: Bar, Line, Pie, Scatter, Histogram, Box, **Heatmap**
- **Download** filtered data as CSV directly from the Explore page
- **AI Analyst** (Offline or Groq-powered):
  - **Offline mode** (no API key required): keyword-based rule planner picks an operation from your question
  - **Online mode**: Groq LLM plans the analysis via LangGraph tool-calling workflow
  - Analysis types: `numeric_summary`, `grouped_analysis`, `time_trend`, **`correlation`**, **`outlier_detection`**
  - Download result as JSON
  - **History panel**: expander showing previous questions in the session

## Analysis types

| Operation | What it does |
|---|---|
| `numeric_summary` | Count, mean, min, max for a chosen column |
| `grouped_analysis` | Aggregate a numeric column by a categorical column |
| `time_trend` | Aggregate a numeric column over a date column |
| `correlation` | Pearson correlation matrix across all numeric columns |
| `outlier_detection` | IQR-fence outlier count for a chosen column |

## Try the sample dataset

Upload [`data/sample_sales.csv`](data/sample_sales.csv) in the app. It contains fictional sales records with dates, regions, products, quantities, sales, profit, and one missing profit value.

Example questions for the AI Analyst:

- **Which region has the highest total sales?** → grouped_analysis, region × sales, Sum
- **What is the average profit by product?** → grouped_analysis, product × profit, Average
- **How do sales change over time?** → time_trend, order_date × sales
- **Show correlations between columns** → correlation heatmap
- **Find outliers in sales** → outlier_detection on sales column

## Run locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optionally set a Groq API key (required only for the online AI Analyst mode):

```bash
export GROQ_API_KEY="your-key"
```

Optionally set `GROQ_MODEL`; the default is `openai/gpt-oss-20b`.

Start the app:

```bash
streamlit run app.py
```

The **Offline** checkbox on the AI Analyst page lets you use the keyword-based planner without any API key.

## Run the evaluation checks

With the virtual environment active:

```bash
python -m unittest discover -s tests -v
```

The checks cover CSV and Excel uploads, known summary/grouping values, filters, charts (including Heatmap), Median/Std aggregations, common invalid inputs, mocked Groq planning/reporting, offline analysis (numeric summary, grouped, correlation, outlier detection, time trend), rejection of invalid tool arguments, and descriptive stats rendering. They do not measure live model accuracy or provider availability.
