# Peak-Demand Capacity Simulator for a Public Emergency-Information Website

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-FF4B4B?logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-128%20Passed-brightgreen)
![Status](https://img.shields.io/badge/Status-Modules%201--10%20Complete-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Project Objective

Build an **end-to-end working prototype** that uses **workload scenarios** — instead of
average utilisation — to estimate infrastructure capacity requirements and demonstrate
service-level compliance during simulated peak demand on a public emergency-information
website.

The simulator answers:

> *"Given a Category-5 hurricane making landfall, can our current infrastructure serve
> every citizen request within the promised response-time SLA?"*

---

## Problem Statement

A public emergency-information website **must remain available during disasters** — the
exact moments when traffic surges far beyond everyday levels. Current capacity planning
relies primarily on **average demand metrics**, which dangerously underestimates the
resources needed when it matters most.

### Why Average Utilisation Is Insufficient

| Aspect | Average-Based Planning | Scenario-Based Planning |
|---|---|---|
| **Traffic model** | Smooth, steady-state | Bursty, event-driven spikes |
| **Peak coverage** | Misses tail events | Explicitly models worst-case surges |
| **Risk visibility** | Hidden until failure | Quantified before deployment |
| **SLA confidence** | Low during crises | Validated per scenario |
| **Cost trade-off** | Under- or over-provisioned | Right-sized to defined risk tolerance |

Average utilisation masks the **variance** in request arrival rates. A server fleet running
at 40 % average CPU can still collapse under a 10× traffic spike that lasts only 15 minutes
— exactly the kind of spike a natural disaster produces.

---

## Measured Results (Validated)

Under identical `DISASTER_PEAK` workload stress testing (~5,200 RPM peak demand):

| Measurement Metric | Baseline (Avg-Based) | Scenario-Based | Measured Delta |
|:---|:---:|:---:|:---:|
| **SLA Compliance** | **20.6%** | **100.0%** | **+79.4%** |
| **SLA Status** | ❌ FAILED | ✅ PASSED | SERVICE RESTORED |
| **Peak Capacity** | 3,000 RPM (capped) | 7,000 RPM | +4,000 RPM (+133%) |
| **Max Queue Depth** | 50,000 requests | 0 requests | -50,000 (-100%) |
| **Max p95 Latency** | 62,630 ms | 384 ms | -62,246 ms (-99.4%) |
| **Max Error Rate** | 65.11% | 0.00% | -65.11% |
| **Dropped Requests** | 350,416 requests | 0 requests | -350,416 (-100%) |

---

## What the Simulator Does

1. **Ingest & profile workload data** — accept historical or synthetic traffic traces and
   characterise their statistical properties (mean, variance, percentiles, burst ratio).
2. **Define disaster scenarios** — model named events (earthquake, hurricane, pandemic
   announcement) with configurable surge multipliers, durations, and ramp profiles.
3. **Simulate request processing** — run a discrete-event time-step simulation of
   requests arriving at a bounded server pool, tracking queue depths, response times,
   and rejection rates.
4. **Evaluate SLA compliance** — compare simulated metrics against defined Service-Level
   Agreements (e.g., p99 latency ≤ 500 ms, availability ≥ 99.9 %).
5. **Recommend capacity** — compute the minimum server count (or auto-scale policy) that
   satisfies the SLA under each scenario.
6. **Visualise results** — present interactive dashboards showing traffic curves, resource
   utilisation heat-maps, SLA pass/fail verdicts, and cost estimates.
7. **Explain recommendations** — produce plain-language, 5-field explainable capacity
   recommendations with evidence and next-action guidance.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core logic, simulation engine |
| Dashboard | Streamlit 1.36+ | Interactive web-based UI |
| Data handling | Pandas, NumPy | Data manipulation & numerical computation |
| Visualisation | Plotly, Matplotlib | Interactive & static charts |
| Simulation | Custom discrete-event engine | Time-step simulation with queue dynamics |
| Statistical | SciPy | Distribution fitting, statistical tests |
| Configuration | PyYAML | Scenario & config file management |
| Testing | Pytest 8.2+ | 128 unit and integration tests |

---

## Implementation Status

| Module | Name | Description | Status |
|---|---|---|---|
| 1 | **Project Setup** | Repository structure, README, landing page | ✅ Complete |
| 2 | **Data Ingestion & Profiling** | Synthetic dataset (3,888 rows × 33 cols), cleaning pipeline, statistical profiler | ✅ Complete |
| 3 | **Scenario Definition Engine** | 5-tier JSON-driven disaster scenario configuration with surge curves | ✅ Complete |
| 4 | **Simulation Core** | Discrete time-step simulation of request processing, queue dynamics, scaling lag | ✅ Complete |
| 5 | **SLA Evaluation** | Compliance checking against p95 latency, error rate, and availability SLAs | ✅ Complete |
| 6 | **Capacity Recommender** | 5 capacity strategies, cost model, scenario-aware right-sizing | ✅ Complete |
| 7 | **Interactive Dashboard** | 10-section Streamlit dashboard with Plotly charts, KPI cards, and RBAC | ✅ Complete |
| 8 | **Multi-Organisation RBAC** | 4 organisations, 4 roles, metric redaction, permission enforcement | ✅ Complete |
| 9 | **Explainable Recommendation Engine** | 5-field plain-language recommendations with traceability CSV export | ✅ Complete |
| 10 | **Final Validation & Reproducibility** | 128-test automated suite, audit report, milestone report, reproducibility checklist | ✅ Complete |

---

## Project Structure

```
peak_demand_capacity_simulator/
│
├── data/
│   ├── raw/                  # Synthetic traffic dataset (emergency_load_raw.csv)
│   ├── processed/            # Cleaned dataset (emergency_load_cleaned.csv)
│   └── scenarios/            # JSON scenario definitions (scenario_config.json, advanced_scenarios.json)
│
├── src/
│   ├── auth/                 # RBAC permission engine (permissions.py)
│   ├── analysis/             # Recommendations engine & historical analysis
│   ├── capacity/             # Baseline capacity model & cost model (baseline.py, cost_model.py)
│   ├── data/                 # Generator, cleaner, profiler, loader
│   ├── simulation/           # Discrete simulator, scenarios, sensitivity, edge cases, experiment
│   ├── sla/                  # SLA package (__init__.py)
│   └── utils/                # Shared utilities & permissions module
│
├── dashboard/                # Interactive Streamlit dashboard (10 sections)
│   ├── app.py                # Main 10-section dashboard (1,393 lines)
│   └── data_profiler.py      # Module 2 dataset profiling page
│
├── tests/                    # Pytest test suite (128 tests, 100% pass rate)
│
├── docs/                     # Project documentation (13 markdown files)
│
├── outputs/                  # Simulation CSV exports and executive reports
│   ├── simulation_results/   # Per-scenario CSV exports
│   ├── milestone_report.md   # 80% milestone report
│   ├── project_audit_report.md
│   └── ...                   # SLA, sensitivity, capacity, failure case reports
│
├── requirements.txt          # Pinned Python dependencies
├── README.md                 # This file
└── main.py                   # Application entry point (Streamlit)
```

---

## How to Run

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Navigate to the project directory
cd peak_demand_capacity_simulator

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Full interactive dashboard (recommended)
streamlit run dashboard/app.py

# Landing page + Data Profiler
streamlit run main.py

# Run all 128 tests
python -m pytest tests/ -v
```

The application opens at `http://localhost:8501`.

---

## Dashboard Sections

The main dashboard (`dashboard/app.py`) provides 10 interactive sections:

| Section | Name | Key Content |
|---|---|---|
| 1 | **Executive Overview** | KPI cards, plain-language summary, scenario context |
| 2 | **Historical Load** | Traffic time-series with event annotations, statistical distribution |
| 3 | **Scenario Selection** | 7 scenarios with surge multipliers and phase breakdown |
| 4 | **Capacity Configuration** | RBAC-enforced sliders, safety margin, auto-scaling settings |
| 5 | **Simulation** | Live demand vs capacity chart, queue, latency, error rate, instances |
| 6 | **SLA Results** | SLA status verdict, compliance %, violation timeline |
| 7 | **Strategy Comparison** | 5 strategies compared on SLA, cost, queue, latency |
| 8 | **Sensitivity Analysis** | 8 planning assumptions, decision-changing classification |
| 9 | **Failure Testing** | 8 stress/failure conditions, recovery time, impact |
| 10 | **Organisation & Permissions** | Role rights, visible features, registered organisations |
| + | **Recommendation Panel** | 5-field explainable capacity recommendation |
| + | **Before vs After Visual** | Average-demand vs scenario-based planning comparison |

---

## Test Coverage

```
128 tests passed  ·  0 failed  ·  ~13 seconds  ·  Python 3.10+

Test Files (18 total):
  test_advanced_failure_cases.py  test_advanced_scenarios.py
  test_advanced_sensitivity.py    test_capacity_baseline.py
  test_capacity_strategies.py     test_data.py
  test_data_pipeline.py           test_edge_cases.py
  test_experiment.py              test_permissions.py
  test_recommendations.py         test_run_scenarios.py
  test_scenarios.py               test_sensitivity.py
  test_simulator.py               test_sla_experiment.py
  test_advanced_failure_cases.py  run_tests.py
```

---

## Reproducibility

All simulation outputs are fully reproducible:

- Scenario generation uses **fixed seed (`SEED=42`)** for deterministic results
- All CSV exports and text reports are regenerated by running `main.py` pipeline functions
- No live production data — all inputs are synthetic and committed to the repository

---

## Current Development Status

**All 10 modules are fully implemented, tested, and integrated.**

The project demonstrates that **scenario-based capacity planning is not optional** for
public emergency-information systems — it is a life-safety requirement. Average-demand
planning fails catastrophically under disaster conditions, while scenario-aware planning
achieves 100% SLA compliance under identical load.

---

## License

This project is developed for academic / internal capacity-planning purposes.
