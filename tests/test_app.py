import io
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
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
        self.assertEqual(app.dataframe[3].value.loc["Count", "Value"], 12)
        self.assertEqual(app.dataframe[3].value.loc["Minimum", "Value"], 4)
        self.assertEqual(app.dataframe[3].value.loc["Maximum", "Value"], 12)
        date_picker = next(item for item in app.selectbox if item.label == "Date column")
        self.assertIn("order_date", date_picker.options)

    def test_grouped_sales_totals_are_correct(self):
        app = run_with_upload("sample_sales.csv", SAMPLE.read_bytes())
        next(item for item in app.selectbox if item.label == "Group by").set_value("region").run()
        next(item for item in app.selectbox if item.label == "Numeric value").set_value("sales").run()

        self.assertFalse(app.exception)
        grouped = app.dataframe[4].value["Result"].to_dict()
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

    def test_invalid_empty_and_unsupported_data_show_messages(self):
        for filename, content in [("empty.csv", b""), ("broken.xlsx", b"not an Excel workbook")]:
            with self.subTest(filename=filename):
                app = run_with_upload(filename, content)
                self.assertFalse(app.exception)
                self.assertTrue(app.error)

        app = run_with_upload("text.csv", b"name,city\nA,Delhi\nB,Mumbai\n")
        self.assertFalse(app.exception)
        self.assertTrue(any("no numeric" in item.value.lower() for item in app.info))
        self.assertTrue(any("needed for a trend chart" in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
