"""
Unit Tests for Capacity Planning Strategies & Cost Model
=========================================================
Tests Average, Peak, Safety Margin, Dynamic Scaling, and Disaster-Aware strategies,
cost calculation breakdown, SLA breach penalties, dropped request penalties, and instance constraints.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.capacity.strategies import run_strategy, compare_all_strategies, STRATEGY_KEYS
from src.capacity.cost_model import calculate_simulation_costs, DEFAULT_COST_CONFIG
from src.simulation.simulator import run_simulation


def test_average_demand_strategy():
    """Test Strategy 1: AVERAGE_DEMAND."""
    res = run_strategy("AVERAGE_DEMAND", "NORMAL", seed=42)
    assert res["strategy"] == "AVERAGE_DEMAND"
    assert res["initial_instances"] == 4
    assert res["max_instance_cap"] == 6
    assert res["total_simulated_cost"] >= 0.0


def test_peak_demand_strategy():
    """Test Strategy 2: PEAK_DEMAND."""
    res = run_strategy("PEAK_DEMAND", "DISASTER_PEAK", seed=42)
    assert res["strategy"] == "PEAK_DEMAND"
    assert res["peak_instances"] >= 10
    assert res["total_simulated_cost"] > 0.0


def test_safety_margin_strategy():
    """Test Strategy 3: SAFETY_MARGIN with 20% margin."""
    res = run_strategy("SAFETY_MARGIN", "DISASTER_PEAK", safety_margin_pct=20.0, seed=42)
    assert res["strategy"] == "SAFETY_MARGIN"
    assert res["max_instance_cap"] >= res["required_instances"]
    assert res["total_simulated_cost"] > 0.0


def test_dynamic_scaling_strategy():
    """Test Strategy 4: DYNAMIC_SCALING."""
    res = run_strategy("DYNAMIC_SCALING", "BREAKING_NEWS", seed=42)
    assert res["strategy"] == "DYNAMIC_SCALING"
    assert res["initial_instances"] == 10
    assert res["max_instance_cap"] == 50
    assert res["sla_compliance_pct"] == 100.0


def test_disaster_aware_strategy():
    """Test Strategy 5: DISASTER_AWARE pre-warming."""
    res = run_strategy("DISASTER_AWARE", "DISASTER_PEAK", seed=42)
    assert res["strategy"] == "DISASTER_AWARE"
    assert res["initial_instances"] == 18  # Pre-warmed fleet
    assert res["total_simulated_cost"] > 0.0


def test_cost_calculation():
    """Test cost calculation function metrics breakdown."""
    df_sim, summary = run_simulation(workload_scenario="NORMAL", seed=42)
    costs = calculate_simulation_costs(df_sim, summary)
    
    assert "infrastructure_cost" in costs
    assert "scaling_cost" in costs
    assert "sla_penalty" in costs
    assert "unmet_request_penalty" in costs
    assert "total_simulated_cost" in costs
    assert costs["total_simulated_cost"] >= 0.0


def test_sla_penalty():
    """Test SLA violation penalty calculation on extreme disaster breach."""
    df_sim, summary = run_simulation(workload_scenario="EXTREME_DISASTER", seed=42)
    costs = calculate_simulation_costs(df_sim, summary)
    
    if summary["compliance_percentage"] < 100.0:
        assert costs["sla_penalty"] > 0.0


def test_unmet_request_penalty():
    """Test dropped request penalty calculation."""
    df_sim, summary = run_simulation(
        workload_scenario="EXTREME_DISASTER",
        initial_instances=2,
        max_instances=5,
        seed=42
    )
    costs = calculate_simulation_costs(df_sim, summary)
    assert costs["unmet_request_penalty"] > 0.0


def test_maximum_instance_constraint():
    """Test max instance ceiling constraint across strategy runs."""
    res = run_strategy("AVERAGE_DEMAND", "EXTREME_DISASTER", seed=42)
    assert res["peak_instances"] <= res["max_instance_cap"]
