"""
Workload Scenario Engine
========================
Generates realistic event-driven demand profiles for emergency website capacity planning.

Supported Workload Scenarios:
1. NORMAL                   (1.0x baseline)
2. SEASONAL_PEAK            (1.5x - 2.0x baseline)
3. BREAKING_NEWS            (2.0x - 3.0x baseline)
4. DISASTER_PEAK            (3.0x - 5.0x baseline)
5. EXTREME_DISASTER         (5.0x - 8.5x baseline)
6. DISASTER_BREAKING_NEWS   (4.0x - 7.0x compound baseline)
7. DISASTER_SEASONAL        (4.0x - 6.5x compound baseline)

Key Features:
- 3-Phase demand curves: Ramp-Up (onset), Sustained Peak, and Exponential Recovery.
- Seeded random generation for 100% deterministic reproducibility.
- Integrates baseline traffic profiles from historical datasets.
- Fully configurable via data/scenarios/advanced_scenarios.json & scenario_config.json.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ADVANCED_CONFIG_PATH = PROJECT_ROOT / "data" / "scenarios" / "advanced_scenarios.json"
LEGACY_CONFIG_PATH = PROJECT_ROOT / "data" / "scenarios" / "scenario_config.json"
DEFAULT_BASELINE_CSV = PROJECT_ROOT / "data" / "processed" / "emergency_load_cleaned.csv"


def load_scenario_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load scenario configuration JSON file (prefers advanced_scenarios.json)."""
    if config_path:
        path = config_path
    elif ADVANCED_CONFIG_PATH.exists():
        path = ADVANCED_CONFIG_PATH
    else:
        path = LEGACY_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Scenario configuration file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_baseline_rpm(baseline_df: Optional[pd.DataFrame] = None, default_rpm: float = 800.0) -> float:
    """Extract median baseline RPM from processed dataset or default."""
    if baseline_df is not None and not baseline_df.empty and "requests_per_minute" in baseline_df.columns:
        normal_df = baseline_df[baseline_df.get("event_type", "normal") == "normal"]
        if not normal_df.empty:
            return float(normal_df["requests_per_minute"].median())
        return float(baseline_df["requests_per_minute"].median())
    return default_rpm


