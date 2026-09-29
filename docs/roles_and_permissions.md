# Role-Based Access Control (RBAC) & Multi-Organisation Permissions

## Overview

The **Peak-Demand Capacity Simulator** implements a lightweight Role-Based Access Control (RBAC) and Multi-Organisation Data Visibility framework. This model ensures that emergency responders, analysts, infrastructure operators, leadership, and external partners access functionality and data appropriate to their operational role and organizational boundaries.

---

## 1. Supported Organisations

The simulator supports four distinct organisation types, each representing a key stakeholder group during disaster emergency operations:

1. **Emergency Operations Centre (EOC)**: Primary incident command and infrastructure management body. Full access to raw telemetry and capacity planning tools.
2. **Government Agency**: Oversight and policy coordination body requiring strategic visibility into SLA compliance and disaster readiness.
3. **Healthcare Partner**: Inter-agency healthcare provider requiring capacity predictions and peak demand metrics for medical emergency routing.
4. **External Information Partner**: Third-party news agencies, public safety feeds, or external vendors. Subject to **Data Privacy & Redaction** rules to protect internal infrastructure topologies.

---

## 2. Permission Levels (Roles)

The access model defines four hierarchical permission levels:

| Permission Level | Description | Key Capabilities | Restricted Actions |
| :--- | :--- | :--- | :--- |
| **1. Viewer** | Read-only access for stakeholders monitoring readiness. | View scenario results, review executive reports & charts. | Cannot run simulations or modify parameters. |
| **2. Analyst** | Technical researcher evaluating stress scenarios. | Run custom simulations, perform sensitivity analysis. | Cannot modify core system safety limits or SLA thresholds. |
| **3. Operator** | Infrastructure engineer managing auto-scaling. | Configure capacity & scaling rules, run simulations, review SLA details. | Cannot modify global scenario profiles or manage organisations. |
| **4. Administrator** | System owner with full administrative authority. | Full system access, manage organisations, edit scenario profiles & system limits. | None. |

---

## 3. Workflow & Permission Matrix

| Functionality / Workflow Step | Viewer | Analyst | Operator | Administrator |
| :--- | :---: | :---: | :---: | :---: |
| **View Scenario Results & Charts** | ✅ | ✅ | ✅ | ✅ |
| **Run / Rerun Custom Simulations** | ❌ | ✅ | ✅ | ✅ |
| **Execute Sensitivity Analysis** | ❌ | ✅ | ✅ | ✅ |
| **Modify Capacity & Scaling Parameters** | ❌ | ❌ | ✅ | ✅ |
| **Modify System Limits & SLA Targets** | ❌ | ❌ | ✅ | ✅ |
| **Configure Global Scenario Definitions** | ❌ | ❌ | ❌ | ✅ |
| **Manage Organisation Policy & Users** | ❌ | ❌ | ❌ | ✅ |

---

## 4. External Partner Data Privacy & Redaction

When an user belongs to an **External Information Partner** organisation:

- **Redacted Metrics**: Specific internal infrastructure details such as raw server instance counts (`peak_instances`, `initial_instances`, `maximum_instances`) and per-node capacity (`capacity_per_instance`) are automatically masked as `[REDACTED - EXTERNAL VIEW]`.
- **Public Metrics**: High-level aggregated demand (`peak_demand`), overall SLA compliance percentage (`sla_compliance_pct`), and high-level advisory recommendations remain visible to ensure operational transparency without exposing internal topology.

---

## 5. UI Demo Role Selector

In the interactive Streamlit dashboard (`dashboard/app.py`), users can select their **Organisation** and **Permission Level** via the sidebar controls. The UI dynamically adjusts input controls:

- **Disabled Inputs**: Sliders and numerical inputs are disabled (`disabled=True`) when the active role lacks edit permissions.
- **Capability Summary Badge**: The UI displays a live permission card showing green checkmarks (`✅`) for allowed actions and red crosses (`❌`) for restricted actions.
- **Role Notices**: Contextual alerts inform users why specific controls are read-only under their selected role.

---

## 6. Verification & Automated Testing

RBAC policies and metric redaction rules are thoroughly verified via automated unit tests located in [`tests/test_permissions.py`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/tests/test_permissions.py):

```bash
python -m pytest tests/test_permissions.py -v
```
