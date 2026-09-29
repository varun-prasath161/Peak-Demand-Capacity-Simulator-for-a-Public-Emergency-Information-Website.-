"""
Data Loader Module for Peak-Demand Capacity Simulator
======================================================
Provides utility functions to load, validate, and filter raw and processed
emergency website operational datasets.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "emergency_load_raw.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "emergency_load_processed.csv"

EXPECTED_COLUMNS = [
    "timestamp", "organisation_id", "region", "service_id",
    "requests_per_minute", "concurrent_users", "traffic_multiplier", "normalised_load",
    "event_type", "event_severity", "seasonal_factor", "disaster_event", "event_duration_minutes",
    "available_instances", "max_instances", "instance_capacity_rpm", "total_capacity_rpm",
    "cpu_utilisation", "memory_utilisation", "queue_depth", "queue_growth_rate", "queue_wait_time",
    "average_latency_ms", "p95_latency_ms", "p99_latency_ms", "error_rate",
    "scaling_action", "scale_out_instances", "scale_in_instances", "scaling_delay_seconds",
    "sla_target_latency_ms", "sla_target_error_rate", "sla_status"
]


def load_raw_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load the raw, uncleaned dataset."""
    path = filepath or RAW_DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {path}. Run generation script first.")
    
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


def load_processed_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load the cleaned & processed dataset."""
    path = filepath or PROCESSED_DATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {path}. Run cleaner script first.")
    
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


def validate_schema(df: pd.DataFrame) -> Tuple[bool, list, list]:
    """
    Validate that a DataFrame matches the required simulator schema.
    Returns: (is_valid, missing_columns, extra_columns)
    """
    cols = list(df.columns)
    missing = [c for c in EXPECTED_COLUMNS if c not in cols]
    extra = [c for c in cols if c not in EXPECTED_COLUMNS]
    is_valid = len(missing) == 0
    return is_valid, missing, extra


def filter_dataset(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_types: Optional[list] = None,
    regions: Optional[list] = None
) -> pd.DataFrame:
    """Filter dataset by date range, event type, and region."""
    filtered = df.copy()
    
    if start_date:
        filtered = filtered[filtered["timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered["timestamp"] <= pd.to_datetime(end_date)]
    if event_types:
        filtered = filtered[filtered["event_type"].isin(event_types)]
    if regions:
        filtered = filtered[filtered["region"].isin(regions)]
        
    return filtered
