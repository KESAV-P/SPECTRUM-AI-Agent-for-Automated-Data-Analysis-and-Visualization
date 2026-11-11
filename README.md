# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is being built as a small, step-by-step learning project. The first release will grow into a simple app for uploading a tabular dataset, asking supported questions, and viewing calculated answers and charts.

## Current status

The app currently supports CSV and Excel (`.xlsx`) upload, row and column counts, inferred column types, per-column missing-value counts, and a ten-row preview. Excel uploads read the first worksheet. Invalid or empty files show a clear message. Analysis will be added in a later, separately reviewed step.

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
