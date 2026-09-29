"""
Discrete-Event Peak-Demand Capacity Simulator MVP
=================================================
Simulates time-series web request demand over constrained server infrastructure,
modeling queue buildup, auto-scaling delays, M/M/1-inspired response latency,
overload error rates, and SLA compliance.

Key Capabilities:
- Constrained auto-scaling policy with provisioning delay.
- Queue accumulation when Demand > Capacity; queue drainage when Capacity > Demand.
- Non-linear latency degradation near 100% utilisation.
- Exponential error rate explosion under severe overload.
- SLA compliance evaluation (p95 latency <= target, error rate <= target).
- Output CSV export to outputs/simulation_results/.
"""

import sys
import math
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, Union, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.scenarios import generate_scenario

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "simulation_results"

DEFAULT_SIM_CONFIG = {
    "initial_instances": 10,
    "max_instances": 50,
    "capacity_per_instance": 500.0,      # RPM per instance
    "scaling_delay_seconds": 180,        # 3 minutes lag
    "scale_out_threshold_pct": 70.0,
    "urgent_scale_out_threshold_pct": 85.0,
    "scale_in_threshold_pct": 40.0,
    "sla_latency_target_ms": 500.0,       # p95 latency target
    "sla_error_target_rate": 0.01,       # 1% error rate target
    "max_queue_capacity": 50000.0,       # hard ceiling on queue depth before request dropping
}


