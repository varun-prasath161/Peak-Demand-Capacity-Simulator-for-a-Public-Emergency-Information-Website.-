# Historical Load Analysis

## 1. Dataset Information

* **Dataset Name**: `emergency_load_cleaned.csv`
* **Number of Rows**: 3,882 records
* **Number of Columns**: 34 operational telemetric features
* **Time Period**: `2025-01-01 00:00:00` to `2025-10-31 22:00:00` (~10 months)
* **Data Source Type**: **Synthetic Historical-Style Operational Data**

> **Note**: This dataset represents realistic **Synthetic Historical-Style Operational Data** generated deterministically to model ~10 months of emergency website load under normal, seasonal, news event, and disaster peak scenarios. It is not real production historical telemetry.

---

## 2. Traffic Analysis

* **Average Requests per Minute**: `953.1 RPM`
* **Median Requests per Minute**: `456.9 RPM`
* **Maximum Requests per Minute**: `43,441.6 RPM`
* **P95 Requests per Minute**: `2,548.8 RPM`
* **P99 Requests per Minute**: `18,479.7 RPM`
* **Peak-to-Average Traffic Ratio**: `45.58x`

---

## 3. Capacity Analysis

* **Average Available Instances**: `10.8 instances`
* **Maximum Available Instances**: `50 instances`
* **Maximum Sustainable Capacity**: `25,000 RPM`
* **Average CPU Utilisation**: `10.3%`
* **Maximum CPU Utilisation**: `100.0%`

---

## 4. Queue Analysis

* **Average Queue Depth**: `1,329,877.4 requests`
* **Maximum Queue Depth**: `5,453,350.1 requests`
* **P95 Queue Depth**: `5,304,670.1 requests`

---

## 5. Performance Analysis

* **Average Response Latency**: `62.0 ms`
* **Maximum Response Latency**: `4,863.3 ms`
* **P95 Response Latency**: `95.5 ms`
* **P99 Response Latency**: `8,717.0 ms`

---

## 6. Error Analysis

* **Average Error Rate**: `0.248%`
* **Maximum Error Rate**: `50.00%`
* **P95 Error Rate**: `0.173%`

---

## 7. Scaling Analysis

* **Number of Scale-Out Events**: `27`
* **Number of Scale-In Events**: `12`
* **Total Scaling Actions**: `39`
* **Average Scaling Propagation Delay**: `3276.9 seconds`

---

## 8. SLA Analysis

* **Total Records Evaluated**: `3,882`
* **SLA Compliant Records**: `3,828`
* **SLA Violation Records**: `54`
* **Overall SLA Compliance Percentage**: `98.61%`

---

## 9. Scenario Comparison

| Scenario Name | Record Count | Avg Traffic (RPM) | Peak Traffic (RPM) | Avg Queue | Max Queue | Max p95 Latency (ms) | Max Error Rate (%) | Max Utilisation (%) | Scaling Actions | SLA Compliance (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **extreme_disaster** | 128 | 12,253.6 | 43,441.6 | 2,416,036.2 | 5,453,350.1 | 11,311.9 | 50.00% | 99.8% | 17 | 68.75% |
| **disaster** | 184 | 3,647.2 | 13,500.2 | 932,076.5 | 1,775,309.8 | 6,386.9 | 8.92% | 99.8% | 22 | 92.39% |
| **breaking_news** | 31 | 637.4 | 3,430.2 | 1,498,160.7 | 5,354,310.1 | 161.3 | 0.17% | 59.8% | 0 | 100.00% |
| **seasonal** | 168 | 551.1 | 1,502.1 | 713,695.8 | 1,718,794.0 | 97.9 | 0.19% | 25.0% | 0 | 100.00% |
| **normal** | 3,371 | 399.8 | 920.0 | 1,339,509.2 | 5,439,110.1 | 107.2 | 0.27% | 100.0% | 0 | 100.00% |

---

## 10. Key Observations

1. **Massive Surge Multipliers During Disasters**:
   - During `extreme_disaster` events, traffic surged up to `43441.6` RPM -- representing a `45.58x` peak-to-average surge ratio over everyday baseline load (`953.1` RPM).
2. **Non-Linear Queue & Latency Degradation**:
   - Normal operating conditions experienced `62.0 ms` average latency and `0.0` queue depth. However, during disaster surges when load exceeded available capacity, queues rapidly accumulated up to `5453350.1` requests and p95 latency degraded up to `95.5 ms`.
3. **Auto-Scaling Propagation Lag Impact**:
   - The average scaling provisioning delay of `3276.9 seconds` created temporary buffer exhaustion during sudden disaster onset, causing brief SLA breach windows before new instances came online.
4. **Disaster Peak Preservation**:
   - High-volume disaster surges were explicitly preserved in dataset cleaning rather than discarded as statistical outliers, accurately capturing worst-case operational stress.

---

## 11. Limitations

* **Synthetic Dataset**: Telemetry is generated via mathematical simulation models and domain rules rather than collected from live web servers.
* **Bounded Infrastructure Ceiling**: Hard instance caps (`max_instances = 50`) prevent unlimited horizontal scaling during catastrophic multi-region events.
* **Simplified Network Topology**: Network transit delays, database lock contentions, and CDN caching edge hits are modeled at an aggregate service layer rather than full distributed trace level.
* **Absence of Live Production Telemetry**: All metrics reflect synthetic historical operational patterns.
