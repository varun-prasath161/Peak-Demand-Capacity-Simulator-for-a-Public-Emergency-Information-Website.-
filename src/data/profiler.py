"""
Statistical Profiler Module
===========================
Computes comprehensive statistical profile of emergency website traffic data,
including burst ratios, latency percentiles, SLA breach rates, queue metrics,
and workload characterisations across event types and regions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_dataset_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes a complete statistical profile dictionary from a dataset DataFrame.
    """
    df = df.copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        
        # Inter-arrival time calculations in minutes
        time_diffs = df["timestamp"].diff().dt.total_seconds().dropna() / 60.0
        inter_arrival_stats = {
            "mean_interval_min": round(float(time_diffs.mean()), 2),
            "median_interval_min": round(float(time_diffs.median()), 2),
            "min_interval_min": round(float(time_diffs.min()), 2),
            "max_interval_min": round(float(time_diffs.max()), 2),
        }
    else:
        inter_arrival_stats = {}

    rpm = df["requests_per_minute"].dropna()
    mean_rpm = float(rpm.mean())
    max_rpm = float(rpm.max())
    burst_ratio = round(max_rpm / mean_rpm, 2) if mean_rpm > 0 else 0.0

    profile = {
        "overview": {
            "total_records": len(df),
            "start_time": str(df["timestamp"].min()) if "timestamp" in df.columns else "N/A",
            "end_time": str(df["timestamp"].max()) if "timestamp" in df.columns else "N/A",
            "columns": len(df.columns),
            "missing_values_total": int(df.isnull().sum().sum()),
        },
        "traffic_statistics": {
            "mean_rpm": round(mean_rpm, 1),
            "std_rpm": round(float(rpm.std()), 1),
            "min_rpm": round(float(rpm.min()), 1),
            "p50_rpm": round(float(rpm.quantile(0.50)), 1),
            "p75_rpm": round(float(rpm.quantile(0.75)), 1),
            "p95_rpm": round(float(rpm.quantile(0.95)), 1),
            "p99_rpm": round(float(rpm.quantile(0.99)), 1),
            "max_rpm": round(max_rpm, 1),
            "burst_ratio": burst_ratio,
        },
        "inter_arrival_time": inter_arrival_stats,
        "performance_and_sla": {
            "avg_latency_ms": round(float(df["average_latency_ms"].dropna().mean()), 2),
            "p95_latency_ms": round(float(df["p95_latency_ms"].dropna().quantile(0.95)), 2),
            "p99_latency_ms": round(float(df["p99_latency_ms"].dropna().quantile(0.99)), 2),
            "max_latency_ms": round(float(df["average_latency_ms"].dropna().max()), 2),
            "mean_error_rate_pct": round(float(df["error_rate"].dropna().mean() * 100), 3),
            "max_error_rate_pct": round(float(df["error_rate"].dropna().max() * 100), 3),
            "sla_breach_count": int((df["sla_status"] == "breached").sum()),
            "sla_breach_rate_pct": round(float((df["sla_status"] == "breached").mean() * 100), 2),
        },
        "infrastructure": {
            "avg_cpu_util_pct": round(float(df["cpu_utilisation"].dropna().mean()), 2),
            "max_cpu_util_pct": round(float(df["cpu_utilisation"].dropna().max()), 2),
            "avg_memory_util_pct": round(float(df["memory_utilisation"].dropna().mean()), 2),
            "max_memory_util_pct": round(float(df["memory_utilisation"].dropna().max()), 2),
            "avg_queue_depth": round(float(df["queue_depth"].dropna().mean()), 2),
            "max_queue_depth": round(float(df["queue_depth"].dropna().max()), 2),
            "scale_out_count": int((df["scaling_action"] == "scale_out").sum()),
            "scale_in_count": int((df["scaling_action"] == "scale_in").sum()),
        }
    }
    return profile


def compute_event_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Computes statistical summary broken down by event_type."""
    if "event_type" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("event_type").agg(
        record_count=("requests_per_minute", "count"),
        mean_rpm=("requests_per_minute", "mean"),
        max_rpm=("requests_per_minute", "max"),
        avg_cpu_pct=("cpu_utilisation", "mean"),
        max_queue=("queue_depth", "max"),
        avg_latency_ms=("average_latency_ms", "mean"),
        p95_latency_ms=("p95_latency_ms", "mean"),
        sla_breach_rate_pct=("sla_status", lambda x: (x == "breached").mean() * 100)
    ).reset_index()

    grouped["mean_rpm"] = grouped["mean_rpm"].round(1)
    grouped["max_rpm"] = grouped["max_rpm"].round(1)
    grouped["avg_cpu_pct"] = grouped["avg_cpu_pct"].round(1)
    grouped["max_queue"] = grouped["max_queue"].round(1)
    grouped["avg_latency_ms"] = grouped["avg_latency_ms"].round(1)
    grouped["p95_latency_ms"] = grouped["p95_latency_ms"].round(1)
    grouped["sla_breach_rate_pct"] = grouped["sla_breach_rate_pct"].round(2)

    return grouped.sort_values("max_rpm", ascending=False)
