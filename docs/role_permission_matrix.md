# Role Permission Matrix

> **Peak-Demand Capacity Simulator**  
> **Security Model**: Application-Level Role-Based Access Control (RBAC) MVP  
> **Security Notice**: *Role selection is implemented as an application-level workflow demonstration. Production deployment would require proper authentication and authorisation (OAuth2/OIDC/SAML).*

---

## 1. Permission Matrix

The table below outlines the capabilities and functional boundaries across the four user roles supported by the simulator:

| Feature / Action | Viewer | Analyst | Operator | Administrator |
| :--- | :---: | :---: | :---: | :---: |
| **Executive Dashboard** | ✓ | ✓ | ✓ | ✓ |
| **Scenario Results Viewing** | ✓ | ✓ | ✓ | ✓ |
| **Historical Load Analysis** | ✓ | ✓ | ✓ | ✓ |
| **Run Interactive Simulation** | No | ✓ | ✓ | ✓ |
| **Scenario Comparison (5 Scenarios)** | No | ✓ | ✓ | ✓ |
| **Change Instance Capacity** | No | No | ✓ | ✓ |
| **Change Scaling Delay / Limits** | No | No | ✓ | ✓ |
| **Sensitivity Analysis** | No | ✓ | ✓ | ✓ |
| **Failure & Edge-Case Testing** | No | No | ✓ | ✓ |
| **Modify SLA Targets** | No | No | No | ✓ |
| **Organisation Configuration** | No | No | No | ✓ |
| **System-Wide Limits & Defaults** | No | No | No | ✓ |
| **Audit Logs & Export Reports** | No | No | No | ✓ |

---

## 2. Role Definitions and Scopes

### 2.1 Viewer (`Role.VIEWER`)
* **Target Audience**: External observers, public communication officers, press liaisons, and executive stakeholders.
* **Permitted Capabilities**:
  * View executive summary and KPI status cards.
  * Inspect workload scenario descriptions and baseline trends.
  * View SLA compliance status (Compliant vs Violated).
  * Review high-level capacity recommendations.
* **Restricted Operations**:
  * Cannot trigger new simulation runs or alter random seeds.
  * Cannot modify instance numbers, capacity per instance, or autoscaling delay.
  * Cannot run advanced sensitivity analyses or stress experiments.
  * Cannot modify SLA performance targets.

### 2.2 Analyst (`Role.ANALYST`)
* **Target Audience**: Data scientists, traffic analysts, and capacity planners studying workload patterns.
* **Permitted Capabilities**:
  * Everything permitted to **Viewer**.
  * Run and re-run simulations across all scenarios.
  * Execute scenario comparison across all five workload profiles.
  * Inspect historical load metrics and percentile distributions.
  * Execute advanced sensitivity analyses and identify decision-changing assumptions.
  * Review formal SLA experiment results and before-vs-after improvements.
* **Restricted Operations**:
  * Cannot alter live operational scaling triggers or modify system limits.
  * Cannot execute disruptive failure and edge-case injections.
  * Cannot modify organisation definitions or SLA targets.

### 2.3 Operator (`Role.OPERATOR`)
* **Target Audience**: Site Reliability Engineers (SREs), infrastructure engineers, and incident commanders.
* **Permitted Capabilities**:
  * Everything permitted to **Analyst**.
  * Adjust initial instance count, maximum instance ceiling, and node capacity.
  * Configure autoscaling delay (provisioning lag) and scale-out thresholds.
  * Execute failure and edge-case tests (extreme spikes, slow scaling, compound failures).
  * Simulate emergency operational runbooks and manual failover adjustments.
* **Restricted Operations**:
  * Cannot modify organisation definitions or system-level permission policies.
  * Cannot relax statutory SLA compliance thresholds.

### 2.4 Administrator (`Role.ADMINISTRATOR`)
* **Target Audience**: System owners, lead infrastructure architects, and compliance officers.
* **Permitted Capabilities**:
  * Complete, unrestricted access across all application sections.
  * Edit organisation definitions, scenario mappings, and default profiles.
  * Configure system-wide SLA targets (p95 latency, error rate tolerance, compliance percentage).
  * Access all audit reports, failure test suites, and data profiling tools.
  * Manage system-wide infrastructure ceilings and cost models.

---

## 3. Multi-Organisation Data Filtering

In addition to role permissions, the simulator applies organisation-level context and data filtering:

| Organisation | Allowed Scenarios | Sensitive Infra Details | Primary Focus |
| :--- | :--- | :---: | :--- |
| **Emergency Operations Centre** | All 5 Scenarios | Full Visibility | Disaster peak response & fleet readiness |
| **Government Agency** | All 5 Scenarios | Full Visibility | Statutory compliance & resilience auditing |
| **Healthcare Partner** | Normal, Seasonal, Breaking, Disaster | Full Visibility | High-reliability SLA uptime monitoring |
| **External Information Partner** | Normal, Seasonal, Breaking News | **REDACTED** | Public advisory status (node details masked) |

---

## 4. Enforcement Architecture

All authorization checks are centralized in `src/utils/permissions.py`:
* `has_permission(role, action, organisation)`: Evaluates boolean eligibility.
* `enforce_permission(role, action, organisation)`: Raises `PermissionError` when an unauthorized operation is attempted in code.
* `get_visible_sections(role, organisation)`: Controls section visibility in the dashboard.
* `filter_metrics_for_organisation(metrics, organisation)`: Automatically redacts confidential infrastructure values (`peak_instances`, `available_capacity`) for external partners.
