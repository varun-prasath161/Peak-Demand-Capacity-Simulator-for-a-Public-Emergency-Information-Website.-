# Project Audit Report

## 1. Project Overview

The **Peak-Demand Capacity Simulator for a Public Emergency-Information Website** is a Python- and Streamlit-based analytical tool designed to model infrastructure capacity requirements during high-surge disaster events. Unlike traditional capacity planning models that rely on average traffic utilization (which conceals worst-case spikes), this simulator uses event-driven workload scenarios (such as earthquakes, Category-5 hurricanes, and breaking news alerts) to evaluate discrete request processing, queue dynamics, auto-scaling propagation delays, and SLA compliance.

The project incorporates synthetic dataset generation, automated data cleaning and quality auditing, non-uniform workload scenario generation, discrete-event simulation, baseline capacity gap analysis, 7-parameter sensitivity analysis, 5 operational failure edge cases, role-based access control (RBAC), multi-organisation metric redaction, and an 8-section interactive dashboard.

---

## 2. Repository Structure

```
peak_demand_capacity_simulator/
│
├── data/
│   ├── raw/                      # Raw synthetic traffic dataset (emergency_load_raw.csv)
│   ├── processed/                # Cleaned & transformed dataset (emergency_load_cleaned.csv)
│   └── scenarios/                # JSON scenario definitions (scenario_config.json)
│
├── src/
│   ├── auth/                     # RBAC & organisation permission logic (permissions.py)
│   ├── capacity/                 # Baseline capacity & shortfall model (baseline.py)
│   ├── data/                     # Generator, cleaner, profiler, loader (generate_dataset.py, clean_data.py, cleaner.py, profiler.py, loader.py)
│   ├── simulation/               # Discrete simulator, scenario engine, sensitivity, edge cases, experiment runner
│   │   ├── edge_cases.py         # Failure mode & edge case suite
│   │   ├── experiment.py         # Measurable before-vs-after experiment
│   │   ├── run_scenarios.py      # Multi-scenario evaluation runner
│   │   ├── scenarios.py          # Workload scenario definition engine
│   │   ├── sensitivity.py        # 7-parameter sensitivity analysis engine
│   │   └── simulator.py          # Discrete-event simulation core MVP
│   ├── sla/                      # SLA package directory (__init__.py only - logic in simulator.py)
│   └── utils/                    # Shared utilities package directory (__init__.py only)
│
├── dashboard/                    # Interactive Streamlit Web UI
│   ├── app.py                    # 8-section interactive simulator dashboard
│   └── data_profiler.py          # Module 2 dataset profiling page
│
├── tests/                        # Automated Pytest suite (64 passing tests across 10 test files)
│   ├── test_capacity_baseline.py
│   ├── test_data.py
│   ├── test_data_pipeline.py
│   ├── test_edge_cases.py
│   ├── test_experiment.py
│   ├── test_permissions.py
│   ├── test_run_scenarios.py
│   ├── test_scenarios.py
│   ├── test_sensitivity.py
│   └── test_simulator.py
│
├── docs/                         # Project documentation and markdown guides (8 docs)
│   ├── architecture.md
│   ├── data_schema.md
│   ├── experiment.md
│   ├── failure_cases.md
│   ├── risk_register.md
│   ├── roles_and_permissions.md
│   ├── stakeholder_assumptions.md
│   └── user_guide.md
│
├── outputs/                      # Simulation CSV exports and executive text reports
│   ├── simulation_results/       # Scenario run CSV exports (sim_result_*.csv)
│   ├── baseline_capacity_report.txt
│   ├── before_after_comparison.csv
│   ├── before_after_report.txt
│   ├── data_quality_report.txt
│   ├── edge_case_results.csv
│   ├── milestone_report.md
│   ├── scenario_comparison.csv
│   ├── scenario_report.txt
│   ├── sensitivity_analysis.csv
│   └── sensitivity_report.txt
│
├── main.py                       # Main Streamlit landing page & entry point
├── pytest.ini                    # Pytest configuration
├── README.md                     # Project overview (Note: status table lists Modules 3–8 as planned despite implementation)
└── requirements.txt              # Pinned Python dependencies
```

---

## 3. Module Status

