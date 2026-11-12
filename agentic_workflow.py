"""Constrained Groq + LangGraph workflow for natural-language dataset analysis."""

from __future__ import annotations

import json
import math
from typing import Any, TypedDict

import pandas as pd
import plotly.express as px
from groq import Groq
from langgraph.graph import END, START, StateGraph


class AnalysisState(TypedDict, total=False):
    question: str
    dataframe: pd.DataFrame
    client: Any
    model: str
    plan: dict[str, Any]
    result: dict[str, Any]
    figure: Any
    explanation: str
    trace: list[dict[str, str]]
    error: str
    offline: bool


def _trace(state: AnalysisState, node: str, detail: str) -> list[dict[str, str]]:
    return [*state.get("trace", []), {"step": node, "detail": detail}]


def _offline_plan(question: str, frame: pd.DataFrame) -> dict:
    """Keyword-based rule planner that requires no API key."""
    q = question.lower()

    # Determine operation
    if any(kw in q for kw in ["correlat", "relationship", "heatmap", "together"]):
        operation = "correlation"
    elif any(kw in q for kw in ["outlier", "anomal", "unusual", "extreme"]):
        operation = "outlier_detection"
    elif any(kw in q for kw in ["trend", "over time", "timeline", "by date", "time series"]):
        operation = "time_trend"
    elif any(kw in q for kw in ["group", "by region", "by product", "by category", "per ", "each "]):
        operation = "grouped_analysis"
    else:
        operation = "numeric_summary"

    # value_column: first numeric column
    numeric_cols = frame.select_dtypes(include="number").columns.tolist()
    value_column = numeric_cols[0] if numeric_cols else ""

    # group_column: first non-numeric, non-date column
    all_cols = frame.columns.tolist()
    date_cols = [c for c in all_cols if "date" in c.lower()]
    non_numeric_cols = frame.select_dtypes(exclude="number").columns.tolist()
    non_date_non_numeric = [c for c in non_numeric_cols if c not in date_cols]
    group_column = non_date_non_numeric[0] if non_date_non_numeric else ""

    # date_column: column with "date" in name, else ""
    date_column = date_cols[0] if date_cols else ""

    # aggregation
    aggregation = "sum" if ("total" in q or "sum" in q) else "average"

    # chart_type
    if operation == "correlation":
        chart_type = "heatmap"
    elif operation == "outlier_detection":
        chart_type = "scatter"
    elif operation == "time_trend":
        chart_type = "line"
    elif operation == "grouped_analysis":
        if "pie" in q or "proportion" in q:
            chart_type = "pie"
        else:
            chart_type = "bar"
    else:  # numeric_summary
        chart_type = "histogram"

    return {
        "operation": operation,
        "value_column": value_column,
        "group_column": group_column,
        "date_column": date_column,
        "aggregation": aggregation,
        "chart_type": chart_type,
    }


def _plan_node(state: AnalysisState) -> dict[str, Any]:
    # Offline mode: use keyword-based planner
    if state.get("offline"):
        frame = state["dataframe"]
        plan = _offline_plan(state["question"], frame)
        return {
            "plan": plan,
            "trace": _trace(state, "Planner (offline)", f"Selected {plan['operation']} on {plan['value_column']}."),
        }

    frame = state["dataframe"]
    numeric = frame.select_dtypes(include="number").columns.tolist()
    if not numeric:
        raise ValueError("This question needs a numeric column, but the dataset has none.")
    non_numeric = frame.select_dtypes(exclude="number").columns.tolist()
    schema = {str(column): str(frame[column].dtype) for column in frame.columns}
    tool = {
        "type": "function",
        "function": {
            "name": "select_analysis",
            "description": "Choose one supported deterministic analysis for the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["numeric_summary", "grouped_analysis", "time_trend"]},
                    "value_column": {"type": "string", "enum": numeric},
                    "group_column": {"type": "string", "enum": non_numeric + [""]},
                    "date_column": {"type": "string", "enum": non_numeric + [""]},
                    "aggregation": {"type": "string", "enum": ["sum", "average"]},
                    "chart_type": {"type": "string", "enum": ["bar", "pie", "line", "histogram"]},
                },
                "required": ["operation", "value_column", "group_column", "date_column", "aggregation", "chart_type"],
            },
        },
    }
    response = state["client"].chat.completions.create(
        model=state["model"],
        temperature=0,
        tool_choice="required",
        tools=[tool],
        messages=[
            {"role": "system", "content": (
                "You are the analysis planner. Choose one supported analysis based only on the question and schema. "
                "Never invent a column. For grouping use grouped_analysis; for change over time use time_trend; "
                "for a single-column description use numeric_summary. Choose a suitable chart."
            )},
            {"role": "user", "content": json.dumps({"question": state["question"], "schema": schema})},
        ],
    )
    calls = response.choices[0].message.tool_calls or []
    if not calls or calls[0].function.name != "select_analysis":
        raise ValueError("The planner did not return a supported analysis plan.")
    plan = json.loads(calls[0].function.arguments)
    if plan.get("value_column") not in numeric:
        raise ValueError("The plan selected a column that is not numeric.")
    operation = plan.get("operation")
    if operation == "grouped_analysis" and plan.get("group_column") not in non_numeric:
        raise ValueError("The plan selected an invalid grouping column.")
    if operation == "time_trend" and plan.get("date_column") not in non_numeric:
        raise ValueError("The plan selected an invalid date column.")
    return {"plan": plan, "trace": _trace(state, "Planner", f"Selected {operation} on {plan['value_column']}.")}


