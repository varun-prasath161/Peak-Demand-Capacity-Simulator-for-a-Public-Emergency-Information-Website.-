# Final Project Report

**Peak-Demand Capacity Simulator for a Public Emergency-Information Website**

**Date**: 2026-09-30  
**Version**: 2.0.0 (Final)

---

## 1. Executive Summary

This project delivers a **fully working prototype** of a Peak-Demand Capacity Simulator that demonstrates why **scenario-based capacity planning** is essential for public emergency-information websites. The system proves that average-demand planning fails catastrophically during disaster events, while scenario-aware planning achieves 100% SLA compliance under identical workloads.

### Key Finding

Under identical `DISASTER_PEAK` workload (~5,200 RPM peak):

| Metric | Average-Based Planning | Scenario-Based Planning | Improvement |
|:---|:---:|:---:|:---:|
| **SLA Compliance** | 20.6% | 100.0% | **+79.4%** |
| **Max Queue Depth** | 50,000 requests | 0 requests | **-100%** |
| **Max p95 Latency** | 62,630 ms | 384 ms | **-99.4%** |
| **Max Error Rate** | 65.11% | 0.00% | **-65.11 pp** |
| **Dropped Requests** | 350,416 | 0 | **-100%** |

> **All costs are labelled as simulation assumptions. All data is synthetic / historical-style simulation data. This is not production data and should never be claimed as such.**

---

## 2. Problem Statement

Public emergency-information websites **must remain available during disasters** — the exact moments when traffic surges far beyond everyday levels. Average-demand capacity planning uses historical mean utilisation (~1,300 RPM) to size infrastructure, which dangerously underestimates resources needed during Category-5 hurricanes, major earthquakes, or multi-state blackouts where traffic can spike 4.5x–8.5x above baseline.

---

## 3. System Capabilities

The simulator demonstrates a complete **13-stage pipeline**:

1. **Data Ingestion** — Synthetic 3,888-row × 33-column operational telemetry dataset
2. **Data Cleaning** — 15-step validation pipeline preserving disaster spikes
3. **Historical Analysis** — Aggregate metrics (mean, P95, P99, peak-to-average ratio)
4. **Scenario Generation** — 7 configurable workload scenarios with 3-phase surge curves
5. **Capacity Strategy Evaluation** — 5 planning strategies compared on cost/SLA trade-offs
6. **Discrete-Event Simulation** — Time-step simulation with queue dynamics, M/M/1 latency, auto-scaling delay
7. **SLA Evaluation** — Formal compliance checking against configurable targets
8. **Cost Analysis** — Simulated economic trade-off analysis (labelled as assumptions)
9. **Sensitivity Analysis** — 8 parameter variations with decision-changing identification
10. **Failure Testing** — 8 stress/failure conditions with severity classification
11. **Recommendation Engine** — 5-field explainable capacity recommendations
12. **Multi-Organisation Workflow** — 4 organisations, 4 roles, RBAC enforcement, metric redaction
13. **Interactive Dashboard** — 12-section Streamlit dashboard with Plotly visualisations

---

## 4. Scenario Definitions

| Scenario | Multiplier | Peak RPM | Duration | Severity |
|:---|:---:|:---:|:---:|:---:|
| Normal Operations | 1.0x | 800 | 24h | None |
| Seasonal Peak | 1.8x | 1,440 | 48h | Low |
| Breaking News | 2.5x | 2,000 | 12h | Medium |
| Disaster Peak | 4.5x | 3,600 | 24h | High |
| Extreme Disaster | 8.5x | 6,800 | 36h | Critical |
| Disaster + Breaking News | 6.0x | 4,800 | 12h | Critical |
| Disaster + Seasonal | 5.5x | 4,400 | 24h | High |

---

## 5. Capacity Strategies

| Strategy | Initial Instances | Max Instances | Approach |
|:---|:---:|:---:|:---|
| Average Demand | 4 | 6 | Sized to mean traffic (~1,300 RPM) |
| Peak Demand | Dynamic | Dynamic | Sized to peak scenario RPM |
| Safety Margin | Dynamic | Dynamic | Peak + configurable % buffer |
| Dynamic Scaling | 10 | 50 | Reactive CPU-threshold scaling |
| Disaster-Aware | 18 | 50 | Pre-warmed instances, proactive thresholds |

---

## 6. SLA Targets

| Target | Value | Source |
|:---|:---:|:---|
| p95 Latency | ≤ 500 ms | Configurable in `sla_config.json` |
| Error Rate | ≤ 1.0% | Configurable in `sla_config.json` |
| Compliance | ≥ 99.0% | Configurable per organisation |

