"""
Unit tests for Role-Based Access Control (RBAC) and Organisation Permissions
=============================================================================
Step 8: Comprehensive test coverage for all 4 roles, 4 organisations,
permission enforcement, and section visibility.
"""

import pytest
from src.utils.permissions import (
    Organisation,
    Role,
    PermissionPolicy,
    has_permission,
    enforce_permission,
    get_visible_sections,
    get_allowed_actions,
    filter_metrics_for_organisation,
    load_organisations,
    get_organisation,
)


class TestPermissionPolicy:
    """Test matrix covering all roles and organisations."""

    def test_viewer_role_permissions(self):
        role = Role.VIEWER
        assert PermissionPolicy.can_view_results(role) is True
        assert PermissionPolicy.can_run_simulation(role) is False
        assert PermissionPolicy.can_run_sensitivity_analysis(role) is False
        assert PermissionPolicy.can_edit_capacity_config(role) is False
        assert PermissionPolicy.can_edit_system_limits(role) is False
        assert PermissionPolicy.can_configure_scenarios(role) is False
        assert PermissionPolicy.can_manage_organisations(role) is False

    def test_analyst_role_permissions(self):
        role = Role.ANALYST
        assert PermissionPolicy.can_view_results(role) is True
        assert PermissionPolicy.can_run_simulation(role) is True
        assert PermissionPolicy.can_run_sensitivity_analysis(role) is True
        assert PermissionPolicy.can_edit_capacity_config(role) is False
        assert PermissionPolicy.can_edit_system_limits(role) is False
        assert PermissionPolicy.can_configure_scenarios(role) is False
        assert PermissionPolicy.can_manage_organisations(role) is False

    def test_operator_role_permissions(self):
        role = Role.OPERATOR
        assert PermissionPolicy.can_view_results(role) is True
        assert PermissionPolicy.can_run_simulation(role) is True
        assert PermissionPolicy.can_run_sensitivity_analysis(role) is True
        assert PermissionPolicy.can_edit_capacity_config(role) is True
        assert PermissionPolicy.can_edit_system_limits(role) is True
        assert PermissionPolicy.can_configure_scenarios(role) is False
        assert PermissionPolicy.can_manage_organisations(role) is False

    def test_administrator_role_permissions(self):
        role = Role.ADMINISTRATOR
        assert PermissionPolicy.can_view_results(role) is True
        assert PermissionPolicy.can_run_simulation(role) is True
        assert PermissionPolicy.can_run_sensitivity_analysis(role) is True
        assert PermissionPolicy.can_edit_capacity_config(role) is True
        assert PermissionPolicy.can_edit_system_limits(role) is True
        assert PermissionPolicy.can_configure_scenarios(role) is True
        assert PermissionPolicy.can_manage_organisations(role) is True

    def test_organisation_data_visibility(self):
        eoc = Organisation.EMERGENCY_OPS_CENTRE
        ext = Organisation.EXTERNAL_INFO_PARTNER
        gov = Organisation.GOVERNMENT_AGENCY
        hc = Organisation.HEALTHCARE_PARTNER

        assert PermissionPolicy.can_view_sensitive_infrastructure_details(eoc) is True
        assert PermissionPolicy.can_view_sensitive_infrastructure_details(gov) is True
        assert PermissionPolicy.can_view_sensitive_infrastructure_details(hc) is True
        assert PermissionPolicy.can_view_sensitive_infrastructure_details(ext) is False

    def test_filter_metrics_for_external_partner(self):
        metrics = {
            "peak_demand": 12000,
            "peak_instances": 15,
            "initial_instances": 10,
            "maximum_instances": 50,
            "capacity_per_instance": 500,
            "sla_compliance_pct": 100.0,
        }

        # Internal org - metrics unchanged
        internal_metrics = PermissionPolicy.filter_metrics_for_organisation(metrics, Organisation.EMERGENCY_OPS_CENTRE)
        assert internal_metrics["peak_instances"] == 15
        assert internal_metrics["capacity_per_instance"] == 500

        # External partner - sensitive infra metrics redacted
        external_metrics = PermissionPolicy.filter_metrics_for_organisation(metrics, Organisation.EXTERNAL_INFO_PARTNER)
        assert external_metrics["peak_demand"] == 12000
        assert external_metrics["sla_compliance_pct"] == 100.0
        assert external_metrics["peak_instances"] == "[REDACTED - EXTERNAL VIEW]"
        assert external_metrics["initial_instances"] == "[REDACTED - EXTERNAL VIEW]"
        assert external_metrics["maximum_instances"] == "[REDACTED - EXTERNAL VIEW]"
        assert external_metrics["capacity_per_instance"] == "[REDACTED - EXTERNAL VIEW]"

    def test_role_capabilities_summary(self):
        capabilities = PermissionPolicy.get_role_capabilities(Role.VIEWER, Organisation.EMERGENCY_OPS_CENTRE)
        assert capabilities["role"] == "Viewer"
        assert capabilities["organisation"] == "Emergency Operations Centre"
        assert capabilities["is_external"] is False
        assert len(capabilities["permissions"]) == 8


