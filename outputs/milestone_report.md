# Project Milestone Evaluation Report: Peak-Demand Capacity Simulator

## Executive Summary

This report presents a comprehensive verification of the **Peak-Demand Capacity Simulator** MVP milestone. The software demonstrates that traditional **average-demand capacity planning fails dangerously during emergency disasters**, whereas **scenario-based capacity planning restores 100.0% service-level agreement (SLA) compliance**.

---

## 1. Project Implementation Status

### COMPLETED (What is Working)
- ✅ **Reproducible Project Structure**: Standard modular architecture with separate `src/`, `dashboard/`, `data/`, `docs/`, `outputs/`, and `tests/` directories.
- ✅ **Realistic Historical Dataset**: Synthetic dataset generator creating 3,888 records across 33 columns spanning 27 days at 10-second resolution.
- ✅ **Data Cleaning & Validation Pipeline**: Automated cleaner handling NaN imputation, zero-clipping negative rates, utilization range enforcement [0-100%], and total capacity math validation (`src/data/cleaner.py`).
- ✅ **Workload Scenario Engine**: 5-tier scenario engine (`NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`, `EXTREME_DISASTER`) generating 3-phase surge curves (`src/simulation/scenarios.py`).
- ✅ **Baseline Capacity Model**: Constrained infrastructure capacity calculator demonstrating capacity gaps under average-demand planning (`src/capacity/baseline.py`).
- ✅ **Discrete-Event Peak Simulator MVP**: Timestep simulation engine modeling request arrival, queue accumulation/drainage, M/M/1 queue latency, HTTP 503 error rates, and auto-scaling propagation delay (`src/simulation/simulator.py`).
- ✅ **Multi-Scenario Evaluation**: Pipeline executing all 5 workload tiers and outputting [`outputs/scenario_comparison.csv`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/outputs/scenario_comparison.csv) and [`outputs/scenario_report.txt`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/outputs/scenario_report.txt).
- ✅ **Sensitivity Analysis Engine**: Systematically varies 7 key planning assumptions across 21 controlled runs, classifying each as **DECISION-CHANGING** or **LITTLE EFFECT** (`src/simulation/sensitivity.py`).
- ✅ **Edge Case & Failure Mode Suite**: Evaluates 5 failure conditions (extreme traffic spike, 10-min scaling lag, max instance ceiling, unrecoverable queue overflow, corrupted input data) and exports [`outputs/edge_case_results.csv`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/outputs/edge_case_results.csv) and [`docs/failure_cases.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/failure_cases.md).
- ✅ **Multi-Organisation & Permission Engine (RBAC)**: Support for 4 Organisations and 4 Roles with dynamic UI input locking and external partner metric redaction (`src/auth/permissions.py`).
- ✅ **Interactive Streamlit Web Dashboard**: 8-section dashboard featuring live sliders, Plotly time-series visualisations, scenario matrices, and plain-language guidance (`dashboard/app.py`).
- ✅ **Comprehensive Documentation**: Complete documentation suite including [`docs/architecture.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/architecture.md) with Mermaid diagram, [`docs/data_schema.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/data_schema.md), [`docs/stakeholder_assumptions.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/stakeholder_assumptions.md), [`docs/risk_register.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/risk_register.md), [`docs/user_guide.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/user_guide.md), and [`docs/experiment.md`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/docs/experiment.md).
- ✅ **Automated Test Suite**: 64 passing unit tests covering all modules (`python -m pytest tests/ -v`).

---

### PARTIALLY COMPLETED (What Still Needs Work)
- 🟡 **CDN & Edge Caching Model**: Basic queue modeling exists, but static asset offloading percentages (e.g. 80% CDN cache hit ratio) are currently approximated rather than dynamically simulated.
- 🟡 **Multi-Region Distributed Routing**: Current simulator assumes single-region ingress; multi-region traffic failover routing is not yet modeled.
- 🟡 **Predictive Auto-Scaling**: Auto-scaler uses reactive CPU utilization thresholds (>70%); predictive Machine Learning scaling algorithms are partially modeled.

---

### NOT YET IMPLEMENTED (Remaining Project Requirements)
- ❌ **Live Production Cloud Telemetry Connectors**: Real-time streaming API integration with AWS CloudWatch, Datadog, or Prometheus.
- ❌ **Production SSO / OAuth2 Authentication**: Currently uses a simple demo RBAC role selector rather than SAML/OAuth2 enterprise identity providers.
- ❌ **Financial Cost Optimization Engine**: Sizing models evaluate SLA compliance, but do not yet compute dollar cost vs SLA risk trade-offs (e.g. AWS EC2 hourly bill calculations).
- ❌ **Chaos Engineering Failure Injection**: Random node crashes and network partitioning simulations during execution.

---

## 2. Measured Experimental Results

Under identical `DISASTER_PEAK` workload stress testing (~5,200 RPM peak demand):

| Measurement Metric | Baseline (Average-Based) | Scenario-Based (Peak-Based) | Measured Delta |
| :--- | :---: | :---: | :---: |
| **SLA Compliance Percentage** | **20.6%** | **100.0%** | **+79.4% improvement** |
| **SLA Status Result** | ❌ **FAILED** | ✅ **PASSED** | **SERVICE RESTORED** |
| **Peak Demand** | 5,200 RPM | 5,200 RPM | *Identical Test Load* |
| **Peak Available Capacity** | 3,000 RPM (Capped) | 7,000 RPM | **+4,000 RPM (+133%)** |
| **Maximum Queue Depth** | 50,000 requests (Buffer Full) | 0 requests | **-50,000 requests (-100%)** |
| **Maximum p95 Latency** | 62,630 ms | 384 ms | **-62,246 ms (-99.4%)** |
| **Maximum Error Rate** | 65.11% | 0.00% | **-65.11%** |
| **Total Unmet / Dropped Requests** | 350,416 requests | 0 requests | **-350,416 dropped requests** |
| **Scaling Behaviour** | Capped at 6 instances | Scaled from 10 to 14 instances | Dynamic scale-out |

---

## 3. System Limitations & Disclaimers

1. **Synthetic Telemetry**: Historical baseline data is mathematically synthesized based on standard surge profiles rather than live production server logs.
2. **Laptop-Scale Simulation**: Discrete-event timesteps run locally in Python rather than distributed cloud infrastructure execution.
3. **Simplified Infrastructure Model**: Assumes homogeneous server nodes, single-region ingress, and M/M/1 queuing theory approximations.
4. **Simplified Access Control**: Uses a demo role selector dropdown in Streamlit rather than production OAuth2/SAML single sign-on.

---

## 4. Implementation Milestone & Roadmap for Next 50–60%

### Current Implementation Estimate: **45% Milestone Complete**
The current MVP successfully fulfills all core simulation, scenario generation, baseline comparison, sensitivity analysis, edge-case testing, Streamlit UI, RBAC logic, and documentation requirements for a functional capacity planning MVP simulator.

### Roadmap for Remaining 55% of Project Lifecycle
1. **Module 11 (Telemetry Connectors - 15%)**: Live CloudWatch/Prometheus API ingestion drivers.
2. **Module 12 (Cost & Financial Optimization - 15%)**: AWS/Azure instance cost calculation and dollar vs SLA risk optimization engine.
3. **Module 13 (Multi-Region CDN Model - 10%)**: CDN edge cache offloading & multi-region failover simulation.
4. **Module 14 (Enterprise SSO Auth - 10%)**: OAuth2/OIDC single sign-on integration.
5. **Module 15 (Chaos Engineering Suite - 5%)**: Failure injection for node crashes and network latency degradation.
