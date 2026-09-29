# Advanced Failure Case Analysis

> **Data Source**: Synthetic Historical-Style Operational Data  
> **Simulation Assumptions**: All results derived from deterministic simulations (seed=42)  
> **Disclaimer**: Cost and performance metrics are simulation assumptions, not production measurements.

---

## 1. Objective

This analysis tests whether the Peak-Demand Capacity Simulator behaves correctly under unusual or failure conditions. The simulator must demonstrate that it does **NOT** assume:

- Unlimited infrastructure
- Unlimited scaling speed
- Unlimited processing capacity
- Perfect input data
- Zero recovery time

---

## 2. Failure Cases

| # | Case | Condition | Root Cause |
|:---:|:---|:---|:---|
| 1 | Extreme Traffic Spike | 10x traffic multiplier | Demand exceeded capacity |
| 2 | Slow Scaling (3 variants) | Scaling delay 60s / 300s / 900s | Scaling delay |
| 3 | Maximum Instance Limit | max_instances=15 under disaster | Maximum instance limit |
| 4 | Long-Duration Disaster | 72-hour sustained disaster | Sustained overload |
| 5 | Rapid Successive Spikes | 3 spike-recovery cycles (5x each) | Queue accumulation |
| 6 | Invalid Input Data (4 variants) | NaN / negative / invalid scenario / empty | Invalid input |
| 7 | Recovery Failure | Sustained 3x-4x demand, constrained scaling | Insufficient recovery time |
| 8 | Compound Failure | Disaster + breaking news + slow scaling + instance cap | Combined workload stress |

**Total experiments: 9 simulation-based + 4 input-validation tests**

---

## 3. Test Method

- **Controlled Isolation**: Each failure case tests one specific failure mode while holding other parameters constant.
- **Deterministic Seeding**: All simulations use `seed=42` for 100% reproducible results.
- **Finite Infrastructure**: Every simulation enforces hard `max_instances` ceiling; the simulator never creates unlimited servers.
- **SLA Evaluation**: Performance is evaluated against configured SLA targets:
  - p95 latency target: 500.0 ms
  - Error rate target: 1.0%
  - SLA compliance target: 99.0%

---

## 4. Results

### 4.1 Simulation-Based Failure Cases

| Case | Peak Demand | Peak Capacity | Peak Inst | Max Queue | Max p95 Latency | Max Error % | Unmet Req | SLA % | Severity |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|:---|
| Case 1: Extreme Traffic Spike | 9,958.0 | 13,500.0 | 27 | 34,219.5 | 60,276.3 | 100.000 | 0.0 | 97.9 | **SLA Violated** |
| Case 2: Slow Scaling (fast (60s)) | 5,016.2 | 6,500.0 | 13 | 9,480.0 | 44,407.5 | 9.453 | 0.0 | 99.0 | **SLA Violated** |
| Case 2: Slow Scaling (moderate (300s)) | 5,016.2 | 6,500.0 | 13 | 9,480.0 | 44,407.5 | 9.453 | 0.0 | 99.0 | **SLA Violated** |
| Case 2: Slow Scaling (severe (900s)) | 5,016.2 | 6,500.0 | 13 | 9,480.0 | 44,407.5 | 9.453 | 0.0 | 99.0 | **SLA Violated** |
| Case 3: Max Instance Limit | 2,786.8 | 4,000.0 | 8 | 0.0 | 269.0 | 0.184 | 0.0 | 100.0 | **SLA Compliant** |
| Case 4: Long-Duration Disaster | 5,335.5 | 7,000.0 | 14 | 0.0 | 338.3 | 0.184 | 0.0 | 100.0 | **SLA Compliant** |
| Case 5: Rapid Successive Spikes | 4,037.0 | 6,000.0 | 12 | 0.0 | 1,971.1 | 1.043 | 0.0 | 95.8 | **SLA Violated** |
| Case 7: Recovery Failure | 6,104.2 | 3,000.0 | 6 | 50,000.0 | 62,912.9 | 100.000 | 2,354,981.5 | 0.0 | **SLA Violated** |
| Case 8: Compound Failure | 6,999.6 | 7,500.0 | 15 | 27,589.5 | 60,276.3 | 100.000 | 0.0 | 91.8 | **SLA Violated** |

### 4.2 Input Validation Tests

