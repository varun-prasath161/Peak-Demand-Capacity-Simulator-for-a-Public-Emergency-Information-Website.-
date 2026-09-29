#!/usr/bin/env python3
"""
Synthetic Emergency Website Load Dataset Generator
===================================================
Generates a realistic synthetic dataset representing ~10 months of
operational behaviour for a public emergency-information website.

Features:
    - Deterministic (seeded) random generation for reproducibility
    - Realistic inter-variable relationships (not independent randoms)
    - Diurnal traffic patterns with day-of-week variation
    - Five event classes: normal, seasonal, breaking_news, disaster, extreme_disaster
    - Sharp disaster spikes (not smooth increases)
    - Queues build when demand exceeds capacity
    - Latency degrades non-linearly as utilisation approaches 100%
    - Error rate spikes under overload
    - Scaling occurs with realistic delays and bounded capacity
    - Intentional anomalies for downstream data-cleaning exercises

Usage:
    python src/data/generate_dataset.py

Output:
    data/raw/emergency_load_raw.csv
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
OUTPUTS = PROJECT_ROOT / "outputs"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — All constants that control the synthetic data
# ═══════════════════════════════════════════════════════════════════════════════

SEED = 42

# --- Time window ---
START_DATE = datetime(2025, 1, 1, 0, 0)
END_DATE   = datetime(2025, 10, 31, 22, 0)
BASE_INTERVAL_H    = 2       # hours between records (normal periods)
EVENT_INTERVAL_MIN = 30      # minutes between records (disaster periods)

# --- Infrastructure ---
BASE_INSTANCES    = 10       # always-on server count
MAX_INSTANCES     = 50       # hard ceiling
INSTANCE_CAP_RPM  = 500      # requests-per-minute each instance can serve
BASELINE_RPM      = 800      # typical peak-hour request rate

# --- SLA thresholds ---
SLA_LATENCY_MS  = 500.0
SLA_ERROR_RATE  = 0.01

# --- Diurnal traffic shape (24 hourly multipliers, 0-indexed) ---
DIURNAL = np.array([
    0.15, 0.12, 0.10, 0.08, 0.08, 0.12,   # 00-05  night
    0.25, 0.45, 0.70, 0.88, 1.00, 0.95,   # 06-11  morning peak
    0.90, 0.95, 1.00, 0.95, 0.85, 0.75,   # 12-17  afternoon peak
    0.65, 0.55, 0.45, 0.35, 0.28, 0.20,   # 18-23  evening decline
])

# --- Day-of-week multipliers (Monday=0 … Sunday=6) ---
DOW_FACTOR = np.array([1.00, 1.00, 1.00, 1.00, 0.95, 0.80, 0.75])

# ═══════════════════════════════════════════════════════════════════════════════
# EVENT SCHEDULE
# Each tuple: (day_offset, duration_hours, event_type, severity,
#               peak_traffic_multiplier, affected_region, high_freq_sampling)
# ═══════════════════════════════════════════════════════════════════════════════

EVENTS = [
    # ── Seasonal (smooth, no high-freq sampling) ────────────────────────────
    (0,   72, "seasonal",  "low",      1.5,  "central",   False),
    (44,  48, "seasonal",  "low",      1.3,  "central",   False),
    (89,  48, "seasonal",  "low",      1.4,  "central",   False),
    (151, 72, "seasonal",  "medium",   1.8,  "central",   False),
    (185, 48, "seasonal",  "medium",   2.0,  "central",   False),
    (244, 48, "seasonal",  "low",      1.4,  "central",   False),

    # ── Breaking news (sharp moderate spikes, normal sampling) ──────────────
    (28,   6,  "breaking_news", "medium", 4.0,  "northeast", False),
    (65,   8,  "breaking_news", "high",   5.5,  "southeast", False),
    (105,  4,  "breaking_news", "medium", 3.5,  "midwest",   False),
    (138, 10,  "breaking_news", "high",   6.0,  "west",      False),
    (172,  3,  "breaking_news", "low",    3.0,  "southwest", False),
    (198,  6,  "breaking_news", "medium", 4.5,  "northeast", False),
    (228, 12,  "breaking_news", "high",   7.0,  "central",   False),
    (258,  4,  "breaking_news", "medium", 3.0,  "southeast", False),
    (278,  8,  "breaking_news", "high",   5.5,  "midwest",   False),

    # ── Disaster (sharp spikes, high-frequency 30-min sampling) ─────────────
    (52,  18, "disaster", "high",     12.0, "northeast",  True),   # winter storm
    (92,  14, "disaster", "critical", 15.0, "midwest",    True),   # tornado
    (158, 28, "disaster", "critical", 18.0, "southeast",  True),   # hurricane
    (208, 16, "disaster", "high",     10.0, "west",       True),   # wildfire
    (248, 16, "disaster", "critical", 14.0, "southwest",  True),   # flood

    # ── Extreme disaster (catastrophic, high-frequency sampling) ────────────
    (118, 36, "extreme_disaster", "critical", 35.0, "southeast", True),  # Cat-5 hurricane
    (268, 28, "extreme_disaster", "critical", 45.0, "west",      True),  # major earthquake
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def interpolate_diurnal(hour_frac):
    """Linearly interpolate the diurnal pattern for fractional hours."""
    h0 = int(hour_frac) % 24
    h1 = (h0 + 1) % 24
    frac = hour_frac - int(hour_frac)
    return DIURNAL[h0] * (1.0 - frac) + DIURNAL[h1] * frac


def active_event(timestamp):
    """
    Return the dominant event at *timestamp*, or None.
    If multiple events overlap, the one with the highest peak multiplier wins.
    Returns: (day_off, dur_h, etype, severity, peak_mult, region, hf, progress)
    """
    best = None
    for day_off, dur_h, etype, sev, peak, region, hf in EVENTS:
        ev_start = START_DATE + timedelta(days=day_off)
        ev_end   = ev_start  + timedelta(hours=dur_h)
        if ev_start <= timestamp < ev_end:
            progress = (timestamp - ev_start).total_seconds() / (dur_h * 3600)
            if best is None or peak > best[4]:
                best = (day_off, dur_h, etype, sev, peak, region, hf, progress)
    return best


def spike_profile(progress, peak, event_type, rng):
    """
    Compute the instantaneous traffic multiplier given how far through
    an event we are (progress ∈ [0, 1]).

    Disaster / extreme_disaster events produce SHARP onsets (1-2 steps).
    Seasonal events produce smooth bell curves.
    """
    if event_type == "seasonal":
        # Gentle bell curve
        return 1.0 + (peak - 1.0) * np.sin(np.pi * progress)

    elif event_type == "breaking_news":
        # Fast rise, sustained, quick fall
        if progress < 0.10:
            return 1.0 + (peak - 1.0) * (progress / 0.10) ** 0.3
        elif progress < 0.70:
            jitter = 1.0 + 0.12 * rng.standard_normal()
            return peak * np.clip(jitter, 0.80, 1.20)
        else:
            decay = (1.0 - progress) / 0.30
            return 1.0 + (peak - 1.0) * decay ** 0.5

    else:  # disaster / extreme_disaster
        # ---- SHARP onset ----
        if progress < 0.03:
            # Near-vertical ramp (completes in 1-2 records)
            return 1.0 + (peak - 1.0) * (progress / 0.03) ** 0.25
        elif progress < 0.50:
            # Chaotic sustained peak
            jitter = 1.0 + 0.18 * rng.standard_normal()
            return peak * np.clip(jitter, 0.70, 1.30)
        elif progress < 0.80:
            # Declining with aftershock waves
            base_decay = peak * (1.0 - (progress - 0.50) / 0.60)
            aftershock = peak * 0.20 * max(0.0, np.sin(progress * 30))
            return max(1.5, base_decay + aftershock)
        else:
            # Tail return to baseline
            return max(1.0, peak * (1.0 - progress) * 2.5)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_dataset():
    """Generate the complete synthetic dataset and return a DataFrame."""

    rng = np.random.default_rng(SEED)

    # ── 1. Build timeline ───────────────────────────────────────────────────
    # Identify windows that need high-frequency sampling
    hf_windows = []
    for day_off, dur_h, etype, sev, peak, region, hf in EVENTS:
        if hf:
            hf_windows.append((
                START_DATE + timedelta(days=day_off),
                START_DATE + timedelta(days=day_off, hours=dur_h),
            ))

    timestamps = set()

    # Base 2-hour grid
    t = START_DATE
    while t <= END_DATE:
        timestamps.add(t)
        t += timedelta(hours=BASE_INTERVAL_H)

    # High-frequency 30-min grid during disaster windows
    for ws, we in hf_windows:
        t = ws
        while t <= we:
            timestamps.add(t)
            t += timedelta(minutes=EVENT_INTERVAL_MIN)

    timestamps = sorted(timestamps)
    n = len(timestamps)
    print(f"[1/10] Timeline generated: {n} timestamps "
          f"({timestamps[0].date()} to {timestamps[-1].date()})")

    # ── 2. Initialise DataFrame ─────────────────────────────────────────────
    df = pd.DataFrame({"timestamp": timestamps})

    # ── 3. Identification columns ───────────────────────────────────────────
    df["organisation_id"] = "GOV-EMERG-001"
    df["region"] = "central"                       # default, overridden per event
    df["service_id"] = rng.choice(
        ["portal-main", "api-data", "status-page"],
        size=n, p=[0.65, 0.25, 0.10],
    )
    print("[2/10] Identification columns assigned")

    # ── 4. Event assignment ─────────────────────────────────────────────────
    event_types      = ["normal"] * n
    event_severities = ["none"]   * n
    disaster_flags   = [False]    * n
    event_durations  = np.zeros(n)
    event_mults      = np.ones(n)
    seasonal_facts   = np.ones(n)
    regions          = list(df["region"])

    for i, ts in enumerate(timestamps):
        ev = active_event(ts)
        if ev is None:
            continue
        _, dur_h, etype, sev, peak, region, _, progress = ev

        event_types[i]      = etype
        event_severities[i] = sev
        regions[i]          = region
        event_durations[i]  = dur_h * 60.0

        if etype in ("disaster", "extreme_disaster"):
            disaster_flags[i] = True

        multiplier = spike_profile(progress, peak, etype, rng)

        if etype == "seasonal":
            seasonal_facts[i] = multiplier
        else:
            event_mults[i] = multiplier

    df["region"]               = regions
    df["event_type"]           = event_types
    df["event_severity"]       = event_severities
    df["seasonal_factor"]      = np.round(seasonal_facts, 4)
    df["disaster_event"]       = disaster_flags
    df["event_duration_minutes"] = event_durations
    print("[3/10] Events mapped to timeline")

    # ── 5. Traffic metrics ──────────────────────────────────────────────────
    hours = np.array([t.hour + t.minute / 60.0 for t in timestamps])
    dows  = np.array([t.weekday() for t in timestamps])

    diurnal_f = np.array([interpolate_diurnal(h) for h in hours])
    dow_f     = DOW_FACTOR[dows]
    noise     = np.clip(1.0 + 0.05 * rng.standard_normal(n), 0.85, 1.15)

    raw_rpm = (BASELINE_RPM * diurnal_f * dow_f
               * seasonal_facts * event_mults * noise)

    df["requests_per_minute"] = np.round(raw_rpm, 1)
    df["traffic_multiplier"]  = np.round(raw_rpm / BASELINE_RPM, 3)

    # Concurrent users ≈ RPM × avg_session_minutes / 60
    session_dur = np.clip(3.0 + 0.5 * rng.standard_normal(n), 1.5, 5.0)
    df["concurrent_users"] = np.maximum(
        1, np.round(raw_rpm * session_dur / 60.0).astype(int)
    )
    print("[4/10] Traffic metrics computed")

    # ── 6. Infrastructure simulation (stateful forward pass) ────────────────
    avail_inst    = np.full(n, BASE_INSTANCES, dtype=float)
    total_cap_arr = np.full(n, BASE_INSTANCES * INSTANCE_CAP_RPM, dtype=float)
    cpu_arr       = np.zeros(n)
    mem_arr       = np.zeros(n)
    q_depth       = np.zeros(n)
    q_growth      = np.zeros(n)
    q_wait        = np.zeros(n)
    sc_actions    = ["none"] * n
    sc_out        = np.zeros(n, dtype=int)
    sc_in         = np.zeros(n, dtype=int)
    sc_delay      = np.zeros(n, dtype=int)

    cur_inst    = float(BASE_INSTANCES)
    pend_out    = 0.0
    pend_in     = 0.0
    steps_out   = 0
    steps_in    = 0
    cooldown    = 0
    prev_queue  = 0.0

    for i in range(n):
        rpm = raw_rpm[i]

        # ---- Apply completed scaling actions ----
        if steps_out > 0:
            steps_out -= 1
            if steps_out == 0:
                cur_inst = min(MAX_INSTANCES, cur_inst + pend_out)
                pend_out = 0.0
        if steps_in > 0:
            steps_in -= 1
            if steps_in == 0:
                cur_inst = max(BASE_INSTANCES, cur_inst - pend_in)
                pend_in = 0.0

        if cooldown > 0:
            cooldown -= 1

        capacity = cur_inst * INSTANCE_CAP_RPM
        load     = rpm / capacity if capacity > 0 else 99.0

        # ---- CPU utilisation (non-linear) ----
        if load <= 0.70:
            cpu = load * 82.0 + rng.normal(0, 2.5)
        elif load <= 1.0:
            cpu = 57.4 + (load - 0.70) / 0.30 * 38.0 + rng.normal(0, 3.0)
        else:
            cpu = 95.0 + (load - 1.0) * 12.0 + rng.normal(0, 1.5)
        cpu = np.clip(cpu, 1.0, 99.8)

        # ---- Memory utilisation (correlated, smoother) ----
        mem = cpu * (0.55 + 0.18 * rng.random()) + rng.normal(0, 3.0)
        mem = np.clip(mem, 4.0, 98.0)

        # ---- Queue dynamics ----
        if i > 0:
            dt_min = (timestamps[i] - timestamps[i - 1]).total_seconds() / 60.0
        else:
            dt_min = BASE_INTERVAL_H * 60.0

        excess    = max(0.0, rpm - capacity)
        drain     = min(prev_queue, capacity * 0.08 * dt_min / 60.0)
        new_queue = max(0.0, prev_queue + excess * dt_min - drain)

        q_depth[i]  = round(new_queue, 1)
        q_growth[i] = round((new_queue - prev_queue) / max(dt_min, 1.0), 2)
        q_wait[i]   = round(min(new_queue / capacity * 60.0, 600.0)
                            if capacity > 0 else 0.0, 2)
        prev_queue   = new_queue

        avail_inst[i]    = cur_inst
        total_cap_arr[i] = capacity
        cpu_arr[i]       = round(cpu, 2)
        mem_arr[i]       = round(mem, 2)

        # ---- Scaling decisions ----
        action = "none"
        if cooldown == 0 and pend_out == 0 and pend_in == 0:
            if cpu > 75.0 and cur_inst < MAX_INSTANCES:
                needed = min(
                    MAX_INSTANCES - cur_inst,
                    max(2.0, np.ceil((rpm - capacity * 0.70) / INSTANCE_CAP_RPM))
                )
                pend_out  = needed
                steps_out = int(rng.integers(1, 4))        # 1-3 step delay
                delay_sec = int(steps_out * dt_min * 60)
                action    = "scale_out"
                sc_out[i]    = int(needed)
                sc_delay[i]  = delay_sec
                cooldown     = 2

            elif cpu < 30.0 and cur_inst > BASE_INSTANCES:
                removable = min(
                    cur_inst - BASE_INSTANCES,
                    max(1.0, np.floor((capacity - rpm * 1.3) / INSTANCE_CAP_RPM))
                )
                if removable > 0:
                    pend_in  = removable
                    steps_in = int(rng.integers(1, 3))
                    delay_sec = int(steps_in * dt_min * 60)
                    action   = "scale_in"
                    sc_in[i]    = int(removable)
                    sc_delay[i] = delay_sec
                    cooldown    = 3

        sc_actions[i] = action

    df["available_instances"]   = avail_inst.astype(int)
    df["max_instances"]         = MAX_INSTANCES
    df["instance_capacity_rpm"] = INSTANCE_CAP_RPM
    df["total_capacity_rpm"]    = total_cap_arr.astype(int)
    df["cpu_utilisation"]       = cpu_arr
    df["memory_utilisation"]    = mem_arr
    df["queue_depth"]           = q_depth
    df["queue_growth_rate"]     = q_growth
    df["queue_wait_time"]       = q_wait
    df["scaling_action"]        = sc_actions
    df["scale_out_instances"]   = sc_out
    df["scale_in_instances"]    = sc_in
    df["scaling_delay_seconds"] = sc_delay

    # Normalised load (can exceed 1.0 during overload)
    df["normalised_load"] = np.round(raw_rpm / total_cap_arr, 4)

    print("[5/10] Infrastructure simulation complete")
    print("[6/10] Queue dynamics computed")

    # ── 7. Performance metrics ──────────────────────────────────────────────
    load_arr = df["normalised_load"].values

    # Average latency: M/M/1-inspired — degrades sharply near capacity
    base_lat       = 25.0   # ms baseline at zero load
    effective_util = np.clip(load_arr, 0.0, 0.985)
    avg_lat = base_lat / (1.0 - effective_util) + rng.normal(0, 4, n)
    avg_lat = np.clip(avg_lat, 8.0, 12000.0)

    # Extra penalty for truly overloaded windows
    overloaded_mask = load_arr > 1.0
    n_over = overloaded_mask.sum()
    if n_over > 0:
        avg_lat[overloaded_mask] += (
            (load_arr[overloaded_mask] - 1.0) * 2500
            + rng.normal(0, 150, n_over)
        )
    avg_lat = np.clip(avg_lat, 8.0, 15000.0)

    df["average_latency_ms"] = np.round(avg_lat, 1)

    # Percentile latencies (realistic multipliers over mean)
    p95_mult = 2.0 + 0.6 * rng.random(n)
    p99_mult = 4.0 + 2.0 * rng.random(n)
    df["p95_latency_ms"] = np.round(avg_lat * p95_mult, 1)
    df["p99_latency_ms"] = np.round(avg_lat * p99_mult, 1)

    # Error rate: exponential blow-up above 85 % load
    base_err = 0.001
    err = np.where(
        load_arr < 0.85,
        base_err + rng.normal(0, 0.0004, n),
        base_err * np.exp(8.0 * (load_arr - 0.85)) + rng.normal(0, 0.002, n),
    )
    df["error_rate"] = np.round(np.clip(err, 0.0, 0.50), 5)
    print("[7/10] Performance metrics computed")

    # ── 8. SLA evaluation ───────────────────────────────────────────────────
    df["sla_target_latency_ms"]  = SLA_LATENCY_MS
    df["sla_target_error_rate"]  = SLA_ERROR_RATE
    df["sla_status"] = np.where(
        (df["average_latency_ms"] <= SLA_LATENCY_MS)
        & (df["error_rate"] <= SLA_ERROR_RATE),
        "met", "breached",
    )
    print("[8/10] SLA evaluation complete")

    # ── 9. Inject intentional anomalies ─────────────────────────────────────
    df = _inject_anomalies(df, rng)
    print("[9/10] Anomalies injected (missing values, negatives, "
          "impossible utilisation, inconsistent capacity, duplicate timestamps)")

    # ── 10. Final column ordering ───────────────────────────────────────────
    col_order = [
        # Identification
        "timestamp", "organisation_id", "region", "service_id",
        # Traffic
        "requests_per_minute", "concurrent_users",
        "traffic_multiplier", "normalised_load",
        # Event information
        "event_type", "event_severity", "seasonal_factor",
        "disaster_event", "event_duration_minutes",
        # System capacity
        "available_instances", "max_instances", "instance_capacity_rpm",
        "total_capacity_rpm", "cpu_utilisation", "memory_utilisation",
        # Queue
        "queue_depth", "queue_growth_rate", "queue_wait_time",
        # Performance
        "average_latency_ms", "p95_latency_ms", "p99_latency_ms", "error_rate",
        # Scaling
        "scaling_action", "scale_out_instances", "scale_in_instances",
        "scaling_delay_seconds",
        # Service level
        "sla_target_latency_ms", "sla_target_error_rate", "sla_status",
    ]
    df = df[col_order]
    print("[10/10] Columns ordered")

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY INJECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _inject_anomalies(df, rng):
    """
    Inject realistic data-quality issues so later modules must perform
    data cleaning and validation.
    """
    n = len(df)

    # 1 ── Missing values (~2 % in selected numeric columns) ─────────────────
    missing_targets = [
        "requests_per_minute", "concurrent_users", "cpu_utilisation",
        "memory_utilisation", "average_latency_ms", "queue_depth",
        "error_rate", "p95_latency_ms",
    ]
    for col in missing_targets:
        k = int(n * 0.018) + rng.integers(0, 5)         # ~1.8-2 %
        idx = rng.choice(n, size=k, replace=False)
        df.loc[idx, col] = np.nan

    # 2 ── Negative values in non-negative columns ──────────────────────────
    for col, count in [("requests_per_minute", 4), ("concurrent_users", 3),
                       ("queue_depth", 3)]:
        valid_idx = df[df[col].notna()].index.tolist()
        idx = rng.choice(valid_idx, size=count, replace=False)
        df.loc[idx, col] = -rng.uniform(1, 60, size=count).round(1)

    # 3 ── Impossible utilisation (> 100 %) ──────────────────────────────────
    for col in ["cpu_utilisation", "memory_utilisation"]:
        valid_idx = df[df[col].notna()].index.tolist()
        idx = rng.choice(valid_idx, size=3, replace=False)
        df.loc[idx, col] = rng.uniform(101, 118, size=3).round(2)

    # 4 ── Inconsistent capacity calculations ───────────────────────────────
    idx = rng.choice(n, size=6, replace=False)
    df.loc[idx, "total_capacity_rpm"] = (
        df.loc[idx, "total_capacity_rpm"] + rng.integers(200, 800, size=6)
    )

    # 5 ── Duplicate timestamps (3 duplicated rows) ─────────────────────────
    dup_idx = rng.choice(n, size=3, replace=False)
    dups = df.iloc[dup_idx].copy()
    for col in ["requests_per_minute", "cpu_utilisation"]:
        dups[col] = dups[col] + rng.normal(0, 3, size=3)
    df = pd.concat([df, dups], ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  SYNTHETIC DATASET GENERATOR")
    print("  Peak-Demand Capacity Simulator")
    print("=" * 65)

    df = generate_dataset()

    # ── Save CSV ────────────────────────────────────────────────────────────
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_RAW / "emergency_load_raw.csv"
    df.to_csv(csv_path, index=False)

    # ── Print summary ───────────────────────────────────────────────────────
    print()
    print("-" * 65)
    print(f"  Dataset saved to: {csv_path}")
    print(f"  Rows:    {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Missing: {df.isnull().sum().sum()}")
    print(f"  Events:  {(df['event_type'] != 'normal').sum()} non-normal records")
    print("-" * 65)

    # Event type breakdown
    print("\n  Event type distribution:")
    for etype, count in df["event_type"].value_counts().items():
        print(f"    {etype:<25s} {count:>6d}")

    print("\n  Generation complete.\n")
    return df


if __name__ == "__main__":
    main()
