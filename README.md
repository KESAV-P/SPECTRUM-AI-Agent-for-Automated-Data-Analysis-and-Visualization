# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is a small, step-by-step learning project. It uploads and profiles tabular data, runs deterministic analyses, creates interactive charts, and includes a Groq-powered planner, analyst, validator, and reporter workflow.

## Current status

The app supports CSV and Excel (`.xlsx`) files up to 25 MB, profiles columns and missing values, filters rows, computes numeric and grouped summaries, and offers bar, line, pie, scatter, histogram, and box visualizations. With `GROQ_API_KEY` configured, its LangGraph workflow plans a supported analysis, runs fixed Python calculations, validates the result, selects a chart, and explains the evidence. It sends the question and column schema to Groq, not raw dataset rows; calculated aggregates are sent for the explanation step.

## Try the sample dataset

Upload [`data/sample_sales.csv`](data/sample_sales.csv) in the app. It contains fictional sales records with dates, regions, products, quantities, sales, profit, and one missing profit value.

Example questions to explore manually:

- Which region has the highest total sales? (Group by `region`, value `sales`, aggregation `Sum`.)
- What is the average profit by product? (Group by `product`, value `profit`, aggregation `Average`.)
- How do sales change over time? (Choose `order_date` and `sales` in the trend section.)
- Which rows have sales greater than 1,500? (Filter `sales` with `greater than` and `1500`.)

For a step-by-step presentation walkthrough with expected results, see [DEMO.md](DEMO.md).

## Run locally

From the project folder, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set a Groq API key in the terminal session. Do not commit the key:

```bash
export GROQ_API_KEY="your-key"
```

Optionally set `GROQ_MODEL`; the default is `openai/gpt-oss-20b`.

Start the app:

```bash
streamlit run app.py
```

## Run the evaluation checks

With the virtual environment active, run:

```bash
python -m unittest discover -s tests -v
```

The checks cover CSV and Excel uploads, known summary/grouping values, filters, charts, common invalid inputs, mocked Groq planning/reporting, and rejection of invalid tool arguments. They do not measure live model accuracy or provider availability.
