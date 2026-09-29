# Permission Workflow Test Results

> **Peak-Demand Capacity Simulator**  
> **Module**: Step 8 – Multi-Organisation & Permission Workflow  
> **Execution Date**: 2026-09-28  
> **Test Framework**: `pytest 9.1.1` under Python 3.11.9  
> **Overall Status**: **PASSED (16 / 16 tests passing, 0 failures)**

---

## 1. Executive Summary

A comprehensive test suite was executed against the newly integrated Multi-Organisation and Role-Based Access Control (RBAC) engine in `src/utils/permissions.py` and `dashboard/app.py`. All 16 targeted test cases passed with 100% success rate, confirming that:

1. **Role Gating Works**: Viewers are strictly restricted to read-only views; Analysts can run modeling and simulations; Operators can alter live capacity and scaling parameters; Administrators have unrestricted access.
2. **Unauthorized Actions are Blocked**: Attempting restricted actions programmatically raises `PermissionError` via `enforce_permission()`.
3. **Organisation Configuration is Enforced**: All 4 organizations (`Emergency Operations Centre`, `Government Agency`, `Healthcare Partner`, `External Information Partner`) load with dedicated scenario whitelists and SLA defaults.
4. **Data Redaction Operates as Expected**: Sensitive infrastructure topology values (`peak_instances`, `maximum_instances`, `capacity_per_instance`) are masked with `[REDACTED - EXTERNAL VIEW]` for external partners.
5. **No Regressions**: Full regression testing against all project steps confirms 116 passing tests with zero regressions.

---

## 2. Test Execution Details

| # | Test Name | Target Module | Scope / Behavior Verified | Result |
|:---:|:---|:---|:---|:---:|
| 1 | `test_viewer_role_permissions` | `PermissionPolicy` | Verifies Viewer can view results, cannot run simulations or edit config | **PASSED** |
| 2 | `test_analyst_role_permissions` | `PermissionPolicy` | Verifies Analyst can run simulation & sensitivity, cannot edit capacity | **PASSED** |
| 3 | `test_operator_role_permissions` | `PermissionPolicy` | Verifies Operator can edit capacity & scaling limits, cannot alter org settings | **PASSED** |
| 4 | `test_administrator_role_permissions` | `PermissionPolicy` | Verifies Administrator has full unrestricted operational & config access | **PASSED** |
| 5 | `test_organisation_data_visibility` | `PermissionPolicy` | Verifies external partner receives redacted infrastructure view | **PASSED** |
| 6 | `test_filter_metrics_for_external_partner` | `PermissionPolicy` | Verifies metric dictionary values are safely replaced with redaction tags | **PASSED** |
| 7 | `test_role_capabilities_summary` | `PermissionPolicy` | Verifies structured permission checklist generation for UI display | **PASSED** |
| 8 | `test_all_four_organisations_load` | `src.utils.permissions` | Verifies `data/organisations.json` contains all 4 valid org schemas | **PASSED** |
| 9 | `test_get_organisation_by_id_and_name` | `src.utils.permissions` | Verifies case-insensitive lookup by ID and Enum name | **PASSED** |
| 10 | `test_viewer_has_permission_and_blocked` | `src.utils.permissions` | Verifies Viewer actions allowed, and mutations throw `PermissionError` | **PASSED** |
| 11 | `test_analyst_has_permission_and_blocked` | `src.utils.permissions` | Verifies Analyst actions allowed, and capacity edits throw `PermissionError` | **PASSED** |
| 12 | `test_operator_has_permission_and_blocked` | `src.utils.permissions` | Verifies Operator actions allowed, and org config throws `PermissionError` | **PASSED** |
| 13 | `test_administrator_has_all_permissions` | `src.utils.permissions` | Verifies Administrator can perform all registered actions without errors | **PASSED** |
| 14 | `test_visible_sections_per_role` | `src.utils.permissions` | Verifies dynamic dashboard section list for each role | **PASSED** |
| 15 | `test_external_partner_section_and_action_restrictions` | `src.utils.permissions` | Verifies external partners cannot access capacity/failure sections | **PASSED** |
| 16 | `test_allowed_actions_list` | `src.utils.permissions` | Verifies `get_allowed_actions()` returns sorted list per role | **PASSED** |

---

## 3. Verified Permission Behaviors

### 3.1 Role Access Hierarchy
* **Viewer**:
  * Allowed: `view_dashboard`, `view_scenario_results`, `view_sla_status`, `view_basic_charts`, `view_recommendations`
  * Blocked: `run_simulation`, `modify_capacity`, `modify_scaling`, `modify_sla_targets`, `run_failure_experiments`
  * Dashboard Sections: Overview, Workload Scenario, Simulation, SLA Results, Recommendation
* **Analyst**:
  * Allowed: Viewer actions + `run_simulation`, `compare_scenarios`, `view_historical_analysis`, `view_sensitivity_analysis`, `run_sensitivity_analysis`, `view_sla_experiment_results`
  * Blocked: `modify_capacity`, `modify_scaling`, `modify_organisation_config`, `modify_sla_targets`
  * Dashboard Sections: Viewer sections + Scenario Comparison, Sensitivity Analysis
* **Operator**:
  * Allowed: Analyst actions + `modify_initial_instances`, `modify_maximum_instances`, `modify_scaling_delay`, `modify_instance_capacity`, `edit_capacity_config`, `edit_system_limits`, `run_failure_experiments`, `view_failure_testing`
  * Blocked: `modify_organisation_config`, `modify_sla_targets`
  * Dashboard Sections: Analyst sections + Capacity Configuration, Failure & Edge-Case Testing
* **Administrator**:
  * Allowed: Complete system access across all 18 registered actions.
  * Dashboard Sections: All sections + Multi-Organisation & System Administration

### 3.2 Multi-Organisation Behavior
* **Emergency Operations Centre**: Full scenario access (Normal, Seasonal, Breaking, Disaster, Extreme Disaster); default SLA 500ms p95 latency.
* **Government Agency**: Full scenario access; default SLA 600ms p95 latency.
* **Healthcare Partner**: Filtered scenario access (Extreme Disaster excluded); default strict SLA 400ms p95 latency.
* **External Information Partner**: Filtered scenario access (Disaster and Extreme Disaster excluded); default SLA 800ms p95 latency; all server counts and raw capacity metrics masked with `[REDACTED - EXTERNAL VIEW]`.

---

## 4. Security Limitations

> **Application-Level Demonstration**: Role selection is currently implemented as an MVP application-level workflow demonstration. In production environments, user authentication must be integrated with an enterprise identity provider (OAuth2/OIDC, SAML, or LDAP) and verified via cryptographically signed tokens.
