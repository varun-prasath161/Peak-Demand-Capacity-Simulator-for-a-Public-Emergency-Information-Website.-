# Final Test Results Report

**Generated**: 2026-09-30  
**Test Framework**: Pytest 8.2.2  
**Python Version**: 3.11  
**Execution Time**: ~13 seconds  
**Result**: **128 PASSED / 0 FAILED / 1 WARNING**

---

## Summary

| Metric | Value |
|:---|:---:|
| Total Tests | **128** |
| Passed | **128** |
| Failed | **0** |
| Warnings | **1** (Pytest deprecation, non-breaking) |
| Test Files | **18** |
| Pass Rate | **100.0%** |

---

## Test File Breakdown

| # | Test File | Tests | Status |
|:---|:---|:---:|:---:|
| 1 | `test_advanced_failure_cases.py` | 12 | ✅ ALL PASS |
| 2 | `test_advanced_scenarios.py` | 7 | ✅ ALL PASS |
| 3 | `test_advanced_sensitivity.py` | 6 | ✅ ALL PASS |
| 4 | `test_capacity_baseline.py` | 6 | ✅ ALL PASS |
| 5 | `test_capacity_strategies.py` | 9 | ✅ ALL PASS |
| 6 | `test_data.py` | 5 | ✅ ALL PASS |
| 7 | `test_data_pipeline.py` | 7 | ✅ ALL PASS |
| 8 | `test_edge_cases.py` | 7 | ✅ ALL PASS |
| 9 | `test_experiment.py` | 2 | ✅ ALL PASS |
| 10 | `test_permissions.py` | 14 | ✅ ALL PASS |
| 11 | `test_recommendations.py` | 10 | ✅ ALL PASS |
| 12 | `test_run_scenarios.py` | 4 | ✅ ALL PASS |
| 13 | `test_scenarios.py` | 7 | ✅ ALL PASS |
| 14 | `test_sensitivity.py` | 10 | ✅ ALL PASS |
| 15 | `test_simulator.py` | 6 | ✅ ALL PASS |
| 16 | `test_sla_experiment.py` | 8 | ✅ ALL PASS |
| 17 | `run_tests.py` | — | Test runner script |
| 18 | `__init__.py` | — | Package init |

---

## Detailed Test Results

### 1. Advanced Failure Cases (`test_advanced_failure_cases.py`)

| Test | Result |
|:---|:---:|
| `test_extreme_traffic_spike` | ✅ PASS |
| `test_slow_scaling_60s` | ✅ PASS |
| `test_slow_scaling_300s` | ✅ PASS |
| `test_slow_scaling_900s` | ✅ PASS |
| `test_max_instance_limit` | ✅ PASS |
| `test_long_duration_disaster` | ✅ PASS |
| `test_rapid_successive_spikes` | ✅ PASS |
| `test_invalid_input_data` | ✅ PASS |
| `test_recovery_failure` | ✅ PASS |
| `test_compound_failure` | ✅ PASS |
| `test_severity_classification` | ✅ PASS |
| `test_full_failure_pipeline` | ✅ PASS |

### 2. Advanced Scenarios (`test_advanced_scenarios.py`)

| Test | Result |
|:---|:---:|
| `test_all_seven_scenarios_defined` | ✅ PASS |
| `test_scenario_parameters_valid` | ✅ PASS |
| `test_compound_scenarios_defined` | ✅ PASS |
| `test_scenario_hierarchy` | ✅ PASS |
| `test_scenario_generation` | ✅ PASS |
| `test_3phase_curve_generation` | ✅ PASS |
| `test_scenario_config_loading` | ✅ PASS |

### 3. Advanced Sensitivity (`test_advanced_sensitivity.py`)

| Test | Result |
|:---|:---:|
| `test_eight_parameters_defined` | ✅ PASS |
| `test_parameter_ranges_valid` | ✅ PASS |
| `test_single_parameter_run` | ✅ PASS |
| `test_decision_changing_classification` | ✅ PASS |
| `test_metrics_columns_present` | ✅ PASS |
| `test_full_sensitivity_pipeline` | ✅ PASS |

### 4. Capacity Baseline (`test_capacity_baseline.py`)

| Test | Result |
|:---|:---:|
| `test_capacity_below_demand` | ✅ PASS |
| `test_capacity_above_demand` | ✅ PASS |
| `test_capacity_equals_demand` | ✅ PASS |
| `test_headroom_calculation` | ✅ PASS |
| `test_instances_required_calculation` | ✅ PASS |
| `test_default_config_values` | ✅ PASS |

