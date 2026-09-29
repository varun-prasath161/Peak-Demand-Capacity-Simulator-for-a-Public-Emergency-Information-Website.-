"""
Unit Tests for Advanced Sensitivity Analysis Module (Step 6)
=============================================================
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.sensitivity_analysis import (
    SENSITIVITY_PARAMETERS,
    SENSITIVITY_SCENARIOS,
    run_advanced_sensitivity_analysis,
    evaluate_decision_changing,
    compute_sensitivity_summary,
    run_full_advanced_sensitivity_pipeline,
)


class TestSensitivityParametersConfig:
    """Verify that parameter definitions adhere to Step 6 requirements."""

    def test_eight_parameters_defined(self):
        """Must test at least 8 specific parameters."""
        assert len(SENSITIVITY_PARAMETERS) >= 8
        expected_params = [
            "traffic_multiplier",
            "scaling_delay_seconds",
            "capacity_per_instance",
            "max_instances",
            "initial_instances",
            "safety_margin_pct",
            "disaster_duration_hours",
            "peak_duration_ratio",
        ]
        for p in expected_params:
            assert p in SENSITIVITY_PARAMETERS, f"Missing parameter definition for '{p}'"

    def test_parameter_variations_contain_baseline(self):
        """Every parameter's variation list must contain its baseline value."""
        for param, cfg in SENSITIVITY_PARAMETERS.items():
            baseline = cfg["baseline"]
            variations = cfg["variations"]
            assert baseline in variations, (
                f"Parameter '{param}' baseline {baseline} not in variations {variations}"
            )
            assert len(variations) >= 3, f"Parameter '{param}' should test at least 3 variations"

    def test_scenarios_coverage(self):
        """Must test at least 4 scenarios."""
        expected_scenarios = ["SEASONAL_PEAK", "DISASTER_PEAK", "EXTREME_DISASTER", "DISASTER_BREAKING_NEWS"]
        for sc in expected_scenarios:
            assert sc in SENSITIVITY_SCENARIOS, f"Missing scenario: '{sc}'"


class TestSensitivityExecution:
    """Verify sensitivity experiment execution and output integrity."""

    @pytest.fixture(scope="class")
    def sensitivity_df(self):
        """Run a minimal sensitivity execution for testing."""
        df = run_advanced_sensitivity_analysis(
            parameters=["traffic_multiplier", "scaling_delay_seconds"],
            scenarios=["SEASONAL_PEAK", "DISASTER_PEAK"],
        )
        return df

    def test_metrics_columns_present(self, sensitivity_df):
        """Ensure all required metrics columns are present in results."""
        required_cols = [
            "parameter_name",
            "parameter_value",
            "scenario",
            "strategy",
            "peak_demand",
            "peak_instances",
            "max_queue",
            "max_p95_latency",
            "max_error_rate",
            "unmet_requests",
            "sla_compliance",
            "sla_violation_duration",
            "recovery_time",
            "total_simulated_cost",
        ]
        for col in required_cols:
            assert col in sensitivity_df.columns, f"Missing metric column '{col}'"

    def test_baseline_preservation(self):
        """Testing a parameter at its baseline value must produce baseline metrics."""
        df_traffic = run_advanced_sensitivity_analysis(
            parameters=["traffic_multiplier"],
            scenarios=["SEASONAL_PEAK"],
        )
        baseline_row = df_traffic[df_traffic["parameter_value"] == 1.0].iloc[0]
        assert baseline_row["peak_demand"] > 0
        assert baseline_row["sla_compliance"] >= 99.0

    def test_repeatability(self):
        """Sensitivity runs must be deterministic."""
        df1 = run_advanced_sensitivity_analysis(
            parameters=["scaling_delay_seconds"],
            scenarios=["SEASONAL_PEAK"],
        )
        df2 = run_advanced_sensitivity_analysis(
            parameters=["scaling_delay_seconds"],
            scenarios=["SEASONAL_PEAK"],
        )
        pd.testing.assert_frame_equal(df1, df2)


class TestDecisionChangingLogic:
    """Test decision-change classification rules."""

    def test_evaluate_decision_changing_structure(self):
        """Verify output structure of evaluate_decision_changing."""
        df_res = run_advanced_sensitivity_analysis(
            parameters=["traffic_multiplier"],
            scenarios=["EXTREME_DISASTER"],
        )
        df_dec = evaluate_decision_changing(df_res)
        required_cols = [
            "parameter", "baseline_value", "tested_value", "scenario",
            "baseline_sla", "tested_sla", "baseline_queue", "tested_queue",
            "baseline_latency", "tested_latency", "baseline_unmet_requests",
            "tested_unmet_requests", "decision_changed", "reason"
        ]
        for c in required_cols:
            assert c in df_dec.columns, f"Missing column '{c}' in decision changing dataframe"

    def test_high_traffic_triggers_decision_change(self):
        """Traffic multiplier of 2.0 on EXTREME_DISASTER must trigger a decision change."""
        df_res = run_advanced_sensitivity_analysis(
            parameters=["traffic_multiplier"],
            scenarios=["EXTREME_DISASTER"],
        )
        df_dec = evaluate_decision_changing(df_res)
        row_2x = df_dec[(df_dec["tested_value"] == 2.0) & (df_dec["scenario"] == "EXTREME_DISASTER")]
        assert len(row_2x) > 0
        assert bool(row_2x.iloc[0]["decision_changed"]) is True


class TestSensitivitySummary:
    """Test min, max, baseline, range, and relative change calculations."""

    def test_summary_calculation(self):
        """Verify compute_sensitivity_summary produces correct summary statistics."""
        df_res = run_advanced_sensitivity_analysis(
            parameters=["traffic_multiplier"],
            scenarios=["SEASONAL_PEAK", "DISASTER_PEAK"],
        )
        df_summary = compute_sensitivity_summary(df_res)
        assert len(df_summary) > 0
        assert "metric" in df_summary.columns
        assert "min_value" in df_summary.columns
        assert "max_value" in df_summary.columns
        assert "range" in df_summary.columns
        assert "relative_change_pct" in df_summary.columns

        # Verify range = max - min
        for _, row in df_summary.iterrows():
            calc_range = row["max_value"] - row["min_value"]
            assert pytest.approx(row["range"], abs=1e-3) == calc_range


class TestInvalidParameterHandling:
    """Verify robust error handling for bad inputs."""

    def test_unknown_parameter_raises_value_error(self):
        """Passing an unknown parameter name should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown parameters"):
            run_advanced_sensitivity_analysis(parameters=["non_existent_param"])

    def test_unknown_scenario_raises_value_error(self):
        """Passing an unknown scenario name should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown scenarios"):
            run_advanced_sensitivity_analysis(scenarios=["NON_EXISTENT_SCENARIO"])