| Module | Status | Evidence | Issues |
| --- | --- | --- | --- |
| **Dataset Generation** | COMPLETED | `src/data/generate_dataset.py` generates 10-month realistic traffic trace (3,800+ rows, 33 columns) with 5 event classes and injected anomalies; outputs `data/raw/emergency_load_raw.csv`. | None. |
| **Data Cleaning** | COMPLETED | `src/data/clean_data.py` & `cleaner.py` perform deduplication, linear time-based interpolation, non-negative enforcement, CPU/memory clamping, capacity math checks, latency percentile ordering, and disaster spike preservation; outputs `emergency_load_cleaned.csv` and `data_quality_report.txt`. | None. |
| **Scenario Engine** | COMPLETED | `src/simulation/scenarios.py` driven by `data/scenarios/scenario_config.json`; generates non-uniform demand profiles (ramp-up, peak with jitter/aftershocks, exponential recovery) for 5 scenarios (`NORMAL`, `SEASONAL_PEAK`, `BREAKING_NEWS`, `DISASTER_PEAK`, `EXTREME_DISASTER`). | None. |
| **Capacity Model** | COMPLETED | `src/capacity/baseline.py` evaluates baseline fleet constraints (current/max instances, capacity per instance, 20% safety margin buffer) vs average and peak demands; generates `baseline_capacity_report.txt`. | None. |
| **Simulator** | COMPLETED | `src/simulation/simulator.py` executes time-series discrete simulation with queue buildup/drainage, 180s scaling delay, M/M/1 response latency, exponential error rate explosion, and SLA checking; outputs to `outputs/simulation_results/`. | None. |
| **SLA Evaluation** | PARTIALLY COMPLETED | SLA evaluation functions exist and execute inside `simulator.py`, `clean_data.py`, and `baseline.py`. However, the dedicated module `src/sla/` contains only `__init__.py`. | Code is functional, but SLA logic is embedded in simulation/data modules rather than decoupled into `src/sla/`. |
| **Sensitivity Analysis** | COMPLETED | `src/simulation/sensitivity.py` tests 7 infrastructure & planning assumptions across 21 controlled simulations, classifying parameters into "DECISION-CHANGING" vs "LITTLE EFFECT"; outputs `sensitivity_analysis.csv` and `sensitivity_report.txt`. | None. |
| **Dashboard** | COMPLETED | `dashboard/app.py` (1,049 lines) & `dashboard/data_profiler.py` (282 lines) provide an 8-section interactive UI with Plotly charts, KPI cards, sidebar controls, and RBAC visibility toggles. `main.py` serves as landing page. | README.md and main.py landing page table misstate project status as "Module 1/2 Complete" despite dashboard having all 8 sections implemented. |
| **Multi-Organisation** | COMPLETED | `src/auth/permissions.py` defines 4 organisations (`EMERGENCY_OPS_CENTRE`, `GOVERNMENT_AGENCY`, `HEALTHCARE_PARTNER`, `EXTERNAL_INFO_PARTNER`) and redacts raw node metrics (`filter_metrics_for_organisation`) for external partners. | None. |
| **Failure Cases** | COMPLETED | `src/simulation/edge_cases.py` evaluates 5 failure conditions (Extreme Traffic Spike, Scaling Delay, Max Instances Ceiling, Queue Overflow, Corrupted Input Data); outputs `edge_case_results.csv` and `docs/failure_cases.md`. | None. |
| **Before/After** | COMPLETED | `src/simulation/experiment.py` executes controlled comparison between Average-Based and Scenario-Based planning under identical stress load; outputs `before_after_comparison.csv` and `before_after_report.txt`. | None. |
| **Testing** | COMPLETED | 64 automated unit & integration tests across 10 test files in `tests/`. All 64 tests pass in 7.00s using `pytest`. | None. |
| **Documentation** | COMPLETED | 8 comprehensive documentation markdown files in `docs/` covering architecture, schemas, experiments, failure cases, risk register, RBAC, assumptions, and user guide. | `README.md` status shield and table are outdated. |

---

## 4. Existing Outputs

The repository contains pre-generated analytical outputs and executive reports in `outputs/`:

1. **Simulation Results Directory** (`outputs/simulation_results/`):
   - `sim_result_normal.csv` (3.0 KB)
   - `sim_result_seasonal_peak.csv` (6.1 KB)
   - `sim_result_breaking_news.csv` (6.1 KB)
   - `sim_result_disaster_peak.csv` (12.0 KB)
   - `sim_result_extreme_disaster.csv` (18.4 KB)
2. **Data Quality & Preprocessing Report**: `outputs/data_quality_report.txt` (3.7 KB)
3. **Baseline Capacity Evaluation Report**: `outputs/baseline_capacity_report.txt` (4.2 KB)
4. **Scenario Comparison CSV & Executive Report**: `outputs/scenario_comparison.csv` (785 B) & `outputs/scenario_report.txt` (4.7 KB)
5. **Sensitivity Analysis CSV & Report**: `outputs/sensitivity_analysis.csv` (2.2 KB) & `outputs/sensitivity_report.txt` (8.6 KB)
6. **Edge Case & Failure Results**: `outputs/edge_case_results.csv` (1.9 KB) & `docs/failure_cases.md` (4.8 KB)
7. **Before-vs-After Experiment CSV & Report**: `outputs/before_after_comparison.csv` (891 B) & `outputs/before_after_report.txt` (4.1 KB)
8. **Milestone Report**: `outputs/milestone_report.md` (8.0 KB)

---

## 5. Existing Tests

* **Test Framework**: Pytest (`pytest.ini` configured, `tests/` testpaths)
* **Total Test Files**: 10
* **Total Executed Tests**: 64
* **Passed Tests**: 64 (100% pass rate)
* **Failed Tests**: 0
* **Execution Time**: 7.00 seconds

