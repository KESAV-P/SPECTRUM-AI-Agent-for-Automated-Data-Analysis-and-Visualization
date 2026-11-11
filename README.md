# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is a small, step-by-step learning project. This prototype currently uploads and profiles tabular data; natural-language analysis and charts will be added in later steps.

## Current status

The app currently supports CSV and Excel (`.xlsx`) files up to 25 MB. It reads the first worksheet in Excel files and shows row and column counts, inferred column types, per-column missing-value counts, and a ten-row preview. Users can filter rows by a category or numeric condition, summarize numeric columns, compare category totals or averages with a bar chart, and view a time trend when usable date data is present. Invalid or empty files show a clear message.

## Try the sample dataset

Upload [`data/sample_sales.csv`](data/sample_sales.csv) in the app. It contains fictional sales records with dates, regions, products, quantities, sales, profit, and one missing profit value.

Example questions to explore manually:

- Which region has the highest total sales? (Group by `region`, value `sales`, aggregation `Sum`.)
- What is the average profit by product? (Group by `product`, value `profit`, aggregation `Average`.)
- How do sales change over time? (Choose `order_date` and `sales` in the trend section.)
- Which rows have sales greater than 1,500? (Filter `sales` with `greater than` and `1500`.)

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

Start the app:

```bash
streamlit run app.py
```
