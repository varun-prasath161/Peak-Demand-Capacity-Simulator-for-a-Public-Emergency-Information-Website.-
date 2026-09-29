"""
Infrastructure Cost Analysis & Economic Modeling Module
========================================================
Calculates synthetic simulated infrastructure costs, scaling action expenses,
SLA breach penalties, and dropped request penalties for capacity planning strategies.

DISCLAIMER:
All cost metrics represent 'Simulation Cost Assumptions' for trade-off analysis
and do not claim to mirror exact live cloud provider pricing.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_COST_CONFIG = {
    "cost_per_instance_hour": 0.50,                 # $0.50 per server instance hour
    "scale_out_cost": 2.00,                           # $2.00 per scale-out provisioning action
    "scale_in_cost": 1.00,                            # $1.00 per scale-in de-provisioning action
    "sla_violation_penalty_per_period": 100.00,      # $100.00 penalty per breached 15-min period
    "unmet_request_penalty": 0.05,                    # $0.05 penalty per dropped user request
    "currency": "USD",
    "disclaimer": "Simulation Cost Assumptions -- Synthetic parameters for economic trade-off analysis."
}


def calculate_simulation_costs(
    df_sim: pd.DataFrame,
    summary: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes transparent cost breakdown for a simulation execution run.

    Returns:
        Dict containing:
        - infrastructure_cost
        - scaling_cost
        - sla_penalty
        - unmet_request_penalty
        - total_simulated_cost
        - currency
        - disclaimer
    """
    cfg = config or DEFAULT_COST_CONFIG

    cost_per_inst_hour = float(cfg.get("cost_per_instance_hour", 0.50))
    scale_out_cost_val = float(cfg.get("scale_out_cost", 2.00))
    scale_in_cost_val = float(cfg.get("scale_in_cost", 1.00))
    sla_penalty_per_period = float(cfg.get("sla_violation_penalty_per_period", 100.00))
    unmet_penalty_per_req = float(cfg.get("unmet_request_penalty", 0.05))

    # 1. Infrastructure Cost: Active instance-hours
    # Sum over each step: active_instances * (dt_minutes / 60) * cost_per_inst_hour
    timestamps = pd.to_datetime(df_sim["timestamp"])
    if len(timestamps) > 1:
        time_diffs_hours = timestamps.diff().dt.total_seconds().fillna(
            (timestamps.iloc[1] - timestamps.iloc[0]).total_seconds()
        ) / 3600.0
    else:
        time_diffs_hours = pd.Series([0.25] * len(df_sim))

    active_inst_hours = (df_sim["active_instances"] * time_diffs_hours).sum()
    infra_cost = float(active_inst_hours * cost_per_inst_hour)

    # 2. Scaling Cost: Scale-out and scale-in events
    scaling_actions = df_sim["scaling_action"]
    n_scale_out = int((scaling_actions.isin(["scale_out", "urgent_scale_out"])).sum())
    n_scale_in = int((scaling_actions == "scale_in").sum())
    scaling_cost = float(n_scale_out * scale_out_cost_val + n_scale_in * scale_in_cost_val)

    # 3. SLA Breach Penalty: Count of breached time intervals
    n_breached_periods = int((df_sim["sla_status"] == "breached").sum())
    sla_penalty = float(n_breached_periods * sla_penalty_per_period)

    # 4. Unmet Request Penalty: Total dropped requests
    total_unmet = float(df_sim["unmet_requests"].sum()) if "unmet_requests" in df_sim.columns else float(summary.get("total_unmet_requests", 0.0))
    unmet_penalty = float(total_unmet * unmet_penalty_per_req)

    # Total Simulated Cost
    total_cost = float(infra_cost + scaling_cost + sla_penalty + unmet_penalty)

    return {
        "infrastructure_cost": round(infra_cost, 2),
        "scaling_cost": round(scaling_cost, 2),
        "sla_penalty": round(sla_penalty, 2),
        "unmet_request_penalty": round(unmet_penalty, 2),
        "total_simulated_cost": round(total_cost, 2),
        "active_instance_hours": round(active_inst_hours, 1),
        "breached_periods_count": n_breached_periods,
        "total_unmet_requests": round(total_unmet, 1),
        "currency": cfg.get("currency", "USD"),
        "disclaimer": cfg.get("disclaimer", DEFAULT_COST_CONFIG["disclaimer"])
    }
