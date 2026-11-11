# SPECTRUM — AI Agent for Automated Data Analysis and Visualization

SPECTRUM is being built as a small, step-by-step learning project. The first release will grow into a simple app for uploading a tabular dataset, asking supported questions, and viewing calculated answers and charts.

## Current status

The app currently supports CSV and Excel (`.xlsx`) upload and a ten-row preview. Excel uploads read the first worksheet. Profiling and analysis will be added in later, separately reviewed steps.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```