### Test File Breakdown

| Test File | Number of Tests | Status | Description |
| --- | --- | --- | --- |
| `tests/test_capacity_baseline.py` | 4 | PASSED | Tests capacity calculations, gap metrics, and baseline report generation |
| `tests/test_data.py` | 4 | PASSED | Tests raw dataset loader, validation, and filtering |
| `tests/test_data_pipeline.py` | 10 | PASSED | Tests preprocessing, interpolation, clamping, deduplication, and quality flags |
| `tests/test_edge_cases.py` | 7 | PASSED | Tests execution of 5 failure modes and corrupt data handling |
| `tests/test_experiment.py` | 2 | PASSED | Tests before-vs-after experiment runner and comparison output |
| `tests/test_permissions.py` | 7 | PASSED | Tests RBAC permissions, role rights, and organisation metric redaction |
| `tests/test_run_scenarios.py` | 4 | PASSED | Tests multi-scenario evaluation and report generation |
| `tests/test_scenarios.py` | 7 | PASSED | Tests scenario definition engine, curve shapes, and seed reproducibility |
| `tests/test_sensitivity.py` | 13 | PASSED | Tests parameter variation, single sensitivity tests, and classification |
| `tests/test_simulator.py` | 6 | PASSED | Tests discrete simulator core, queue buildup, latency degradation, and output CSV |

---

## 6. Missing Functionality

1. **Modular SLA Package Refactoring (`src/sla/`)**:
   - The directory `src/sla/` contains only `__init__.py`. While SLA evaluation logic is fully implemented and tested inside `src/simulation/simulator.py` and `src/data/clean_data.py`, it has not been decoupled into dedicated modules under `src/sla/` (e.g., `src/sla/evaluator.py`, `src/sla/targets.py`).
2. **Shared Utilities Package (`src/utils/`)**:
   - The directory `src/utils/` contains only `__init__.py`. Helper functions (such as formatting or math helpers) are currently defined inline across individual files rather than shared via `src/utils/`.
3. **SimPy Integration**:
   - `requirements.txt` includes `simpy==4.1.1`, but the simulation engine (`src/simulation/simulator.py`) is implemented using custom step-wise Python/NumPy discrete simulation rather than SimPy discrete-event objects.

---

## 7. Broken Functionality

1. **Outdated Status Documentation**:
   - `README.md` displays a status badge reading `Module 1 Complete` and marks Modules 2–8 as `🔲 Planned`.
   - `main.py` landing page lists Modules 1 & 2 as `✅ Complete` and Modules 3–8 as `🔲 Planned`.
   - In reality, all core modules (Modules 1 through 8) are already fully implemented, tested, and integrated into `dashboard/app.py`. This documentation mismatch misleads reviewers into believing the project is only 25% to 40% complete.
2. **None identified in runtime execution**:
   - All 64 Pytest tests pass cleanly without errors, warnings, or regressions.
   - Data generation, cleaning, scenario generation, simulation, sensitivity analysis, edge case testing, before/after experiment, and dashboard rendering execute cleanly.

---

## 8. Recommended Next Steps

To refine the repository and align documentation with actual implementation:

1. **Update `README.md` and `main.py` Status Badges**:
   - Update the module status table in `README.md` and `main.py` to reflect that Modules 1 through 8 are fully implemented.
2. **Refactor SLA Logic into `src/sla/`**:
   - Create `src/sla/evaluator.py` to encapsulate SLA compliance calculation logic currently residing in `src/simulation/simulator.py`.
3. **Populate `src/utils/`**:
   - Extract common configuration constants and formatting helpers into `src/utils/config.py` and `src/utils/helpers.py`.
4. **Dashboard Navigation Integration**:
   - Update `main.py` sidebar navigation so users can toggle directly to the full 8-section interactive dashboard (`dashboard/app.py`).

---

## 9. Completion Estimate

* **Initial User Baseline Estimate**: 40–45% (based on `README.md` status table)
* **Actual Evidence-Based Implementation Level**: **95%**

### Breakdown of Completion Evidence:

- **Data Engineering & Ingestion**: 100% (Generator, cleaner, profiler, loader fully implemented and tested)
- **Scenario & Workload Engine**: 100% (5 non-uniform scenarios, YAML/JSON driven, deterministic)
- **Simulation Core**: 100% (Discrete time-series simulator, queue dynamics, auto-scaling lag, latency degradation)
- **SLA Evaluation**: 90% (Functional logic 100% working and tested; `src/sla/` folder structure requires cleanup)
- **Capacity Analysis & Sensitivity**: 100% (Baseline gap model, 7-parameter sensitivity engine, 5 edge cases, before/after experiment)
- **RBAC & Multi-Organisation**: 100% (4 roles, 4 organisations, metric redaction)
- **Dashboard & UI**: 100% (1,049-line Streamlit dashboard with Plotly charts and controls)
- **Testing & Documentation**: 95% (64/64 pytest tests pass, 8 docs written; README status table needs update)
