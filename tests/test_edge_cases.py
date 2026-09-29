"""
Unit tests for Edge Case & Failure Mode Analysis
=================================================
"""

import pytest
import pandas as pd
from pathlib import Path
from src.simulation.edge_cases import run_single_edge_case, run_all_edge_cases, EDGE_CASES


class TestEdgeCases:
    """Automated tests for 5 edge and failure cases."""

    def test_five_edge_cases_defined(self):
        assert len(EDGE_CASES) == 5
        ids = [c["id"] for c in EDGE_CASES]
        assert ids == ["CASE_1", "CASE_2", "CASE_3", "CASE_4", "CASE_5"]

    def test_extreme_traffic_spike_case_1(self):
        res = run_single_edge_case(EDGE_CASES[0])
        assert res["case_id"] == "CASE_1"
        assert res["peak_demand_rpm"] > 8000
        assert res["sla_compliant"] is False


    def test_scaling_delay_disaster_case_2(self):
        res = run_single_edge_case(EDGE_CASES[1])
        assert res["case_id"] == "CASE_2"
        assert res["max_p95_latency_ms"] > 300
        assert len(res["failure_explanation"]) > 0

    def test_max_instance_limit_case_3(self):
        res = run_single_edge_case(EDGE_CASES[2])
        assert res["case_id"] == "CASE_3"
        assert res["peak_capacity_rpm"] == 2500.0  # 5 * 500
        assert res["sla_compliant"] is False

    def test_queue_overflow_case_4(self):
        res = run_single_edge_case(EDGE_CASES[3])
        assert res["case_id"] == "CASE_4"
        assert res["max_queue_depth"] > 0
        assert "dropped" in res["system_response"].lower() or "http 503" in res["system_response"].lower()

    def test_corrupted_input_data_case_5(self):
        res = run_single_edge_case(EDGE_CASES[4])
        assert res["case_id"] == "CASE_5"
        assert res["sla_compliant"] is True
        assert "handled corruption gracefully" in res["system_response"].lower()

    def test_full_edge_case_pipeline(self, tmp_path):
        out_dir = tmp_path / "outputs"
        doc_dir = tmp_path / "docs"
        df = run_all_edge_cases(output_dir=str(out_dir), docs_dir=str(doc_dir))

        assert len(df) == 5
        assert (out_dir / "edge_case_results.csv").exists()
        assert (doc_dir / "failure_cases.md").exists()
