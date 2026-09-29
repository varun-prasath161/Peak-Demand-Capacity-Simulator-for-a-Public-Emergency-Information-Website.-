# Dashboard User Guide
## Peak-Demand Capacity Simulator for Public Emergency-Information Websites

This comprehensive guide details the structure, user workflows, operational configurations, and interpretation of metrics for the Peak-Demand Capacity Simulator Streamlit Dashboard.

---

## 1. Dashboard Overview

The Peak-Demand Capacity Simulator is an interactive web-based decision-support tool engineered to evaluate the resilience of public emergency-information portals during crisis surges. By moving beyond static average-demand provisioning, the simulator allows emergency response planners, infrastructure operators, policy analysts, and leadership executives to stress-test capacity strategies against empirical disaster profiles.

The dashboard integrates:
* **Plain-Language Executive Summary:** Translates raw metrics into non-technical operational advisories at the very top of the dashboard.
* **10 Operational Sections:** Spanning real-time simulation, historical telemetry, multi-scenario comparisons, sensitivity evaluations, and failure-case stress-tests.
* **Explainable Recommendation Engine:** Provides evidence-backed capacity actions detailing *Situation, Evidence, Impact, Recommended Action,* and *Reason*.
* **Before vs After Visual Comparison:** Contrasts traditional average-demand planning with scenario-based capacity models.
* **Multi-Organisation Role-Based Access Control (RBAC):** Restricts features and operational controls according to organizational profile and authenticated roles.

---

## 2. Organisation Selection

Located in the left sidebar, the **Organisation** selector sets the active organizational context. Each organisation has distinct statutory mandates, scenario authorizations, and statutory SLA baselines:

1. **Emergency Operations Centre (EOC):**
   * *Mandate:* Primary disaster coordination authority managing crisis alerts and emergency broadcasts.
   * *Allowed Scenarios:* All 7 scenarios (`NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`, `EXTREME_DISASTER`, `DISASTER_BREAKING_NEWS`, `DISASTER_SEASONAL`).
   * *Default SLA Target:* 500 ms p95 latency, 1.0% error rate, 99.0% compliance.
   * *Infrastructure Visibility:* Full visibility into instance counts, container metrics, and scaling internals.

2. **Government Agency:**
   * *Mandate:* Regional and federal oversight authority managing inter-agency resilience audits.
   * *Allowed Scenarios:* All 7 scenarios.
   * *Default SLA Target:* 600 ms p95 latency, 1.0% error rate, 98.0% compliance.
   * *Infrastructure Visibility:* Full visibility across audit reports and system configurations.

3. **Healthcare Partner:**
   * *Mandate:* Regional hospital networks and emergency services monitoring clinical advisories.
   * *Allowed Scenarios:* `NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`.
   * *Default SLA Target:* Strict uptime requirement: 400 ms p95 latency, 0.5% error rate, 99.5% compliance.

4. **External Information Partner:**
   * *Mandate:* Commercial media syndicates and civic relays distributing public advisories.
   * *Allowed Scenarios:* `NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`.
   * *Default SLA Target:* 800 ms p95 latency, 2.0% error rate, 95.0% compliance.
   * *Infrastructure Visibility:* **Sensitive Infrastructure Redaction Active.** Server instance numbers, cluster capacity, and backend thresholds are redacted (`[REDACTED]`).

---

## 3. Role Selection

The **User Permission Level** selector in the sidebar governs operational privileges and dashboard viewability:

| Role | Intended Audience | Permitted Actions | Visible Dashboard Sections |
| :--- | :--- | :--- | :--- |
| **Viewer** | Public stakeholders, non-technical observers, external media | Read-only inspection of simulation results and high-level charts. | Executive Overview, Historical Load, Scenario Selection, Simulation, SLA Results, Capacity Recommendation, Before vs After |
| **Analyst** | Policy researchers, performance auditors | Execute simulations, compare scenarios, inspect historical telemetry and sensitivity analyses. | All Viewer sections + Strategy Comparison, Sensitivity Analysis |
| **Operator** | SREs, cloud engineers, emergency site administrators | Modify operational parameters (initial/max instances, scaling delay, capacity, safety margin), run failure testing. | All Analyst sections + Capacity Configuration, Failure Testing |
| **Administrator** | Systems architects, IT directors | Modify statutory SLA thresholds, configure multi-org policies, inspect all internal audit records. | All Operator sections + Organisation Settings, System Administration |