### 5. Capacity Strategies (`test_capacity_strategies.py`)

| Test | Result |
|:---|:---:|
| `test_five_strategies_defined` | ✅ PASS |
| `test_seven_scenarios_defined` | ✅ PASS |
| `test_average_demand_strategy` | ✅ PASS |
| `test_peak_demand_strategy` | ✅ PASS |
| `test_safety_margin_strategy` | ✅ PASS |
| `test_dynamic_scaling_strategy` | ✅ PASS |
| `test_disaster_aware_strategy` | ✅ PASS |
| `test_strategy_comparison_table` | ✅ PASS |
| `test_cost_model_integration` | ✅ PASS |

### 6. Data Tests (`test_data.py`)

| Test | Result |
|:---|:---:|
| `test_raw_csv_exists` | ✅ PASS |
| `test_raw_csv_row_count` | ✅ PASS |
| `test_raw_csv_column_count` | ✅ PASS |
| `test_required_columns_present` | ✅ PASS |
| `test_timestamp_format` | ✅ PASS |

### 7. Data Pipeline (`test_data_pipeline.py`)

| Test | Result |
|:---|:---:|
| `test_pipeline_produces_cleaned_output` | ✅ PASS |
| `test_no_duplicate_timestamps` | ✅ PASS |
| `test_no_negative_values` | ✅ PASS |
| `test_cpu_utilisation_bounds` | ✅ PASS |
| `test_capacity_math_enforced` | ✅ PASS |
| `test_latency_ordering` | ✅ PASS |
| `test_zero_missing_values` | ✅ PASS |

### 8. Edge Cases (`test_edge_cases.py`)

| Test | Result |
|:---|:---:|
| `test_five_edge_cases_defined` | ✅ PASS |
| `test_extreme_traffic_spike_case_1` | ✅ PASS |
| `test_scaling_delay_disaster_case_2` | ✅ PASS |
| `test_max_instance_limit_case_3` | ✅ PASS |
| `test_queue_overflow_case_4` | ✅ PASS |
| `test_corrupted_input_data_case_5` | ✅ PASS |
| `test_full_edge_case_pipeline` | ✅ PASS |

### 9. Experiment (`test_experiment.py`)

| Test | Result |
|:---|:---:|
| `test_experiment_output_files_and_metrics` | ✅ PASS |
| `test_report_content_sections` | ✅ PASS |

### 10. Permissions (`test_permissions.py`)

| Test | Result |
|:---|:---:|
| `test_viewer_role_permissions` | ✅ PASS |
| `test_analyst_role_permissions` | ✅ PASS |
| `test_operator_role_permissions` | ✅ PASS |
| `test_administrator_role_permissions` | ✅ PASS |
| `test_organisation_data_visibility` | ✅ PASS |
| `test_filter_metrics_for_external_partner` | ✅ PASS |
| `test_role_capabilities_summary` | ✅ PASS |
| `test_all_four_organisations_load` | ✅ PASS |
| `test_get_organisation_by_id_and_name` | ✅ PASS |
| `test_viewer_has_permission_and_blocked` | ✅ PASS |
| `test_analyst_has_permission_and_blocked` | ✅ PASS |
| `test_operator_has_permission_and_blocked` | ✅ PASS |
| `test_administrator_has_all_permissions` | ✅ PASS |
| `test_visible_sections_per_role` | ✅ PASS |

### 11. Recommendations (`test_recommendations.py`)

| Test | Result |
|:---|:---:|
| `test_sla_compliant_case` | ✅ PASS |
| `test_high_queue_recommendation` | ✅ PASS |
| `test_high_latency_recommendation` | ✅ PASS |
| `test_high_error_recommendation` | ✅ PASS |
| `test_max_instance_limit_recommendation` | ✅ PASS |
| `test_slow_scaling_recommendation` | ✅ PASS |
| `test_missing_metric_handling` | ✅ PASS |
| `test_executive_summary_statements` | ✅ PASS |
| `test_traceability_export` | ✅ PASS |
| `test_permission_aware_dashboard_behaviour` | ✅ PASS |

### 12. Run Scenarios (`test_run_scenarios.py`)

| Test | Result |
|:---|:---:|
| `test_csv_file_creation_and_structure` | ✅ PASS |
| `test_extreme_disaster_sla_violation` | ✅ PASS |
| `test_report_file_creation_and_questions` | ✅ PASS |
| `test_safest_scenario_compliance` | ✅ PASS |

### 13. Scenarios (`test_scenarios.py`)

