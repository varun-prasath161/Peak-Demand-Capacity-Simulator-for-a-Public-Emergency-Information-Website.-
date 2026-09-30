# System Risk Register

## Overview

This Risk Register identifies potential operational, technical, and architectural risks associated with the Peak-Demand Capacity Simulator for a Public Emergency-Information Website. Each risk includes a structured assessment of impact, likelihood, mitigation strategy, and current status.

> **Important**: Stakeholder validation of these risk assessments has not been independently conducted and remains future work. These risks are based on technical analysis of the simulator architecture and assumptions.

---

## Risk Matrix

| Risk ID | Risk | Impact | Likelihood | Mitigation | Current Status |
|:---|:---|:---:|:---:|:---|:---|
| **R-01** | **Synthetic Data Limitation**: The simulator uses synthetic generated data (3,888 rows) rather than real production traffic traces. Synthetic data may not capture all real-world traffic patterns, burst characteristics, or geographic distribution effects. | **High** | **High** | Clearly label all data as "Synthetic / Historical-Style Simulation Data". When real production logs become available, re-run the pipeline with actual traffic traces. Design the data pipeline to accept external CSV files without code changes. | **Mitigated** — Data is labelled synthetic throughout; pipeline accepts external CSV input. |
| **R-02** | **Workload Assumption Risk**: Scenario surge multipliers (1.0x–8.5x baseline) are estimated assumptions, not measured from actual disaster events. Real disasters may produce higher or lower traffic multipliers depending on population density, media coverage, and public awareness. | **High** | **Medium** | Provide configurable scenario parameters via JSON configuration files. Run sensitivity analysis across traffic multiplier variations (0.7x–2.0x) to identify decision-changing thresholds. Never present scenario multipliers as validated facts. | **Mitigated** — Configurable via `advanced_scenarios.json`; sensitivity analysis performed. |
| **R-03** | **Capacity Assumption Risk**: The assumption of 500 RPM per server instance and a 50-instance ceiling represents simplified infrastructure modeling. Real cloud environments have variable instance types, geographic regions, and performance characteristics. | **Medium** | **Medium** | Allow configurable `capacity_per_instance` and `max_instances` parameters. Sensitivity analysis tests capacity at 300/500/800 RPM and max instances at 20/50/80. Cost model clearly labelled as "Simulation Cost Assumptions". | **Mitigated** — Parameters configurable; sensitivity analysis performed on both parameters. |
| **R-04** | **Scaling Delay Assumption**: The simulated 180-second auto-scaling delay is an assumption. Real cloud provisioning times vary by provider, region, instance type, and container readiness state (60s–600s observed in practice). | **High** | **Medium** | Sensitivity analysis tests scaling delay at 60s, 180s, 300s, and 600s. Decision-changing analysis shows that delays above 300s cause SLA failures during disaster scenarios. Pre-warming strategy (Disaster-Aware Scaling) provides mitigation. | **Mitigated** — Delay is configurable; sensitivity analysis identifies critical thresholds. |
| **R-05** | **SLA Assumption Risk**: SLA targets (p95 latency ≤ 500ms, error rate ≤ 1%, compliance ≥ 99%) are configurable simulation parameters, not contracted service level agreements with real organisations. Actual SLA requirements may differ by organisation and jurisdiction. | **Medium** | **Medium** | SLA targets are stored in `data/scenarios/sla_config.json` and configurable per organisation in `data/organisations.json`. Each organisation can define different p95 latency, error rate, and compliance targets. | **Mitigated** — Per-organisation configurable SLA targets implemented. |
| **R-06** | **Lack of Real Production Validation**: No simulated scenario has been validated against actual production traffic logs from a real emergency event. All results represent theoretical model behaviour under assumed conditions. | **Critical** | **High** | Explicitly state in all documentation and dashboard UI that results are from simulation, not production monitoring. Include disclaimers in executive summary, architecture documentation, and cost reports. Future work: validate against actual disaster event traffic logs. | **Accepted** — Documented as future work; disclaimers present throughout. |
| **R-07** | **Simplified Infrastructure Model**: The simulator uses a simplified M/M/1 queuing model for latency, a step-function for scaling, and homogeneous instances. Real production systems involve multi-tier architectures (CDN, load balancer, application, database), heterogeneous hardware, and network effects. | **Medium** | **High** | Document the simplification clearly in architecture documentation. The simulator is designed for strategic capacity planning (order-of-magnitude right-sizing), not exact latency prediction. Provide a "Simulation vs Real-World" comparison table. | **Accepted** — Documented in `docs/final_architecture.md` and `docs/stakeholder_assumptions.md`. |
| **R-08** | **Application-Level Permissions Only**: Role-based access control (RBAC) is implemented as application-level role selection without authentication, session management, encryption, or audit logging. This is a demonstration workflow, not a security system. | **Medium** | **Low** | Clearly label the permission system as "Application-Level Workflow Demonstration" in all documentation and code comments. Do not claim production-grade security. Future work: integrate with SSO/OAuth2 for production deployment. | **Accepted** — Labelled as demonstration; security disclaimer in `src/utils/permissions.py`. |
| **R-09** | **Security Limitations**: The system has no authentication, no HTTPS enforcement, no input sanitisation beyond data pipeline validation, no rate limiting, and no audit logging. It is designed to run locally on a single developer machine. | **Low** | **Low** | The system is designed as a research and planning prototype, not a production-deployed web service. Document all security limitations in the risk register. Recommend production security hardening as future work. | **Accepted** — Prototype scope; documented as limitation. |
| **R-10** | **Deployment Limitations**: The simulator runs as a local Streamlit application on a single machine. It has no containerisation (Docker), no CI/CD pipeline, no cloud deployment configuration, and no horizontal scaling of the simulator itself. | **Low** | **Low** | Document deployment as local-only. Provide clear installation and execution instructions in README.md. Future work: Dockerise the application and add CI/CD for automated testing. | **Accepted** — Local deployment documented; future work identified. |

---

## Risk Summary

| Risk Level | Count | IDs |
|:---|:---:|:---|
| **Critical Impact** | 1 | R-06 |
| **High Impact** | 3 | R-01, R-02, R-04 |
| **Medium Impact** | 4 | R-03, R-05, R-07, R-08 |
| **Low Impact** | 2 | R-09, R-10 |

---

## Risk Mitigation Status

| Status | Count | Description |
|:---|:---:|:---|
| **Mitigated** | 5 | Risk reduced through implemented controls (configurable parameters, sensitivity analysis, disclaimers) |
| **Accepted** | 5 | Risk acknowledged and documented; mitigation deferred to future work or accepted as inherent to prototype scope |
