# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is a small, step-by-step learning project. This prototype currently uploads and profiles tabular data; natural-language analysis and charts will be added in later steps.

## Current status

The app currently supports CSV and Excel (`.xlsx`) files up to 25 MB. It reads the first worksheet in Excel files and shows row and column counts, inferred column types, per-column missing-value counts, and a ten-row preview. Invalid or empty files show a clear message.

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
