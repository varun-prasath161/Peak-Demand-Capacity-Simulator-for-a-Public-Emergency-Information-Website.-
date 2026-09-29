"""
Baseline Capacity Model
=======================
Estimates public emergency website capacity requirements under constrained infrastructure.

Key Capability:
Demonstrates the dangerous flaw of planning using AVERAGE demand versus
planning using PEAK WORKLOAD SCENARIOS during natural disasters.

Features:
- Constrained server fleet modeling (current instances, max allowed instances, per-instance throughput limit).
- Safety margin buffering (e.g. 20% headroom).
- Capacity gap and shortfall metrics calculation.
- Scenario comparison demonstrating infrastructure collapse under un-planned peak surges.
"""

import json
import math
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.scenarios import generate_scenario, load_scenario_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "emergency_load_cleaned.csv"
REPORT_PATH = PROJECT_ROOT / "outputs" / "baseline_capacity_report.txt"

# Default Infrastructure Constraints
DEFAULT_CONFIG = {
    "current_instances": 10,
    "max_instances": 50,
    "instance_capacity_rpm": 500.0,
    "safety_margin_pct": 20.0,          # 20% safety margin buffer
    "scaling_delay_seconds": 180,
}


def evaluate_capacity_for_demand(
    demand_rpm: float,
    demand_label: str = "Target Demand",
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates infrastructure capacity required to serve a specified request rate (RPM).

    Returns a dictionary containing:
    - current_instances, max_instances, instance_capacity_rpm, safety_margin_pct
    - current_capacity_rpm, max_sustainable_capacity_rpm
    - demand_rpm, buffered_demand_rpm
    - capacity_gap_rpm, capacity_shortfall_rpm
    - required_instances, instance_shortfall
    - is_within_current_capacity, is_within_max_capacity
    """
    cfg = config or DEFAULT_CONFIG
    cur_inst = int(cfg.get("current_instances", 10))
    max_inst = int(cfg.get("max_instances", 50))
    inst_cap = float(cfg.get("instance_capacity_rpm", 500.0))
    safety_margin = float(cfg.get("safety_margin_pct", 20.0))

    current_capacity_rpm = cur_inst * inst_cap
    max_sustainable_capacity_rpm = max_inst * inst_cap

    buffered_demand_rpm = demand_rpm * (1.0 + safety_margin / 100.0)

    # Capacity Gap: Demand vs Current Capacity
    capacity_gap_rpm = max(0.0, demand_rpm - current_capacity_rpm)
    buffered_gap_rpm = max(0.0, buffered_demand_rpm - current_capacity_rpm)

    # Instances required
    required_instances_raw = math.ceil(demand_rpm / inst_cap) if inst_cap > 0 else 999
    required_instances = math.ceil(buffered_demand_rpm / inst_cap) if inst_cap > 0 else 999

    # Shortfall: Amount by which demand exceeds MAX sustainable capacity
    instance_shortfall = max(0, required_instances - max_inst)
    capacity_shortfall_rpm = max(0.0, buffered_demand_rpm - max_sustainable_capacity_rpm)

    is_within_current = demand_rpm <= current_capacity_rpm
    is_within_max = buffered_demand_rpm <= max_sustainable_capacity_rpm

    return {
        "demand_label": demand_label,
        "demand_rpm": round(demand_rpm, 1),
        "buffered_demand_rpm": round(buffered_demand_rpm, 1),
        "current_instances": cur_inst,
        "max_instances": max_inst,
        "instance_capacity_rpm": round(inst_cap, 1),
        "safety_margin_pct": safety_margin,
        "current_capacity_rpm": round(current_capacity_rpm, 1),
        "max_sustainable_capacity_rpm": round(max_sustainable_capacity_rpm, 1),
        "capacity_gap_rpm": round(capacity_gap_rpm, 1),
        "buffered_gap_rpm": round(buffered_gap_rpm, 1),
        "required_instances_raw": required_instances_raw,
        "required_instances": required_instances,
        "instance_shortfall": instance_shortfall,
        "capacity_shortfall_rpm": round(capacity_shortfall_rpm, 1),
        "is_within_current_capacity": is_within_current,
        "is_within_max_capacity": is_within_max,
        "status": "SUFFICIENT" if is_within_max else "CAPACITY_SHORTFALL"
    }


def evaluate_baseline_capacity(
    dataset_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Evaluates baseline historical average demand, baseline peak demand,
    and all 5 workload scenarios against constrained infrastructure.
    """
    path = dataset_path or PROCESSED_DATA_PATH
    if path.exists():
        df_hist = pd.read_csv(path)
        avg_demand = float(df_hist["requests_per_minute"].mean())
        normal_df = df_hist[df_hist.get("event_type", "normal") == "normal"]
        hist_peak_demand = float(normal_df["requests_per_minute"].max()) if not normal_df.empty else float(df_hist["requests_per_minute"].max())
    else:
        avg_demand = 800.0
        hist_peak_demand = 1200.0

    eval_avg = evaluate_capacity_for_demand(avg_demand, "Average Everyday Demand", config)
    eval_hist_peak = evaluate_capacity_for_demand(hist_peak_demand, "Normal Operating Peak", config)

    # Evaluate 5 Workload Scenarios
    scenarios_eval = {}
    scenario_names = ["NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"]

    for name in scenario_names:
        sc_df = generate_scenario(name, seed=seed)
        peak_rpm = float(sc_df["requests_per_minute"].max())
        scenarios_eval[name] = evaluate_capacity_for_demand(peak_rpm, f"Scenario: {name}", config)

    return {
        "config": config or DEFAULT_CONFIG,
        "average_demand_eval": eval_avg,
        "historical_peak_eval": eval_hist_peak,
        "scenarios_eval": scenarios_eval
    }



def generate_baseline_report(
    evaluations: Dict[str, Any],
    report_path: Path = REPORT_PATH
) -> str:
    """
    Generates a non-specialist understandable text report comparing average-based
    capacity planning against scenario-based peak disaster planning.
    """
    cfg = evaluations["config"]
    avg_eval = evaluations["average_demand_eval"]
    hist_peak_eval = evaluations["historical_peak_eval"]
    sc_eval = evaluations["scenarios_eval"]

    cur_cap = avg_eval["current_capacity_rpm"]
    max_cap = avg_eval["max_sustainable_capacity_rpm"]
    cur_inst = avg_eval["current_instances"]
    max_inst = avg_eval["max_instances"]
    inst_cap = avg_eval["instance_capacity_rpm"]
    margin = avg_eval["safety_margin_pct"]

    disaster_eval = sc_eval["DISASTER_PEAK"]
    extreme_eval = sc_eval["EXTREME_DISASTER"]

    report = f"""================================================================================
PEAK-DEMAND CAPACITY SIMULATOR -- BASELINE CAPACITY EVALUATION REPORT
================================================================================
Generated Date: 2026-09-05
Scope: Baseline Capacity Model & Workload Scenario Stress Testing

--------------------------------------------------------------------------------
1. INFRASTRUCTURE CONSTRAINTS SUMMARY
--------------------------------------------------------------------------------
- Current Active Server Fleet:    {cur_inst} instances
- Maximum Allowed Infrastructure:  {max_inst} instances (hard ceiling)
- Capacity per Server Instance:   {inst_cap:,.0f} requests/minute (RPM)
- Planning Safety Margin Buffer:  {margin:.0f}%
- Current Baseline Capacity:      {cur_cap:,.0f} RPM ({cur_inst} servers x {inst_cap:.0f} RPM)
- Maximum Sustainable Capacity:   {max_cap:,.0f} RPM ({max_inst} servers x {inst_cap:.0f} RPM)

--------------------------------------------------------------------------------
2. AVERAGE DEMAND PLANNING vs PEAK WORKLOAD SCENARIOS
--------------------------------------------------------------------------------
Demand Type                  Peak Demand      Req. Servers   Capacity Gap    Status
--------------------------------------------------------------------------------
Average Demand (Everyday)    {avg_eval['demand_rpm']:>10,.1f} RPM {avg_eval['required_instances']:>12d} {avg_eval['capacity_gap_rpm']:>12,.1f} RPM  {avg_eval['status']}
Historical Peak (Normal)     {hist_peak_eval['demand_rpm']:>10,.1f} RPM {hist_peak_eval['required_instances']:>12d} {hist_peak_eval['capacity_gap_rpm']:>12,.1f} RPM  {hist_peak_eval['status']}
Scenario: NORMAL             {sc_eval['NORMAL']['demand_rpm']:>10,.1f} RPM {sc_eval['NORMAL']['required_instances']:>12d} {sc_eval['NORMAL']['capacity_gap_rpm']:>12,.1f} RPM  {sc_eval['NORMAL']['status']}
Scenario: SEASONAL_PEAK      {sc_eval['SEASONAL_PEAK']['demand_rpm']:>10,.1f} RPM {sc_eval['SEASONAL_PEAK']['required_instances']:>12d} {sc_eval['SEASONAL_PEAK']['capacity_gap_rpm']:>12,.1f} RPM  {sc_eval['SEASONAL_PEAK']['status']}
Scenario: BREAKING_NEWS      {sc_eval['BREAKING_NEWS']['demand_rpm']:>10,.1f} RPM {sc_eval['BREAKING_NEWS']['required_instances']:>12d} {sc_eval['BREAKING_NEWS']['capacity_gap_rpm']:>12,.1f} RPM  {sc_eval['BREAKING_NEWS']['status']}
Scenario: DISASTER_PEAK      {disaster_eval['demand_rpm']:>10,.1f} RPM {disaster_eval['required_instances']:>12d} {disaster_eval['capacity_gap_rpm']:>12,.1f} RPM  {disaster_eval['status']}
Scenario: EXTREME_DISASTER   {extreme_eval['demand_rpm']:>10,.1f} RPM {extreme_eval['required_instances']:>12d} {extreme_eval['capacity_gap_rpm']:>12,.1f} RPM  {extreme_eval['status']}
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
3. NON-TECHNICAL STAKEHOLDER EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
The current system can handle approximately {cur_cap:,.0f} requests per minute under 
normal baseline conditions using its standard fleet of {cur_inst} servers.

Under everyday average demand ({avg_eval['demand_rpm']:,.0f} requests per minute), the 
system operates smoothly with low resource utilisation, requiring only {avg_eval['required_instances']} servers.

HOWEVER, planning infrastructure based strictly on average demand creates a 
DANGEROUS FALSE SENSE OF SECURITY:

1. During a Major Disaster Scenario (e.g. Cat-3 Hurricane or major flood), 
   traffic surges to approximately {disaster_eval['demand_rpm']:,.0f} requests per minute.
   - This creates an immediate Capacity Gap of {disaster_eval['capacity_gap_rpm']:,.0f} requests per minute 
     above current capacity.
   - To serve this disaster surge safely with a {margin:.0f}% buffer, the system requires 
     {disaster_eval['required_instances']} server instances.
   - Since current max infrastructure allows up to {max_inst} servers, max capacity ({max_cap:,.0f} RPM) 
     CAN handle this surge if scaling triggers in time.

2. During a Catastrophic Extreme Disaster (e.g. Cat-5 Hurricane or earthquake), 
   traffic surges to {extreme_eval['demand_rpm']:,.0f} requests per minute.
   - This produces a massive Capacity Gap of {extreme_eval['capacity_gap_rpm']:,.0f} requests per minute.
   - Serving this peak requires {extreme_eval['required_instances']} servers -- exceeding our hard 
     infrastructure limit of {max_inst} servers by {extreme_eval['instance_shortfall']} servers.
   - Result: A unhandled Capacity Shortfall of {extreme_eval['capacity_shortfall_rpm']:,.0f} requests per minute, 
     causing server overload, website crashes, and emergency SLA breaches.

--------------------------------------------------------------------------------
4. KEY TAKEAWAYS & RECOMMENDATIONS
--------------------------------------------------------------------------------
- Average-based planning masks extreme peak spikes and guarantees website failure 
  when citizens need emergency information most.
- Scenario-based capacity planning identifies exact server provisioning limits 
  BEFORE disaster strikes.

================================================================================
REPORT COMPLETE -- Baseline Capacity Analysis Completed Successfully.
================================================================================
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return report


def run_capacity_analysis():
    """Execute baseline capacity evaluation, print summary table, and save report."""
    evals = evaluate_baseline_capacity()
    report_text = generate_baseline_report(evals, REPORT_PATH)

    print("=" * 80)
    print("  PEAK-DEMAND CAPACITY SIMULATOR -- BASELINE CAPACITY ANALYSIS")
    print("=" * 80)
    print(f"[OK] Capacity evaluation complete.")
    print(f"[OK] Baseline capacity report saved to: {REPORT_PATH}\n")
    print(report_text)
    return evals


if __name__ == "__main__":
    run_capacity_analysis()