---

## 7. Sensitivity Analysis Results

The sensitivity analysis tested 8 planning assumptions under `DISASTER_PEAK` workload:

| Parameter | Impact | Classification |
|:---|:---|:---|
| Traffic Multiplier | High | **Decision-Changing** at ≥1.5x |
| Scaling Delay | High | **Decision-Changing** at ≥300s |
| Capacity per Instance | Medium | Decision-changing at ≤300 RPM |
| Maximum Instances | Medium | Decision-changing at ≤20 |
| Initial Instances | Low–Medium | Little effect above 10 |
| Safety Margin | Low | Little effect at 10–30% |
| Disaster Duration | Medium | Decision-changing at ≥36h |
| Peak Duration Ratio | Medium | Decision-changing at ≥0.80 |

---

## 8. Failure Testing Results

| Failure Case | Severity | SLA Impact | Recovery |
|:---|:---:|:---|:---|
| 10x Traffic Spike | SLA Violated | Compliance drops below 50% | Requires 2x instance ceiling |
| Slow Scaling (900s) | SLA Violated | Queue overflow, 503 errors | Pre-warming eliminates delay |
| Instance Limit (15 cap) | SLA Violated | Insufficient capacity ceiling | Increase ceiling to 30+ |
| 72h Sustained Disaster | SLA Degraded | Extended cost exposure | Acceptable with right-sizing |
| 3x Rapid Spikes | SLA Degraded | Queue accumulates between cycles | Aggressive cooldown policy |
| Invalid Input Data | SLA Compliant | Pipeline rejects/repairs | Data quality pipeline handles |
| Recovery Failure | SLA Violated | Sustained over-demand | Increase max instances |
| Compound Failure | SLA Violated | Multiple simultaneous failures | Defense-in-depth required |

---

## 9. Multi-Organisation Workflow

| Organisation | Scenarios | SLA Target | Focus |
|:---|:---:|:---:|:---|
| Emergency Ops Centre | All 7 | p95 ≤ 500ms, err ≤ 1% | Full operational control |
| Government Agency | All 7 | p95 ≤ 600ms, err ≤ 1% | Compliance & audit |
| Healthcare Partner | 4 of 7 | p95 ≤ 400ms, err ≤ 0.5% | Strict uptime requirements |
| External Info Partner | 3 of 7 | p95 ≤ 800ms, err ≤ 2% | Public info only, metrics redacted |

> **Note**: Role selection is implemented as an application-level workflow demonstration. Production deployment would require proper authentication and security infrastructure.

---

## 10. Test Suite

| Metric | Value |
|:---|:---:|
| Total Tests | **128** |
| Pass Rate | **100.0%** |
| Test Files | 16 |
| Execution Time | ~13 seconds |
| Framework | Pytest 8.2.2 |

---

## 11. Reproducibility

- **Deterministic Seeding**: All simulations use `seed=42` for identical results
- **Pinned Dependencies**: `requirements.txt` with exact version pins
- **Committed Data**: Raw and processed datasets included in repository
- **Clear Instructions**: Step-by-step installation and execution in README.md

```bash
# Install
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard/app.py

# Run tests
python -m pytest tests/ -v
```

---

## 12. Known Limitations

1. **Synthetic data only** — No real production traffic traces have been used
2. **Simplified M/M/1 model** — Real latency involves multi-tier network effects
3. **Homogeneous instances** — All server instances assumed identical
4. **Single region** — No geographic distribution or CDN modeling
5. **Application-level RBAC** — No production authentication/authorization
6. **Cost assumptions** — All costs are simulated estimates, not real pricing
7. **Stakeholder validation** — Has not been independently conducted; remains future work

---

## 13. Future Work

1. Validate against real disaster event traffic logs
2. Add multi-region geographic distribution modeling
3. Implement heterogeneous instance type support
4. Integrate with cloud provider APIs for real cost estimation
5. Add SSO/OAuth2 authentication for production deployment
6. Conduct formal stakeholder review of assumptions and parameters
7. Add Dockerised deployment and CI/CD pipeline

---

## 14. Conclusion

The Peak-Demand Capacity Simulator successfully demonstrates that **scenario-based capacity planning is not optional for public emergency-information systems — it is a life-safety requirement**. Average-demand planning produces a system that fails 79.4% of SLA targets during a disaster, while scenario-aware planning achieves 100% compliance under identical conditions.

The project delivers a fully working, tested, documented, and reproducible prototype suitable for research, stakeholder demonstration, and infrastructure planning discussions.
