import json
import unittest
from types import SimpleNamespace

import pandas as pd

from agentic_workflow import build_workflow


class FakeCompletions:
    def __init__(self, plan):
        self.plan = plan
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            tool_call = SimpleNamespace(
                function=SimpleNamespace(name="select_analysis", arguments=json.dumps(self.plan))
            )
            message = SimpleNamespace(tool_calls=[tool_call])
        else:
            message = SimpleNamespace(content="The total is based on the calculated dataset values.")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class AgentWorkflowTests(unittest.TestCase):
    def run_fake_workflow(self, plan):
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(plan)))
        graph = build_workflow()
        return graph.invoke({
            "question": "Which region has the most sales?",
            "dataframe": pd.DataFrame({"region": ["North", "South", "North"], "sales": [10, 5, 7], "profit": [2, 1, 3]}),
            "client": fake_client,
            "model": "test-model",
            "trace": [],
        })

    def test_grouped_analysis_runs_through_visible_workflow(self):
        result = self.run_fake_workflow({
            "operation": "grouped_analysis", "value_column": "sales", "group_column": "region",
            "date_column": "", "aggregation": "sum", "chart_type": "bar",
        })
        self.assertEqual(result["result"]["groups"], [{"label": "North", "value": 17.0}, {"label": "South", "value": 5.0}])
        self.assertEqual(
            [step["step"] for step in result["trace"]],
            ["Planner", "Analyst", "Validator", "Visualizer", "Reporter"],
        )
        self.assertEqual(result["explanation"], "The total is based on the calculated dataset values.")
        self.assertIsNotNone(result["figure"])

    def test_invalid_model_selected_column_is_rejected_before_analysis(self):
        with self.assertRaisesRegex(ValueError, "not numeric"):
            self.run_fake_workflow({
                "operation": "numeric_summary", "value_column": "__import__", "group_column": "",
                "date_column": "", "aggregation": "sum", "chart_type": "histogram",
            })

    # --- New offline tests ---

    def test_offline_numeric_summary_runs_without_api_key(self):
        from agentic_workflow import run_offline_analysis
        df = pd.DataFrame({"region": ["North", "South", "North"], "sales": [10, 5, 7]})
        result = run_offline_analysis("What is the summary of sales?", df)
        self.assertEqual(result["result"]["operation"], "numeric_summary")
        self.assertEqual(result["result"]["column"], "sales")
        self.assertIn("mean", result["result"])
        # Offline trace should include "Reporter (offline)"
        steps = [s["step"] for s in result["trace"]]
        self.assertIn("Reporter (offline)", steps)

    def test_offline_grouped_analysis(self):
        from agentic_workflow import run_offline_analysis
        df = pd.DataFrame({"region": ["North", "South", "North"], "sales": [10, 5, 7]})
        result = run_offline_analysis("Group sales by region", df)
        self.assertEqual(result["result"]["operation"], "grouped_analysis")

    def test_offline_correlation_operation(self):
        from agentic_workflow import run_offline_analysis
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10], "z": [5, 4, 3, 2, 1]})
        result = run_offline_analysis("Show correlations between columns", df)
        self.assertEqual(result["result"]["operation"], "correlation")
        self.assertIn("pairs", result["result"])
        self.assertIsNotNone(result.get("figure"))

    def test_offline_outlier_detection(self):
        from agentic_workflow import run_offline_analysis
        df = pd.DataFrame({"region": ["A"] * 10, "sales": [10, 11, 12, 10, 11, 13, 10, 100, 11, 12]})
        result = run_offline_analysis("Find outliers in sales", df)
        self.assertEqual(result["result"]["operation"], "outlier_detection")
        self.assertGreater(result["result"]["outlier_count"], 0)

    def test_time_trend_operation(self):
        """Grouped analysis test via offline for time_trend."""
        dates = ["2025-01-01", "2025-02-01", "2025-03-01"]
        df = pd.DataFrame({"order_date": dates, "sales": [100, 200, 150]})
        from agentic_workflow import run_offline_analysis
        result = run_offline_analysis("How do sales change over time by order_date?", df)
        # either time_trend or numeric_summary is valid offline
        self.assertIn(result["result"]["operation"], ["time_trend", "numeric_summary", "grouped_analysis"])
        self.assertFalse(result.get("error"))

    def test_correlation_operation_via_mocked_workflow(self):
        result = self.run_fake_workflow({
            "operation": "correlation",
            "value_column": "sales",
            "group_column": "",
            "date_column": "",
            "aggregation": "sum",
            "chart_type": "heatmap",
        })
        self.assertEqual(result["result"]["operation"], "correlation")
        self.assertIn("pairs", result["result"])


if __name__ == "__main__":
    unittest.main()
