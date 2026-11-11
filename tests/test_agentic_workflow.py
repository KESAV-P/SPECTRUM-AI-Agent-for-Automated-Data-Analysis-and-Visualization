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
            "dataframe": pd.DataFrame({"region": ["North", "South", "North"], "sales": [10, 5, 7]}),
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


if __name__ == "__main__":
    unittest.main()
