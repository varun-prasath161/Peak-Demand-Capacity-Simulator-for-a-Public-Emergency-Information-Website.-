"""
Unit Tests for Baseline Capacity Model
======================================
Tests src.capacity.baseline module:
- Infrastructure constraint modeling (current/max instances, capacity per instance)
- Capacity gap, required instances, and shortfall math calculations
- Safety margin buffer calculations
- Scenario comparison demonstrating capacity failure under peak surge
- Report generation at outputs/baseline_capacity_report.txt
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from src.capacity.baseline import (
    evaluate_capacity_for_demand,
    evaluate_baseline_capacity,
    generate_baseline_report,
    DEFAULT_CONFIG,
    REPORT_PATH
)


class TestBaselineCapacityModel(unittest.TestCase):

    def test_evaluate_capacity_within_bounds(self):
        """Verify evaluation when demand is well within current fleet capacity."""
        custom_config = {
            "current_instances": 10,
            "max_instances": 50,
            "instance_capacity_rpm": 500.0,
            "safety_margin_pct": 20.0,
        }

        # 1000 RPM demand -> Current capacity 5000 RPM
        result = evaluate_capacity_for_demand(1000.0, "Test Demand", custom_config)

        self.assertEqual(result["demand_rpm"], 1000.0)
        self.assertEqual(result["buffered_demand_rpm"], 1200.0)
        self.assertEqual(result["current_capacity_rpm"], 5000.0)
        self.assertEqual(result["max_sustainable_capacity_rpm"], 25000.0)
        self.assertEqual(result["capacity_gap_rpm"], 0.0)
        self.assertEqual(result["required_instances"], 3)             # ceil(1200 / 500) = 3
        self.assertEqual(result["instance_shortfall"], 0)
        self.assertTrue(result["is_within_current_capacity"])
        self.assertTrue(result["is_within_max_capacity"])
        self.assertEqual(result["status"], "SUFFICIENT")

    def test_evaluate_capacity_overload_shortfall(self):
        """Verify evaluation under extreme overload exceeding max sustainable capacity."""
        custom_config = {
            "current_instances": 10,
            "max_instances": 50,
            "instance_capacity_rpm": 500.0,
            "safety_margin_pct": 20.0,
        }

        # 30,000 RPM demand -> Max sustainable capacity 25,000 RPM
        result = evaluate_capacity_for_demand(30000.0, "Overload Surge", custom_config)

        self.assertEqual(result["demand_rpm"], 30000.0)
        self.assertEqual(result["buffered_demand_rpm"], 36000.0)       # 30000 * 1.20 = 36000
        self.assertEqual(result["capacity_gap_rpm"], 25000.0)          # 30000 - 5000 = 25000
        self.assertEqual(result["required_instances"], 72)             # ceil(36000 / 500) = 72
        self.assertEqual(result["instance_shortfall"], 22)             # 72 - 50 = 22
        self.assertEqual(result["capacity_shortfall_rpm"], 11000.0)    # 36000 - 25000 = 11000
        self.assertFalse(result["is_within_current_capacity"])
        self.assertFalse(result["is_within_max_capacity"])
        self.assertEqual(result["status"], "CAPACITY_SHORTFALL")

    def test_evaluate_baseline_capacity_full(self):
        """Verify full baseline evaluation across historical dataset & 5 scenarios."""
        evals = evaluate_baseline_capacity(seed=42)

        self.assertIn("average_demand_eval", evals)
        self.assertIn("historical_peak_eval", evals)
        self.assertIn("scenarios_eval", evals)

        sc_evals = evals["scenarios_eval"]
        self.assertEqual(len(sc_evals), 5)
        self.assertIn("NORMAL", sc_evals)
        self.assertIn("EXTREME_DISASTER", sc_evals)

        # Verify EXTREME_DISASTER demands significantly more instances than NORMAL
        self.assertGreater(
            sc_evals["EXTREME_DISASTER"]["required_instances"],
            sc_evals["NORMAL"]["required_instances"]
        )

    def test_generate_baseline_report(self):
        """Verify report generation writes non-empty text file containing executive summary."""
        evals = evaluate_baseline_capacity(seed=42)
        report_text = generate_baseline_report(evals, REPORT_PATH)

        self.assertTrue(REPORT_PATH.exists())
        self.assertIn("INFRASTRUCTURE CONSTRAINTS SUMMARY", report_text)
        self.assertIn("NON-TECHNICAL STAKEHOLDER EXECUTIVE SUMMARY", report_text)
        self.assertIn("FALSE SENSE OF SECURITY", report_text)


if __name__ == "__main__":
    unittest.main()
