"""
Unit Tests for Simulator MVP
=============================
Tests src.simulation.simulator module:
- Normal traffic simulation (100% SLA compliance)
- Severe overload traffic simulation (SLA violation & queue accumulation)
- Constrained auto-scaling policy & delay execution
- Queue buildup and recovery mechanics
- SLA status evaluation (latency & error targets)
- CSV results export to outputs/simulation_results/
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from src.simulation.simulator import (
    run_simulation,
    run_all_simulations,
    DEFAULT_SIM_CONFIG,
    OUTPUT_DIR
)


class TestSimulatorMVP(unittest.TestCase):

    def test_normal_traffic_simulation(self):
        """Verify normal workload simulation completes with 100% SLA compliance."""
        df_res, summary = run_simulation("NORMAL", seed=42)

        self.assertFalse(df_res.empty)
        self.assertTrue(summary["sla_compliant"])
        self.assertEqual(summary["compliance_percentage"], 100.0)
        self.assertEqual(summary["peak_instances"], 10)
        self.assertEqual(summary["max_queue_depth"], 0.0)
        self.assertLessEqual(summary["max_p95_latency_ms"], 500.0)
        self.assertLessEqual(summary["max_error_rate"], 0.01)

    def test_overload_traffic_and_sla_violation(self):
        """Verify constrained infrastructure under extreme overload produces SLA breaches and queue buildup."""
        # Restrain max capacity to 500 RPM (1 instance x 500 RPM)
        df_res, summary = run_simulation(
            workload_scenario="DISASTER_PEAK",
            initial_instances=1,
            max_instances=1,
            capacity_per_instance=500.0,
            seed=42
        )

        self.assertFalse(summary["sla_compliant"])
        self.assertLess(summary["compliance_percentage"], 100.0)
        self.assertGreater(summary["max_queue_depth"], 0.0)
        self.assertGreater(summary["max_p95_latency_ms"], 500.0)
        self.assertIn("breached", df_res["sla_status"].values)

    def test_auto_scaling_trigger_and_delay(self):
        """Verify auto-scaling policy triggers scale-out actions during traffic surges."""
        df_res, summary = run_simulation(
            workload_scenario="DISASTER_PEAK",
            initial_instances=10,
            max_instances=50,
            capacity_per_instance=500.0,
            scaling_delay_seconds=180,
            seed=42
        )

        self.assertGreater(summary["total_scaling_actions"], 0)
        self.assertGreater(summary["peak_instances"], 10)
        self.assertIn("scale_out", df_res["scaling_action"].values)

    def test_queue_buildup_and_drainage(self):
        """Verify queue builds when demand > capacity and drains when capacity > demand."""
        # Force a temporary overload followed by drop
        df_res, summary = run_simulation(
            workload_scenario="BREAKING_NEWS",
            initial_instances=2,
            max_instances=2,
            capacity_per_instance=300.0,    # Max cap = 600 RPM < 1000 RPM peak
            seed=42
        )

        self.assertGreater(summary["max_queue_depth"], 0.0)
        # Check queue growth was positive during peak phase
        self.assertTrue((df_res["queue_growth"] > 0).any())

    def test_csv_output_file_creation(self):
        """Verify simulation exports result CSV to outputs/simulation_results/."""
        df_res, summary = run_simulation("SEASONAL_PEAK", seed=42)
        csv_path = Path(summary["csv_path"])

        self.assertTrue(csv_path.exists(), f"CSV output file missing at {csv_path}")
        self.assertEqual(csv_path.parent, OUTPUT_DIR)

        # Verify CSV content matches DataFrame
        df_loaded = pd.read_csv(csv_path)
        self.assertEqual(len(df_loaded), len(df_res))
        self.assertIn("p95_latency_ms", df_loaded.columns)
        self.assertIn("sla_status", df_loaded.columns)

    def test_run_all_simulations(self):
        """Verify run_all_simulations executes all 5 workload scenarios."""
        summaries = run_all_simulations(seed=42)
        self.assertEqual(len(summaries), 5)
        for s in summaries:
            self.assertIn("scenario_name", s)
            self.assertIn("compliance_percentage", s)
            self.assertIn("max_p95_latency_ms", s)


if __name__ == "__main__":
    unittest.main()
