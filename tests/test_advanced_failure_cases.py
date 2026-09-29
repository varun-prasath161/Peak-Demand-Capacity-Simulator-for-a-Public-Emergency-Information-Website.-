"""
Test Suite for Step 7: Advanced Failure and Edge-Case Testing
=============================================================
Verifies that the simulator:
1. Does NOT assume unlimited infrastructure (strictly respects instance caps)
2. Does NOT assume unlimited scaling speed (scaling delays cause realistic queue build-up)
3. Does NOT assume unlimited processing capacity (request throttling and queue dropping)
4. Does NOT assume perfect input data (gracefully handles corrupt/negative/missing data)
5. Does NOT assume zero recovery time (models realistic lag and backlog clearance)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.analysis.failure_case_analysis import (
    run_case_1_extreme_traffic,
    run_case_2_slow_scaling,
    run_case_3_max_instance_limit,
    run_case_4_long_duration_disaster,
    run_case_5_rapid_successive_spikes,
    run_case_6_invalid_input,
    run_case_7_recovery_failure,
    run_case_8_compound_failure,
    run_all_failure_cases,
    FAILURE_CSV,
    FAILURE_REPORT,
)


class TestFailureCases:
    """Tests for all 8 failure and edge cases."""

    def test_case_1_extreme_traffic(self):
        """Case 1: 10x traffic spike must not crash simulator and must show elevated load."""
        rec, df = run_case_1_extreme_traffic(seed=42)
        assert isinstance(rec, dict)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "Extreme Traffic Spike" in rec["failure_case"]
        assert rec["peak_demand_rpm"] > 5000.0
        assert "severity" in rec
        assert rec["peak_instances"] > 0

    def test_case_2_slow_scaling_delays(self):
        """Case 2: Longer scaling delays must result in higher queue, latency, or degradation."""
        results = run_case_2_slow_scaling(seed=42)
        assert len(results) == 3
        
        recs = [r[0] for r in results]
        recs.sort(key=lambda x: x["scaling_delay_seconds"])
        
        delays = [r["scaling_delay_seconds"] for r in recs]
        assert delays == [60, 300, 900]
        
        # 900s delay should show more latency or queue than 60s
        fast_rec = recs[0]
        slow_rec = recs[-1]
        assert slow_rec["max_queue_depth"] >= fast_rec["max_queue_depth"]
        assert slow_rec["max_p95_latency_ms"] >= fast_rec["max_p95_latency_ms"]

    def test_case_3_hard_instance_limit(self):
        """Case 3: Simulator must strictly enforce max_instances ceiling (15 instances)."""
        hard_limit = 15
        rec, df = run_case_3_max_instance_limit(seed=42, hard_limit=hard_limit)
        assert rec["hard_instance_limit"] == hard_limit
        assert df["active_instances"].max() <= hard_limit, (
            f"Active instances exceeded limit: {df['active_instances'].max()} > {hard_limit}"
        )

    def test_case_4_long_duration_disaster(self):
        """Case 4: Long disaster (72h) runs stably without data loss."""
        rec, df = run_case_4_long_duration_disaster(seed=42, duration_hours=72.0)
        assert len(df) > 0
        assert rec["simulation_duration_hours"] == 72.0
        assert rec["estimated_cost_usd"] > 0
        assert not df["active_instances"].isna().any()

    def test_case_5_rapid_successive_spikes(self):
        """Case 5: Successive spike-recovery cycles create distinct dynamic phases."""
        rec, df = run_case_5_rapid_successive_spikes(seed=42)
        assert rec["spike_cycles"] == 3
        assert len(df) > 0
        assert rec["peak_demand_rpm"] > 2000.0

    def test_case_6_invalid_input_safety(self):
        """Case 6: Corrupted/negative/missing/out-of-bounds input is safely handled without unhandled exceptions."""
        sub_results = run_case_6_invalid_input(seed=42)
        assert len(sub_results) == 4
        for sub in sub_results:
            assert sub.get("input_handled_safely") is True, f"Failed on: {sub['failure_case']}"
            assert "handling_description" in sub

    def test_case_7_recovery_failure(self):
        """Case 7: Sustained demand above capacity correctly diagnoses chronic saturation."""
        rec, df = run_case_7_recovery_failure(seed=42)
        assert len(df) > 0
        assert rec["sla_compliance_pct"] < 99.0
        assert rec["severity"] in ["SLA Violated", "SLA Degraded"]

    def test_case_8_compound_failure(self):
        """Case 8: Compound multi-factor failure demonstrates non-linear degradation."""
        rec, df = run_case_8_compound_failure(seed=42)
        assert len(df) > 0
        assert rec["hard_instance_limit"] == 15
        assert rec["scaling_delay_seconds"] == 600
        assert df["active_instances"].max() <= 15
        assert rec["sla_compliance_pct"] < 99.0

    def test_artifacts_generated(self):
        """Verify that outputs and reports exist after full execution."""
        assert FAILURE_CSV.exists(), f"Missing CSV: {FAILURE_CSV}"
        df_csv = pd.read_csv(FAILURE_CSV)
        assert len(df_csv) >= 8
        assert FAILURE_REPORT.exists(), f"Missing report: {FAILURE_REPORT}"