class TestStep8WorkflowPermissions:
    """Step 8 specific tests for RBAC, organisation configuration, and enforcement."""

    def test_all_four_organisations_load(self):
        """Verify data/organisations.json contains all 4 required organisations with valid schemas."""
        orgs = load_organisations()
        assert len(orgs) == 4
        expected_ids = {
            "emergency_ops_centre",
            "government_agency",
            "healthcare_partner",
            "external_info_partner",
        }
        actual_ids = {o["organisation_id"] for o in orgs}
        assert actual_ids == expected_ids

        for org in orgs:
            assert "organisation_name" in org
            assert "description" in org
            assert "allowed_scenarios" in org
            assert len(org["allowed_scenarios"]) > 0
            assert "default_SLA_target" in org
            assert "allowed_actions" in org

    def test_get_organisation_by_id_and_name(self):
        """Verify organisation lookup by ID and Enum value."""
        eoc = get_organisation("emergency_ops_centre")
        assert eoc is not None
        assert eoc["organisation_name"] == "Emergency Operations Centre"

        hc = get_organisation("Healthcare Partner")
        assert hc is not None
        assert hc["organisation_id"] == "healthcare_partner"
        assert "EXTREME_DISASTER" not in hc["allowed_scenarios"]

    def test_viewer_has_permission_and_blocked(self):
        """Viewer has read-only actions and is blocked from active mutations."""
        role = Role.VIEWER
        assert has_permission(role, "view_dashboard") is True
        assert has_permission(role, "view_scenario_results") is True
        assert has_permission(role, "view_sla_status") is True
        assert has_permission(role, "view_basic_charts") is True
        assert has_permission(role, "view_recommendations") is True

        # Forbidden
        assert has_permission(role, "run_simulation") is False
        assert has_permission(role, "modify_capacity") is False
        assert has_permission(role, "modify_scaling") is False
        assert has_permission(role, "modify_sla_targets") is False

        # Enforcement raises PermissionError
        with pytest.raises(PermissionError):
            enforce_permission(role, "run_simulation")
        with pytest.raises(PermissionError):
            enforce_permission(role, "modify_initial_instances")

    def test_analyst_has_permission_and_blocked(self):
        """Analyst can run simulations and sensitivity, but cannot change capacity or admin settings."""
        role = Role.ANALYST
        assert has_permission(role, "run_simulation") is True
        assert has_permission(role, "compare_scenarios") is True
        assert has_permission(role, "run_sensitivity_analysis") is True

        # Forbidden
        assert has_permission(role, "modify_initial_instances") is False
        assert has_permission(role, "modify_maximum_instances") is False
        assert has_permission(role, "modify_scaling_delay") is False
        assert has_permission(role, "modify_organisation_config") is False
        assert has_permission(role, "modify_sla_targets") is False

        with pytest.raises(PermissionError):
            enforce_permission(role, "modify_initial_instances")

    def test_operator_has_permission_and_blocked(self):
        """Operator can tune capacity and run failure tests, but cannot modify org or SLA policies."""
        role = Role.OPERATOR
        assert has_permission(role, "run_simulation") is True
        assert has_permission(role, "modify_initial_instances") is True
        assert has_permission(role, "modify_maximum_instances") is True
        assert has_permission(role, "modify_scaling_delay") is True
        assert has_permission(role, "run_failure_experiments") is True

        # Forbidden
        assert has_permission(role, "modify_organisation_config") is False
        assert has_permission(role, "modify_sla_targets") is False

        with pytest.raises(PermissionError):
            enforce_permission(role, "modify_organisation_config")

    def test_administrator_has_all_permissions(self):
        """Administrator has complete permissions across all modules."""
        role = Role.ADMINISTRATOR
        all_actions = [
            "view_dashboard", "run_simulation", "compare_scenarios",
            "modify_initial_instances", "modify_maximum_instances", "modify_scaling_delay",
            "run_failure_experiments", "modify_organisation_config", "modify_sla_targets",
            "configure_scenarios", "manage_organisations",
        ]
        for act in all_actions:
            assert has_permission(role, act) is True
            # Should not raise
            enforce_permission(role, act)

    def test_visible_sections_per_role(self):
        """Verify dynamic dashboard section visibility for each role."""
        viewer_sec = get_visible_sections(Role.VIEWER)
        assert "Overview" in viewer_sec
        assert "Workload Scenario" in viewer_sec
        assert "Simulation" in viewer_sec
        assert "SLA Results" in viewer_sec
        assert "Recommendation" in viewer_sec
        assert "Capacity Configuration" not in viewer_sec
        assert "Scenario Comparison" not in viewer_sec
        assert "Sensitivity Analysis" not in viewer_sec
        assert "Failure Testing" not in viewer_sec
        assert "Organisation Settings" not in viewer_sec

        analyst_sec = get_visible_sections(Role.ANALYST)
        assert "Scenario Comparison" in analyst_sec
        assert "Sensitivity Analysis" in analyst_sec
        assert "Capacity Configuration" not in analyst_sec
        assert "Failure Testing" not in analyst_sec

        operator_sec = get_visible_sections(Role.OPERATOR)
        assert "Capacity Configuration" in operator_sec
        assert "Failure Testing" in operator_sec
        assert "Organisation Settings" not in operator_sec

        admin_sec = get_visible_sections(Role.ADMINISTRATOR)
        assert "Organisation Settings" in admin_sec
        assert "Failure Testing" in admin_sec
        assert "Capacity Configuration" in admin_sec

    def test_external_partner_section_and_action_restrictions(self):
        """External information partners never see raw infra config even if operator role is requested."""
        ext_sections = get_visible_sections(Role.OPERATOR, Organisation.EXTERNAL_INFO_PARTNER)
        assert "Capacity Configuration" not in ext_sections
        assert "Failure Testing" not in ext_sections

        # Action check
        assert has_permission(Role.OPERATOR, "modify_capacity", Organisation.EXTERNAL_INFO_PARTNER) is False
        with pytest.raises(PermissionError):
            enforce_permission(Role.OPERATOR, "modify_capacity", Organisation.EXTERNAL_INFO_PARTNER)

    def test_allowed_actions_list(self):
        """Check get_allowed_actions returns structured and sorted action list."""
        v_acts = get_allowed_actions(Role.VIEWER)
        assert isinstance(v_acts, list)
        assert len(v_acts) > 0
        assert "view_dashboard" in v_acts
        assert "run_simulation" not in v_acts

        admin_acts = get_allowed_actions(Role.ADMINISTRATOR)
        assert len(admin_acts) > len(v_acts)
        assert "manage_organisations" in admin_acts
