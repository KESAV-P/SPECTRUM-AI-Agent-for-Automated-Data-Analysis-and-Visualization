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


def _trace(state: AnalysisState, node: str, detail: str) -> list[dict[str, str]]:
    return [*state.get("trace", []), {"step": node, "detail": detail}]


def _plan_node(state: AnalysisState) -> dict[str, Any]:
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