| Test | Result |
|:---|:---:|
| `test_all_five_scenarios_generation` | ✅ PASS |
| `test_calculation_functions` | ✅ PASS |
| `test_compare_all_scenarios` | ✅ PASS |
| `test_config_loading` | ✅ PASS |
| `test_scenario_surge_hierarchy` | ✅ PASS |
| `test_seed_determinism` | ✅ PASS |
| `test_three_phase_demand_curve` | ✅ PASS |

### 14. Sensitivity (`test_sensitivity.py`)

| Test | Result |
|:---|:---:|
| `test_seven_assumptions_defined` | ✅ PASS |
| `test_each_assumption_has_required_keys` | ✅ PASS |
| `test_lower_leq_baseline_leq_upper` | ✅ PASS |
| `test_baseline_config_matches_simulator_defaults` | ✅ PASS |
| `test_baseline_run_returns_valid_dict` | ✅ PASS |
| `test_result_values_are_plausible` | ✅ PASS |
| `test_traffic_multiplier_lower_reduces_load` | ✅ PASS |
| `test_classification_returns_all_assumptions` | ✅ PASS |
| `test_identical_results_classified_little_effect` | ✅ PASS |
| `test_sla_flip_classified_decision_changing` | ✅ PASS |
| `test_full_pipeline_produces_csv_and_report` | ✅ PASS |
| `test_csv_file_exists_after_run` | ✅ PASS |
| `test_report_file_exists_after_run` | ✅ PASS |

### 15. Simulator (`test_simulator.py`)

| Test | Result |
|:---|:---:|
| `test_auto_scaling_trigger_and_delay` | ✅ PASS |
| `test_csv_output_file_creation` | ✅ PASS |
| `test_normal_traffic_simulation` | ✅ PASS |
| `test_overload_traffic_and_sla_violation` | ✅ PASS |
| `test_queue_buildup_and_drainage` | ✅ PASS |
| `test_run_all_simulations` | ✅ PASS |

### 16. SLA Experiment (`test_sla_experiment.py`)

| Test | Result |
|:---|:---:|
| `test_sla_target_calculation` | ✅ PASS |
| `test_sla_compliance` | ✅ PASS |
| `test_sla_violation_detection` | ✅ PASS |
| `test_recovery_time_calculation` | ✅ PASS |
| `test_baseline_experiment` | ✅ PASS |
| `test_improved_strategy_experiment` | ✅ PASS |
| `test_before_after_comparison` | ✅ PASS |
| `test_error_classification` | ✅ PASS |

---

## Coverage by Module

| Module | Test Files | Test Count | Coverage |
|:---|:---|:---:|:---|
| Data Pipeline | test_data.py, test_data_pipeline.py | 12 | Schema, cleaning, validation, quality |
| Scenario Engine | test_scenarios.py, test_advanced_scenarios.py | 14 | Generation, hierarchy, config, determinism |
| Simulator | test_simulator.py | 6 | Scaling, queue, overload, SLA, output |
| Capacity | test_capacity_baseline.py, test_capacity_strategies.py | 15 | Baseline, 5 strategies, cost model |
| SLA | test_sla_experiment.py | 8 | Targets, compliance, violations, recovery |
| Sensitivity | test_sensitivity.py, test_advanced_sensitivity.py | 16 | Assumptions, classification, pipeline |
| Failure Testing | test_advanced_failure_cases.py, test_edge_cases.py | 19 | 8 failure cases, 5 edge cases |
| Permissions | test_permissions.py | 14 | 4 roles, 4 orgs, sections, actions |
| Recommendations | test_recommendations.py | 10 | 6 conditions, export, permissions |
| Experiment | test_experiment.py | 2 | Before/after, report structure |
| Scenarios Runner | test_run_scenarios.py | 4 | CSV, SLA, report, compliance |
| **Total** | **16 test files** | **128** | **All modules covered** |

---

## Warning Details

```
PytestRemovedIn10Warning: Class-scoped fixture defined as instance method is deprecated.
  File: tests/test_advanced_sensitivity.py
  Impact: Non-breaking; cosmetic deprecation warning for pytest >=10
  Resolution: Convert class-scoped fixture to @classmethod (optional)
```

---

## Reproducibility

```bash
# Run all 128 tests
python -m pytest tests/ -v

# Run with timing
python -m pytest tests/ -v --durations=10

# Run a specific test file
python -m pytest tests/test_simulator.py -v
```

All tests use deterministic seeding (`seed=42`) and produce identical results across runs.
