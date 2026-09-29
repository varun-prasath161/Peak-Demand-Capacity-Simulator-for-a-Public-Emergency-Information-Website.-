# Measurable Experiment Documentation: Average vs. Scenario-Based Capacity Planning

## Executive Summary

This document presents the methodology, experimental design, and empirical results of the **MVP Capacity Planning Experiment**. The objective was to test whether **Scenario-Based Capacity Planning** significantly improves service-level compliance over traditional **Average-Based Capacity Planning** under disaster stress workloads.

---

## Experimental Setup & Methodology

- **Test Workload**: `DISASTER_PEAK` scenario curve (peak demand: ~5,200 Requests Per Minute).
- **Service Level Targets**:
  - **p95 Response Latency**: <= 500 ms
  - **HTTP Error Rate**: <= 1.0%
- **Tested Models**:
  1. **Baseline Model (Average-Based Planning)**: Sized using historical mean demand (~1,300 RPM). Configured with 4 initial instances and a hard ceiling of 6 instances (3,000 RPM max capacity).
  2. **Scenario-Based Model (Peak Disaster Planning)**: Sized using anticipated disaster surge curves. Configured with 10 initial instances and a maximum ceiling of 20 instances (10,000 RPM max capacity).

---

## Empirical Comparison Matrix

| Measurement Metric | Baseline (Average-Based) | Scenario-Based (Peak-Based) | Measured Improvement / Delta |
| :--- | :---: | :---: | :---: |
| **Initial Instance Count** | 4 instances | 10 instances | +6 instances (+150%) |
| **Maximum Instance Ceiling** | 6 instances | 20 instances | +14 instances (+233%) |
| **Peak Demand (RPM)** | 5,200 RPM | 5,200 RPM | *Identical Test Load* |
| **Peak Provisioned Capacity** | 3,000 RPM | 7,000 RPM | **+4,000 RPM (+133%)** |
| **Peak Instances Reached** | 6 instances (Capped) | 14 instances | +8 instances |
| **Maximum Queue Depth** | 50,000 requests | 0 requests | **-50,000 requests (-100%)** |
| **Maximum p95 Latency** | 62,630 ms | 384 ms | **-62,246 ms (-99.4%)** |
| **Maximum Error Rate** | 65.11% | 0.00% | **-65.11%** |
| **Total Unmet / Dropped Requests** | 350,416 requests | 0 requests | **-350,416 dropped requests** |
| **SLA Compliance Percentage** | 20.6% | 100.0% | **+79.4% improvement** |
| **SLA Status Result** | ❌ **FAILED** | ✅ **PASSED** | **SERVICE RESTORED** |

---

## Detailed Findings & Error Analysis

### Why Baseline Average-Based Planning Fails
1. **Unbridgeable Shortfall**: Sizing infrastructure for 1,300 RPM average demand caps the server fleet at 6 instances (3,000 RPM). When a disaster surge hits 5,200 RPM, a 2,200 RPM capacity deficit immediately forms.
2. **Buffer Exhaustion**: Queuing theory (M/M/1) shows that when arrival rate exceeds service rate ($\lambda > \mu$), queue depth expands infinitely. The queue buffer hits its 50,000-request limit within 12 minutes.
3. **Severe SLA Degradation**: Response time explodes to 62,630ms, and 350,416 requests are dropped with HTTP 503 errors.

### Why Scenario-Based Planning Succeeds
1. **Surge-Matched Capacity Ceiling**: Expanding max instances to 20 servers allows the auto-scaler to scale to 14 instances (7,000 RPM capacity), maintaining positive headroom above 5,200 RPM peak demand.
2. **Elimination of Queue Buildup**: Request arrival rates stay below total fleet processing capacity, preventing queue accumulation.
3. **Flawless SLA Compliance**: p95 latency remains at 384ms (well within the 500ms SLA target), achieving **100.0% SLA compliance**.

---

## Conclusion & Recommendation

The experiment empirically proves that **Scenario-Based Capacity Planning improves service-level compliance from 20.6% to 100.0%**, completely eliminating dropped requests during disaster emergencies.

**Artifacts Generated**:
- Data CSV: [`outputs/before_after_comparison.csv`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/outputs/before_after_comparison.csv)
- Text Report: [`outputs/before_after_report.txt`](file:///c:/Users/Varun%20Prasath.J/Desktop/coe%20project/peak_demand_capacity_simulator/outputs/before_after_report.txt)
