"""
Unit Tests for Multi-Scenario Evaluation & Stakeholder Reporting
================================================================
Tests src.simulation.run_scenarios module:
- 5-scenario evaluation pipeline
- Generation of outputs/scenario_comparison.csv
- Generation of outputs/scenario_report.txt answering Q1-Q5
- SLA violation detection for Extreme Disaster scenario
"""

import unittest
import pandas as pd
from pathlib import Path

from src.simulation.run_scenarios import run_and_export_scenarios, CSV_PATH, REPORT_PATH


class TestRunScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run multi-scenario evaluation pipeline once for testing."""
        cls.df_comp, cls.report_text = run_and_export_scenarios(seed=42)

    def test_csv_file_creation_and_structure(self):
        """Verify scenario_comparison.csv exists and has 5 scenario records."""
        self.assertTrue(CSV_PATH.exists(), f"Missing CSV comparison file at {CSV_PATH}")
        df = pd.read_csv(CSV_PATH)
        self.assertEqual(len(df), 5, f"Expected 5 scenario records in CSV, got {len(df)}")

        required_cols = [
            "scenario_name", "peak_demand_rpm", "average_demand_rpm",
            "initial_capacity_rpm", "maximum_capacity_rpm", "peak_utilisation_pct",
            "maximum_queue_depth", "maximum_p95_latency_ms", "maximum_error_rate_pct",
            "peak_instances", "scaling_actions", "unmet_requests",
            "sla_compliance", "sla_compliance_percentage"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column {col} in CSV")

    def test_report_file_creation_and_questions(self):
        """Verify scenario_report.txt exists and answers Q1 to Q5."""
        self.assertTrue(REPORT_PATH.exists(), f"Missing report file at {REPORT_PATH}")
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Q1: WHICH SCENARIO IS SAFEST?", content)
        self.assertIn("Q2: WHICH SCENARIO IS MOST DIFFICULT?", content)
        self.assertIn("Q3: WHERE DOES THE BASELINE FAIL?", content)
        self.assertIn("Q4: WHICH CAPACITY RECOMMENDATION IS MADE?", content)
        self.assertIn("Q5: WHY IS THIS RECOMMENDATION REASONABLE?", content)

    def test_extreme_disaster_sla_violation(self):
        """Verify Extreme Disaster scenario reports VIOLATED SLA status explicitly."""
        df = pd.read_csv(CSV_PATH)
        extreme_row = df[df["scenario_name"] == "Extreme Disaster"].iloc[0]

        self.assertEqual(extreme_row["sla_compliance"], "VIOLATED")
        self.assertGreater(extreme_row["maximum_p95_latency_ms"], 500.0)

    def test_safest_scenario_compliance(self):
        """Verify Normal Day scenario reports COMPLIANT SLA status with 100% compliance."""
        df = pd.read_csv(CSV_PATH)
        normal_row = df[df["scenario_name"] == "Normal Day"].iloc[0]

        self.assertEqual(normal_row["sla_compliance"], "COMPLIANT")
        self.assertEqual(normal_row["sla_compliance_percentage"], 100.0)


if __name__ == "__main__":
    unittest.main()
