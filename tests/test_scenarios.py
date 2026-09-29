"""
Unit Tests for Workload Scenario Engine
========================================
Tests src.simulation.scenarios module:
- Config loading from data/scenarios/scenario_config.json
- Generation of 5 standard workload scenarios
- Non-uniform 3-phase demand curve shape (ramp_up, peak, recovery)
- Seed determinism for 100% reproducible generation
- Peak demand, duration, and multiplier calculation functions
- Monotonic scenario surge ordering (Normal < Seasonal < Breaking < Disaster < Extreme)
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from src.simulation.scenarios import (
    generate_scenario,
    calculate_peak_demand,
    calculate_scenario_duration,
    calculate_traffic_multiplier,
    get_scenario_summary,
    compare_all_scenarios,
    load_scenario_config
)


class TestWorkloadScenarios(unittest.TestCase):

    def test_config_loading(self):
        """Verify scenario configuration JSON loads correctly."""
        config = load_scenario_config()
        self.assertIn("scenarios", config)
        self.assertIn("assumptions", config)
        self.assertIn("NORMAL", config["scenarios"])
        self.assertIn("EXTREME_DISASTER", config["scenarios"])

    def test_all_five_scenarios_generation(self):
        """Verify all 5 standard scenarios can be generated with required columns."""
        scenario_names = ["NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"]
        required_cols = [
            "timestamp", "scenario_name", "event_type", "event_severity", "phase",
            "requests_per_minute", "concurrent_users", "traffic_multiplier",
            "scaling_delay_seconds", "expected_queue_growth_rpm"
        ]

        for name in scenario_names:
            df = generate_scenario(name, seed=42)
            self.assertFalse(df.empty, f"Scenario {name} returned empty DataFrame")
            for col in required_cols:
                self.assertIn(col, df.columns, f"Missing column {col} in scenario {name}")

    def test_three_phase_demand_curve(self):
        """Verify demand curves include ramp_up, peak, and recovery phases."""
        df = generate_scenario("DISASTER_PEAK", seed=42)
        phases = set(df["phase"].unique())
        self.assertEqual(phases, {"ramp_up", "peak", "recovery"})

    def test_seed_determinism(self):
        """Verify generator produces 100% identical outputs given the same seed."""
        df1 = generate_scenario("BREAKING_NEWS", seed=123)
        df2 = generate_scenario("BREAKING_NEWS", seed=123)
        pd.testing.assert_frame_equal(df1, df2)

        # Different seeds should produce slightly different jitter/noise
        df3 = generate_scenario("BREAKING_NEWS", seed=999)
        self.assertFalse(df1["requests_per_minute"].equals(df3["requests_per_minute"]))

    def test_calculation_functions(self):
        """Verify helper calculation functions return valid floats."""
        df = generate_scenario("SEASONAL_PEAK", seed=42)
        peak_rpm = calculate_peak_demand(df)
        dur_h = calculate_scenario_duration(df)
        multiplier = calculate_traffic_multiplier(df)

        self.assertGreater(peak_rpm, 0)
        self.assertEqual(dur_h, 48.0)
        self.assertGreater(multiplier, 1.0)

    def test_scenario_surge_hierarchy(self):
        """Verify peak demand increases monotonically across scenario tiers."""
        scenarios = ["NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"]
        peaks = []
        multipliers = []

        for name in scenarios:
            df = generate_scenario(name, seed=42)
            peaks.append(calculate_peak_demand(df))
            multipliers.append(calculate_traffic_multiplier(df))

        # Check monotonic increase in peak demand
        for i in range(len(peaks) - 1):
            self.assertLess(
                peaks[i], peaks[i + 1],
                f"Peak RPM for {scenarios[i]} ({peaks[i]}) is not less than {scenarios[i+1]} ({peaks[i+1]})"
            )
            self.assertLess(
                multipliers[i], multipliers[i + 1],
                f"Multiplier for {scenarios[i]} ({multipliers[i]}) is not less than {scenarios[i+1]} ({multipliers[i+1]})"
            )

    def test_compare_all_scenarios(self):
        """Verify compare_all_scenarios returns 5 summary dictionaries."""
        summaries = compare_all_scenarios(seed=42)
        self.assertEqual(len(summaries), 5)
        for s in summaries:
            self.assertIn("scenario_name", s)
            self.assertIn("peak_requests_per_minute", s)
            self.assertIn("duration_hours", s)
            self.assertIn("traffic_multiplier", s)
            self.assertIn("estimated_peak_concurrency", s)


if __name__ == "__main__":
    unittest.main()