def generate_scenario(
    scenario_name: str,
    baseline_df: Optional[pd.DataFrame] = None,
    config_path: Optional[Path] = None,
    seed: int = 42,
    custom_multiplier: Optional[float] = None,
    duration_hours: Optional[float] = None,
    start_time: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Generates a deterministic workload scenario time-series DataFrame with Ramp-Up, Peak, and Recovery phases.

    Parameters:
        scenario_name: Name of scenario (e.g., 'NORMAL', 'DISASTER_BREAKING_NEWS', 'DISASTER_SEASONAL').
        baseline_df: Optional historical DataFrame to derive baseline RPM.
        config_path: Optional path to JSON config file.
        seed: Random seed for deterministic generation.
        custom_multiplier: Optional override for traffic multiplier.
        duration_hours: Optional override for scenario duration in hours.
        start_time: Optional start datetime (defaults to 2025-10-01 00:00:00).
    """
    config = load_scenario_config(config_path)
    scenarios_cfg = config.get("scenarios", {})

    scenario_key = scenario_name.upper()
    if scenario_key not in scenarios_cfg:
        raise ValueError(f"Unknown scenario '{scenario_name}'. Valid options: {list(scenarios_cfg.keys())}")

    sc_cfg = scenarios_cfg[scenario_key]
    assumptions = config.get("assumptions", {})

    rng = np.random.default_rng(seed)

    # Base parameters
    base_rpm = _get_baseline_rpm(baseline_df, assumptions.get("baseline_rpm_default", 800.0))
    peak_mult = custom_multiplier or sc_cfg.get("multiplier_peak", sc_cfg.get("traffic_multiplier", 1.0))
    dur_h = duration_hours or sc_cfg.get("duration_hours", 24.0)
    step_min = sc_cfg.get("sampling_interval_minutes", 15 if "DISASTER" in scenario_key or "BREAKING" in scenario_key else 60)

    start_dt = start_time or datetime(2025, 10, 1, 0, 0)
    total_steps = int(np.ceil(dur_h * 60 / step_min)) + 1
    timestamps = [start_dt + timedelta(minutes=i * step_min) for i in range(total_steps)]

    # Phase boundaries
    r_ramp = sc_cfg.get("ramp_up_ratio", 0.10)
    r_peak = sc_cfg.get("peak_ratio", 0.60)

    n_ramp = max(1, int(np.round(total_steps * r_ramp)))
    n_peak = max(1, int(np.round(total_steps * r_peak)))
    n_recovery = max(1, total_steps - n_ramp - n_peak)

    multipliers = np.zeros(total_steps)
    phases = []

    for i in range(total_steps):
        if i < n_ramp:
            # Phase 1 – Ramp Up Phase: Traffic gradually/rapidly increases to peak multiplier
            ramp_prog = (i + 1) / max(1, n_ramp)
            if "DISASTER" in scenario_key or "BREAKING" in scenario_key:
                # Fast non-linear ramp up for emergency shock
                mult = 1.0 + (peak_mult - 1.0) * (ramp_prog ** 0.35)
            else:
                # Smooth sinusoidal ramp up
                mult = 1.0 + (peak_mult - 1.0) * (0.5 * (1.0 - np.cos(np.pi * ramp_prog)))
            phases.append("ramp_up")

        elif i < (n_ramp + n_peak):
            # Phase 2 – Peak Phase: Traffic reaches and sustains scenario peak with micro-jitter
            peak_prog = (i - n_ramp) / max(1, n_peak)
            jitter = 1.0 + 0.06 * rng.standard_normal()
            if "DISASTER" in scenario_key:
                # Secondary aftershock oscillation
                aftershock = 0.12 * peak_mult * max(0.0, np.sin(peak_prog * 10))
                mult = (peak_mult + aftershock) * np.clip(jitter, 0.85, 1.15)
            else:
                mult = peak_mult * np.clip(jitter, 0.90, 1.10)
            phases.append("peak")

        else:
            # Phase 3 – Recovery Phase: Traffic gradually decreases back toward baseline
            rec_step = i - n_ramp - n_peak
            rec_prog = (rec_step + 1) / max(1, n_recovery)
            decay = np.exp(-3.0 * rec_prog)
            mult = 1.0 + (peak_mult - 1.0) * decay
            phases.append("recovery")

        multipliers[i] = max(0.8, mult)

    # Diurnal variation wave
    hours = np.array([t.hour + t.minute / 60.0 for t in timestamps])
    diurnal_wave = 1.0 + 0.15 * np.sin((hours - 8) * np.pi / 12)

    # Stochastic noise
    noise = np.clip(1.0 + 0.04 * rng.standard_normal(total_steps), 0.90, 1.10)

    # Compute final RPM and concurrency
    requests_per_minute = np.round(base_rpm * multipliers * diurnal_wave * noise, 1)
    traffic_multipliers = np.round(requests_per_minute / base_rpm, 3)

    session_dur = assumptions.get("baseline_session_duration_minutes", 3.5)
    concurrent_users = np.maximum(1, np.round(requests_per_minute * session_dur / 60.0).astype(int))

    df = pd.DataFrame({
        "timestamp": timestamps,
        "scenario_name": scenario_key,
        "event_type": sc_cfg.get("event_type", "normal"),
        "event_severity": sc_cfg.get("event_severity", "none"),
        "phase": phases,
        "requests_per_minute": requests_per_minute,
        "concurrent_users": concurrent_users,
        "traffic_multiplier": traffic_multipliers,
        "scaling_delay_seconds": sc_cfg.get("scaling_delay_seconds", 180),
        "expected_queue_growth_rpm": sc_cfg.get("expected_queue_growth_rpm", 0.0),
        "duration_minutes": float(dur_h * 60)
    })

    return df


def calculate_peak_demand(scenario_df: pd.DataFrame) -> float:
    """Calculate the maximum requests per minute (peak demand) in a scenario."""
    if "requests_per_minute" not in scenario_df.columns:
        raise KeyError("requests_per_minute column not found in scenario DataFrame")
    return float(scenario_df["requests_per_minute"].max())


def calculate_scenario_duration(scenario_df: pd.DataFrame) -> float:
    """Calculate the duration of a scenario in hours."""
    if "timestamp" not in scenario_df.columns:
        raise KeyError("timestamp column not found in scenario DataFrame")
    ts = pd.to_datetime(scenario_df["timestamp"])
    return round(float((ts.max() - ts.min()).total_seconds() / 3600.0), 2)


def calculate_traffic_multiplier(scenario_df: pd.DataFrame) -> float:
    """Calculate the peak traffic multiplier relative to baseline."""
    if "traffic_multiplier" not in scenario_df.columns:
        raise KeyError("traffic_multiplier column not found in scenario DataFrame")
    return float(scenario_df["traffic_multiplier"].max())


def get_scenario_summary(scenario_df: pd.DataFrame) -> Dict[str, Any]:
    """Get a structured summary dictionary of key scenario metrics."""
    sc_name = scenario_df["scenario_name"].iloc[0] if "scenario_name" in scenario_df.columns else "UNKNOWN"
    return {
        "scenario_name": sc_name,
        "peak_requests_per_minute": calculate_peak_demand(scenario_df),
        "duration_hours": calculate_scenario_duration(scenario_df),
        "traffic_multiplier": calculate_traffic_multiplier(scenario_df),
        "estimated_peak_concurrency": int(scenario_df["concurrent_users"].max()),
        "event_severity": scenario_df["event_severity"].iloc[0] if "event_severity" in scenario_df.columns else "none"
    }


def compare_all_scenarios(
    baseline_df: Optional[pd.DataFrame] = None,
    seed: int = 42,
    include_compound: bool = False
) -> List[Dict[str, Any]]:
    """
    Generates workload scenarios and returns summary metrics.
    By default returns 5 baseline scenarios; set include_compound=True to return all 7 scenarios.
    """
    if include_compound:
        scenario_keys = [
            "NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK",
            "EXTREME_DISASTER", "DISASTER_BREAKING_NEWS", "DISASTER_SEASONAL"
        ]
    else:
        scenario_keys = ["NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"]

    summaries = []

    print("=" * 85)
    print("  PEAK-DEMAND CAPACITY SIMULATOR -- WORKLOAD SCENARIO COMPARISON")
    print("=" * 85)
    print(f"{'Scenario Name':<30s} {'Peak RPM':>12s} {'Duration (h)':>14s} {'Multiplier':>12s} {'Concurrency':>14s}")
    print("-" * 85)

    for name in scenario_keys:
        df_sc = generate_scenario(name, baseline_df=baseline_df, seed=seed)
        summary = get_scenario_summary(df_sc)
        summaries.append(summary)
        print(f"{summary['scenario_name']:<30s} {summary['peak_requests_per_minute']:>12,.1f} {summary['duration_hours']:>14.1f} {summary['traffic_multiplier']:>11.2f}x {summary['estimated_peak_concurrency']:>14,d}")

    print("=" * 85)
    return summaries


if __name__ == "__main__":
    baseline = pd.read_csv(DEFAULT_BASELINE_CSV) if DEFAULT_BASELINE_CSV.exists() else None
    compare_all_scenarios(baseline, include_compound=True)
