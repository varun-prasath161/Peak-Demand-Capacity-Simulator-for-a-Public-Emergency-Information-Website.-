"""
Unit Tests for Formal SLA Experiment & Error Analysis
=====================================================
Tests SLA target configuration, SLA compliance evaluation, violation duration calculation,
baseline experiment execution, improved strategy evaluation, before/after comparison,
and error classification.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.analysis.sla_experiment import (
    load_sla_config,
    run_formal_sla_experiment,
    calculate_recovery_time_minutes,
    calculate_sla_violation_duration_minutes,
    compute_before_after_comparison
)
from src.analysis.error_analysis import classify_sla_violations, run_pipeline
from src.simulation.simulator import run_simulation


def test_sla_target_calculation():
    """Test loading configurable SLA targets from config."""
    cfg = load_sla_config()
    assert "sla_targets" in cfg
    targets = cfg["sla_targets"]
    assert targets["p95_latency_target_ms"] == 500.0
    assert targets["error_rate_target"] == 0.01


def test_sla_compliance():
    """Test SLA compliance calculation on normal vs extreme simulation runs."""
    df_sim, summary = run_simulation(workload_scenario="NORMAL", seed=42)
    assert summary["compliance_percentage"] == 100.0

    df_sim2, summary2 = run_simulation(
        workload_scenario="EXTREME_DISASTER",
        initial_instances=4,
        max_instances=6,
        seed=42
    )
    assert summary2["compliance_percentage"] < 90.0


def test_sla_violation_detection():
    """Test SLA violation duration calculation."""
    df_sim, summary = run_simulation(
        workload_scenario="EXTREME_DISASTER",
        initial_instances=4,
        max_instances=6,
        seed=42
    )
    viol_dur = calculate_sla_violation_duration_minutes(df_sim)
    assert viol_dur > 0.0


def test_recovery_time_calculation():
    """Test recovery time calculation in minutes."""
    df_sim, summary = run_simulation(workload_scenario="DISASTER_PEAK", seed=42)
    rec_min = calculate_recovery_time_minutes(df_sim)
    assert rec_min >= 0.0


def test_baseline_experiment():
    """Test baseline experiment execution."""
    df_exp, df_ba = run_formal_sla_experiment(seed=42)
    assert not df_exp.empty
    assert "AVERAGE_DEMAND" in df_exp["strategy"].values


def test_improved_strategy_experiment():
    """Test that improved strategies outperform baseline under disaster workload."""
    df_exp, df_ba = run_formal_sla_experiment(seed=42)
    disaster_df = df_exp[df_exp["scenario"] == "DISASTER_PEAK"]
    
    base_sla = disaster_df[disaster_df["strategy"] == "AVERAGE_DEMAND"]["sla_compliance"].iloc[0]
    improved_sla = disaster_df[disaster_df["strategy"] == "DYNAMIC_SCALING"]["sla_compliance"].iloc[0]

    assert improved_sla > base_sla


def test_before_after_comparison():
    """Test computation of before-vs-after comparison delta values."""
    df_exp, df_ba = run_formal_sla_experiment(seed=42)
    assert not df_ba.empty
    assert "sla_difference" in df_ba.columns
    assert "queue_difference" in df_ba.columns


def test_error_classification():
    """Test classification of SLA violation root causes."""
    df_exp, df_ba = run_formal_sla_experiment(seed=42)
    df_err = classify_sla_violations(df_exp, seed=42)

    assert not df_err.empty
    assert "violation_detected" in df_err.columns
    assert "explanation" in df_err.columns
    
    # Check that baseline disaster run is flagged with violation
    base_disaster_err = df_err[(df_err["scenario"] == "DISASTER_PEAK") & (df_err["strategy"] == "AVERAGE_DEMAND")].iloc[0]
    assert bool(base_disaster_err["violation_detected"]) is True
    assert len(base_disaster_err["explanation"]) > 0
