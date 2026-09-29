"""
Unit Tests for Explainable Recommendation Engine
================================================
Step 9: Verifies rule triggers, structured 5-field recommendations,
executive summary statements, and traceability export.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analysis.recommendations import (
    generate_explainable_recommendation,
    generate_executive_summary_statements,
    export_recommendations_csv,
    RECOMMENDATIONS_CSV,
)


class TestRecommendationEngine:
    """Test suite for evidence-based explainable recommendations."""

    def test_sla_compliant_case(self):
        """When SLA is met with low queue, recommend maintaining configuration without unnecessary spend."""
        summary = {
            "sla_compliant": True,
            "compliance_percentage": 100.0,
            "peak_demand_rpm": 967.0,
            "peak_instances": 4,
            "max_queue_depth": 0.0,
            "max_p95_latency_ms": 100.0,
            "max_error_rate_pct": 0.14,
            "total_unmet_requests": 0.0,
        }
        cfg = {"initial_instances": 4, "max_instances": 50, "capacity_per_instance": 500.0, "scaling_delay_seconds": 180}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "NORMAL", cfg, sla)

        assert rec["recommendation_type"] == "SLA_COMPLIANT"
        assert rec["severity"] == "success"
        assert "situation" in rec
        assert "evidence" in rec
        assert "impact" in rec
        assert "recommended_action" in rec
        assert "reason" in rec
        assert "Maintain the current baseline" in rec["recommended_action"]
        assert rec["supporting_metrics"]["peak_demand_rpm"] == 967.0

    def test_high_queue_recommendation(self):
        """When queue depth exceeds threshold, trigger high queue recommendation."""
        summary = {
            "sla_compliant": True,
            "compliance_percentage": 95.0,
            "peak_demand_rpm": 4500.0,
            "peak_instances": 10,
            "max_queue_depth": 2500.0,
            "max_p95_latency_ms": 420.0,
            "max_error_rate_pct": 0.5,
            "total_unmet_requests": 0.0,
        }
        cfg = {"initial_instances": 4, "max_instances": 50, "capacity_per_instance": 500.0, "scaling_delay_seconds": 180}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "SEASONAL_PEAK", cfg, sla)

        assert rec["recommendation_type"] == "HIGH_QUEUE"
        assert rec["severity"] == "warning"
        assert "accumulating in the wait queue" in rec["situation"]
        assert "2,500" in rec["evidence"]

    def test_high_latency_recommendation(self):
        """When p95 latency breaches SLA target, trigger latency reduction recommendation."""
        summary = {
            "sla_compliant": False,
            "compliance_percentage": 88.0,
            "peak_demand_rpm": 4800.0,
            "peak_instances": 12,
            "max_queue_depth": 800.0,
            "max_p95_latency_ms": 780.0,
            "max_error_rate_pct": 0.8,
            "total_unmet_requests": 0.0,
        }
        cfg = {"initial_instances": 6, "max_instances": 50, "capacity_per_instance": 500.0, "scaling_delay_seconds": 180}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "BREAKING_NEWS", cfg, sla)

        assert rec["recommendation_type"] == "HIGH_LATENCY"
        assert rec["severity"] in ["warning", "danger"]
        assert "slow" in rec["situation"].lower()
        assert "780" in rec["evidence"]
        assert "pre-warm" in rec["recommended_action"].lower()

    def test_high_error_recommendation(self):
        """When error rate exceeds statutory threshold, trigger high error recommendation."""
        summary = {
            "sla_compliant": False,
            "compliance_percentage": 70.0,
            "peak_demand_rpm": 6000.0,
            "peak_instances": 10,
            "max_queue_depth": 500.0,
            "max_p95_latency_ms": 450.0,
            "max_error_rate_pct": 3.8,  # > 1.0%
            "total_unmet_requests": 0.0,
        }
        cfg = {"initial_instances": 6, "max_instances": 50, "capacity_per_instance": 500.0, "scaling_delay_seconds": 180}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "DISASTER_PEAK", cfg, sla)

        assert rec["recommendation_type"] == "HIGH_ERROR_RATE"
        assert rec["severity"] == "danger"
        assert "error" in rec["situation"].lower()
        assert "3.80%" in rec["evidence"]

    def test_max_instance_limit_recommendation(self):
        """When fleet hits max instances ceiling and fails SLA, recommend raising ceiling."""
        summary = {
            "sla_compliant": False,
            "compliance_percentage": 65.0,
            "peak_demand_rpm": 8500.0,
            "peak_instances": 15,  # = max_instances
            "max_queue_depth": 12000.0,
            "max_p95_latency_ms": 1200.0,
            "max_error_rate_pct": 4.5,
            "total_unmet_requests": 350.0,
        }
        cfg = {"initial_instances": 6, "max_instances": 15, "capacity_per_instance": 500.0, "scaling_delay_seconds": 180}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "EXTREME_DISASTER", cfg, sla)

        assert rec["recommendation_type"] == "MAX_INSTANCE_LIMIT"
        assert rec["severity"] == "danger"
        assert "ceiling" in rec["situation"].lower()
        assert "Increase the maximum server ceiling" in rec["recommended_action"]
        assert rec["threshold"] == 15.0

    def test_slow_scaling_recommendation(self):
        """When scaling delay is >= 300s and SLA is violated during ramp, recommend reducing delay."""
        summary = {
            "sla_compliant": False,
            "compliance_percentage": 94.0,
            "peak_demand_rpm": 4000.0,
            "peak_instances": 12,
            "max_queue_depth": 900.0,
            "max_p95_latency_ms": 480.0,
            "max_error_rate_pct": 0.4,
            "total_unmet_requests": 0.0,
        }
        cfg = {"initial_instances": 4, "max_instances": 50, "capacity_per_instance": 500.0, "scaling_delay_seconds": 600}
        sla = {"p95_latency_target_ms": 500.0, "error_rate_target": 0.01, "sla_compliance_target_pct": 99.0}

        rec = generate_explainable_recommendation(summary, "BREAKING_NEWS", cfg, sla)

        assert rec["recommendation_type"] == "SLOW_SCALING"
        assert "provisioning delay" in rec["recommended_action"].lower() or "600s" in rec["recommended_action"]

    def test_missing_metric_handling(self):
        """Engine gracefully handles empty/missing metric dictionaries without raising unhandled errors."""
        empty_summary = {}
        rec = generate_explainable_recommendation(empty_summary, "NORMAL")
        assert isinstance(rec, dict)
        assert rec["recommendation_type"] in ["SLA_COMPLIANT", "HIGH_QUEUE", "MAX_INSTANCE_LIMIT"]
        assert "situation" in rec
        assert "evidence" in rec
        assert "impact" in rec
        assert "recommended_action" in rec
        assert "reason" in rec

    def test_executive_summary_statements(self):
        """Verifies 4-statement executive summary generation."""
        summary = {
            "sla_compliant": False,
            "compliance_percentage": 85.0,
            "peak_demand_rpm": 6200.0,
            "peak_instances": 15,
            "max_queue_depth": 3000.0,
            "max_p95_latency_ms": 950.0,
        }
        cfg = {"max_instances": 15, "capacity_per_instance": 500.0, "scaling_delay_seconds": 300}
        sla = {"p95_latency_target_ms": 500.0}

        stmts = generate_executive_summary_statements(summary, "DISASTER_PEAK", cfg, sla)

        assert "current_situation" in stmts
        assert "system_impact" in stmts
        assert "sla_impact" in stmts
        assert "operational_action" in stmts
        assert len(stmts["current_situation"]) > 20
        assert len(stmts["operational_action"]) > 20

    def test_traceability_export(self, tmp_path):
        """Recommendations export successfully to CSV with complete traceability schema."""
        summary = {"sla_compliant": True, "compliance_percentage": 100.0, "peak_demand_rpm": 1000.0}
        rec = generate_explainable_recommendation(summary, "NORMAL")
        
        csv_path = tmp_path / "test_recommendations.csv"
        saved = export_recommendations_csv([rec], output_file=csv_path)

        assert saved.exists()
        df = pd.read_csv(saved)
        assert len(df) == 1
        expected_cols = {
            "scenario", "strategy", "recommendation_type", "evidence_metric",
            "metric_value", "threshold", "recommendation", "reason", "situation", "evidence", "impact"
        }
        assert expected_cols.issubset(set(df.columns))

    def test_permission_aware_dashboard_behaviour(self):
        """Verifies role and organisation permission filtering in recommendation and dashboard contexts."""
        from src.utils.permissions import Organisation, Role, PermissionPolicy, get_visible_sections

        # 1. Viewer cannot edit operational settings or run simulations
        assert PermissionPolicy.can_run_simulation(Role.VIEWER) is False
        assert PermissionPolicy.can_edit_capacity_config(Role.VIEWER) is False
        assert PermissionPolicy.can_edit_system_limits(Role.VIEWER) is False

        # 2. Operator and Admin can edit capacity and run simulations
        assert PermissionPolicy.can_run_simulation(Role.OPERATOR) is True
        assert PermissionPolicy.can_edit_capacity_config(Role.OPERATOR) is True
        assert PermissionPolicy.can_run_simulation(Role.ADMINISTRATOR) is True
        assert PermissionPolicy.can_edit_system_limits(Role.ADMINISTRATOR) is True

        # 3. External partner has sensitive infrastructure details redacted
        raw_metrics = {
            "peak_demand": 5000,
            "peak_instances": 14,
            "capacity_per_instance": 500,
            "sla_compliance_pct": 99.5,
        }
        filtered_ext = PermissionPolicy.filter_metrics_for_organisation(
            raw_metrics, Organisation.EXTERNAL_INFO_PARTNER
        )
        assert "[REDACTED" in str(filtered_ext["peak_instances"])
        assert "[REDACTED" in str(filtered_ext["capacity_per_instance"])
        assert filtered_ext["peak_demand"] == 5000

        # 4. Visible sections expand properly per role hierarchy
        viewer_sections = get_visible_sections(Role.VIEWER, Organisation.EMERGENCY_OPS_CENTRE)
        admin_sections = get_visible_sections(Role.ADMINISTRATOR, Organisation.EMERGENCY_OPS_CENTRE)
        assert "Capacity Configuration" not in viewer_sections
        assert "Capacity Configuration" in admin_sections
        assert "Organisation Settings" in admin_sections

