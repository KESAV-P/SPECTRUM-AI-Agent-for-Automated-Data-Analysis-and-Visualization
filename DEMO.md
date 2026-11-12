# SPECTRUM Prototype Demo

## Before the demo

From the project folder, activate the virtual environment and run:

```bash
streamlit run app.py
```

Open the local URL shown in the terminal (normally `http://localhost:8501`) and upload `data/sample_sales.csv`.

## Five-minute walkthrough

1. **Introduce the prototype.** SPECTRUM has three pages: **Explore Data**, **AI Analyst**, and **About**. The Explore page works without any API key. The AI Analyst supports both an offline (keyword-based) mode and a Groq-powered mode.

2. **Show the data profile.** On the Explore page, upload `sample_sales.csv`. The app confirms "Loaded 12 rows and 7 columns." Point out the inferred column types, the missing `profit` value, the 10-row preview, and the new **Descriptive statistics** table (count/mean/std/min/max for each numeric column).

3. **Show a numeric summary.** Select `sales`. Expected: count 12, mean 1375, minimum 300, maximum 2400.

4. **Compare regions.** In the Group analysis section, choose `region`, `sales`, and **Sum**. Expected totals: West 5,550; North 3,900; South 3,800; East 3,250. Try switching the aggregation to **Median** or **Std** to show the new options.

5. **Show the correlation heatmap.** The heatmap appears automatically below the Group analysis section since the dataset has multiple numeric columns. Point out positive and negative correlations.

6. **Personalize the chart.** Change the chart type to **Heatmap** to show the correlation matrix as a visualization choice. Try **Bar**, **Pie**, or **Line** to see different views. Adjust the theme.

7. **Show a trend.** Choose **Line**, then select `order_date` and `sales`. The chart shows 12 dated records in chronological order.

8. **Demonstrate a filter.** Select `sales`, choose `greater than`, enter `1500`. The status caption confirms "Analysis uses 5 of 12 rows."

9. **Download filtered data.** Click the **Download filtered data as CSV** button to export the current filtered view.

10. **Switch to the AI Analyst page.** Check the **Offline mode** checkbox (no API key required).

    - **Offline correlation demo.** Ask: *"Show correlations between columns"*
      - The keyword planner detects "correlat" and selects `correlation`.
      - The analyst computes the full Pearson correlation matrix.
      - A heatmap figure is generated locally.
      - The offline reporter gives a template explanation — no API call is made.
      - The trace shows: Planner (offline) → Analyst → Validator → Visualizer → Reporter (offline).

    - **Offline outlier detection demo.** Ask: *"Find outliers in sales"*
      - The keyword planner detects "outlier" and selects `outlier_detection`.
      - The analyst applies IQR fences and counts rows outside Q1 − 1.5 × IQR and Q3 + 1.5 × IQR.
      - A box-plot is shown highlighting the distribution.
      - The result shows the fence values and outlier count.

11. **Show the agent workflow (online, with API key).** Uncheck Offline mode. Ask: *"Which region had the highest sales?"* Show the planner's selected operation (grouped_analysis), the locally calculated grouped totals, the validation step, the chart, and the reporter's explanation. Point out that only the question, schema, and aggregated results are sent to Groq — not raw data rows.

12. **Show the history panel.** After asking multiple questions, expand the **Previous questions** expander to review the session history.

13. **Download result.** Click the **Download result as JSON** button to export the analysis result for further use.

## What to say about the current limits

- The first worksheet is used for Excel files.
- Uploads are limited to 25 MB.
- Offline mode uses keyword matching; it does not understand complex or ambiguous questions.
- Online mode supports a fixed set of analysis operations — it does not generate or execute arbitrary Python code.
- Correlation requires at least two numeric columns; outlier detection requires at least one.
- Dataset rows stay in the app; in online mode, the question, column schema, and calculated aggregates are sent to Groq for planning and explanation.
- Live AI answers require a working Groq API key and network access; the automated suite uses a mock model response.