*Note:* In Viewer and Analyst modes, operational sliders in the sidebar are disabled with a visual lock indicator to prevent inadvertent configuration changes.

---

## 4. Scenario Selection

Permitted users can select from seven standardized emergency workload profiles:

1. **Normal (`NORMAL`):** Typical daily baseline traffic (1.0x baseline, ~960 RPM).
2. **Seasonal Peak (`SEASONAL_PEAK`):** Predictable holiday or seasonal weather watch surges (1.5x - 2.0x baseline, ~1,740 RPM).
3. **Breaking News (`BREAKING_NEWS`):** Sudden breaking events causing rapid bursts within 10-15 minutes (2.0x - 3.0x baseline, ~2,080 RPM).
4. **Disaster Peak (`DISASTER_PEAK`):** Major regional crisis (Category 3 Hurricane / Major Flood) sustaining high traffic for several hours (3.0x - 5.0x baseline, ~5,020 RPM).
5. **Extreme Disaster (`EXTREME_DISASTER`):** Catastrophic regional emergency (Category 5 Hurricane / Tsunami) pushing demand to 5.0x - 8.5x baseline (~8,460 RPM).
6. **Disaster + Breaking News (`DISASTER_BREAKING_NEWS`):** Ongoing disaster compounded by emergency evacuation or dam breach announcements (4.0x - 7.0x baseline, ~6,000 RPM).
7. **Disaster + Seasonal Peak (`DISASTER_SEASONAL`):** Major disaster striking during peak seasonal travel or holiday volume (4.0x - 6.5x baseline, ~5,830 RPM).

---

## 5. Capacity Configuration

Authorized Operators and Administrators can adjust the following parameters:

* **Initial Instances (2 to 30):** Baseline pool of servers active prior to surge arrival.
* **Maximum Instances (10 to 100):** Upper ceiling enforced by budget or infrastructure quotas.
* **Instance Capacity (100 to 1500 RPM):** Sustainable throughput per individual web instance under linear queueing before response latency begins degrading.
* **Scaling Delay (30 to 600 seconds):** Provisioning latency required for a new cloud VM/container to boot, configure, and register with the load balancer.
* **Safety Margin (0% to 50%):** Headroom over-provisioning factor applied above expected demand.

---

## 6. Running a Simulation

1. Set the desired **Organisation** and **Role** in the sidebar.
2. Choose a **Workload Scenario** authorized for that profile.
3. If an Operator or Administrator, adjust capacity settings (or leave at calibrated defaults).
4. Click **🚀 Re-Run Simulation** in the sidebar.
5. The discrete-event simulation engine executes, processing minute-by-minute request arrivals, queue buffering, dynamic scaling triggers, latency degradation curves, and SLA compliance checks.
6. All dashboard charts and the Explainable Recommendation Engine update automatically.

---

## 7. Understanding SLA Results

Section 6 evaluates performance against statutory Service-Level Agreement targets:

* **SLA Targets:**
  * *Latency Target:* Statutory limit on 95th percentile response time (typically 500 ms).
  * *Error Rate Target:* Statutory ceiling on failed or timed-out requests (typically 1.0%).
  * *Compliance Percentage Target:* Statutory proportion of the incident where targets must be satisfied (typically 99.0%).
* **SLA Status Classifications:**
  * **SLA Compliant (Green):** Compliance >= Target, max p95 latency <= Target, and error rate <= Target.
  * **SLA Degraded (Amber):** Compliance is between 90.0% and the target, or transient brief spikes occurred during the surge onset.
  * **SLA Violated (Red):** Compliance < 90.0%, sustained queue accumulation, or requests dropped due to queue exhaustion.
