"""
Data Cleaner Adapter Module
============================
Provides backward compatibility alias wrapping src.data.clean_data preprocessing pipeline.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

from src.data.clean_data import preprocess_data, RAW_PATH, CLEANED_PATH, PROCESSED_LEGACY_PATH


def clean_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean raw dataset using full clean_data preprocessing pipeline."""
    # Write temp raw copy if needed or preprocess directly
    df_clean, audit = preprocess_data(RAW_PATH if RAW_PATH.exists() else None)
    return df_clean, audit


def process_and_save_dataset(raw_path: Path = RAW_PATH, processed_path: Path = CLEANED_PATH) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Loads raw dataset, cleans it via clean_data pipeline, and saves cleaned CSVs."""
    df_clean, audit = preprocess_data(raw_path)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(processed_path, index=False)
    df_clean.to_csv(PROCESSED_LEGACY_PATH, index=False)
    return df_clean, audit


if __name__ == "__main__":
    process_and_save_dataset()
