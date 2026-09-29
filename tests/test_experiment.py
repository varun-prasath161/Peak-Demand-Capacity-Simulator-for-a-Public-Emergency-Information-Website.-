"""
Unit tests for Baseline vs Scenario-Based Capacity Planning Experiment
========================================================================
"""

import pytest
import pandas as pd
from pathlib import Path
from src.simulation.experiment import run_baseline_vs_scenario_experiment


class TestBaselineVsScenarioExperiment:
    """Automated tests for the measurable comparison experiment."""

    def test_experiment_output_files_and_metrics(self, tmp_path):
        out_dir = tmp_path / "outputs"
        df_comp, rep_text = run_baseline_vs_scenario_experiment(output_dir=str(out_dir))

        # Check CSV file creation
        csv_path = out_dir / "before_after_comparison.csv"
        report_path = out_dir / "before_after_report.txt"
        assert csv_path.exists()
        assert report_path.exists()

        # Check DataFrame structure
        assert len(df_comp) == 12
        assert "Baseline (Average-Based)" in df_comp.columns
        assert "Scenario-Based (Peak-Based)" in df_comp.columns

        # Check key metrics in DataFrame
        sla_row = df_comp[df_comp["Metric"] == "SLA Status Result"].iloc[0]
        assert "FAILED" in sla_row["Baseline (Average-Based)"]
        assert "PASSED" in sla_row["Scenario-Based (Peak-Based)"]

    def test_report_content_sections(self, tmp_path):
        out_dir = tmp_path / "outputs"
        _, rep_text = run_baseline_vs_scenario_experiment(output_dir=str(out_dir))

        # Verify 5 mandatory report sections present
        assert "1. BASELINE" in rep_text
        assert "2. TARGET" in rep_text
        assert "3. MEASURED RESULT" in rep_text
        assert "4. ERROR ANALYSIS" in rep_text
        assert "5. RECOMMENDATION" in rep_text

        # Verify compliance logic
        assert "100.0%" in rep_text
        assert "PASSED" in rep_text
