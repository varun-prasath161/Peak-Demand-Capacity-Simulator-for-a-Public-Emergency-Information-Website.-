"""
Role-Based Access Control (RBAC) & Organisation Permission Engine
===================================================================
Bridge file pointing to src.utils.permissions to maintain backwards compatibility.
"""

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

__all__ = [
    "Organisation",
    "Role",
    "PermissionPolicy",
    "has_permission",
    "enforce_permission",
    "get_visible_sections",
    "get_allowed_actions",
    "filter_metrics_for_organisation",
    "load_organisations",
    "get_organisation",
]
