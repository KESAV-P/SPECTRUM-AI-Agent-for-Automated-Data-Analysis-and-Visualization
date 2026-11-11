# SPECTRUM Prototype Demo

## Before the demo

From the project folder, activate the virtual environment and run:

```bash
streamlit run app.py
```

Open the local URL shown in the terminal (normally `http://localhost:8501`) and upload `data/sample_sales.csv`.

## Four-minute walkthrough

1. **Introduce the prototype.** It profiles tables and supports both manual exploration and a Groq-powered agent workflow. For live agent questions, start the app with `GROQ_API_KEY` set in the environment.
2. **Show the data profile.** The sample has 12 records and 7 columns, with one missing `profit` value. Point out the inferred column types and the ten-row preview.
3. **Show a numeric summary.** Select `sales`. The expected count is 12, mean is 1,375, minimum is 300, and maximum is 2,400.
4. **Compare regions.** Choose `Bar`, then select `region`, `sales`, and `Sum`. Expected totals: West 5,550; North 3,900; South 3,800; East 3,250. The table and chart should agree.
5. **Personalize the chart.** Change the chart type to `Pie` and try a different theme. The displayed visualization responds to those choices.
6. **Show a trend.** Choose `Line`, then select `order_date` and `sales`. The chart should show 12 dated sales records in chronological order.
7. **Demonstrate a filter.** Select `sales`, choose `greater than`, and enter `1500`. The status should say that analysis uses 5 of 12 rows.
8. **Show the agent workflow.** With `GROQ_API_KEY` configured, ask “Which region had the highest sales?” Show the planner's selected operation, the locally calculated grouped totals, the validation and visualization steps, the chart, and the reporter's explanation.

## What to say about the current limits

- The first worksheet is used for Excel files.
- Uploads are limited to 25 MB.
- The app supports the listed filters and summaries; it does not generate arbitrary analyses.
- The agent supports a limited set of analysis operations. It does not generate or execute Python code.
- Dataset rows stay in the app; the question, schema, and calculated aggregates are sent to Groq for planning and explanation.
- Live AI answers require a working Groq API key and network access; the automated suite uses a mock model response.
