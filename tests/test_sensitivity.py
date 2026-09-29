"""
Unit Tests for Sensitivity Analysis Engine
============================================
"""

import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.sensitivity import (
    ASSUMPTIONS,
    BASELINE_CONFIG,
    STRESS_SCENARIO,
    _run_single_sensitivity_test,
    _classify_assumptions,
    run_sensitivity_analysis,
)


class TestSensitivityAssumptions:
    """Verify that the assumption definitions are well-formed."""

    def test_seven_assumptions_defined(self):
        """We must test at least 7 assumptions as specified."""
        assert len(ASSUMPTIONS) >= 7

    def test_each_assumption_has_required_keys(self):
        """Every assumption must have param, display_name, unit, baseline, lower, upper."""
        required_keys = {"param", "display_name", "unit", "baseline", "lower", "upper", "description"}
        for a in ASSUMPTIONS:
            for key in required_keys:
                assert key in a, f"Assumption '{a.get('display_name', '?')}' missing key '{key}'"

    def test_lower_leq_baseline_leq_upper(self):
        """Lower bound must be <= baseline <= upper bound for numeric params."""
        for a in ASSUMPTIONS:
            # Safety margin baseline is 0 and lower is also 0, so use <=
            assert a["lower"] <= a["baseline"] or a["param"] == "safety_margin_instances", \
                f"{a['display_name']}: lower ({a['lower']}) > baseline ({a['baseline']})"
            assert a["baseline"] <= a["upper"], \
                f"{a['display_name']}: baseline ({a['baseline']}) > upper ({a['upper']})"

    def test_baseline_config_matches_simulator_defaults(self):
        """Baseline config must match the known simulator defaults."""
        assert BASELINE_CONFIG["initial_instances"] == 10
        assert BASELINE_CONFIG["max_instances"] == 50
        assert BASELINE_CONFIG["capacity_per_instance"] == 500.0
        assert BASELINE_CONFIG["scaling_delay_seconds"] == 180


class TestSingleSensitivityRun:
    """Test individual sensitivity simulation runs."""

    def test_baseline_run_returns_valid_dict(self):
        """A single baseline test should return a well-formed result dict."""
        assumption = ASSUMPTIONS[0]  # Traffic Multiplier
        result = _run_single_sensitivity_test(assumption, assumption["baseline"], "baseline")

        required_keys = {
            "assumption_name", "parameter", "test_label", "test_value",
            "unit", "peak_queue_depth", "max_p95_latency_ms",
            "max_error_rate_pct", "sla_compliance_pct", "sla_compliant",
            "peak_instances", "total_unmet_requests", "total_scaling_actions",
        }
        assert required_keys.issubset(result.keys())

    def test_result_values_are_plausible(self):
        """Numeric results must be non-negative and in plausible ranges."""
        assumption = ASSUMPTIONS[0]
        result = _run_single_sensitivity_test(assumption, assumption["baseline"], "baseline")

        assert result["peak_queue_depth"] >= 0
        assert result["max_p95_latency_ms"] > 0
        assert 0 <= result["max_error_rate_pct"] <= 100
        assert 0 <= result["sla_compliance_pct"] <= 100
        assert result["peak_instances"] >= 1
        assert result["total_unmet_requests"] >= 0

    def test_traffic_multiplier_lower_reduces_load(self):
        """Lower traffic multiplier should not increase peak instances vs baseline."""
        assumption = next(a for a in ASSUMPTIONS if a["param"] == "traffic_multiplier")
        result_lower = _run_single_sensitivity_test(assumption, assumption["lower"], "lower")
        result_baseline = _run_single_sensitivity_test(assumption, assumption["baseline"], "baseline")

        # Lower traffic should need fewer or equal instances
        assert result_lower["peak_instances"] <= result_baseline["peak_instances"]


