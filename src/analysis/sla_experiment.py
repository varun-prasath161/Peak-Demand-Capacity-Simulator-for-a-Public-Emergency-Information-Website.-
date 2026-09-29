"""
Formal SLA Experiment & Before-vs-After Comparison Engine
==========================================================
Executes controlled SLA experiments comparing Baseline Average-Demand Planning
against Improved Capacity Strategies across 7 identical workload scenarios.

Outputs:
- outputs/sla_experiment_results.csv
- outputs/final_before_after_comparison.csv
"""

import sys
import json
import math
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.capacity.strategies import run_strategy, STRATEGY_KEYS, SCENARIO_KEYS
from src.simulation.simulator import run_simulation
from src.simulation.scenarios import generate_scenario

SLA_CONFIG_PATH = PROJECT_ROOT / "data" / "scenarios" / "sla_config.json"
EXP_RESULTS_CSV = PROJECT_ROOT / "outputs" / "sla_experiment_results.csv"
BEFORE_AFTER_CSV = PROJECT_ROOT / "outputs" / "final_before_after_comparison.csv"


def load_sla_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configurable SLA targets from JSON config file."""
    path = config_path or SLA_CONFIG_PATH
    if not path.exists():
        return {
            "sla_targets": {
                "p95_latency_target_ms": 500.0,
                "error_rate_target": 0.01,
                "sla_compliance_target_pct": 99.0
            }
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_recovery_time_minutes(df_sim: pd.DataFrame) -> float:
    """
    Calculates recovery time in minutes:
    Time elapsed from peak demand step until queue depth returns to < 100 requests.
    """
    if "queue_depth" not in df_sim.columns or "timestamp" not in df_sim.columns:
        return 0.0

    ts = pd.to_datetime(df_sim["timestamp"])
    peak_idx = df_sim["incoming_requests"].idxmax()
    peak_ts = ts.iloc[peak_idx]

    # Post-peak dataframe
    post_peak_df = df_sim.iloc[peak_idx:]
    recovered_rows = post_peak_df[post_peak_df["queue_depth"] < 100.0]

    if recovered_rows.empty:
        # If queue never recovers below 100 before simulation end
        rec_ts = ts.iloc[-1]
    else:
        rec_ts = ts.iloc[recovered_rows.index[0]]

    recovery_minutes = (rec_ts - peak_ts).total_seconds() / 60.0
    return round(float(max(0.0, recovery_minutes)), 1)


def calculate_sla_violation_duration_minutes(df_sim: pd.DataFrame) -> float:
    """
    Calculates total duration in minutes where SLA was breached.
    """
    if "sla_status" not in df_sim.columns or "timestamp" not in df_sim.columns:
        return 0.0

    ts = pd.to_datetime(df_sim["timestamp"])
    breached_mask = df_sim["sla_status"] == "breached"
    
    if not breached_mask.any():
        return 0.0

    # Calculate step time intervals in minutes
    step_diffs = ts.diff().dt.total_seconds().fillna(
        (ts.iloc[1] - ts.iloc[0]).total_seconds() if len(ts) > 1 else 900.0
    ) / 60.0

    violation_minutes = step_diffs[breached_mask].sum()
    return round(float(violation_minutes), 1)


def run_formal_sla_experiment(seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes formal SLA experiment across 5 strategies x 7 scenarios (35 runs),
    calculating recovery times, SLA violation durations, and before-vs-after deltas.
    """
    sla_cfg = load_sla_config()
    sla_targets = sla_cfg.get("sla_targets", {})
    sla_lat_target = sla_targets.get("p95_latency_target_ms", 500.0)
    sla_err_target = sla_targets.get("error_rate_target", 0.01)

    exp_records = []

    print("=" * 90)
    print("  PEAK-DEMAND CAPACITY SIMULATOR -- FORMAL SLA EXPERIMENT")
    print("=" * 90)
    print(f"  SLA Targets: p95 Latency <= {sla_lat_target:.0f}ms | Error Rate <= {sla_err_target*100:.1f}%")
    print("-" * 90)

    for sc_key in SCENARIO_KEYS:
        for st_key in STRATEGY_KEYS:
            res = run_strategy(st_key, sc_key, seed=seed)

            # Generate raw simulation DataFrame for recovery time and violation duration calculations
            df_sc = generate_scenario(sc_key, seed=seed)
            df_sim, summary = run_simulation(
                workload_scenario=df_sc,
                initial_instances=res["initial_instances"],
                max_instances=res["max_instance_cap"],
                capacity_per_instance=500.0,
                sla_latency_target_ms=sla_lat_target,
                sla_error_target_rate=sla_err_target,
                seed=seed
            )

            rec_time_min = calculate_recovery_time_minutes(df_sim)
            viol_dur_min = calculate_sla_violation_duration_minutes(df_sim)

            rec = {
                "scenario": sc_key,
                "strategy": st_key,
                "peak_demand": res["peak_demand"],
                "peak_capacity": res["total_capacity_rpm"],
                "peak_instances": res["peak_instances"],
                "max_utilisation": res["max_utilisation_pct"],
                "max_queue": res["max_queue"],
                "max_p95_latency": res["max_p95_latency"],
                "max_error_rate": res["max_error_rate"],
                "unmet_requests": res["unmet_requests"],
                "scaling_actions": res["scaling_actions"],
                "recovery_time": rec_time_min,
                "sla_compliance": res["sla_compliance_pct"],
                "sla_violation_duration": viol_dur_min
            }
            exp_records.append(rec)

    df_exp = pd.DataFrame(exp_records)
    EXP_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_exp.to_csv(EXP_RESULTS_CSV, index=False)
    print(f"[OK] SLA experiment results exported to: {EXP_RESULTS_CSV}")

    # Generate Before-vs-After Comparison
    df_before_after = compute_before_after_comparison(df_exp)
    df_before_after.to_csv(BEFORE_AFTER_CSV, index=False)
    print(f"[OK] Final Before-vs-After comparison exported to: {BEFORE_AFTER_CSV}")

    return df_exp, df_before_after


