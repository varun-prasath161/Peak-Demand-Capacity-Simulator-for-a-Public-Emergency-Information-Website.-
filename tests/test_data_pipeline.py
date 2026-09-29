"""
Automated Data Pipeline Validation Tests
========================================
Tests the data engineering & preprocessing pipeline (src.data.clean_data),
verifying missing value handling, anomaly corrections, capacity formula math,
disaster spike preservation, quality flag generation, and report generation.
"""

import unittest
import os
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.clean_data import preprocess_data, generate_quality_report, RAW_PATH, CLEANED_PATH, REPORT_PATH


class TestDataPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run preprocessing pipeline once to test artifacts."""
        cls.df_clean, cls.audit = preprocess_data(RAW_PATH)
        generate_quality_report(cls.audit, REPORT_PATH)

    def test_file_outputs_exist(self):
        """Verify cleaned CSV and quality report exist on filesystem."""
        self.assertTrue(CLEANED_PATH.exists(), f"Cleaned CSV missing at {CLEANED_PATH}")
        self.assertTrue(REPORT_PATH.exists(), f"Data quality report missing at {REPORT_PATH}")

    def test_row_count_and_deduplication(self):
        """Verify row count logic and chronological sorting without duplicate timestamps."""
        self.assertEqual(len(self.df_clean), 3882)
        self.assertEqual(self.df_clean["timestamp"].duplicated().sum(), 0, "Duplicate timestamps found")
        self.assertTrue(self.df_clean["timestamp"].is_monotonic_increasing, "Timestamps not chronologically sorted")

    def test_zero_missing_values(self):
        """Verify no NaN/null values remain after domain-specific interpolation."""
        null_count = int(self.df_clean.isnull().sum().sum())
        self.assertEqual(null_count, 0, f"Cleaned dataset contains {null_count} null values")

    def test_non_negative_metrics(self):
        """Verify impossible negative values in operational metrics were corrected."""
        non_neg_cols = [
            "requests_per_minute", "concurrent_users", "queue_depth",
            "queue_wait_time", "average_latency_ms", "p95_latency_ms",
            "p99_latency_ms", "error_rate", "total_capacity_rpm"
        ]
        for col in non_neg_cols:
            self.assertTrue((self.df_clean[col] >= 0).all(), f"Negative values found in column: {col}")

    def test_utilisation_range_bounds(self):
        """Verify CPU and Memory utilisation strictly bounded in [0.0, 100.0]."""
        for col in ["cpu_utilisation", "memory_utilisation"]:
            self.assertTrue(
                (self.df_clean[col] >= 0.0).all() and (self.df_clean[col] <= 100.0).all(),
                f"{col} contains values outside range [0, 100]"
            )

    def test_capacity_formula_math(self):
        """Verify total_capacity_rpm = available_instances * instance_capacity_rpm."""
        expected_cap = self.df_clean["available_instances"] * self.df_clean["instance_capacity_rpm"]
        self.assertTrue(
            (self.df_clean["total_capacity_rpm"] == expected_cap).all(),
            "Total capacity does not match active instances * instance capacity"
        )

    def test_latency_percentile_ordering(self):
        """Verify mathematical latency constraint: p99 >= p95 >= average_latency_ms."""
        self.assertTrue(
            (self.df_clean["p95_latency_ms"] >= self.df_clean["average_latency_ms"]).all(),
            "Found p95_latency_ms < average_latency_ms"
        )
        self.assertTrue(
            (self.df_clean["p99_latency_ms"] >= self.df_clean["p95_latency_ms"]).all(),
            "Found p99_latency_ms < p95_latency_ms"
        )

    def test_disaster_spikes_preserved(self):
        """Verify high-traffic disaster surge records were preserved (not dropped as outliers)."""
        disaster_df = self.df_clean[self.df_clean["event_type"].isin(["disaster", "extreme_disaster"])]
        self.assertGreater(len(disaster_df), 300, "Disaster event records were incorrectly removed!")
        self.assertGreater(disaster_df["requests_per_minute"].max(), 10000, "Peak disaster traffic spike was trimmed!")

    def test_data_quality_flags(self):
        """Verify data_quality_flag column exists and contains valid tags."""
        self.assertIn("data_quality_flag", self.df_clean.columns)
        valid_tags = {
            "VALID", "IMPUTED_MISSING", "IMPUTED_CATEGORICAL",
            "REPAIRED_NEGATIVE", "REPAIRED_UTILISATION", "REPAIRED_CAPACITY",
            "REPAIRED_LATENCY_PERCENTILE", "REPAIRED_ERROR_RATE", "MULTIPLE_REPAIRS"
        }
        actual_tags = set(self.df_clean["data_quality_flag"].unique())
        self.assertTrue(actual_tags.issubset(valid_tags), f"Unexpected quality flags found: {actual_tags - valid_tags}")

    def test_quality_report_contents(self):
        """Verify quality report text file contains required audit metrics."""
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("DATASET RECORD COUNT & SUMMARY", content)
        self.assertIn("Original Raw Records:       3,885", content)
        self.assertIn("Cleaned Final Records:      3,882", content)
        self.assertIn("Disaster Surge Preservation", content)


if __name__ == "__main__":
    unittest.main()
