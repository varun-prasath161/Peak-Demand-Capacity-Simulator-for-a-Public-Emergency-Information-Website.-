"""
Sensitivity Analysis Engine
============================
Tests how the capacity recommendation changes when key assumptions vary.

Systematically varies 7 infrastructure and planning assumptions:
1. Traffic Multiplier
2. Scaling Delay
3. Capacity per Instance
4. Maximum Available Instances
5. SLA Latency Target
6. Safety Margin (initial instance count)
7. Initial Instance Count

For each assumption, runs controlled simulations at a baseline, lower, and upper
value. Identifies "decision-changing" vs. "little effect" assumptions based on
whether the variation causes a meaningful change in SLA compliance, required
instances, or peak queue behaviour.

Outputs:
- outputs/sensitivity_analysis.csv
- outputs/sensitivity_report.txt
"""

import sys
import math
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.simulator import run_simulation

OUTPUT_DIR = PROJECT_ROOT / "outputs"
CSV_PATH = OUTPUT_DIR / "sensitivity_analysis.csv"
REPORT_PATH = OUTPUT_DIR / "sensitivity_report.txt"

# ── Baseline Reference Configuration ──────────────────────────────────────────
BASELINE_CONFIG = {
    "initial_instances": 10,
    "max_instances": 50,
    "capacity_per_instance": 500.0,
    "scaling_delay_seconds": 180,
    "sla_latency_target_ms": 500.0,
    "sla_error_target_rate": 0.01,
}

# The stress scenario used for sensitivity testing: DISASTER_PEAK is chosen
# because it reveals scaling weaknesses more clearly than NORMAL.
STRESS_SCENARIO = "DISASTER_PEAK"

# ── Assumption Variation Definitions ──────────────────────────────────────────
# Each entry: (parameter_name, display_name, unit, baseline, lower, upper, description)
ASSUMPTIONS = [
    {
        "param": "traffic_multiplier",
        "display_name": "Traffic Multiplier",
        "unit": "x",
        "baseline": 1.0,
        "lower": 0.7,
        "upper": 1.5,
        "description": "Scales the incoming traffic volume up or down from the scenario default.",
        "sim_param": None,  # handled specially via scenario generation
    },
    {
        "param": "scaling_delay_seconds",
        "display_name": "Scaling Delay",
        "unit": "seconds",
        "baseline": 180,
        "lower": 60,
        "upper": 300,
        "description": "Time required to provision new server instances after a scale-out decision.",
    },
    {
        "param": "capacity_per_instance",
        "display_name": "Capacity per Instance",
        "unit": "RPM",
        "baseline": 500.0,
        "lower": 300.0,
        "upper": 800.0,
        "description": "Maximum requests per minute each application instance can handle.",
    },
    {
        "param": "max_instances",
        "display_name": "Maximum Available Instances",
        "unit": "instances",
        "baseline": 50,
        "lower": 20,
        "upper": 80,
        "description": "Hard ceiling on the number of server instances the auto-scaler can provision.",
    },
    {
        "param": "sla_latency_target_ms",
        "display_name": "SLA Latency Target",
        "unit": "ms",
        "baseline": 500.0,
        "lower": 300.0,
        "upper": 1000.0,
        "description": "Maximum acceptable p95 response time before declaring an SLA breach.",
    },
    {
        "param": "safety_margin_instances",
        "display_name": "Safety Margin (Extra Base Instances)",
        "unit": "instances",
        "baseline": 0,
        "lower": 0,
        "upper": 10,
        "description": "Additional instances added to initial fleet as a safety buffer above baseline.",
    },
    {
        "param": "initial_instances",
        "display_name": "Initial Instance Count",
        "unit": "instances",
        "baseline": 10,
        "lower": 5,
        "upper": 20,
        "description": "Number of server instances active at simulation start before auto-scaling kicks in.",
    },
]