def compute_before_after_comparison(df_exp: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Before (AVERAGE_DEMAND) vs After (PEAK_DEMAND, SAFETY_MARGIN, DYNAMIC_SCALING, DISASTER_AWARE)
    delta metrics and percentage improvements across all scenarios.
    """
    before_after_records = []

    for sc_key in SCENARIO_KEYS:
        sc_df = df_exp[df_exp["scenario"] == sc_key]
        before_row = sc_df[sc_df["strategy"] == "AVERAGE_DEMAND"].iloc[0]

        for st_key in [s for s in STRATEGY_KEYS if s != "AVERAGE_DEMAND"]:
            after_row = sc_df[sc_df["strategy"] == st_key].iloc[0]

            cap_diff = after_row["peak_capacity"] - before_row["peak_capacity"]
            cap_pct = (cap_diff / max(1.0, before_row["peak_capacity"])) * 100.0

            q_diff = after_row["max_queue"] - before_row["max_queue"]
            q_pct = (q_diff / max(1.0, before_row["max_queue"])) * 100.0

            lat_diff = after_row["max_p95_latency"] - before_row["max_p95_latency"]
            lat_pct = (lat_diff / max(1.0, before_row["max_p95_latency"])) * 100.0

            err_diff = after_row["max_error_rate"] - before_row["max_error_rate"]
            err_pct = (err_diff / max(0.001, before_row["max_error_rate"])) * 100.0

            sla_diff = after_row["sla_compliance"] - before_row["sla_compliance"]
            sla_pct = (sla_diff / max(1.0, before_row["sla_compliance"])) * 100.0

            unmet_diff = after_row["unmet_requests"] - before_row["unmet_requests"]
            unmet_pct = (unmet_diff / max(1.0, before_row["unmet_requests"])) * 100.0 if before_row["unmet_requests"] > 0 else 0.0

            inst_diff = after_row["peak_instances"] - before_row["peak_instances"]
            inst_pct = (inst_diff / max(1.0, before_row["peak_instances"])) * 100.0

            act_diff = after_row["scaling_actions"] - before_row["scaling_actions"]

            before_after_records.append({
                "scenario": sc_key,
                "strategy_after": st_key,
                "before_strategy": "AVERAGE_DEMAND",
                "before_sla_compliance": before_row["sla_compliance"],
                "after_sla_compliance": after_row["sla_compliance"],
                "sla_difference": round(sla_diff, 1),
                "sla_change_pct": round(sla_pct, 1),
                "before_peak_capacity": before_row["peak_capacity"],
                "after_peak_capacity": after_row["peak_capacity"],
                "capacity_difference": round(cap_diff, 1),
                "capacity_change_pct": round(cap_pct, 1),
                "before_max_queue": before_row["max_queue"],
                "after_max_queue": after_row["max_queue"],
                "queue_difference": round(q_diff, 1),
                "queue_change_pct": round(q_pct, 1),
                "before_max_p95_latency": before_row["max_p95_latency"],
                "after_max_p95_latency": after_row["max_p95_latency"],
                "latency_difference": round(lat_diff, 1),
                "latency_change_pct": round(lat_pct, 1),
                "before_max_error_rate": before_row["max_error_rate"],
                "after_max_error_rate": after_row["max_error_rate"],
                "error_rate_difference": round(err_diff, 2),
                "error_rate_change_pct": round(err_pct, 1),
                "before_unmet_requests": before_row["unmet_requests"],
                "after_unmet_requests": after_row["unmet_requests"],
                "unmet_request_difference": round(unmet_diff, 1),
                "unmet_request_change_pct": round(unmet_pct, 1),
                "before_peak_instances": before_row["peak_instances"],
                "after_peak_instances": after_row["peak_instances"],
                "instance_difference": inst_diff,
                "instance_change_pct": round(inst_pct, 1),
                "before_scaling_actions": before_row["scaling_actions"],
                "after_scaling_actions": after_row["scaling_actions"],
                "scaling_action_difference": act_diff
            })

    return pd.DataFrame(before_after_records)


if __name__ == "__main__":
    run_formal_sla_experiment()