* **Violation Duration:** The total elapsed minutes during which latency or error rate exceeded SLA boundaries.
* **SLA Status Timeline:** A color-coded bar chart marking met (green) vs breached (red) intervals across the simulated timeline.

---

## 8. Understanding Sensitivity Analysis

Section 8 presents the findings of multi-factor sensitivity experiments across 8 critical operational parameters:
1. **Traffic Multiplier:** Peak arrival amplitude scaling (0.7x to 2.0x).
2. **Scaling Delay:** Boot latency from 60s to 600s.
3. **Instance Capacity:** Server throughput from 300 to 800 RPM.
4. **Maximum Instances:** Fleet ceiling from 20 to 80 instances.
5. **Initial Instances:** Standby base pool from 5 to 20 instances.
6. **Safety Margin:** Buffer headroom from 0% to 30%.
7. **Disaster Duration:** Crisis duration from 12h to 36h.
8. **Peak Duration Ratio:** Proportion of time spent at maximum surge (0.4 to 0.8).

**Decision-Changing Assumptions:** The dashboard explicitly separates parameters whose variation causes an SLA status flip or major queue backlog ("Decision-Changing") from those that have minor impact ("Little Effect"), directing engineering attention to critical bottlenecks.

---

## 9. Understanding Failure Cases

Section 9 details resilience stress-tests under 8 extreme failure conditions:
* **Extreme Traffic Spike:** 10x multiplier on Extreme Disaster.
* **Slow Scaling Lag:** Provisioning delays of 300s to 900s.
* **Max Instance Exhaustion:** Premature instance ceiling under moderate disaster.
* **Long-Duration Overload:** Sustained 72-hour disaster window.
* **Rapid Successive Spikes:** Repeated oscillation without cooldown.
* **Recovery Failure:** Indefinite queue saturation where drain time exceeds arrival rates.
* **Compound Failure:** Combined multi-vector stress (high surge, slow provisioning, capped instances).

Metrics evaluated include Peak Demand, Peak Capacity, Queue Depth, Latency, Error Rate, SLA Status, and Recovery Time.

---

## 10. Understanding Recommendations

The **Explainable Recommendation Engine** translates complex technical simulation outputs into 5 plain-language fields:
1. **Situation:** What is occurring in non-technical terms.
2. **Evidence:** Measured numerical facts supporting the finding (e.g. peak demand reached 5,016 RPM while fleet capacity was 3,000 RPM).
3. **Impact:** Consequences if no corrective action is taken (e.g. user queue delay, citizen inability to access evacuation maps).
4. **Recommended Action:** Concrete operational guidance (e.g. increase maximum instance ceiling or pre-warm servers before the surge).
5. **Reason (Why?):** The mechanical justification for why the recommendation resolves the problem.

All recommendations are traceable to specific metric thresholds and logged to `outputs/recommendations.csv`.

---

## 11. Important Assumptions

* **Linear Capacity Scaling:** Application instances are assumed to scale horizontally with stateless web workers; database contention is modeled via queue buildup rather than non-linear locking.
* **Scaling Boot Lag:** The autoscaler incurs a delay (`scaling_delay_seconds`) between issuing a scale-out trigger and the instance becoming healthy to serve traffic.
* **Queue Buffering:** Inbound requests beyond instant capacity accumulate in memory queues. If queues persist too long, response times spike, eventually triggering timeout errors.
* **Pre-Warming Lead Time:** Disaster-aware planning assumes emergency weather alerts provide sufficient advance notice to spin up instances before public demand spikes.

---

## 12. Synthetic-Data Limitation

* **Synthetic Workload Telemetry:** All historical load telemetry and simulated scenario envelopes are synthetic models calibrated against public incident case studies (e.g. government emergency announcements, hurricane alerts).
* **Environment Differences:** Real-world cloud platforms may experience variable provisioning times, network jitter, or third-party dependency outages not fully captured in deterministic discrete-event simulations.
* **Operational Intent:** The simulator is intended as a strategic capacity planning and policy analysis tool, rather than a substitute for live end-to-end load testing in production environments.
