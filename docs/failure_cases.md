# Edge Case & Failure Mode Analysis Report

## Executive Overview

This report documents the empirical behavior of the **Peak-Demand Capacity Simulator** under five extreme operational edge cases and failure modes. To ensure realistic capacity planning, **failures are transparently analyzed** rather than hidden.

---

## Edge Case Evaluation Summary

| Case ID | Edge / Failure Case Name | Peak Demand | Max p95 Latency | SLA Status | Unmet Requests / Queue |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **CASE_1** | Extreme Traffic Spike | 8,412 RPM | 56,709 ms | ❌ VIOLATED | Queue: 50,000 | 
| **CASE_2** | Scaling Delay During Disaster | 5,027 RPM | 505 ms | ✅ COMPLIANT | Queue: 0 | 
| **CASE_3** | Maximum Instance Limit Reached | 5,027 RPM | 62,630 ms | ❌ VIOLATED | Queue: 50,000 | 
| **CASE_4** | Queue Grows Faster Than Recovery | 8,412 RPM | 62,913 ms | ❌ VIOLATED | Queue: 50,000 | 
| **CASE_5** | Missing or Corrupted Input Data | 1,200 RPM | 20 ms | ✅ COMPLIANT | Queue: 0 | 


---

## Detailed Failure Mode Breakdowns

### CASE_1: Extreme Traffic Spike

- **Description**: Traffic suddenly spikes to extreme disaster levels, exceeding maximum fleet capacity.
- **SLA Status**: `❌ SLA VIOLATED` (Compliance: `40.0%`)
- **Peak Demand**: `8,412 RPM` | **Peak Capacity**: `6,000 RPM`
- **Max Queue Depth**: `50,000` | **Max p95 Latency**: `56,709 ms` | **Max Error Rate**: `21.19%`

#### Failure Mechanism
> Traffic surged to 8,412 RPM, exceeding max capacity of 6,000 RPM.

#### System Response & Graceful Handling
> Fleet scaled to max (12 instances). Queue rose to 50,000 requests; 119,230 requests dropped.

---
### CASE_2: Scaling Delay During Disaster

- **Description**: Auto-scaling is delayed by 10 minutes (600s) during a sudden 4.0x disaster surge.
- **SLA Status**: `✅ SLA MET` (Compliance: `99.0%`)
- **Peak Demand**: `5,027 RPM` | **Peak Capacity**: `6,500 RPM`
- **Max Queue Depth**: `0` | **Max p95 Latency**: `505 ms` | **Max Error Rate**: `0.18%`

#### Failure Mechanism
> Severe 600s scaling lag prevented new instances from launching during early peak.

#### System Response & Graceful Handling
> System operated on initial 5 instances during peak surge, causing p95 latency to hit 505ms.

---
### CASE_3: Maximum Instance Limit Reached

- **Description**: Infrastructure ceiling hard-capped at 5 instances despite 5.0x disaster demand.
- **SLA Status**: `❌ SLA VIOLATED` (Compliance: `16.5%`)
- **Peak Demand**: `5,027 RPM` | **Peak Capacity**: `2,500 RPM`
- **Max Queue Depth**: `50,000` | **Max p95 Latency**: `62,630 ms` | **Max Error Rate**: `100.0%`

#### Failure Mechanism
> Maximum instance cap (5) reached while demand reached 5,027 RPM.

#### System Response & Graceful Handling
> Auto-scaler halted at instance ceiling; backlog accumulated to 50,000 queued requests.

---
### CASE_4: Queue Grows Faster Than Recovery

- **Description**: Sustained overload causes queue backlog to exceed maximum queue capacity, dropping requests.
- **SLA Status**: `❌ SLA VIOLATED` (Compliance: `20.7%`)
- **Peak Demand**: `8,412 RPM` | **Peak Capacity**: `3,200 RPM`
- **Max Queue Depth**: `50,000` | **Max p95 Latency**: `62,913 ms` | **Max Error Rate**: `100.0%`

#### Failure Mechanism
> Incoming request rate exceeded processing speed for sustained duration, causing queue buffer exhaustion.

#### System Response & Graceful Handling
> Queue reached capacity cap; 3,911,562 unmet requests were dropped with HTTP 503 error rate of 100.00%.

---
### CASE_5: Missing or Corrupted Input Data

- **Description**: Input dataset contains missing timestamps, negative traffic rates, and non-numeric values.
- **SLA Status**: `✅ SLA MET` (Compliance: `100.0%`)
- **Peak Demand**: `1,200 RPM` | **Peak Capacity**: `2,500 RPM`
- **Max Queue Depth**: `0` | **Max p95 Latency**: `20 ms` | **Max Error Rate**: `0.0%`

#### Failure Mechanism
> Input dataset contained NaN values, negative rates, and out-of-bound percentages.

#### System Response & Graceful Handling
> Pipeline handled corruption gracefully: Impugned/dropped 3882 records, set zero missing values remaining.

---
## Key Lessons & Architectural Guidance

1. **Auto-Scaling Delay is the Primary Vector for Initial Latency Spikes**: Even when total server ceiling is adequate, a 10-minute scaling delay creates an unavoidable queue backlog during early disaster surge phases.
2. **Hard Instance Caps Guarantee Failure During Extreme Disaster**: Hard-capping instances at baseline limits under a 5x surge leads directly to buffer exhaustion and dropped user requests.
3. **Graceful Degradation via Defensive Cleaning**: Invalid telemetry (missing timestamps, negative traffic) must be sanitized before driving automated scaling actions to prevent improper scaling decisions.