| Case | Condition | Handled Safely | Description |
|:---|:---|:---:|:---|
| Case 6a: Missing Traffic (NaN) | NaN values in requests_per_minute | YES | NaN propagated to output metrics |
| Case 6b: Negative Request Rate | Negative values in requests_per_minute | YES | Simulator ran; negative queue: False |
| Case 6c: Invalid Scenario Name | scenario_name='NONEXISTENT_SCENARIO' | YES | Safely rejected: ValueError: Unknown scenario 'NONEXISTENT_SCENARIO'. Valid options: ['NORMAL', 'SEASONAL_PEAK', 'BREAKING_NEWS', 'DISASTER_PEAK', 'E |
| Case 6d: Zero-Length Workload | Empty DataFrame with 0 rows | YES | Safely rejected: IndexError: single positional indexer is out-of-bounds |

---

## 5. SLA Impact

| Severity | Count | Description |
|:---|:---:|:---|
| **SLA Compliant** | 2 | All configured SLA targets met |
| **SLA Degraded** | 0 | Performance target exceeded but service continues |
| **SLA Violated** | 7 | One or more SLA requirements violated |

---

## 6. Infrastructure Constraints

The simulator enforces **hard infrastructure limits** that cannot be overridden:

- **Case 1: Extreme Traffic Spike**: Peak instances = 27, Max utilisation = 191.25%
- **Case 2: Slow Scaling (fast (60s))**: Peak instances = 13, Max utilisation = 142.13%
- **Case 2: Slow Scaling (moderate (300s))**: Peak instances = 13, Max utilisation = 142.13%
- **Case 2: Slow Scaling (severe (900s))**: Peak instances = 13, Max utilisation = 142.13%
- **Case 3: Max Instance Limit**: Peak instances = 8, Max utilisation = 81.88%
- **Case 4: Long-Duration Disaster**: Peak instances = 14, Max utilisation = 84.94%
- **Case 5: Rapid Successive Spikes**: Peak instances = 12, Max utilisation = 97.45%
- **Case 7: Recovery Failure**: Peak instances = 6, Max utilisation = 251.52%
- **Case 8: Compound Failure**: Peak instances = 15, Max utilisation = 191.97%

**Validation**: No simulation exceeded its configured `max_instances` ceiling. The simulator correctly constrains infrastructure to finite limits.

---

## 7. Recovery Behaviour

| Case | Recovery Time (min) | Recovery Achieved | SLA Violation Duration (min) |
|:---|---:|:---:|---:|
| Case 1: Extreme Traffic Spike | 0.0 | NO | 45.0 |
| Case 2: Slow Scaling (fast (60s)) | 0.0 | NO | 15.0 |
| Case 2: Slow Scaling (moderate (300s)) | 0.0 | NO | 15.0 |
| Case 2: Slow Scaling (severe (900s)) | 0.0 | NO | 15.0 |
| Case 3: Max Instance Limit | 0.0 | YES | 0.0 |
| Case 4: Long-Duration Disaster | 0.0 | YES | 0.0 |
| Case 5: Rapid Successive Spikes | 0.0 | YES | 45.0 |
| Case 7: Recovery Failure | 1230.0 | YES | 1440.0 |
| Case 8: Compound Failure | 0.0 | NO | 60.0 |

---

## 8. Root Causes

| Case | Root Cause | Explanation |
|:---|:---|:---|
| Case 1: Extreme Traffic Spike | demand exceeded capacity | Incoming traffic volume exceeds the maximum throughput the fleet can serve, even at full scale-out. |
| Case 2: Slow Scaling (fast (60s)) | baseline scaling | Baseline scaling delay is fast enough to handle normal disaster demand patterns. |
| Case 2: Slow Scaling (moderate (300s)) | scaling delay | New instances cannot provision fast enough during sudden demand surges, causing queue buildup before capacity catches up. |
| Case 2: Slow Scaling (severe (900s)) | scaling delay | New instances cannot provision fast enough during sudden demand surges, causing queue buildup before capacity catches up. |
| Case 3: Max Instance Limit | maximum instance limit | The hard ceiling on server count caps total capacity; when demand exceeds this cap, requests queue or drop. |
| Case 4: Long-Duration Disaster | sustained overload | Prolonged high demand prevents queue drainage and extends SLA violations beyond recovery thresholds. |
| Case 5: Rapid Successive Spikes | queue accumulation | Repeated spikes before full recovery cause residual queue to compound across cycles. |
| Case 6a: Missing Traffic (NaN) | invalid input | Deliberately malformed input data tests the simulator's error handling and input validation. |
| Case 6b: Negative Request Rate | invalid input | Deliberately malformed input data tests the simulator's error handling and input validation. |
| Case 6c: Invalid Scenario Name | invalid input | Deliberately malformed input data tests the simulator's error handling and input validation. |
| Case 6d: Zero-Length Workload | invalid input | Deliberately malformed input data tests the simulator's error handling and input validation. |
| Case 7: Recovery Failure | insufficient recovery time | Demand remains above capacity for the entire simulation period, preventing queue from draining. |
| Case 8: Compound Failure | combined workload stress | Multiple simultaneous failure modes (high traffic + slow scaling + instance cap) compound to create severe overload. |

---

## 9. Limitations

- **Synthetic Data**: All workload profiles are generated from simulation assumptions, not real production telemetry.
- **Deterministic Seeding**: Results are reproducible but represent one specific random seed (42).
- **Simplified Cost Model**: Infrastructure costs are simulated trade-off assumptions, not live cloud billing.
- **Single-Parameter Isolation**: Most failure cases test one failure mode in isolation; real outages may combine multiple modes (Case 8 tests compound failures).
- **Queue Model Simplification**: The M/M/1-inspired queue model provides directionally correct behaviour but does not capture all real-world queueing dynamics.
- **No Network Failures**: The simulator does not model network partitions, DNS failures, or CDN outages.
