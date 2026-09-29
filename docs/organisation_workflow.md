# Multi-Organisation & Permission Workflow Guide

> **Peak-Demand Capacity Simulator for a Public Emergency-Information Website**  
> **Module**: Multi-Organisation Support + Role-Based Permission Workflow (Step 8)  
> **Security Notice**: *Role selection is implemented as an application-level workflow demonstration. Production deployment would require proper authentication and authorisation (OAuth2/OIDC/SAML).*

---

## 1. Supported Organisations

The simulator supports four distinct stakeholder organisations configured in [`data/organisations.json`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/data/organisations.json):

1. **Emergency Operations Centre (EOC)** (`emergency_ops_centre`)
   * **Scope**: Primary disaster coordination authority managing crisis response, emergency broadcasts, and high-priority public advisories.
   * **Allowed Scenarios**: All five scenarios (`NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`, `EXTREME_DISASTER`).
   * **Default SLA Target**: 500 ms p95 latency, 1.0% error rate, 99.0% compliance.
   * **Focus**: Rapid operational scale-out and disaster capacity limits.

2. **Government Agency** (`government_agency`)
   * **Scope**: State/national oversight department ensuring statutory service availability and infrastructure accountability.
   * **Allowed Scenarios**: All five scenarios.
   * **Default SLA Target**: 600 ms p95 latency, 1.0% error rate, 98.0% compliance.
   * **Focus**: Long-term resilience auditing, before-vs-after improvements, and budget adherence.

3. **Healthcare Partner** (`healthcare_partner`)
   * **Scope**: Regional hospital consortia and public health clinics requiring zero-downtime access to public safety triage instructions.
   * **Allowed Scenarios**: `NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`.
   * **Default SLA Target**: 400 ms p95 latency, 0.5% error rate, 99.5% compliance (strict SLA).
   * **Focus**: Low latency and minimal packet drop during health advisories.

4. **External Information Partner** (`external_info_partner`)
   * **Scope**: Commercial media outlets, news syndicates, and community volunteer groups consuming public updates.
   * **Allowed Scenarios**: `NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`.
   * **Default SLA Target**: 800 ms p95 latency, 2.0% error rate, 95.0% compliance.
   * **Data Masking**: Internal server counts and raw capacity numbers are masked with `[REDACTED - EXTERNAL VIEW]` tags.

---

## 2. Supported Roles

1. **Viewer**: Read-only oversight. Views dashboards, scenario trends, SLA compliance status, and plain-language recommendations. Configuration sliders and simulation execution buttons are hidden or disabled.
2. **Analyst**: Workload investigation and modeling. Can run simulations, compare scenarios, inspect historical traffic distributions, and execute sensitivity analyses. Live operational controls and admin settings are restricted.
3. **Operator**: Infrastructure operations and incident response. Full access to tune initial/max servers, change scaling delays, run failure and edge-case simulations, and test emergency pre-warming procedures.
4. **Administrator**: Platform administration. Complete control over organisation settings, system SLA targets, default scenario parameters, and system-wide audit reports.

---

## 3. Permission Model Architecture

The permission model is implemented in [`src/utils/permissions.py`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/src/utils/permissions.py):

* **Single Source of Truth**: Centralized action-to-role mappings (`ACTIONS_VIEWER`, `ACTIONS_ANALYST`, `ACTIONS_OPERATOR`, `ACTIONS_ADMINISTRATOR`).
* **Non-Bypassable Enforcement**: `enforce_permission(role, action, organisation)` raises `PermissionError` when an unauthorized action is attempted in Python code.
* **Dynamic Section Filtering**: `get_visible_sections(role, organisation)` dynamically computes the active sections displayed to the user.
* **Sensitive Data Redaction**: `filter_metrics_for_organisation(metrics, organisation)` strips internal topology metrics when serving external partners.

---

## 4. Dashboard Workflow

When opening the Streamlit dashboard:

1. **Organisation Selector**: Choose from the four registered organisations in the sidebar. This sets the scenario whitelist, default SLA parameters, and data redaction policies.
2. **Role Selector**: Choose user clearance (`Viewer`, `Analyst`, `Operator`, `Administrator`).
3. **Role Rights Card**: An expandable visual checklist displays which operations are allowed (✅) or blocked (❌) for the active selection.
4. **Adaptive UI Controls**: Sliders and buttons change state dynamically:
   * Viewers see read-only informative views with sliders disabled.
   * Analysts can trigger simulations and sensitivity runs.
   * Operators can adjust live capacity parameters.
   * Administrators see dedicated administrative tabs.

---

## 5. Walkthrough: Role-Specific User Journeys

### 5.1 Viewer Workflow
1. Navigate to the dashboard; select **Viewer** role.
2. The sidebar displays read-only indicators; simulation run buttons are disabled.
3. Review **Section 1: Executive Overview** showing high-level demand and SLA status.
4. Inspect **Section 2 & 4: Scenario and Simulation Results** to review demand vs capacity curves and latency percentiles.
5. Read **Section 8: Plain-Language Recommendation** to understand whether current capacity is adequate.
6. Advanced capacity sliders and sensitivity controls are hidden.

### 5.2 Analyst Workflow
1. Select **Analyst** role.
2. Choose a scenario from the permitted scenario list (e.g. `DISASTER_PEAK`).
3. Click **🚀 Run Simulation** to execute discrete-event workload modeling.
4. Inspect **Section 5: SLA Results** to identify timeline periods where p95 latency breached targets.
5. Review **Section 6: Scenario Comparison** to evaluate demand and server scale across all 5 profiles.
6. Explore **Section 7: Sensitivity Analysis** to review which parameters are *Decision-Changing* vs *Little Effect*.

### 5.3 Operator Workflow
1. Select **Operator** role and organisation **Emergency Operations Centre**.
2. Unlocked capacity controls become active in the sidebar.
3. Increase `Initial Instances` from 4 to 8 to model pre-warming for an impending storm.
4. Decrease `Scaling Delay` from 300s to 120s to model rapid container autoscaling.
5. Re-run simulation and confirm that queue backlog drops to zero and SLA compliance reaches 100%.
6. Access **Section: Failure Testing** to execute edge-case stress runs (10x spikes, instance caps).

### 5.4 Administrator Workflow
1. Select **Administrator** role.
2. All dashboard controls, administrative drawers, and failure testing suites are unlocked.
3. Modify global SLA targets (e.g., tighten p95 latency from 500ms to 400ms).
4. Review organisation mappings and default scenarios in **Organisation Settings**.
5. Access exportable audit logs and comprehensive performance reports.

---

## 6. Security Limitations and Future Roadmap

> [!WARNING]
> **MVP Security Scope**  
> Role selection is implemented as an **application-level workflow demonstration** to illustrate role-based behavior, adaptive UI rendering, and permission gating.
>
> In a production deployment:
> 1. Authentication must be backed by a cryptographic identity provider (e.g., OAuth 2.0 / OpenID Connect, SAML 2.0).
> 2. Roles must be securely mapped from JWT claims or Active Directory groups.
> 3. API endpoints must enforce token verification and session signing on the backend server.
