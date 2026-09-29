"""
Unit Tests for Advanced Workload Scenario Engine & Validation
=============================================================
Tests standard scenarios, compound scenarios, phase transitions,
invalid configurations, and finite infrastructure constraints.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.simulation.scenarios import (
    generate_scenario,
    load_scenario_config,
    get_scenario_summary,
    calculate_peak_demand
)
from src.simulation.simulator import run_simulation
from src.simulation.scenario_validation import (
    validate_single_scenario,
    run_all_advanced_scenarios
)


def test_normal_scenario():
    """Test generation and simulation of NORMAL scenario."""
    df_sc = generate_scenario("NORMAL", seed=42)
    assert not df_sc.empty
    assert "requests_per_minute" in df_sc.columns
    assert (df_sc["requests_per_minute"] >= 0).all()
    
    df_sim, summary = run_simulation(workload_scenario="NORMAL", seed=42)
    assert summary["sla_compliant"] is True
    assert summary["max_queue_depth"] < 1000.0


def test_disaster_scenario():
    """Test generation and simulation of DISASTER_PEAK scenario."""
    df_sc = generate_scenario("DISASTER_PEAK", seed=42)
    assert not df_sc.empty
    assert df_sc["requests_per_minute"].max() > 2500.0

    df_sim, summary = run_simulation(workload_scenario="DISASTER_PEAK", seed=42)
    assert summary["peak_instances"] > 10


def test_extreme_scenario():
    """Test generation and simulation of EXTREME_DISASTER scenario."""
    df_sc = generate_scenario("EXTREME_DISASTER", seed=42)
    assert df_sc["requests_per_minute"].max() > 5000.0

    df_sim, summary = run_simulation(workload_scenario="EXTREME_DISASTER", seed=42)
    assert summary["peak_instances"] > 10
    assert summary["peak_instances"] <= 50


def test_compound_scenario_disaster_breaking_news():
    """Test Compound Scenario 1: DISASTER_BREAKING_NEWS."""
    df_sc = generate_scenario("DISASTER_BREAKING_NEWS", seed=42)
    assert not df_sc.empty
    assert df_sc["scenario_name"].iloc[0] == "DISASTER_BREAKING_NEWS"
    assert df_sc["requests_per_minute"].max() > 3500.0

    df_sim, summary = run_simulation(workload_scenario="DISASTER_BREAKING_NEWS", seed=42)
    assert summary["total_scaling_actions"] > 0


def test_compound_scenario_disaster_seasonal():
    """Test Compound Scenario 2: DISASTER_SEASONAL."""
    df_sc = generate_scenario("DISASTER_SEASONAL", seed=42)
    assert not df_sc.empty
    assert df_sc["scenario_name"].iloc[0] == "DISASTER_SEASONAL"
    assert df_sc["requests_per_minute"].max() > 3000.0

    df_sim, summary = run_simulation(workload_scenario="DISASTER_SEASONAL", seed=42)
    assert "active_instances" in df_sim.columns


def test_invalid_configuration():
    """Test validation failure on invalid configuration."""
    invalid_config = {
        "scenarios": {
            "INVALID_TEST": {
                "traffic_multiplier": -1.0,  # Invalid negative multiplier
                "duration_hours": -5,        # Invalid negative duration
                "ramp_up_minutes": 0,
                "peak_duration_minutes": 0,
                "recovery_duration_minutes": 0,
                "initial_instances": 20,
                "max_instances": 5           # Invalid max < initial
            }
        }
    }
    val_res = validate_single_scenario("INVALID_TEST", invalid_config, seed=42)
    assert val_res["is_valid"] is False
    assert len(val_res["errors"]) > 0


def test_recovery_phase():
    """Test that traffic in recovery phase decreases after peak phase."""
    df_sc = generate_scenario("DISASTER_PEAK", seed=42)
    peak_df = df_sc[df_sc["phase"] == "peak"]
    rec_df = df_sc[df_sc["phase"] == "recovery"]

    assert not peak_df.empty
    assert not rec_df.empty

    mean_peak_rpm = peak_df["requests_per_minute"].mean()
    end_rec_rpm = rec_df["requests_per_minute"].iloc[-1]

    # Traffic at end of recovery phase must be substantially lower than average peak traffic
    assert end_rec_rpm < mean_peak_rpm


def test_maximum_instance_constraint():
    """Test that finite infrastructure bounds (max_instances) are strictly enforced."""
    max_cap = 15
    df_sim, summary = run_simulation(
        workload_scenario="EXTREME_DISASTER",
        initial_instances=5,
        max_instances=max_cap,
        seed=42
    )
    assert (df_sim["active_instances"] <= max_cap).all()
    assert summary["peak_instances"] == max_cap
