"""
Role-Based Access Control (RBAC) & Multi-Organisation Permission Engine
=======================================================================
Step 8: Application-level permission workflow and multi-organisation support.

Security Note:
Role selection is implemented as an application-level workflow demonstration.
Production deployment would require proper authentication and authorisation.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "data" / "organisations.json"


class Organisation(str, Enum):
    EMERGENCY_OPS_CENTRE = "Emergency Operations Centre"
    GOVERNMENT_AGENCY = "Government Agency"
    HEALTHCARE_PARTNER = "Healthcare Partner"
    EXTERNAL_INFO_PARTNER = "External Information Partner"


class Role(str, Enum):
    VIEWER = "Viewer"
    ANALYST = "Analyst"
    OPERATOR = "Operator"
    ADMINISTRATOR = "Administrator"


# Canonical feature action identifiers
ACTIONS_VIEWER: Set[str] = {
    "view_dashboard",
    "view_scenario_results",
    "view_sla_status",
    "view_basic_charts",
    "view_recommendations",
}

ACTIONS_ANALYST: Set[str] = ACTIONS_VIEWER | {
    "run_simulation",
    "compare_scenarios",
    "view_historical_analysis",
    "view_sensitivity_analysis",
    "run_sensitivity_analysis",
    "view_sla_experiment_results",
}

ACTIONS_OPERATOR: Set[str] = ACTIONS_ANALYST | {
    "modify_initial_instances",
    "modify_maximum_instances",
    "modify_scaling_delay",
    "modify_instance_capacity",
    "edit_capacity_config",
    "edit_system_limits",
    "run_failure_experiments",
    "view_failure_testing",
    "run_capacity_simulations",
}

ACTIONS_ADMINISTRATOR: Set[str] = ACTIONS_OPERATOR | {
    "modify_organisation_config",
    "modify_sla_targets",
    "modify_system_configuration",
    "configure_scenarios",
    "manage_organisations",
    "access_all_reports",
    "access_all_experiments",
}

ROLE_ACTIONS_MAP: Dict[str, Set[str]] = {
    Role.VIEWER.value: ACTIONS_VIEWER,
    Role.ANALYST.value: ACTIONS_ANALYST,
    Role.OPERATOR.value: ACTIONS_OPERATOR,
    Role.ADMINISTRATOR.value: ACTIONS_ADMINISTRATOR,
}

# Visible dashboard sections per role
SECTIONS_VIEWER: List[str] = [
    "Overview",
    "Executive Overview",
    "Historical Load",
    "Workload Scenario",
    "Scenario Selection",
    "Simulation",
    "SLA Results",
    "Recommendation",
    "Before vs After",
]

SECTIONS_ANALYST: List[str] = [
    "Overview",
    "Executive Overview",
    "Historical Load",
    "Workload Scenario",
    "Scenario Selection",
    "Simulation",
    "SLA Results",
    "Scenario Comparison",
    "Strategy Comparison",
    "Sensitivity Analysis",
    "Recommendation",
    "Before vs After",
]

SECTIONS_OPERATOR: List[str] = [
    "Overview",
    "Executive Overview",
    "Historical Load",
    "Workload Scenario",
    "Scenario Selection",
    "Capacity Configuration",
    "Simulation",
    "SLA Results",
    "Scenario Comparison",
    "Strategy Comparison",
    "Sensitivity Analysis",
    "Failure Testing",
    "Recommendation",
    "Before vs After",
]

SECTIONS_ADMINISTRATOR: List[str] = [
    "Overview",
    "Executive Overview",
    "Historical Load",
    "Workload Scenario",
    "Scenario Selection",
    "Capacity Configuration",
    "Simulation",
    "SLA Results",
    "Scenario Comparison",
    "Strategy Comparison",
    "Sensitivity Analysis",
    "Failure Testing",
    "Organisation Settings",
    "SLA Configuration",
    "System Configuration",
    "All Reports",
    "Recommendation",
    "Before vs After",
]

ROLE_SECTIONS_MAP: Dict[str, List[str]] = {
    Role.VIEWER.value: SECTIONS_VIEWER,
    Role.ANALYST.value: SECTIONS_ANALYST,
    Role.OPERATOR.value: SECTIONS_OPERATOR,
    Role.ADMINISTRATOR.value: SECTIONS_ADMINISTRATOR,
}


def load_organisations(config_file: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Loads organisations definitions from data/organisations.json."""
    path = config_file or CONFIG_PATH
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("organisations", [])


