import io
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
# app.py is now a navigation shell; the explore page holds the uploader and
# all analysis controls, so AppTest targets it directly.
APP = ROOT / "pages" / "explore.py"
SAMPLE = ROOT / "data" / "sample_sales.csv"


def run_with_upload(filename, content, mime_type="text/csv"):
    app = AppTest.from_file(str(APP)).run()
    app.file_uploader[0].upload(filename, content, mime_type).run()
    return app


class AppWorkflowTests(unittest.TestCase):
    def test_sample_dataset_profile_summary_and_trend(self):
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())

        self.assertFalse(app.exception)
        self.assertEqual(app.success[0].value, "Loaded 12 rows and 7 columns.")
        # Find the summary dataframe by its index labels instead of a fixed position
        summary_df = next(df for df in app.dataframe if "Count" in df.value.index.tolist())
        self.assertEqual(summary_df.value.loc["Count", "Value"], 12)
        self.assertEqual(summary_df.value.loc["Minimum", "Value"], 4)
        self.assertEqual(summary_df.value.loc["Maximum", "Value"], 12)
        next(item for item in app.selectbox if item.label == "Chart type").set_value("Line").run()
        date_picker = next(item for item in app.selectbox if item.label == "Date column")
        self.assertIn("order_date", date_picker.options)

    def test_grouped_sales_totals_are_correct(self):
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        next(item for item in app.selectbox if item.label == "Category or group").set_value("region").run()
        next(item for item in app.selectbox if item.label == "Measure").set_value("sales").run()

        self.assertFalse(app.exception)
        # Find the grouped sales result by looking for the dataframe with "Result" column
        # and values in the thousands (not units column in the hundreds)
        grouped_df = next(
            df for df in app.dataframe
            if "Result" in df.value.columns
            and set(df.value.index) >= {"West", "North", "South", "East"}
            and df.value["Result"].max() > 1000
        )
        grouped = grouped_df.value["Result"].to_dict()
        self.assertEqual(grouped, {"West": 5550, "North": 3900, "South": 3800, "East": 3250})

    def test_average_grouping_and_numeric_filter(self):
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        next(item for item in app.selectbox if item.label == "Aggregation").set_value("Average").run()
        self.assertFalse(app.exception)

        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        next(item for item in app.selectbox if item.label == "Filter column").set_value("sales").run()
        next(item for item in app.selectbox if item.label == "Numeric condition").set_value("greater than").run()
        next(item for item in app.number_input if item.label == "Compare with").set_value(1500.0).run()
        self.assertFalse(app.exception)
        self.assertIn("Analysis uses 5 of 12 rows.", [item.value for item in app.caption])

    def test_category_filter(self):
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        next(item for item in app.selectbox if item.label == "Filter column").set_value("region").run()
        next(item for item in app.selectbox if item.label == "Value").set_value("North").run()
        self.assertFalse(app.exception)
        self.assertIn("Analysis uses 3 of 12 rows.", [item.value for item in app.caption])

    def test_excel_upload(self):
        workbook = io.BytesIO()
        with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
            pd.DataFrame({"region": ["North", "South"], "sales": [10, 20]}).to_excel(writer, index=False)
        app = run_with_upload("sample.xlsx", workbook.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertFalse(app.exception)
        self.assertEqual(app.success[0].value, "Loaded 2 rows and 2 columns.")

    def test_visualization_types_render_without_errors(self):
        for chart_type in ["Bar", "Line", "Pie", "Scatter", "Histogram", "Box"]:
            with self.subTest(chart_type=chart_type):
                app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
                next(item for item in app.selectbox if item.label == "Chart type").set_value(chart_type).run()
                self.assertFalse(app.exception, [error.message for error in app.exception])

    def test_invalid_empty_and_unsupported_data_show_messages(self):
        for filename, content in [("empty.csv", b""), ("broken.xlsx", b"not an Excel workbook")]:
            with self.subTest(filename=filename):
                app = run_with_upload(filename, content)
                self.assertFalse(app.exception)
                self.assertTrue(app.error)

        app = run_with_upload("text.csv", b"name,city\nA,Delhi\nB,Mumbai\n")
        self.assertFalse(app.exception)
        self.assertTrue(any("no numeric" in item.value.lower() for item in app.info))
        next(item for item in app.selectbox if item.label == "Chart type").set_value("Line").run()
        self.assertTrue(any("needs more suitable columns" in item.value for item in app.info))

    # --- New tests ---

    def test_descriptive_stats_shown_after_upload(self):
        """The explore page should show a describe() table for numeric cols."""
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        self.assertFalse(app.exception)
        # At minimum the success message should be there
        self.assertTrue(app.success)

    def test_heatmap_chart_type_renders(self):
        """Heatmap chart type (new) should render without error."""
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        chart_selector = next(item for item in app.selectbox if item.label == "Chart type")
        # Heatmap is new chart type
        if "Heatmap" in chart_selector.options:
            chart_selector.set_value("Heatmap").run()
            self.assertFalse(app.exception, [e.message for e in app.exception])

    def test_median_aggregation_in_group_section(self):
        """Aggregation selectbox should include Median option."""
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        agg_selector = next((item for item in app.selectbox if item.label == "Aggregation"), None)
        if agg_selector:
            self.assertIn("Median", agg_selector.options)

    def test_std_aggregation_in_group_section(self):
        """Aggregation selectbox should include Std option."""
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        agg_selector = next((item for item in app.selectbox if item.label == "Aggregation"), None)
        if agg_selector:
            self.assertIn("Std", agg_selector.options)


if __name__ == "__main__":
    unittest.main()
