# Telemetry Data Schema & Field Definitions

## Overview

The **Peak-Demand Capacity Simulator** utilizes a standardized data schema across raw historical telemetry, cleaned data pipelines, and simulation time-series outputs.

---

## Field Specifications

| Column Name | Data Type | Units | Valid Range / Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | `datetime64[ns]` | ISO Timestamp | YYYY-MM-DD HH:MM:SS | Time marker for telemetry record (10-second intervals). |
| `requests_per_minute` | `float64` | RPM | `[0.0, ∞)` | Inbound request volume per minute arriving at the web application. |
| `concurrent_users` | `int64` | Users | `[0, ∞)` | Active concurrent sessions connected to the application. |
| `cpu_utilisation` | `float64` | Percent (%) | `[0.0, 100.0]` | Average CPU utilization across active application instances. |
| `memory_utilisation` | `float64` | Percent (%) | `[0.0, 100.0]` | Average RAM utilization across active application instances. |
| `queue_depth` | `float64` | Requests | `[0.0, 50000.0]` | Number of incoming requests waiting in queue buffer. |
| `p95_latency_ms` | `float64` | Milliseconds | `[10.0, ∞)` | 95th percentile request processing response time. |
| `p99_latency_ms` | `float64` | Milliseconds | `[15.0, ∞)` | 99th percentile request processing response time. |
| `available_instances` | `int64` | Servers | `[1, 100]` | Number of operational application server instances currently active. |
| `instance_capacity_rpm` | `int64` | RPM / Server | `[100, 2000]` | Sustainable request throughput per single server instance (Default: 500 RPM). |
| `total_capacity_rpm` | `float64` | RPM | `[0.0, ∞)` | Combined fleet throughput (`available_instances * instance_capacity_rpm`). |
| `error_rate` | `float64` | Fractional (%) | `[0.0, 1.0]` | Proportion of requests resulting in HTTP 503 Service Unavailable errors. |
| `unmet_requests` | `float64` | Requests | `[0.0, ∞)` | Count of requests dropped during the timestep due to queue buffer overflow. |
| `event_type` | `string` | Categorical | `normal`, `seasonal`, `breaking_news`, `disaster`, `extreme_disaster` | Workload scenario classification tag. |
| `sla_status` | `string` | Categorical | `COMPLIANT`, `VIOLATED` | Indicator of whether performance met latency and availability SLA targets. |

---

## Data Cleaning & Validation Audit Rules

1. **Missing Values (NaN)**: Imputed using forward-fill followed by backward-fill.
2. **Negative Rates**: Clipped at `0.0`.
3. **Percentage Bounds**: Constrained strictly within `[0.0, 100.0]`.
4. **Total Capacity Math**: Recalculated as `active_instances * instance_capacity_rpm`.