def get_organisation(org_key_or_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves organisation config dictionary by id, enum value, or name."""
    orgs = load_organisations()
    target = org_key_or_name.strip().lower()
    for o in orgs:
        if (
            o.get("organisation_id", "").lower() == target
            or o.get("organisation_name", "").lower() == target
        ):
            return o
    return None


def _normalize_role(role: Any) -> str:
    if isinstance(role, Role):
        return role.value
    return str(role).capitalize()


def _normalize_org(org: Any) -> str:
    if isinstance(org, Organisation):
        return org.value
    return str(org)


def has_permission(role: Any, action: str, organisation: Optional[Any] = None) -> bool:
    """
    Checks if a given role (and optional organisation) is authorized to perform action.
    """
    role_str = _normalize_role(role)
    allowed_for_role = ROLE_ACTIONS_MAP.get(role_str, set())
    if action not in allowed_for_role:
        return False

    # Organisation-level restriction check if organisation provided
    if organisation:
        org_str = _normalize_org(organisation)
        # External information partners cannot access sensitive infra actions
        if org_str == Organisation.EXTERNAL_INFO_PARTNER.value:
            sensitive_actions = {
                "modify_capacity",
                "modify_scaling",
                "modify_initial_instances",
                "modify_maximum_instances",
                "modify_scaling_delay",
                "modify_instance_capacity",
                "edit_capacity_config",
                "edit_system_limits",
                "run_failure_experiments",
                "view_detailed_infrastructure",
            }
            if action in sensitive_actions:
                return False

    return True


def enforce_permission(role: Any, action: str, organisation: Optional[Any] = None) -> None:
    """
    Enforces permission check; raises PermissionError if unauthorized.
    Use in application logic before executing sensitive actions.
    """
    if not has_permission(role, action, organisation):
        role_str = _normalize_role(role)
        raise PermissionError(
            f"Action '{action}' is forbidden for role '{role_str}'"
            + (f" in organisation '{_normalize_org(organisation)}'" if organisation else "")
        )


def get_visible_sections(role: Any, organisation: Optional[Any] = None) -> List[str]:
    """Returns list of visible dashboard sections for the role."""
    role_str = _normalize_role(role)
    sections = ROLE_SECTIONS_MAP.get(role_str, SECTIONS_VIEWER).copy()
    
    # If external partner, hide deep infrastructure configuration sections
    if organisation:
        org_str = _normalize_org(organisation)
        if org_str == Organisation.EXTERNAL_INFO_PARTNER.value:
            sections = [s for s in sections if s not in ["Capacity Configuration", "Failure Testing", "System Configuration"]]

    return sections


def get_allowed_actions(role: Any, organisation: Optional[Any] = None) -> List[str]:
    """Returns sorted list of permitted action strings."""
    role_str = _normalize_role(role)
    actions = ROLE_ACTIONS_MAP.get(role_str, set()).copy()
    if organisation:
        org_str = _normalize_org(organisation)
        if org_str == Organisation.EXTERNAL_INFO_PARTNER.value:
            actions = {a for a in actions if has_permission(role, a, organisation)}
    return sorted(list(actions))


def filter_metrics_for_organisation(metrics: Dict[str, Any], organisation: Any) -> Dict[str, Any]:
    """
    Redacts sensitive infrastructure metrics for External Information Partners.
    """
    org_str = _normalize_org(organisation)
    if org_str != Organisation.EXTERNAL_INFO_PARTNER.value:
        return metrics

    filtered = metrics.copy()
    redacted_tag = "[REDACTED - EXTERNAL VIEW]"
    for sensitive_key in [
        "peak_instances",
        "initial_instances",
        "maximum_instances",
        "capacity_per_instance",
        "peak_capacity",
        "available_capacity",
    ]:
        if sensitive_key in filtered:
            filtered[sensitive_key] = redacted_tag
    return filtered


class PermissionPolicy:
    """
    Bridge policy engine matching existing project interface.
    """

    @staticmethod
    def is_external_partner(org: Any) -> bool:
        org_str = _normalize_org(org)
        return org_str == Organisation.EXTERNAL_INFO_PARTNER.value

    @staticmethod
    def can_view_results(role: Any) -> bool:
        return has_permission(role, "view_scenario_results")

    @staticmethod
    def can_edit_capacity_config(role: Any) -> bool:
        return has_permission(role, "edit_capacity_config")

    @staticmethod
    def can_edit_system_limits(role: Any) -> bool:
        return has_permission(role, "edit_system_limits")

    @staticmethod
    def can_run_simulation(role: Any) -> bool:
        return has_permission(role, "run_simulation")

    @staticmethod
    def can_run_sensitivity_analysis(role: Any) -> bool:
        return has_permission(role, "run_sensitivity_analysis")

    @staticmethod
    def can_configure_scenarios(role: Any) -> bool:
        return has_permission(role, "configure_scenarios")

    @staticmethod
    def can_manage_organisations(role: Any) -> bool:
        return has_permission(role, "manage_organisations")

    @staticmethod
    def can_view_sensitive_infrastructure_details(org: Any) -> bool:
        return not PermissionPolicy.is_external_partner(org)

    @classmethod
    def get_role_capabilities(cls, role: Any, org: Any) -> Dict[str, Any]:
        is_ext = cls.is_external_partner(org)
        role_str = _normalize_role(role)
        org_str = _normalize_org(org)
        return {
            "role": role_str,
            "organisation": org_str,
            "is_external": is_ext,
            "permissions": [
                ("View Scenario Results", cls.can_view_results(role)),
                ("Run Custom Simulations", cls.can_run_simulation(role)),
                ("Run Sensitivity Analysis", cls.can_run_sensitivity_analysis(role)),
                ("Modify Capacity & Scaling Config", cls.can_edit_capacity_config(role)),
                ("Modify System Limits & SLA Targets", cls.can_edit_system_limits(role)),
                ("Configure Scenario Profiles", cls.can_configure_scenarios(role)),
                ("Manage Organisation Settings", cls.can_manage_organisations(role)),
                ("View Detailed Infra Metrics", cls.can_view_sensitive_infrastructure_details(org)),
            ],
        }

    @classmethod
    def filter_metrics_for_organisation(cls, metrics: Dict[str, Any], org: Any) -> Dict[str, Any]:
        return filter_metrics_for_organisation(metrics, org)
