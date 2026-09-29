# Stakeholder Assumptions & Parameter Baselines

## Overview

Capacity planning for public emergency websites requires aligning technical simulation parameters with realistic operational assumptions agreed upon by stakeholders (emergency operations centers, state disaster authorities, and infrastructure teams).

---

## Key Assumption Categories

### 1. Expected Traffic Behaviour
- **Baseline Demand**: Everyday non-emergency traffic operates at an average of **1,300 Requests Per Minute (RPM)** with mild diurnal variation (+/- 20%).
- **Surge Multipliers**:
  - `NORMAL`: 1.0x baseline (~1,300 RPM peak)
  - `SEASONAL_PEAK`: 1.8x baseline (~2,340 RPM peak)
  - `BREAKING_NEWS`: 2.5x baseline (~3,250 RPM peak)
  - `DISASTER_PEAK`: 4.0x baseline (~5,200 RPM peak)
  - `EXTREME_DISASTER`: 6.5x baseline (~8,450 RPM peak)
- **Surge Structure**: Traffic surges follow a 3-phase curve: rapid 15-minute ramp-up, sustained peak plateau, and exponential recovery decay.

### 2. Infrastructure Capacity Constraints
- **Single Instance Throughput**: Each application server instance can process up to **500 RPM** at standard SLA latency.
- **Base Fleet Sizing**: Baseline non-emergency infrastructure is provisioned with **10 initial instances** (5,000 RPM capacity).
- **Maximum Fleet Ceiling**: Maximum allowable cloud instance limit is capped at **50 instances** (25,000 RPM capacity) due to cloud quota and budget boundaries.

### 3. Auto-Scaling Propagation Delay
- **Provisioning Lag**: Cloud auto-scaling step actions require **180 seconds (3 minutes)** from scale-out trigger to instance health check pass and traffic ingress.
- **Scale-Out Trigger**: Triggered when fleet average CPU/RPM utilization exceeds **70%**. Urgency increases when utilization exceeds **85%**.
- **Scale-In Cooldown**: Sustained low utilization (< 40%) required for 10 minutes before instance scale-in is permitted.

### 4. Service Level Agreement (SLA) Targets
- **Latency SLA**: 95th percentile response time (p95 latency) must remain **<= 500 milliseconds**.
- **Availability SLA**: HTTP 503 error rate must remain **<= 1.0%** of total inbound requests.
- **Target Compliance**: Minimum acceptable scenario SLA compliance is **100.0%**.

### 5. Disaster Event Severity
- **Disaster Peak Duration**: Extreme disaster surges maintain peak demand for at least **30 to 45 minutes** before decaying.
- **Concurrent User Surge**: Concurrent connected users scale linearly with incoming request volume during crisis events.

### 6. Data & Simulation Limitations
- **Homogeneous Node Performance**: Assumes all application server instances possess identical CPU and RAM capacity.
- **Simplified Queuing Model**: Uses M/M/1 queuing approximations for latency degradation under load.
- **Single Region Ingress**: Assumes a single geographic ingress point without global multi-region CDN caching effects.
