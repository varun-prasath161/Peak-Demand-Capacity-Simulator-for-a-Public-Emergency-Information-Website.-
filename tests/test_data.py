"""
Unit Tests for Data Module
===========================
Tests synthetic dataset generation, loading, cleaning, and profiling.
Uses Python standard library unittest.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.generate_dataset import generate_dataset
from src.data.loader import load_raw_data, load_processed_data, validate_schema
from src.data.cleaner import clean_dataset, process_and_save_dataset
from src.data.profiler import compute_dataset_profile, compute_event_breakdown


class TestDataModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Generate raw dataset once for all tests to run fast."""
        cls.df_raw = generate_dataset()
        cls.df_clean, cls.audit = clean_dataset(cls.df_raw)

    def test_generate_dataset_shape_and_columns(self):
        """Verify that dataset generator creates ~3800-3900 rows and 33 columns."""
        self.assertTrue(3800 <= len(self.df_raw) <= 3900, f"Expected 3800-3900 rows, got {len(self.df_raw)}")
        self.assertEqual(len(self.df_raw.columns), 33, f"Expected 33 columns, got {len(self.df_raw.columns)}")
        self.assertIn("timestamp", self.df_raw.columns)
        self.assertIn("requests_per_minute", self.df_raw.columns)
        self.assertIn("sla_status", self.df_raw.columns)

    def test_schema_validation(self):
        """Verify schema validator detects missing or valid columns."""
        is_valid, missing, extra = validate_schema(self.df_raw)
        self.assertTrue(is_valid, f"Schema validation failed. Missing: {missing}")
        self.assertEqual(len(missing), 0)

    def test_cleaning_pipeline(self):
        """Verify that cleaner removes all anomalies."""
        # 1. No nulls remaining in cleaned dataset
        self.assertEqual(self.df_clean.isnull().sum().sum(), 0, "Cleaned dataset still contains NaN values")

        # 2. Non-negative checks
        non_neg_cols = ["requests_per_minute", "concurrent_users", "queue_depth"]
        for col in non_neg_cols:
            self.assertTrue((self.df_clean[col] >= 0).all(), f"Found negative values in column {col}")

        # 3. Utilization bounded between 0 and 100
        for col in ["cpu_utilisation", "memory_utilisation"]:
            self.assertTrue((self.df_clean[col] >= 0.0).all() and (self.df_clean[col] <= 100.0).all(), f"{col} out of range [0, 100]")

        # 4. Total capacity recalculation check
        expected_cap = self.df_clean["available_instances"] * self.df_clean["instance_capacity_rpm"]
        self.assertTrue((self.df_clean["total_capacity_rpm"] == expected_cap).all(), "Total capacity mismatch")

        # 5. Audit summary metrics present
        self.assertGreater(self.audit["cleaned_rows"], 0)
        self.assertEqual(self.audit["missing_after"], 0)


    def test_statistical_profiler(self):
        """Verify that profiler computes valid summary metrics."""
        profile = compute_dataset_profile(self.df_clean)

        self.assertEqual(profile["overview"]["total_records"], len(self.df_clean))
        self.assertGreater(profile["traffic_statistics"]["mean_rpm"], 0)
        self.assertGreater(profile["traffic_statistics"]["burst_ratio"], 1.0)
        self.assertGreaterEqual(profile["performance_and_sla"]["sla_breach_rate_pct"], 0.0)

        breakdown = compute_event_breakdown(self.df_clean)
        self.assertFalse(breakdown.empty)
        self.assertIn("event_type", breakdown.columns)
        self.assertTrue(set(breakdown["event_type"]).issubset({"normal", "seasonal", "breaking_news", "disaster", "extreme_disaster"}))


if __name__ == "__main__":
    unittest.main()