def _analysis_node(state: AnalysisState) -> dict[str, Any]:
    frame, plan = state["dataframe"], state["plan"]
    value_column = plan["value_column"]
    operation = plan["operation"]
    if operation == "numeric_summary":
        values = frame[value_column].dropna()
        if values.empty:
            raise ValueError(f"Column '{value_column}' has no numeric values.")
        result = {"operation": operation, "column": value_column, "count": int(values.count()),
                  "mean": float(values.mean()), "minimum": float(values.min()), "maximum": float(values.max())}
    elif operation == "grouped_analysis":
        group_column = plan["group_column"]
        grouped = frame.groupby(group_column, dropna=False)[value_column]
        values = grouped.sum() if plan["aggregation"] == "sum" else grouped.mean()
        result = {"operation": operation, "group_column": group_column, "value_column": value_column,
                  "aggregation": plan["aggregation"], "groups": [
                      {"label": str(label), "value": float(value)} for label, value in values.items() if pd.notna(value)
                  ]}
    elif operation == "time_trend":
        date_column = plan["date_column"]
        dates = pd.to_datetime(frame[date_column], errors="coerce", format="mixed")
        trend = pd.DataFrame({"Date": dates, "Value": frame[value_column]}).dropna()
        trend = trend.groupby("Date", as_index=False)["Value"].sum().sort_values("Date")
        if trend.empty:
            raise ValueError(f"Column '{date_column}' has no usable dates paired with '{value_column}'.")
        result = {"operation": operation, "date_column": date_column, "value_column": value_column,
                  "points": int(len(trend)), "start": trend["Date"].min().isoformat(),
                  "end": trend["Date"].max().isoformat(), "total": float(trend["Value"].sum())}
    elif operation == "correlation":
        numerics = frame.select_dtypes(include="number")
        if numerics.shape[1] < 2:
            raise ValueError("Correlation needs at least two numeric columns.")
        corr = numerics.corr()
        pairs = [
            {"col_a": a, "col_b": b, "r": round(float(corr.loc[a, b]), 4)}
            for a in corr.columns for b in corr.columns if a < b
        ]
        result = {"operation": operation, "pairs": pairs, "columns": list(numerics.columns)}
    elif operation == "outlier_detection":
        values = frame[value_column].dropna()
        q1, q3 = float(values.quantile(0.25)), float(values.quantile(0.75))
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (frame[value_column] < lower) | (frame[value_column] > upper)
        outlier_count = int(mask.sum())
        result = {
            "operation": operation, "column": value_column,
            "q1": q1, "q3": q3, "iqr": round(iqr, 4),
            "lower_fence": round(lower, 4), "upper_fence": round(upper, 4),
            "outlier_count": outlier_count,
            "total_rows": int(len(frame[value_column].dropna()))
        }
    else:
        raise ValueError("Unsupported analysis operation.")
    return {"result": result,
            "trace": _trace(state, "Analyst", f"Calculated results with Python from {len(frame):,} rows.")}