def run_simulation(
    workload_scenario: Union[str, pd.DataFrame] = "DISASTER_PEAK",
    baseline_traffic: Optional[pd.DataFrame] = None,
    initial_instances: int = 10,
    max_instances: int = 50,
    capacity_per_instance: float = 500.0,
    scaling_delay_seconds: int = 180,
    scaling_policy: Optional[Dict[str, Any]] = None,
    sla_latency_target_ms: float = 500.0,
    sla_error_target_rate: float = 0.01,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes a time-series discrete simulation of website load against constrained infrastructure.

    Parameters:
        workload_scenario: Scenario name (e.g. 'NORMAL', 'DISASTER_PEAK') or scenario DataFrame.
        baseline_traffic: Optional historical baseline DataFrame.
        initial_instances: Base server count at start.
        max_instances: Hard ceiling on max servers.
        capacity_per_instance: Requests per minute each instance can serve.
        scaling_delay_seconds: Provisioning delay in seconds for new instances.
        scaling_policy: Custom dictionary for auto-scaling thresholds.
        sla_latency_target_ms: Maximum allowable p95 response time in ms.
        sla_error_target_rate: Maximum allowable error rate (e.g. 0.01 = 1%).
        seed: Random seed for deterministic simulation reproducibility.
        output_dir: Directory path to save output CSV.

    Returns:
        (simulation_results_df, summary_metrics_dict)
    """
    # ── Load or prepare Scenario DataFrame ──────────────────────────────────
    if isinstance(workload_scenario, str):
        sc_name = workload_scenario.upper()
        sc_df = generate_scenario(sc_name, baseline_df=baseline_traffic, seed=seed)
    elif isinstance(workload_scenario, pd.DataFrame):
        sc_df = workload_scenario.copy()
        sc_name = sc_df["scenario_name"].iloc[0] if "scenario_name" in sc_df.columns else "CUSTOM"
    else:
        raise ValueError("workload_scenario must be a string name or DataFrame")

    rng = np.random.default_rng(seed)

    # Policy thresholds
    policy = scaling_policy or {}
    th_out = policy.get("scale_out_threshold_pct", DEFAULT_SIM_CONFIG["scale_out_threshold_pct"])
    th_urgent = policy.get("urgent_scale_out_threshold_pct", DEFAULT_SIM_CONFIG["urgent_scale_out_threshold_pct"])
    th_in = policy.get("scale_in_threshold_pct", DEFAULT_SIM_CONFIG["scale_in_threshold_pct"])
    max_queue_cap = policy.get("max_queue_capacity", DEFAULT_SIM_CONFIG["max_queue_capacity"])

    n_steps = len(sc_df)
    timestamps = pd.to_datetime(sc_df["timestamp"])

    # Arrays for recording step metrics
    incoming_requests_arr = sc_df["requests_per_minute"].values
    active_instances_arr  = np.zeros(n_steps, dtype=int)
    available_cap_arr     = np.zeros(n_steps, dtype=float)
    utilisation_arr       = np.zeros(n_steps, dtype=float)
    cpu_util_arr          = np.zeros(n_steps, dtype=float)
    queue_depth_arr       = np.zeros(n_steps, dtype=float)
    queue_growth_arr      = np.zeros(n_steps, dtype=float)
    avg_latency_arr       = np.zeros(n_steps, dtype=float)
    p95_latency_arr       = np.zeros(n_steps, dtype=float)
    p99_latency_arr       = np.zeros(n_steps, dtype=float)
    error_rate_arr        = np.zeros(n_steps, dtype=float)
    scaling_action_arr    = ["none"] * n_steps
    unmet_requests_arr    = np.zeros(n_steps, dtype=float)
    sla_status_arr        = ["met"] * n_steps

    # Simulation State Variables
    cur_instances = float(initial_instances)
    pending_scale_out = 0.0
    pending_scale_in = 0.0
    steps_until_scale_out = 0
    steps_until_scale_in = 0
    cooldown_steps = 0
    consecutive_low_util = 0
    prev_queue = 0.0
    total_scaling_actions = 0

    for i in range(n_steps):
        ts = timestamps.iloc[i]
        rpm = float(incoming_requests_arr[i])

        # Step time interval in minutes
        if i > 0:
            dt_min = (ts - timestamps.iloc[i - 1]).total_seconds() / 60.0
        else:
            dt_min = 15.0

        # ---- 1. Process Pending Scale Actions ----
        if steps_until_scale_out > 0:
            steps_until_scale_out -= 1
            if steps_until_scale_out == 0:
                cur_instances = min(float(max_instances), cur_instances + pending_scale_out)
                pending_scale_out = 0.0

        if steps_until_scale_in > 0:
            steps_until_scale_in -= 1
            if steps_until_scale_in == 0:
                cur_instances = max(float(initial_instances), cur_instances - pending_scale_in)
                pending_scale_in = 0.0

        if cooldown_steps > 0:
            cooldown_steps -= 1

        active_inst = int(round(cur_instances))
        avail_cap = active_inst * capacity_per_instance

        # ---- 2. Compute Utilisation Ratio & CPU % ----
        util_ratio = rpm / avail_cap if avail_cap > 0 else 99.0
        
        # CPU utilisation mapping
        if util_ratio <= 0.70:
            cpu_pct = util_ratio * 80.0 + rng.normal(0, 1.5)
        elif util_ratio <= 1.0:
            cpu_pct = 56.0 + (util_ratio - 0.70) / 0.30 * 38.0 + rng.normal(0, 2.0)
        else:
            cpu_pct = 94.0 + (util_ratio - 1.0) * 10.0 + rng.normal(0, 1.0)
        cpu_pct = float(np.clip(cpu_pct, 1.0, 99.9))

        # ---- 3. Queue Dynamics ----
        excess_demand = max(0.0, rpm - avail_cap)
        drain_rate = min(prev_queue, avail_cap * 0.15 * dt_min)
        raw_new_queue = max(0.0, prev_queue + excess_demand * dt_min - drain_rate)

        # Unmet requests dropped when queue exceeds max queue capacity
        if raw_new_queue > max_queue_cap:
            unmet = raw_new_queue - max_queue_cap
            new_queue = max_queue_cap
        else:
            unmet = 0.0
            new_queue = raw_new_queue

        q_growth = (new_queue - prev_queue) / max(1.0, dt_min)
        prev_queue = new_queue

        # ---- 4. Latency Behavior (M/M/1-inspired queueing delay) ----
        base_lat = 25.0
        eff_util = min(0.985, util_ratio)
        lat_base = base_lat / (1.0 - eff_util) + rng.normal(0, 3.0)
        
        # Queue wait time penalty (ms)
        queue_wait_ms = (new_queue / max(1.0, avail_cap)) * 60.0 * 1000.0
        avg_lat = max(10.0, lat_base + queue_wait_ms * 0.05 + rng.normal(0, 5.0))
        
        # Overload penalty for unhandled traffic
        if util_ratio > 1.0:
            avg_lat += (util_ratio - 1.0) * 3500.0

        avg_lat = float(np.clip(avg_lat, 8.0, 30000.0))
        p95_lat = float(np.round(avg_lat * (1.8 + 0.3 * rng.random()), 1))
        p99_lat = float(np.round(p95_lat * (1.4 + 0.4 * rng.random()), 1))
        avg_lat = float(np.round(avg_lat, 1))

        # ---- 5. Error Rate Behavior ----
        base_err = 0.001
        if util_ratio < 0.85:
            err = base_err + rng.normal(0, 0.0003)
        else:
            err = base_err * np.exp(7.5 * (util_ratio - 0.85)) + (new_queue / max_queue_cap) * 0.15 + rng.normal(0, 0.005)
        err_rate = float(np.clip(err, 0.0, 1.0))
        err_rate = float(np.round(err_rate, 5))

        # ---- 6. Constrained Auto-scaling Policy ----
        action = "none"
        if cooldown_steps == 0 and pending_scale_out == 0 and pending_scale_in == 0:
            if cpu_pct > th_out and active_inst < max_instances:
                needed = max(2.0, np.ceil((rpm - avail_cap * 0.70) / capacity_per_instance))
                if cpu_pct > th_urgent:
                    needed = min(max_instances - active_inst, needed + 3.0)
                    action = "urgent_scale_out"
                else:
                    needed = min(max_instances - active_inst, needed)
                    action = "scale_out"

                if needed > 0:
                    pending_scale_out = needed
                    delay_steps = max(1, int(np.ceil(scaling_delay_seconds / (dt_min * 60.0))))
                    steps_until_scale_out = delay_steps
                    cooldown_steps = 2
                    total_scaling_actions += 1

            elif cpu_pct < th_in and active_inst > initial_instances:
                consecutive_low_util += 1
                if consecutive_low_util >= 3:
                    removable = min(active_inst - initial_instances, 2)
                    pending_scale_in = removable
                    delay_steps = max(1, int(np.ceil(scaling_delay_seconds / (dt_min * 60.0))))
                    steps_until_scale_in = delay_steps
                    cooldown_steps = 3
                    action = "scale_in"
                    consecutive_low_util = 0
                    total_scaling_actions += 1
            else:
                consecutive_low_util = 0

        # ---- 7. SLA Compliance Checking ----
        sla_met = (p95_lat <= sla_latency_target_ms) and (err_rate <= sla_error_target_rate)
        sla_status_arr[i] = "met" if sla_met else "breached"

        # Record metrics
        active_instances_arr[i] = active_inst
        available_cap_arr[i]    = round(avail_cap, 1)
        utilisation_arr[i]      = round(util_ratio, 4)
        cpu_util_arr[i]         = round(cpu_pct, 2)
        queue_depth_arr[i]      = round(new_queue, 1)
        queue_growth_arr[i]     = round(q_growth, 2)
        avg_latency_arr[i]      = avg_lat
        p95_latency_arr[i]      = p95_lat
        p99_latency_arr[i]      = p99_lat
        error_rate_arr[i]       = err_rate
        scaling_action_arr[i]   = action
        unmet_requests_arr[i]   = round(unmet, 1)

    # Build Output DataFrame
    results_df = pd.DataFrame({
        "timestamp": timestamps,
        "scenario_name": sc_name,
        "incoming_requests": incoming_requests_arr,
        "active_instances": active_instances_arr,
        "available_capacity": available_cap_arr,
        "utilisation": utilisation_arr,
        "cpu_utilisation_pct": cpu_util_arr,
        "queue_depth": queue_depth_arr,
        "queue_growth": queue_growth_arr,
        "average_latency_ms": avg_latency_arr,
        "p95_latency_ms": p95_latency_arr,
        "p99_latency_ms": p99_latency_arr,
        "error_rate": error_rate_arr,
        "scaling_action": scaling_action_arr,
        "unmet_requests": unmet_requests_arr,
        "sla_target_latency_ms": sla_latency_target_ms,
        "sla_target_error_rate": sla_error_target_rate,
        "sla_status": sla_status_arr
    })

    # Save Output CSV
    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = out_dir / f"sim_result_{sc_name.lower()}.csv"
    results_df.to_csv(csv_file, index=False)

    # ── Summary Metrics Dictionary ──────────────────────────────────────────
    met_count = int((results_df["sla_status"] == "met").sum())
    compliance_pct = round(float(met_count / n_steps * 100.0), 2)
    overall_sla_compliant = bool(compliance_pct >= 95.0)

    summary = {
        "scenario_name": sc_name,
        "sla_compliant": overall_sla_compliant,
        "compliance_percentage": compliance_pct,
        "max_queue_depth": round(float(results_df["queue_depth"].max()), 1),
        "max_p95_latency_ms": round(float(results_df["p95_latency_ms"].max()), 1),
        "max_error_rate": round(float(results_df["error_rate"].max()), 5),
        "peak_instances": int(results_df["active_instances"].max()),
        "total_scaling_actions": total_scaling_actions,
        "total_unmet_requests": round(float(results_df["unmet_requests"].sum()), 1),
        "csv_path": str(csv_file)
    }

    return results_df, summary


def run_all_simulations(seed: int = 42) -> List[Dict[str, Any]]:
    """Runs simulations for all 5 workload scenarios and prints a summary."""
    scenarios = ["NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"]
    summaries = []

    print("=" * 95)
    print("  PEAK-DEMAND CAPACITY SIMULATOR MVP -- DISCRETE SIMULATION RESULTS")
    print("=" * 95)
    print(f"{'Scenario Name':<20s} {'SLA Compliant':<15s} {'SLA Met %':>10s} {'Max Queue':>12s} {'Max p95 (ms)':>14s} {'Max Error %':>12s} {'Peak Inst':>10s}")
    print("-" * 95)

    for sc in scenarios:
        _, summary = run_simulation(workload_scenario=sc, seed=seed)
        summaries.append(summary)
        comp_str = "YES [MET]" if summary["sla_compliant"] else "NO [BREACHED]"
        err_pct = summary["max_error_rate"] * 100.0
        print(f"{summary['scenario_name']:<20s} {comp_str:<15s} {summary['compliance_percentage']:>9.1f}% {summary['max_queue_depth']:>12,.1f} {summary['max_p95_latency_ms']:>14,.1f} {err_pct:>11.2f}% {summary['peak_instances']:>10d}")


    print("=" * 95)
    return summaries


if __name__ == "__main__":
    run_all_simulations()