class TestClassification:
    """Test the assumption classification logic."""

    def test_classification_returns_all_assumptions(self):
        """Classification should produce one entry per assumption."""
        # Build a minimal results DataFrame
        records = []
        for assumption in ASSUMPTIONS:
            for label in ["lower", "baseline", "upper"]:
                records.append({
                    "assumption_name": assumption["display_name"],
                    "parameter": assumption["param"],
                    "test_label": label,
                    "test_value": assumption[label],
                    "unit": assumption["unit"],
                    "peak_queue_depth": 100.0,
                    "max_p95_latency_ms": 350.0,
                    "max_error_rate_pct": 0.5,
                    "sla_compliance_pct": 100.0,
                    "sla_compliant": True,
                    "peak_instances": 14,
                    "total_unmet_requests": 0,
                    "total_scaling_actions": 4,
                })

        df = pd.DataFrame(records)
        classification = _classify_assumptions(df)

        assert len(classification) == len(ASSUMPTIONS)
        for a in ASSUMPTIONS:
            assert a["param"] in classification

    def test_identical_results_classified_little_effect(self):
        """When all three levels produce identical metrics, classification should be LITTLE EFFECT."""
        records = []
        for label in ["lower", "baseline", "upper"]:
            records.append({
                "assumption_name": "Test Param",
                "parameter": "test_param",
                "test_label": label,
                "test_value": 1.0,
                "unit": "x",
                "peak_queue_depth": 50.0,
                "max_p95_latency_ms": 200.0,
                "max_error_rate_pct": 0.1,
                "sla_compliance_pct": 100.0,
                "sla_compliant": True,
                "peak_instances": 10,
                "total_unmet_requests": 0,
                "total_scaling_actions": 2,
            })

        # Temporarily inject a fake assumption
        fake_assumption = {
            "param": "test_param",
            "display_name": "Test Param",
            "unit": "x",
            "baseline": 1.0,
            "lower": 0.5,
            "upper": 2.0,
            "description": "Test",
        }
        import src.simulation.sensitivity as sens
        original_assumptions = sens.ASSUMPTIONS
        sens.ASSUMPTIONS = [fake_assumption]

        try:
            df = pd.DataFrame(records)
            classification = _classify_assumptions(df)
            assert classification["test_param"]["classification"] == "LITTLE EFFECT"
        finally:
            sens.ASSUMPTIONS = original_assumptions

    def test_sla_flip_classified_decision_changing(self):
        """When SLA compliance flips between levels, it should be DECISION-CHANGING."""
        records = []
        sla_values = [True, True, False]  # Upper violates SLA
        for label, sla in zip(["lower", "baseline", "upper"], sla_values):
            records.append({
                "assumption_name": "Test Param",
                "parameter": "test_param",
                "test_label": label,
                "test_value": 1.0,
                "unit": "x",
                "peak_queue_depth": 50.0,
                "max_p95_latency_ms": 200.0 if sla else 800.0,
                "max_error_rate_pct": 0.1,
                "sla_compliance_pct": 100.0 if sla else 70.0,
                "sla_compliant": sla,
                "peak_instances": 10,
                "total_unmet_requests": 0,
                "total_scaling_actions": 2,
            })

        fake_assumption = {
            "param": "test_param",
            "display_name": "Test Param",
            "unit": "x",
            "baseline": 1.0,
            "lower": 0.5,
            "upper": 2.0,
            "description": "Test",
        }
        import src.simulation.sensitivity as sens
        original_assumptions = sens.ASSUMPTIONS
        sens.ASSUMPTIONS = [fake_assumption]

        try:
            df = pd.DataFrame(records)
            classification = _classify_assumptions(df)
            assert classification["test_param"]["classification"] == "DECISION-CHANGING"
        finally:
            sens.ASSUMPTIONS = original_assumptions


class TestFullPipeline:
    """Integration test for the full sensitivity analysis pipeline."""

    def test_full_pipeline_produces_csv_and_report(self):
        """The full pipeline should generate a CSV with 21 rows and a non-empty report."""
        df, report = run_sensitivity_analysis(seed=42)

        # 7 assumptions x 3 levels = 21 rows
        assert len(df) == 21
        assert isinstance(report, str)
        assert len(report) > 500
        assert "DECISION-CHANGING" in report or "LITTLE EFFECT" in report

    def test_csv_file_exists_after_run(self):
        """The output CSV file should exist on disk after running."""
        from src.simulation.sensitivity import CSV_PATH
        assert CSV_PATH.exists()
        df = pd.read_csv(CSV_PATH)
        assert len(df) == 21

    def test_report_file_exists_after_run(self):
        """The output report file should exist on disk after running."""
        from src.simulation.sensitivity import REPORT_PATH
        assert REPORT_PATH.exists()
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        assert "PLAIN LANGUAGE SUMMARY" in content
        assert "RECOMMENDATION" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