def _visualizer_node(state: AnalysisState) -> dict[str, Any]:
    frame, plan, result = state["dataframe"], state["plan"], state["result"]
    operation = plan["operation"]
    value_column = plan["value_column"]
    chart_type = plan["chart_type"]
    figure = None
    if operation == "numeric_summary" and chart_type == "histogram":
        figure = px.histogram(frame, x=value_column, title=f"Distribution of {value_column}")
    elif operation == "grouped_analysis":
        values = pd.Series(
            {group["label"]: group["value"] for group in result["groups"]}, name="Value"
        )
        chart_frame = values.rename_axis(plan["group_column"]).reset_index()
        if chart_type == "pie":
            figure = px.pie(chart_frame, names=plan["group_column"], values="Value")
        else:
            figure = px.bar(chart_frame, x=plan["group_column"], y="Value")
    elif operation == "time_trend":
        dates = pd.to_datetime(frame[plan["date_column"]], errors="coerce", format="mixed")
        trend = pd.DataFrame({"Date": dates, "Value": frame[value_column]}).dropna()
        trend = trend.groupby("Date", as_index=False)["Value"].sum().sort_values("Date")
        figure = px.line(trend, x="Date", y="Value", markers=True, title=f"{value_column} over time")
    elif operation == "correlation":
        numerics = frame.select_dtypes(include="number")
        corr = numerics.corr()
        figure = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                           zmin=-1, zmax=1, title="Correlation Heatmap")
    elif operation == "outlier_detection":
        figure = px.box(frame, y=value_column, title=f"Outlier view: {value_column}")
    return {"figure": figure, "trace": _trace(state, "Visualizer", f"Selected a {chart_type} chart for {operation}.")}


def _validation_node(state: AnalysisState) -> dict[str, Any]:
    result = state["result"]
    def numeric_values(value: Any) -> list[float]:
        if isinstance(value, dict):
            return [number for nested in value.values() for number in numeric_values(nested)]
        if isinstance(value, list):
            return [number for nested in value for number in numeric_values(nested)]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return [float(value)]
        return []

    numbers = numeric_values(result)
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError("Validation found a non-finite numeric result.")
    return {"trace": _trace(state, "Validator", "Checked selected columns and confirmed finite numeric results.")}


def _report_node(state: AnalysisState) -> dict[str, Any]:
    if state.get("offline"):
        op = state["result"]["operation"]
        col = state["result"].get("column") or state["result"].get("value_column", "")
        templates = {
            "numeric_summary": f"The numeric summary shows the count, mean, minimum, and maximum values for '{col}'. These descriptive statistics help understand the central tendency and spread of the data.",
            "grouped_analysis": f"The grouped analysis aggregated '{col}' across categories. The result shows how values differ between groups, which helps identify which group contributes the most.",
            "time_trend": f"The time trend analysis shows how '{col}' changed over time. Look for patterns such as growth, seasonality, or sudden changes.",
            "correlation": "The correlation heatmap shows how strongly pairs of numeric columns are related. Values near +1 indicate a strong positive relationship, near -1 a strong negative one, and near 0 means little linear relationship.",
            "outlier_detection": f"Outlier detection used the IQR (interquartile range) method on '{col}'. Points outside 1.5×IQR from the quartiles are flagged as outliers.",
        }
        explanation = templates.get(op, "Analysis completed. See the computed result below.")
        return {"explanation": explanation, "trace": _trace(state, "Reporter (offline)", "Generated a template explanation from the computed result.")}

    response = state["client"].chat.completions.create(
        model=state["model"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": (
                "Explain the user's analysis in plain language using only the supplied computed result. "
                "Do not invent numbers, causes, or recommendations. State when the result is descriptive, not causal."
            )},
            {"role": "user", "content": json.dumps({"question": state["question"], "computed_result": state["result"]})},
        ],
    )
    explanation = response.choices[0].message.content or "The calculation completed; see the verified result below."
    return {"explanation": explanation, "trace": _trace(state, "Reporter", "Prepared an explanation grounded in the computed result.")}


def build_workflow():
    graph = StateGraph(AnalysisState)
    graph.add_node("planner", _plan_node)
    graph.add_node("analyst", _analysis_node)
    graph.add_node("validator", _validation_node)
    graph.add_node("visualizer", _visualizer_node)
    graph.add_node("reporter", _report_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "analyst")
    graph.add_edge("analyst", "validator")
    graph.add_edge("validator", "visualizer")
    graph.add_edge("visualizer", "reporter")
    graph.add_edge("reporter", END)
    return graph.compile()


def run_analysis(question: str, dataframe: pd.DataFrame, api_key: str, model: str = "openai/gpt-oss-20b") -> AnalysisState:
    if not api_key:
        raise ValueError("Set GROQ_API_KEY to enable the AI analyst.")
    client = Groq(api_key=api_key)
    workflow = build_workflow()
    return workflow.invoke({
        "question": question,
        "dataframe": dataframe,
        "client": client,
        "model": model,
        "trace": [],
    })


def run_offline_analysis(question: str, dataframe: pd.DataFrame) -> AnalysisState:
    """Run the full workflow with no API key using the keyword-based planner."""
    workflow = build_workflow()
    return workflow.invoke({
        "question": question,
        "dataframe": dataframe,
        "client": None,
        "model": "",
        "offline": True,
        "trace": [],
    })