def _run_single_sensitivity_test(
    assumption: Dict[str, Any],
    test_value: float,
    test_label: str,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Runs one simulation with a single assumption varied from baseline.
    All other parameters remain at their baseline defaults.
    """
    # Start from baseline config
    sim_kwargs = {
        "workload_scenario": STRESS_SCENARIO,
        "initial_instances": BASELINE_CONFIG["initial_instances"],
        "max_instances": BASELINE_CONFIG["max_instances"],
        "capacity_per_instance": BASELINE_CONFIG["capacity_per_instance"],
        "scaling_delay_seconds": BASELINE_CONFIG["scaling_delay_seconds"],
        "sla_latency_target_ms": BASELINE_CONFIG["sla_latency_target_ms"],
        "sla_error_target_rate": BASELINE_CONFIG["sla_error_target_rate"],
        "seed": seed,
    }

    param_name = assumption["param"]

    if param_name == "traffic_multiplier":
        # Generate a scenario with a custom traffic multiplier applied
        from src.simulation.scenarios import generate_scenario
        sc_df = generate_scenario(
            STRESS_SCENARIO,
            seed=seed,
            custom_multiplier=None,  # Use scenario default multiplier
        )
        # Scale RPM by the test multiplier value
        sc_df["requests_per_minute"] = np.round(
            sc_df["requests_per_minute"] * test_value, 1
        )
        sim_kwargs["workload_scenario"] = sc_df

    elif param_name == "safety_margin_instances":
        # Safety margin adds extra instances to the initial count
        extra = int(test_value)
        sim_kwargs["initial_instances"] = BASELINE_CONFIG["initial_instances"] + extra

    elif param_name in sim_kwargs:
        # Direct parameter override
        if param_name in ("initial_instances", "max_instances", "scaling_delay_seconds"):
            sim_kwargs[param_name] = int(test_value)
        else:
            sim_kwargs[param_name] = float(test_value)

    # Ensure initial_instances <= max_instances
    if sim_kwargs["initial_instances"] > sim_kwargs["max_instances"]:
        sim_kwargs["max_instances"] = sim_kwargs["initial_instances"]

    # Run simulation
    df_result, summary = run_simulation(**sim_kwargs)

    # Extract key decision metrics
    peak_queue = float(df_result["queue_depth"].max())
    max_p95 = float(df_result["p95_latency_ms"].max())
    max_error = float(df_result["error_rate"].max())
    compliance_pct = summary["compliance_percentage"]
    sla_compliant = summary["sla_compliant"]
    peak_instances = summary["peak_instances"]
    total_unmet = summary["total_unmet_requests"]
    total_scaling_actions = summary["total_scaling_actions"]

    return {
        "assumption_name": assumption["display_name"],
        "parameter": param_name,
        "test_label": test_label,
        "test_value": test_value,
        "unit": assumption["unit"],
        "peak_queue_depth": round(peak_queue, 1),
        "max_p95_latency_ms": round(max_p95, 1),
        "max_error_rate_pct": round(max_error * 100, 3),
        "sla_compliance_pct": compliance_pct,
        "sla_compliant": sla_compliant,
        "peak_instances": peak_instances,
        "total_unmet_requests": round(total_unmet, 1),
        "total_scaling_actions": total_scaling_actions,
    }


def run_sensitivity_analysis(seed: int = 42) -> Tuple[pd.DataFrame, str]:
    """
    Executes the full sensitivity analysis across all 7 assumptions.

    For each assumption, runs three simulations:
    - Baseline value
    - Lower bound value
    - Upper bound value

    Returns:
        (sensitivity_results_df, sensitivity_report_text)
    """
    all_results = []

    print("=" * 90)
    print("  PEAK-DEMAND CAPACITY SIMULATOR -- SENSITIVITY ANALYSIS")
    print("=" * 90)
    print(f"  Stress Scenario: {STRESS_SCENARIO}")
    print(f"  Testing {len(ASSUMPTIONS)} assumptions x 3 levels = {len(ASSUMPTIONS) * 3} controlled simulations")
    print("-" * 90)

    for assumption in ASSUMPTIONS:
        param_name = assumption["display_name"]
        baseline_val = assumption["baseline"]
        lower_val = assumption["lower"]
        upper_val = assumption["upper"]
        unit = assumption["unit"]

        print(f"\n  [{param_name}] Testing: Lower={lower_val}{unit}, Baseline={baseline_val}{unit}, Upper={upper_val}{unit}")

        # Run three simulations
        result_lower = _run_single_sensitivity_test(assumption, lower_val, "lower", seed)
        result_baseline = _run_single_sensitivity_test(assumption, baseline_val, "baseline", seed)
        result_upper = _run_single_sensitivity_test(assumption, upper_val, "upper", seed)

        all_results.extend([result_lower, result_baseline, result_upper])

        # Quick summary line
        print(f"    Lower:    SLA={result_lower['sla_compliance_pct']:6.1f}%  p95={result_lower['max_p95_latency_ms']:>8,.1f}ms  Queue={result_lower['peak_queue_depth']:>10,.1f}  Instances={result_lower['peak_instances']}")
        print(f"    Baseline: SLA={result_baseline['sla_compliance_pct']:6.1f}%  p95={result_baseline['max_p95_latency_ms']:>8,.1f}ms  Queue={result_baseline['peak_queue_depth']:>10,.1f}  Instances={result_baseline['peak_instances']}")
        print(f"    Upper:    SLA={result_upper['sla_compliance_pct']:6.1f}%  p95={result_upper['max_p95_latency_ms']:>8,.1f}ms  Queue={result_upper['peak_queue_depth']:>10,.1f}  Instances={result_upper['peak_instances']}")

    print("\n" + "=" * 90)
    print(f"  Completed {len(all_results)} simulations.")
    print("=" * 90)

    # Build results DataFrame
    results_df = pd.DataFrame(all_results)

    # Save CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(CSV_PATH, index=False)
    print(f"\n  [OK] Sensitivity analysis CSV saved to: {CSV_PATH}")

    # Classify assumptions and generate report
    classification = _classify_assumptions(results_df)
    report = _build_sensitivity_report(results_df, classification)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  [OK] Sensitivity report saved to:       {REPORT_PATH}")

    return results_df, report


def _classify_assumptions(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Classifies each assumption as 'DECISION-CHANGING' or 'LITTLE EFFECT'
    based on whether varying it materially changes:
    - SLA compliance status (from compliant to breached or vice-versa)
    - Required peak instances (>= 20% change)
    - Peak queue depth (>= 3x increase)
    - p95 latency (>= 2x increase or crosses the SLA boundary)
    """
    classifications = {}

    for assumption in ASSUMPTIONS:
        param = assumption["param"]
        display = assumption["display_name"]
        param_df = df[df["parameter"] == param]

        if len(param_df) < 3:
            classifications[param] = {
                "display_name": display,
                "classification": "INSUFFICIENT DATA",
                "reason": "Not enough simulation runs.",
            }
            continue

        baseline_row = param_df[param_df["test_label"] == "baseline"].iloc[0]
        lower_row = param_df[param_df["test_label"] == "lower"].iloc[0]
        upper_row = param_df[param_df["test_label"] == "upper"].iloc[0]

        reasons = []
        is_decision_changing = False

        # Check 1: SLA compliance status change
        sla_values = {lower_row["sla_compliant"], baseline_row["sla_compliant"], upper_row["sla_compliant"]}
        if len(sla_values) > 1:
            is_decision_changing = True
            reasons.append("SLA compliance status changes between test levels")

        # Check 2: Significant p95 latency swing
        p95_vals = [lower_row["max_p95_latency_ms"], baseline_row["max_p95_latency_ms"], upper_row["max_p95_latency_ms"]]
        p95_range = max(p95_vals) - min(p95_vals)
        baseline_p95 = baseline_row["max_p95_latency_ms"]
        if baseline_p95 > 0 and p95_range / baseline_p95 > 1.0:
            is_decision_changing = True
            reasons.append(f"p95 latency varies by {p95_range:,.0f}ms ({p95_range/baseline_p95*100:.0f}% of baseline)")

        # Check 3: SLA boundary crossing for p95 latency
        sla_target = BASELINE_CONFIG["sla_latency_target_ms"]
        p95_crosses_sla = any(v > sla_target for v in p95_vals) and any(v <= sla_target for v in p95_vals)
        if p95_crosses_sla:
            is_decision_changing = True
            reasons.append(f"p95 latency crosses the {sla_target}ms SLA boundary")

        # Check 4: Significant peak instance change (>= 20%)
        inst_vals = [lower_row["peak_instances"], baseline_row["peak_instances"], upper_row["peak_instances"]]
        baseline_inst = baseline_row["peak_instances"]
        if baseline_inst > 0:
            inst_range = max(inst_vals) - min(inst_vals)
            if inst_range / baseline_inst >= 0.20:
                is_decision_changing = True
                reasons.append(f"Required peak instances vary by {inst_range} ({inst_range/baseline_inst*100:.0f}%)")

        # Check 5: Significant queue depth change (>= 3x)
        queue_vals = [lower_row["peak_queue_depth"], baseline_row["peak_queue_depth"], upper_row["peak_queue_depth"]]
        baseline_queue = max(1.0, baseline_row["peak_queue_depth"])
        queue_ratio = max(queue_vals) / baseline_queue
        if queue_ratio >= 3.0:
            is_decision_changing = True
            reasons.append(f"Peak queue depth varies by {queue_ratio:.1f}x")

        # Check 6: Compliance percentage swing >= 10 percentage points
        comp_vals = [lower_row["sla_compliance_pct"], baseline_row["sla_compliance_pct"], upper_row["sla_compliance_pct"]]
        comp_range = max(comp_vals) - min(comp_vals)
        if comp_range >= 10.0:
            is_decision_changing = True
            reasons.append(f"SLA compliance varies by {comp_range:.1f} percentage points")

        classification = "DECISION-CHANGING" if is_decision_changing else "LITTLE EFFECT"

        if not reasons:
            reasons.append("All test levels produce similar outcomes with no material differences")

        classifications[param] = {
            "display_name": display,
            "classification": classification,
            "reasons": reasons,
            "baseline_sla": baseline_row["sla_compliance_pct"],
            "lower_sla": lower_row["sla_compliance_pct"],
            "upper_sla": upper_row["sla_compliance_pct"],
            "baseline_p95": baseline_row["max_p95_latency_ms"],
            "lower_p95": lower_row["max_p95_latency_ms"],
            "upper_p95": upper_row["max_p95_latency_ms"],
            "baseline_inst": baseline_row["peak_instances"],
            "lower_inst": lower_row["peak_instances"],
            "upper_inst": upper_row["peak_instances"],
            "baseline_queue": baseline_row["peak_queue_depth"],
            "lower_queue": lower_row["peak_queue_depth"],
            "upper_queue": upper_row["peak_queue_depth"],
        }

    return classifications


def _build_sensitivity_report(
    df: pd.DataFrame,
    classification: Dict[str, Dict[str, Any]]
) -> str:
    """Builds a human-readable sensitivity analysis report for non-specialists."""

    # Separate decision-changing from little-effect assumptions
    decision_changing = []
    little_effect = []
    for param, info in classification.items():
        if info.get("classification") == "DECISION-CHANGING":
            decision_changing.append((param, info))
        else:
            little_effect.append((param, info))

    # Build the report text
    lines = []
    lines.append("=" * 90)
    lines.append("PEAK-DEMAND CAPACITY SIMULATOR -- SENSITIVITY ANALYSIS REPORT")
    lines.append("=" * 90)
    lines.append(f"Generated Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Stress Scenario: {STRESS_SCENARIO}")
    lines.append(f"Total Assumptions Tested: {len(ASSUMPTIONS)}")
    lines.append(f"Total Simulations Executed: {len(df)}")
    lines.append("")
    lines.append("PURPOSE:")
    lines.append("This analysis tests which planning assumptions materially affect")
    lines.append("the capacity recommendation. If changing an assumption causes")
    lines.append("SLA compliance to flip, peak instances to change significantly,")
    lines.append("or latency to cross the SLA threshold, it is classified as")
    lines.append("'DECISION-CHANGING'. Otherwise it has 'LITTLE EFFECT'.")
    lines.append("")

    # ── Section 1: Summary Table ──────────────────────────────────────────────
    lines.append("-" * 90)
    lines.append("1. ASSUMPTION CLASSIFICATION SUMMARY")
    lines.append("-" * 90)
    lines.append("")
    lines.append(f"  {'Assumption':<35s} {'Classification':<22s} {'Lower SLA%':>10s} {'Base SLA%':>10s} {'Upper SLA%':>10s}")
    lines.append("  " + "-" * 87)

    for param, info in sorted(classification.items(), key=lambda x: x[1]["classification"]):
        cls_str = info["classification"]
        lower_sla = info.get("lower_sla", "N/A")
        baseline_sla = info.get("baseline_sla", "N/A")
        upper_sla = info.get("upper_sla", "N/A")
        display = info["display_name"]

        if isinstance(lower_sla, (int, float)):
            lines.append(f"  {display:<35s} {cls_str:<22s} {lower_sla:>9.1f}% {baseline_sla:>9.1f}% {upper_sla:>9.1f}%")
        else:
            lines.append(f"  {display:<35s} {cls_str:<22s} {'N/A':>10s} {'N/A':>10s} {'N/A':>10s}")

    lines.append("")

    # ── Section 2: Decision-Changing Assumptions ──────────────────────────────
    lines.append("-" * 90)
    lines.append("2. DECISION-CHANGING ASSUMPTIONS")
    lines.append("-" * 90)
    lines.append("")

    if decision_changing:
        lines.append(f"  {len(decision_changing)} assumption(s) materially change the capacity recommendation:")
        lines.append("")
        for i, (param, info) in enumerate(decision_changing, 1):
            display = info["display_name"]
            # Find the assumption definition to get values
            assumption_def = next((a for a in ASSUMPTIONS if a["param"] == param), None)
            if assumption_def:
                lower_val = assumption_def["lower"]
                baseline_val = assumption_def["baseline"]
                upper_val = assumption_def["upper"]
                unit = assumption_def["unit"]
                desc = assumption_def["description"]
            else:
                lower_val = baseline_val = upper_val = "?"
                unit = ""
                desc = ""

            lines.append(f"  {i}. {display}")
            lines.append(f"     Description: {desc}")
            lines.append(f"     Tested Range: Lower={lower_val}{unit}, Baseline={baseline_val}{unit}, Upper={upper_val}{unit}")
            lines.append("")
            lines.append(f"     {'Metric':<30s} {'Lower':>12s} {'Baseline':>12s} {'Upper':>12s}")
            lines.append(f"     {'-'*66}")
            lines.append(f"     {'SLA Compliance %':<30s} {info.get('lower_sla', 0):>11.1f}% {info.get('baseline_sla', 0):>11.1f}% {info.get('upper_sla', 0):>11.1f}%")
            lines.append(f"     {'Max p95 Latency (ms)':<30s} {info.get('lower_p95', 0):>12,.1f} {info.get('baseline_p95', 0):>12,.1f} {info.get('upper_p95', 0):>12,.1f}")
            lines.append(f"     {'Peak Instances':<30s} {info.get('lower_inst', 0):>12d} {info.get('baseline_inst', 0):>12d} {info.get('upper_inst', 0):>12d}")
            lines.append(f"     {'Peak Queue Depth':<30s} {info.get('lower_queue', 0):>12,.1f} {info.get('baseline_queue', 0):>12,.1f} {info.get('upper_queue', 0):>12,.1f}")
            lines.append("")
            lines.append(f"     Why it matters:")
            for reason in info.get("reasons", []):
                lines.append(f"       - {reason}")
            lines.append("")
    else:
        lines.append("  No assumptions were classified as decision-changing.")
        lines.append("  The capacity recommendation appears robust to all tested variations.")
        lines.append("")

    # ── Section 3: Little Effect Assumptions ──────────────────────────────────
    lines.append("-" * 90)
    lines.append("3. ASSUMPTIONS WITH LITTLE EFFECT")
    lines.append("-" * 90)
    lines.append("")

    if little_effect:
        lines.append(f"  {len(little_effect)} assumption(s) have little effect on the outcome:")
        lines.append("")
        for i, (param, info) in enumerate(little_effect, 1):
            display = info["display_name"]
            assumption_def = next((a for a in ASSUMPTIONS if a["param"] == param), None)
            if assumption_def:
                desc = assumption_def["description"]
            else:
                desc = ""
            lines.append(f"  {i}. {display}")
            lines.append(f"     {desc}")
            lines.append(f"     SLA Compliance: {info.get('lower_sla', 0):.1f}% / {info.get('baseline_sla', 0):.1f}% / {info.get('upper_sla', 0):.1f}% (Lower/Base/Upper)")
            for reason in info.get("reasons", []):
                lines.append(f"     - {reason}")
            lines.append("")
    else:
        lines.append("  All tested assumptions materially affect the outcome.")
        lines.append("")

    # ── Section 4: Plain Language Summary ─────────────────────────────────────
    lines.append("-" * 90)
    lines.append("4. PLAIN LANGUAGE SUMMARY")
    lines.append("-" * 90)
    lines.append("")
    lines.append("  This sensitivity analysis tested what happens to the capacity plan when we")
    lines.append("  change each assumption individually, while keeping everything else constant.")
    lines.append("")

    if decision_changing:
        lines.append("  The following assumptions are CRITICAL to get right:")
        lines.append("")
        for param, info in decision_changing:
            display = info["display_name"]
            reasons = info.get("reasons", [])
            assumption_def = next((a for a in ASSUMPTIONS if a["param"] == param), None)

            # Generate a plain-language explanation
            if param == "scaling_delay_seconds":
                lines.append(f"  - {display}: If scaling takes {assumption_def['upper']}{assumption_def['unit']} instead of")
                lines.append(f"    {assumption_def['baseline']}{assumption_def['unit']}, the system may violate the latency SLA during")
                lines.append(f"    the first peak of a disaster event. Faster provisioning ({assumption_def['lower']}{assumption_def['unit']})")
                lines.append(f"    significantly improves resilience.")
            elif param == "capacity_per_instance":
                lines.append(f"  - {display}: If each server handles only {assumption_def['lower']} RPM instead")
                lines.append(f"    of {assumption_def['baseline']} RPM, the system needs substantially more instances")
                lines.append(f"    and queues grow much larger during peak demand.")
            elif param == "max_instances":
                lines.append(f"  - {display}: Reducing the scaling ceiling from")
                lines.append(f"    {assumption_def['baseline']} to {assumption_def['lower']} instances severely limits disaster")
                lines.append(f"    absorption capacity. The system cannot scale enough to meet extreme demand.")
            elif param == "traffic_multiplier":
                lines.append(f"  - {display}: If actual disaster traffic is {assumption_def['upper']}x higher than")
                lines.append(f"    modeled, the infrastructure plan may not absorb the load. This is")
                lines.append(f"    the single most impactful assumption because it directly controls demand volume.")
            elif param == "sla_latency_target_ms":
                lines.append(f"  - {display}: A stricter target ({assumption_def['lower']}ms) makes it much harder")
                lines.append(f"    to achieve compliance, while a relaxed target ({assumption_def['upper']}ms) allows the")
                lines.append(f"    system to remain compliant even under heavier load.")
            elif param == "initial_instances":
                lines.append(f"  - {display}: Starting with only {assumption_def['lower']} servers instead of")
                lines.append(f"    {assumption_def['baseline']} creates a deeper initial capacity gap, leading to queue buildup")
                lines.append(f"    before auto-scaling can react.")
            elif param == "safety_margin_instances":
                lines.append(f"  - {display}: Adding {assumption_def['upper']} extra pre-warmed instances")
                lines.append(f"    significantly reduces queue depth during the first minutes of a disaster surge.")
            else:
                lines.append(f"  - {display}: Changes to this parameter significantly affect the outcome.")
                for reason in reasons:
                    lines.append(f"      {reason}")
            lines.append("")

    if little_effect:
        lines.append("  The following assumptions have LITTLE EFFECT within the tested range:")
        lines.append("")
        for param, info in little_effect:
            display = info["display_name"]
            lines.append(f"  - {display}: Varying this within the tested range does not materially")
            lines.append(f"    change the capacity recommendation or SLA compliance outcome.")
        lines.append("")

    lines.append("-" * 90)
    lines.append("5. RECOMMENDATION")
    lines.append("-" * 90)
    lines.append("")

    if decision_changing:
        lines.append("  Focus planning effort on the DECISION-CHANGING assumptions listed above.")
        lines.append("  These are the parameters where getting the estimate wrong could lead to")
        lines.append("  either over-provisioning (wasting budget) or under-provisioning (SLA breach).")
        lines.append("")
        lines.append("  For LITTLE EFFECT assumptions, the current baseline values are acceptable.")
        lines.append("  Small estimation errors in these parameters will not change the final decision.")
    else:
        lines.append("  The capacity recommendation appears robust across all tested variations.")
        lines.append("  No single assumption change flips the SLA compliance decision.")

    lines.append("")
    lines.append("=" * 90)
    lines.append("REPORT COMPLETE -- Sensitivity Analysis Saved to outputs/")
    lines.append("=" * 90)

    return "\n".join(lines)


if __name__ == "__main__":
    df, report = run_sensitivity_analysis()
    print("\n" + report)
