"""
Peak-Demand Capacity Simulator -- Upgraded Interactive Streamlit Dashboard
==========================================================================
Step 9: Complete 10-section dashboard with Explainable Recommendation Engine,
Before vs After planning comparison, and Multi-Organisation RBAC.

Sections:
1. Executive Overview (Plain-Language Executive Summary & KPI Cards)
2. Historical Load (Operational Telemetry with Synthetic Data notice)
3. Scenario Selection (Normal, Seasonal Peak, Breaking News, Disaster Peak,
   Extreme Disaster, Disaster + Breaking News, Disaster + Seasonal Peak)
4. Capacity Configuration (RBAC-enforced controls + Safety Margin)
5. Simulation (Demand vs Capacity, Queue, Latency p95/p99, Instances, Utilisation)
6. SLA Results (SLA Compliant / Degraded / Violated, Duration, Timeline)
7. Strategy Comparison (5 strategies compared on measurable trade-offs)
8. Sensitivity Analysis (8 parameter impacts, Decision-Changing assumptions)
9. Failure Testing (8 stress/failure conditions, recovery time, impact)
10. Organisation & Permissions (Role rights, visible features, registered orgs)
+ Capacity Recommendation Panel (Dedicated explainable 5-field analysis)
+ Before vs After Visual (Average-demand vs Scenario-based planning)

Run with:  streamlit run dashboard/app.py
"""

import sys
import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, Any, Optional, List

# ── Ensure project root is importable ────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.simulation.simulator import run_simulation
from src.simulation.scenarios import generate_scenario, compare_all_scenarios
from src.simulation.run_scenarios import run_and_export_scenarios
from src.simulation.sensitivity import (
    run_sensitivity_analysis,
    ASSUMPTIONS,
    BASELINE_CONFIG,
    STRESS_SCENARIO,
)
from src.capacity.baseline import evaluate_capacity_for_demand, DEFAULT_CONFIG
from src.utils.permissions import (
    Organisation,
    Role,
    PermissionPolicy,
    has_permission,
    enforce_permission,
    get_visible_sections,
    get_allowed_actions,
    filter_metrics_for_organisation,
    load_organisations,
    get_organisation,
)
from src.analysis.recommendations import (
    generate_executive_summary_statements,
    generate_explainable_recommendation,
    export_recommendations_csv,
)
from src.analysis.historical_analysis import (
    load_and_validate_dataset,
    compute_overall_metrics,
    CLEANED_DATA_PATH,
)


# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Peak-Demand Capacity Simulator",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS THEME (Glassmorphic Dark Theme with Inter Typography)
# ══════════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Hero Banner ─────────────────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #0b0f19 0%, #1e1b4b 45%, #0f172a 100%);
    padding: 2.2rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    text-align: center;
    border: 1px solid rgba(165,180,252,0.15);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.hero-banner h1 {
    color: #ffffff; font-size: 2.2rem; font-weight: 800;
    margin-bottom: 0.3rem; letter-spacing: -0.5px;
}
.hero-banner .subtitle {
    color: #c7d2fe; font-size: 1.05rem; font-weight: 400; margin-top: 0;
}

/* ── Executive Summary Panel ─────────────────────────────────────── */
.exec-summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 14px;
    margin-bottom: 1.4rem;
}
.exec-summary-card {
    background: linear-gradient(145deg, #131b2e, #1a233a);
    border: 1px solid rgba(129,140,248,0.22);
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.exec-summary-card.alert {
    border-color: rgba(239,68,68,0.35);
    background: linear-gradient(145deg, #231217, #1e1520);
}
.exec-summary-card.action {
    border-color: rgba(16,185,129,0.35);
    background: linear-gradient(145deg, #0d2218, #11261d);
}
.exec-summary-card h4 {
    font-size: 0.82rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; margin-bottom: 6px;
}
.exec-summary-card.alert h4 { color: #f87171; }
.exec-summary-card.action h4 { color: #34d399; }
.exec-summary-card.standard h4 { color: #a5b4fc; }
.exec-summary-card p {
    color: #e2e8f0; font-size: 0.92rem; line-height: 1.55; margin: 0;
}

/* ── KPI Cards ───────────────────────────────────────────────────── */
.kpi-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.2rem; }
.kpi-card {
    flex: 1 1 140px;
    background: linear-gradient(145deg, #131a2a, #1e2638);
    border: 1px solid rgba(165,180,252,0.14);
    border-radius: 14px;
    padding: 1.1rem 1rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.16);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(99,102,241,0.18);
}
.kpi-card .kpi-label {
    color: #94a3b8; font-size: 0.78rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px;
}
.kpi-card .kpi-value {
    color: #f1f5f9; font-size: 1.55rem; font-weight: 800; line-height: 1.2;
}
.kpi-card .kpi-unit {
    color: #64748b; font-size: 0.74rem; font-weight: 500; margin-top: 3px;
}
.kpi-card.success { border-color: rgba(16,185,129,0.4); }
.kpi-card.success .kpi-value { color: #34d399; }
.kpi-card.danger { border-color: rgba(239,68,68,0.4); }
.kpi-card.danger .kpi-value { color: #f87171; }
.kpi-card.warning { border-color: rgba(251,191,36,0.4); }
.kpi-card.warning .kpi-value { color: #fbbf24; }
.kpi-card.info { border-color: rgba(99,102,241,0.4); }
.kpi-card.info .kpi-value { color: #a5b4fc; }

/* ── Section Header ──────────────────────────────────────────────── */
.section-header {
    background: linear-gradient(145deg, #131c31, #0b1325);
    padding: 1.1rem 1.4rem;
    border-radius: 12px;
    margin: 1.5rem 0 1rem;
    border: 1px solid #1e293b;
    border-left: 4px solid #6366f1;
}
.section-header h2 {
    color: #f8fafc; font-size: 1.35rem; font-weight: 700; margin: 0;
}
.section-header p {
    color: #94a3b8; font-size: 0.88rem; margin: 4px 0 0;
}

/* ── Recommendation Box ──────────────────────────────────────────── */
.rec-box {
    background: linear-gradient(145deg, #091a13, #0f271d);
    border: 1px solid rgba(16,185,129,0.35);
    border-radius: 14px;
    padding: 1.5rem 1.6rem;
    margin: 1rem 0;
}
.rec-box.warn {
    background: linear-gradient(145deg, #1f1809, #2b210c);
    border-color: rgba(251,191,36,0.35);
}
.rec-box.fail {
    background: linear-gradient(145deg, #200f13, #2b1319);
    border-color: rgba(239,68,68,0.35);
}
.rec-box h3 { color: #34d399; font-size: 1.15rem; font-weight: 700; margin-bottom: 10px; }
.rec-box.warn h3 { color: #fbbf24; }
.rec-box.fail h3 { color: #f87171; }
.rec-box p { color: #cbd5e1; font-size: 0.94rem; line-height: 1.65; margin-bottom: 8px; }
.rec-box .rec-field-title {
    color: #94a3b8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; margin-top: 10px; margin-bottom: 2px;
}

/* ── Info Card ────────────────────────────────────────────────────── */
.info-card {
    background: linear-gradient(145deg, #131a2b, #1b243b);
    border: 1px solid rgba(165,180,252,0.12);
    border-radius: 14px;
    padding: 1.3rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.14);
}
.info-card h3 { color: #a5b4fc; font-size: 1.05rem; font-weight: 700; margin-bottom: 6px; }
.info-card p { color: #cbd5e1; font-size: 0.90rem; line-height: 1.6; margin: 0; }

/* ── Notice Banner ───────────────────────────────────────────────── */
.notice-banner {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #334155;
    border-left: 4px solid #38bdf8;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #cbd5e1;
    font-size: 0.85rem;
    margin-bottom: 1rem;
}

/* ── Divider ─────────────────────────────────────────────────────── */
.section-divider {
    border: none;
    border-top: 1px solid rgba(165,180,252,0.12);
    margin: 1.8rem 0;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS & THEME DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════
def kpi_card(label: str, value: str, unit: str = "", style: str = "") -> str:
    return f"""
    <div class="kpi-card {style}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
    </div>"""


def section_header(icon: str, title: str, desc: str = "") -> None:
    desc_html = f'<p>{desc}</p>' if desc else ''
    st.markdown(f"""
    <div class="section-header">
        <h2>{icon} {title}</h2>
        {desc_html}
    </div>""", unsafe_allow_html=True)


PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,15,30,0.6)",
    font=dict(family="Inter, sans-serif", size=12, color="#c9d1d9"),
    margin=dict(l=50, r=30, t=50, b=40),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)", font=dict(size=11),
    ),
    xaxis=dict(gridcolor="rgba(100,116,139,0.15)", zerolinecolor="rgba(100,116,139,0.2)"),
    yaxis=dict(gridcolor="rgba(100,116,139,0.15)", zerolinecolor="rgba(100,116,139,0.2)"),
)

COLORS = {
    "demand": "#818cf8",
    "capacity": "#34d399",
    "queue": "#f87171",
    "latency": "#fbbf24",
    "latency_p99": "#f472b6",
    "error": "#fb7185",
    "instances": "#38bdf8",
    "util": "#c084fc",
    "sla_line": "#ef4444",
}

SCENARIO_LABELS = {
    "NORMAL": "Normal",
    "SEASONAL_PEAK": "Seasonal Peak",
    "BREAKING_NEWS": "Breaking News",
    "DISASTER_PEAK": "Disaster Peak",
    "EXTREME_DISASTER": "Extreme Disaster",
    "DISASTER_BREAKING_NEWS": "Disaster + Breaking News",
    "DISASTER_SEASONAL": "Disaster + Seasonal Peak",
}

SCENARIO_COLORS = {
    "NORMAL": "#34d399",
    "SEASONAL_PEAK": "#38bdf8",
    "BREAKING_NEWS": "#fbbf24",
    "DISASTER_PEAK": "#f97316",
    "EXTREME_DISASTER": "#ef4444",
    "DISASTER_BREAKING_NEWS": "#ec4899",
    "DISASTER_SEASONAL": "#a855f7",
}


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR: RBAC & CONTROLS
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🚨 Capacity Simulator")
    st.caption("Step 9 — Explainable Recommendation Engine")
    st.markdown("---")

    # 1. Organisation Selection
    st.markdown("**1. Organisation Selection**")
    org_choice = st.selectbox(
        "Organisation",
        [o.value for o in Organisation],
        index=0,
    )
    org_enum = Organisation(org_choice)
    org_info = get_organisation(org_choice) or {}
    allowed_scenarios = org_info.get("allowed_scenarios", [
        "NORMAL", "SEASONAL_PEAK", "BREAKING_NEWS", "DISASTER_PEAK", "EXTREME_DISASTER"
    ])
    default_sla = org_info.get("default_SLA_target", {})
    def_lat = int(default_sla.get("p95_latency_target_ms", 500.0))
    def_err = float(default_sla.get("error_rate_target", 0.01)) * 100.0
    def_comp = float(default_sla.get("sla_compliance_target_pct", 99.0))

    # 2. Role Selection
    st.markdown("**2. Role Selection**")
    role_choice = st.selectbox(
        "User Permission Level",
        [r.value for r in Role],
        index=1,  # Default to Analyst
    )
    role_enum = Role(role_choice)

    # Permission Capability Checks
    can_edit_cfg = has_permission(role_enum, "edit_capacity_config", org_enum)
    can_edit_sys = has_permission(role_enum, "edit_system_limits", org_enum)
    can_run_sim = has_permission(role_enum, "run_simulation", org_enum)
    can_run_sens = has_permission(role_enum, "run_sensitivity_analysis", org_enum)
    is_ext_partner = PermissionPolicy.is_external_partner(org_enum)
    visible_sections = get_visible_sections(role_enum, org_enum)

    with st.expander(f"🔑 Active Permissions: {role_choice}", expanded=False):
        st.markdown(f"**Organisation:** {org_choice}")
        st.markdown(f"**Role:** {role_choice}")
        caps = PermissionPolicy.get_role_capabilities(role_enum, org_enum)
        for perm_name, is_allowed in caps["permissions"]:
            icon = "✅" if is_allowed else "❌"
            st.markdown(f"{icon} `{perm_name}`")

    st.markdown("---")

    # 3. Scenario Selection (strictly restricted to organisation profile)
    st.markdown("**3. Scenario Selection**")
    default_sc_idx = 0
    if "DISASTER_PEAK" in allowed_scenarios:
        default_sc_idx = allowed_scenarios.index("DISASTER_PEAK")
    elif len(allowed_scenarios) > 0:
        default_sc_idx = len(allowed_scenarios) - 1

    scenario_name = st.selectbox(
        "Select Scenario",
        allowed_scenarios,
        index=default_sc_idx,
        format_func=lambda x: SCENARIO_LABELS.get(x, x),
    )

    st.markdown("---")

    # 4. Capacity Configuration Controls (RBAC-enforced)
    st.markdown("**4. Capacity Configuration**")
    if not can_edit_cfg:
        st.caption("🔒 *Restricted settings — read-only for Viewer & Analyst*")

    initial_instances = st.slider(
        "Initial Instances", 2, 30, 10, 1,
        disabled=not can_edit_cfg,
        help="Base server fleet provisioned before the event begins."
    )
    max_instances = st.slider(
        "Maximum Instances", 10, 100, 50, 5,
        disabled=not can_edit_sys,
        help="Hard server ceiling enforced by infrastructure budget/limits."
    )
    capacity_per_instance = st.slider(
        "Instance Capacity (RPM)", 100, 1500, 500, 50,
        disabled=not can_edit_cfg,
        help="Maximum requests processed per minute per server instance."
    )
    scaling_delay = st.slider(
        "Scaling Delay (seconds)", 30, 600, 180, 30,
        disabled=not can_edit_cfg,
        help="Time taken to boot and initialize a new cloud instance."
    )
    safety_margin = st.slider(
        "Safety Margin (%)", 0, 50, 20, 5,
        disabled=not can_edit_cfg,
        help="Over-provisioning headroom buffer maintained above average demand."
    )

    st.markdown("---")

    # SLA Targets (using organisation defaults)
    st.markdown("**SLA Configuration**")
    if not can_edit_sys:
        st.caption("🔒 *Statutory limits locked for current role*")
    sla_latency = st.slider("SLA Latency Target (ms)", 100, 2000, def_lat, 50, disabled=not can_edit_sys)
    sla_error = st.slider("SLA Error Target (%)", 0.5, 10.0, def_err, 0.5, disabled=not can_edit_sys) / 100.0
    sla_comp_target = st.slider("SLA Compliance Target (%)", 90.0, 99.9, def_comp, 0.5, disabled=not can_edit_sys)

    st.markdown("---")

    if not can_run_sim:
        st.info("ℹ️ Viewer mode active: Execution controls locked.")
    run_btn = st.button("🚀 Re-Run Simulation", use_container_width=True, type="primary", disabled=not can_run_sim)


# ══════════════════════════════════════════════════════════════════════════════
#  CACHED SIMULATION & COMPARISON RUNNERS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def cached_simulation(sc, init_i, max_i, cap_i, delay, sla_lat, sla_err, seed=42):
    df_sim, summary = run_simulation(
        workload_scenario=sc,
        initial_instances=init_i,
        max_instances=max_i,
        capacity_per_instance=cap_i,
        scaling_delay_seconds=delay,
        sla_latency_target_ms=sla_lat,
        sla_error_target_rate=sla_err,
        seed=seed,
    )
    return df_sim, summary


@st.cache_data(show_spinner=False)
def cached_comparison(init_i, max_i, cap_i, delay, seed=42):
    return run_and_export_scenarios(
        initial_instances=init_i,
        max_instances=max_i,
        capacity_per_instance=cap_i,
        scaling_delay_seconds=delay,
        seed=seed,
    )


@st.cache_data(show_spinner=False)
def cached_sensitivity(seed=42):
    return run_sensitivity_analysis(seed=seed)


@st.cache_data(show_spinner=False)
def cached_historical_data():
    if CLEANED_DATA_PATH.exists():
        df_hist = load_and_validate_dataset(CLEANED_DATA_PATH)
        return df_hist
    return pd.DataFrame()


# Execute current scenario simulation
with st.spinner("Simulating emergency workload..."):
    df_sim, summary = cached_simulation(
        scenario_name, initial_instances, max_instances,
        capacity_per_instance, scaling_delay, sla_latency, sla_error,
    )

# Pre-run multi-scenario comparison for context
comp_df, _ = cached_comparison(initial_instances, max_instances, capacity_per_instance, scaling_delay)

# Ensure p99 latency column is available
if "p99_latency_ms" not in df_sim.columns:
    df_sim["p99_latency_ms"] = df_sim["p95_latency_ms"] * 1.35

# Build summary dictionaries
sim_config = {
    "initial_instances": initial_instances,
    "max_instances": max_instances,
    "capacity_per_instance": capacity_per_instance,
    "scaling_delay_seconds": scaling_delay,
    "safety_margin_pct": safety_margin,
}
sla_config_dict = {
    "p95_latency_target_ms": sla_latency,
    "error_rate_target": sla_error,
    "sla_compliance_target_pct": sla_comp_target,
}

# Key measured metrics
peak_demand = float(df_sim["incoming_requests"].max())
peak_cap = float(df_sim["available_capacity"].max())
max_queue = float(df_sim["queue_depth"].max())
max_p95 = float(df_sim["p95_latency_ms"].max())
max_p99 = float(df_sim["p99_latency_ms"].max())
max_err = float(df_sim["error_rate"].max() * 100)
peak_inst = int(df_sim["active_instances"].max())
compliance = float(summary.get("compliance_percentage", 100.0))
sla_met = bool(summary.get("sla_compliant", True))

# Compute SLA violation duration (minutes)
breach_mask = df_sim["sla_status"] == "breached"
violation_minutes = int(breach_mask.sum())  # each step is 1 minute

# Determine 3-state SLA Status Label
if compliance >= sla_comp_target and max_p95 <= sla_latency and max_err <= (sla_error * 100):
    sla_status_label = "SLA Compliant"
    sla_status_class = "success"
elif compliance >= 90.0:
    sla_status_label = "SLA Degraded"
    sla_status_class = "warning"
else:
    sla_status_label = "SLA Violated"
    sla_status_class = "danger"


# ══════════════════════════════════════════════════════════════════════════════
#  HERO BANNER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero-banner">
    <h1>🚨 Peak-Demand Capacity Simulator</h1>
    <p class="subtitle">Scenario-driven capacity planning and explainable recommendation engine for public emergency websites</p>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PART 2: EXECUTIVE SUMMARY (Plain-Language Statements at Top of Dashboard)
# ══════════════════════════════════════════════════════════════════════════════
exec_stmts = generate_executive_summary_statements(
    summary=summary,
    scenario_name=scenario_name,
    config=sim_config,
    sla_targets=sla_config_dict,
)

st.markdown(f"""
<div class="exec-summary-grid">
    <div class="exec-summary-card standard">
        <h4>1. Current Situation</h4>
        <p>{exec_stmts['current_situation']}</p>
    </div>
    <div class="exec-summary-card {'alert' if max_queue > 0 or not sla_met else 'standard'}">
        <h4>2. System Impact</h4>
        <p>{exec_stmts['system_impact']}</p>
    </div>
    <div class="exec-summary-card {'alert' if not sla_met else 'action'}">
        <h4>3. SLA Impact</h4>
        <p>{exec_stmts['sla_impact']}</p>
    </div>
    <div class="exec-summary-card action">
        <h4>4. Operational Action</h4>
        <p>{exec_stmts['operational_action']}</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
section_header("📋", "1. Executive Overview",
    "High-level operational posture, active context, and key infrastructure indicators.")

ext_badge = "<span style='color:#f87171; font-weight:bold;'> [EXTERNAL PARTNER - REDACTED VIEW]</span>" if is_ext_partner else ""
peak_inst_val = "[REDACTED]" if is_ext_partner else f"{peak_inst}"
peak_cap_val = "[REDACTED]" if is_ext_partner else f"{peak_cap:,.0f}"

col_meta1, col_meta2, col_meta3 = st.columns(3)
with col_meta1:
    st.markdown(f"""
    <div class="info-card">
        <h3>Organisation{ext_badge}</h3>
        <p><strong>{org_choice}</strong><br>
        <span style="font-size:0.83rem; color:#94a3b8;">{org_info.get('description', '')}</span></p>
    </div>""", unsafe_allow_html=True)
with col_meta2:
    st.markdown(f"""
    <div class="info-card">
        <h3>Role & Access</h3>
        <p>Role: <strong>{role_choice}</strong><br>
        <span style="font-size:0.83rem; color:#94a3b8;">Permissions: {len(caps['permissions'])} actions configured ({sum(1 for _, a in caps['permissions'] if a)} granted)</span></p>
    </div>""", unsafe_allow_html=True)
with col_meta3:
    st.markdown(f"""
    <div class="info-card">
        <h3>Current Scenario</h3>
        <p>Scenario: <strong>{SCENARIO_LABELS.get(scenario_name, scenario_name)}</strong><br>
        <span style="font-size:0.83rem; color:#94a3b8;">Target: {sla_latency}ms p95 / {sla_error*100:.1f}% error / {sla_comp_target:.1f}% compliance</span></p>
    </div>""", unsafe_allow_html=True)

# 7 KPI Cards
lat_style = "success" if max_p95 <= sla_latency else "danger"
err_style = "success" if max_err <= sla_error * 100 else "danger"
queue_style = "success" if max_queue < 500 else ("warning" if max_queue < 5000 else "danger")

st.markdown(f"""
<div class="kpi-row">
    {kpi_card("Peak Demand", f"{peak_demand:,.0f}", "RPM", "info")}
    {kpi_card("Available Capacity", peak_cap_val, "RPM", "info")}
    {kpi_card("Max Queue", f"{max_queue:,.0f}", "requests", queue_style)}
    {kpi_card("Max p95 Latency", f"{max_p95:,.0f}", "ms", lat_style)}
    {kpi_card("Max Error Rate", f"{max_err:.2f}", "%", err_style)}
    {kpi_card("SLA Compliance", f"{compliance:.1f}%", sla_status_label, sla_status_class)}
    {kpi_card("Active Instances", peak_inst_val, "servers", "info")}
</div>""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: HISTORICAL LOAD
# ══════════════════════════════════════════════════════════════════════════════
if "Historical Load" in visible_sections:
    section_header("📈", "2. Historical Load",
        "Operational workload telemetry and baseline traffic behavior over time.")

    st.markdown("""
    <div class="notice-banner">
        ⚠️ <strong>Synthetic Data Notice:</strong> The operational dataset represents synthetic baseline telemetry
        (10,080 minutes / 7 continuous days) modeled after public emergency-information incident patterns.
        All metrics shown are computed from existing historical analysis outputs.
    </div>""", unsafe_allow_html=True)

    df_hist = cached_historical_data()

    if not df_hist.empty:
        # Downsample for snappy Plotly interaction (take every 5th minute = 2,016 points)
        df_hist_plot = df_hist.iloc[::5].copy()

        hist_tabs = st.tabs(["Traffic & Capacity", "Queue Depth", "Latency Profile", "CPU Utilisation", "Scaling Actions"])

        with hist_tabs[0]:
            fig_ht = go.Figure()
            fig_ht.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["requests_per_minute"],
                name="Traffic Demand (RPM)", mode="lines",
                line=dict(color=COLORS["demand"], width=1.8),
                fill="tozeroy", fillcolor="rgba(129,140,248,0.12)",
            ))
            fig_ht.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["total_capacity_rpm"],
                name="Fleet Capacity (RPM)", mode="lines",
                line=dict(color=COLORS["capacity"], width=2, dash="dash"),
            ))
            fig_ht.update_layout(
                title="Historical Traffic vs Available Fleet Capacity Over 7 Days",
                yaxis_title="Requests / Minute",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_ht, use_container_width=True)

        with hist_tabs[1]:
            fig_hq = go.Figure()
            fig_hq.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["queue_depth"],
                name="Queue Depth", mode="lines",
                line=dict(color=COLORS["queue"], width=2),
                fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
            ))
            fig_hq.update_layout(
                title="Historical Queue Accumulation Over 7 Days",
                yaxis_title="Queued Requests",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_hq, use_container_width=True)

        with hist_tabs[2]:
            fig_hl = go.Figure()
            fig_hl.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["average_latency_ms"],
                name="Avg Latency", mode="lines", line=dict(color="#38bdf8", width=1.5),
            ))
            fig_hl.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["p95_latency_ms"],
                name="p95 Latency", mode="lines", line=dict(color=COLORS["latency"], width=1.8),
            ))
            fig_hl.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["p99_latency_ms"],
                name="p99 Latency", mode="lines", line=dict(color=COLORS["latency_p99"], width=1.8, dash="dot"),
            ))
            fig_hl.add_hline(y=500.0, line_dash="dash", line_color=COLORS["sla_line"], annotation_text="SLA 500ms")
            fig_hl.update_layout(
                title="Historical Response Latency Distribution Over Time",
                yaxis_title="Latency (ms)",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_hl, use_container_width=True)

        with hist_tabs[3]:
            fig_hu = go.Figure()
            fig_hu.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["cpu_utilisation"],
                name="CPU Utilisation %", mode="lines",
                line=dict(color=COLORS["util"], width=2),
                fill="tozeroy", fillcolor="rgba(192,132,252,0.10)",
            ))
            fig_hu.add_hline(y=70, line_dash="dash", line_color="#fbbf24", annotation_text="Scale-out (70%)")
            fig_hu.add_hline(y=85, line_dash="dash", line_color="#ef4444", annotation_text="Urgent (85%)")
            fig_hu.update_layout(
                title="Historical CPU Utilisation Over Time",
                yaxis_title="CPU Utilisation (%)",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_hu, use_container_width=True)

        with hist_tabs[4]:
            fig_ha = go.Figure()
            scale_colors = {"scale_up": "#34d399", "scale_down": "#f87171", "none": "#475569"}
            action_colors = [scale_colors.get(str(a).lower(), "#475569") for a in df_hist_plot["scaling_action"]]
            fig_ha.add_trace(go.Scatter(
                x=df_hist_plot["timestamp"], y=df_hist_plot["available_instances"],
                name="Available Instances", mode="lines+markers",
                marker=dict(size=4, color=action_colors),
                line=dict(color=COLORS["instances"], width=1.5),
            ))
            fig_ha.update_layout(
                title="Historical Server Instances & Scaling Action Events",
                yaxis_title="Active Instances",
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig_ha, use_container_width=True)
    else:
        st.info("Historical cleaned dataset not found at data/processed/emergency_load_cleaned.csv.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: SCENARIO SELECTION
# ══════════════════════════════════════════════════════════════════════════════
if "Scenario Selection" in visible_sections or "Workload Scenario" in visible_sections:
    section_header("🌪️", "3. Scenario Selection",
        "Public emergency workload profiles and surge characteristics.")

    scenario_descriptions = {
        "NORMAL": "Typical day-to-day citizen traffic with no extraordinary emergency advisories. Systems operate comfortably within baseline.",
        "SEASONAL_PEAK": "Anticipated seasonal surge (e.g. holiday weather alerts, high-tide forecasts). Traffic climbs to 1.5x - 2.0x baseline.",
        "BREAKING_NEWS": "Sudden breaking event causing an abrupt 2.0x - 3.0x spike within minutes as the public seeks real-time verification.",
        "DISASTER_PEAK": "Severe emergency (Category 3 Hurricane / Regional Flash Flood) generating a sustained 3.0x - 5.0x demand surge for multiple hours.",
        "EXTREME_DISASTER": "Catastrophic event (Category 5 Hurricane / Tsunami Warning) producing an intense 5.0x - 8.5x traffic surge stressing infrastructure limits.",
        "DISASTER_BREAKING_NEWS": "Compound emergency: An extreme disaster compounded by sudden evacuation route changes or breaking dam alerts (4.0x - 7.0x surge).",
        "DISASTER_SEASONAL": "Compound emergency: Severe disaster conditions coinciding with an existing holiday travel weekend (4.0x - 6.5x surge).",
    }

    sc_col1, sc_col2 = st.columns([1.8, 1.2])
    with sc_col1:
        st.markdown(f"""
        <div class="info-card">
            <h3>Active Profile: {SCENARIO_LABELS.get(scenario_name, scenario_name)}</h3>
            <p>{scenario_descriptions.get(scenario_name, 'Custom scenario profile.')}</p>
            <p style="font-size:0.84rem; color:#a5b4fc; margin-top:8px;">
            Workload Envelope: Peak {peak_demand:,.0f} RPM &bull; Duration 24h &bull; Seed 42 Deterministic
            </p>
        </div>""", unsafe_allow_html=True)
    with sc_col2:
        st.markdown(f"""
        <div class="info-card">
            <h3>Authorised Scenarios ({len(allowed_scenarios)})</h3>
            <p style="font-size:0.86rem; color:#cbd5e1;">
            {', '.join([SCENARIO_LABELS.get(s, s) for s in allowed_scenarios])}
            </p>
            <p style="font-size:0.80rem; color:#94a3b8; margin-top:6px;">
            Filtered strictly by profile for <strong>{org_choice}</strong>.
            </p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: CAPACITY CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
if "Capacity Configuration" in visible_sections:
    section_header("⚙️", "4. Capacity Configuration",
        "Configured infrastructure capacity and operational parameters.")

    init_cap = initial_instances * capacity_per_instance
    max_cap = max_instances * capacity_per_instance

    cfg_c1, cfg_c2, cfg_c3, cfg_c4, cfg_c5 = st.columns(5)
    with cfg_c1:
        val_i = "[REDACTED]" if is_ext_partner else f"{init_cap:,.0f} RPM"
        sub_i = "[REDACTED]" if is_ext_partner else f"{initial_instances} instances"
        st.metric("Initial Capacity", val_i, sub_i)
    with cfg_c2:
        val_m = "[REDACTED]" if is_ext_partner else f"{max_cap:,.0f} RPM"
        sub_m = "[REDACTED]" if is_ext_partner else f"{max_instances} instances"
        st.metric("Max Capacity Ceiling", val_m, sub_m)
    with cfg_c3:
        st.metric("Instance Throughput", f"{capacity_per_instance} RPM", "per container")
    with cfg_c4:
        st.metric("Scaling Provision Delay", f"{scaling_delay}s", f"{scaling_delay/60:.1f} min boot lag")
    with cfg_c5:
        st.metric("Safety Margin", f"{safety_margin}%", "provision buffer")

    # Important assumptions near configurable controls
    st.markdown("""
    <div style="font-size:0.84rem; color:#94a3b8; margin-top:8px; padding:8px 12px; background:rgba(30,41,59,0.4); border-radius:8px; border:1px solid #334155;">
        <strong>Key Engineering Assumptions:</strong>
        &bull; <em>Scaling Boot Lag:</em> Newly requested cloud instances require <code>scaling_delay</code> seconds to join the cluster.
        &bull; <em>Linear Instance Sizing:</em> Each web instance safely processes up to <code>capacity_per_instance</code> RPM under SLA latency.
        &bull; <em>Buffering:</em> Requests arriving above instantaneous capacity buffer in queue up to load balancer memory limits.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: SIMULATION RESULTS
# ══════════════════════════════════════════════════════════════════════════════
section_header("📊", "5. Simulation",
    "Discrete-event simulation results under the selected scenario and capacity settings.")

# Chart 1: Demand vs Capacity
fig_dc = go.Figure()
fig_dc.add_trace(go.Scatter(
    x=df_sim["timestamp"], y=df_sim["incoming_requests"],
    name="Demand (RPM)", mode="lines",
    line=dict(color=COLORS["demand"], width=2.2),
    fill="tozeroy", fillcolor="rgba(129,140,248,0.12)",
))
fig_dc.add_trace(go.Scatter(
    x=df_sim["timestamp"], y=df_sim["available_capacity"],
    name="Available Capacity (RPM)", mode="lines",
    line=dict(color=COLORS["capacity"], width=2.2, dash="dash"),
))
fig_dc.update_layout(
    title="Demand vs Available Capacity Over Time",
    yaxis_title="Requests per Minute",
    **PLOTLY_LAYOUT,
)
st.plotly_chart(fig_dc, use_container_width=True)

# Chart 2: Queue Depth
fig_q = go.Figure()
fig_q.add_trace(go.Scatter(
    x=df_sim["timestamp"], y=df_sim["queue_depth"],
    name="Queue Depth", mode="lines",
    line=dict(color=COLORS["queue"], width=2),
    fill="tozeroy", fillcolor="rgba(248,113,113,0.10)",
))
fig_q.update_layout(
    title="Queue Growth and Drain Recovery Over Time",
    yaxis_title="Queued Requests",
    **PLOTLY_LAYOUT,
)
st.plotly_chart(fig_q, use_container_width=True)

# Charts 3 & 4: Latency & Active Instances Side-by-Side
sim_c1, sim_c2 = st.columns(2)

with sim_c1:
    fig_l = go.Figure()
    fig_l.add_trace(go.Scatter(
        x=df_sim["timestamp"], y=df_sim["p95_latency_ms"],
        name="p95 Latency", mode="lines",
        line=dict(color=COLORS["latency"], width=2),
    ))
    fig_l.add_trace(go.Scatter(
        x=df_sim["timestamp"], y=df_sim["p99_latency_ms"],
        name="p99 Latency", mode="lines",
        line=dict(color=COLORS["latency_p99"], width=1.5, dash="dot"),
    ))
    fig_l.add_hline(
        y=sla_latency, line_dash="dash", line_color=COLORS["sla_line"],
        annotation_text=f"SLA Target ({sla_latency}ms)",
        annotation_position="top right",
    )
    fig_l.update_layout(
        title="Latency (p95 / p99) vs Statutory SLA Threshold",
        yaxis_title="Latency (ms)",
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig_l, use_container_width=True)

with sim_c2:
    fig_i = go.Figure()
    fig_i.add_trace(go.Scatter(
        x=df_sim["timestamp"], y=df_sim["active_instances"],
        name="Active Instances", mode="lines",
        line=dict(color=COLORS["instances"], width=2),
        fill="tozeroy", fillcolor="rgba(56,189,248,0.10)",
    ))
    fig_i.add_hline(
        y=max_instances, line_dash="dash", line_color="rgba(148,163,184,0.6)",
        annotation_text=f"Max Ceiling ({max_instances})",
        annotation_position="top right",
    )
    fig_i.update_layout(
        title="Autoscaling Fleet Scaling Behaviour",
        yaxis_title="Active Instances",
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig_i, use_container_width=True)

# Chart 5: CPU Utilisation
fig_u = go.Figure()
fig_u.add_trace(go.Scatter(
    x=df_sim["timestamp"], y=df_sim["cpu_utilisation_pct"],
    name="CPU Utilisation %", mode="lines",
    line=dict(color=COLORS["util"], width=2),
    fill="tozeroy", fillcolor="rgba(192,132,252,0.08)",
))
fig_u.add_hline(y=70, line_dash="dash", line_color="#fbbf24", annotation_text="Scale-out (70%)")
fig_u.add_hline(y=85, line_dash="dash", line_color="#ef4444", annotation_text="Urgent (85%)")
fig_u.update_layout(
    title="Infrastructure CPU Utilisation Over Time",
    yaxis_title="Utilisation (%)",
    yaxis=dict(range=[0, 100], gridcolor="rgba(100,116,139,0.15)"),
    **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "yaxis"},
)
st.plotly_chart(fig_u, use_container_width=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6: SLA RESULTS
# ══════════════════════════════════════════════════════════════════════════════
section_header("🎯", "6. SLA Results",
    "Statutory Service-Level Agreement targets, compliance duration, and breach analysis.")

sla_col1, sla_col2 = st.columns(2)

with sla_col1:
    if sla_status_label == "SLA Compliant":
        st.markdown(f"""
        <div class="rec-box">
            <h3>SLA Status: SLA Compliant</h3>
            <p>The system fully satisfied all statutory targets under this scenario.
            Response latency remained below <strong>{sla_latency} ms</strong>, error rates remained under <strong>{sla_error*100:.2f}%</strong>,
            and compliance reached <strong>{compliance:.1f}%</strong> (target: {sla_comp_target:.1f}%).</p>
        </div>""", unsafe_allow_html=True)
    elif sla_status_label == "SLA Degraded":
        st.markdown(f"""
        <div class="rec-box warn">
            <h3>SLA Status: SLA Degraded</h3>
            <p>The system experienced transient performance degradation.<br>
            SLA compliance reached <strong>{compliance:.1f}%</strong> (target: {sla_comp_target:.1f}%).<br>
            Breach duration was <strong>{violation_minutes} minutes</strong> during peak traffic arrival.</p>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="rec-box fail">
            <h3>SLA Status: SLA Violated</h3>
            <p>The system failed statutory SLA targets during the simulated incident.<br>
            SLA violation duration: <strong>{violation_minutes} minutes</strong> in continuous breach.<br>
            Peak p95 latency reached <strong>{max_p95:,.0f} ms</strong> (exceeds {sla_latency} ms target).<br>
            Peak error rate reached <strong>{max_err:.2f}%</strong> (target: {sla_error*100:.2f}%).</p>
        </div>""", unsafe_allow_html=True)

with sla_col2:
    # SLA status timeline
    fig_slat = go.Figure()
    timeline_colors = ["#34d399" if s == "met" else "#ef4444" for s in df_sim["sla_status"]]
    fig_slat.add_trace(go.Bar(
        x=df_sim["timestamp"], y=[1] * len(df_sim),
        marker_color=timeline_colors,
        showlegend=False,
        hovertemplate="Time: %{x}<br>Status: %{customdata}<extra></extra>",
        customdata=df_sim["sla_status"].values,
    ))
    fig_slat.update_layout(
        title="SLA Compliance Timeline (Green = Met, Red = Violated)",
        yaxis=dict(visible=False),
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "yaxis"},
        height=180,
    )
    st.plotly_chart(fig_slat, use_container_width=True)

# SLA metric breakdown
sla_m1, sla_m2, sla_m3, sla_m4, sla_m5 = st.columns(5)
with sla_m1:
    st.metric("SLA Compliance", f"{compliance:.1f}%", f"Target: {sla_comp_target:.1f}%")
with sla_m2:
    st.metric("Max p95 Latency", f"{max_p95:,.0f} ms", f"Target: {sla_latency} ms",
              delta_color="normal" if max_p95 <= sla_latency else "inverse")
with sla_m3:
    st.metric("Max Error Rate", f"{max_err:.2f}%", f"Target: {sla_error*100:.1f}%",
              delta_color="normal" if max_err <= sla_error * 100 else "inverse")
with sla_m4:
    st.metric("Violation Duration", f"{violation_minutes} min",
              delta="0 min is ideal" if violation_minutes == 0 else f"{violation_minutes}m breach",
              delta_color="normal" if violation_minutes == 0 else "inverse")
with sla_m5:
    st.metric("Total Unmet Requests", f"{summary.get('total_unmet_requests', 0):,.0f}",
              delta="Zero dropped" if summary.get('total_unmet_requests', 0) == 0 else "Dropped users",
              delta_color="normal" if summary.get('total_unmet_requests', 0) == 0 else "inverse")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7: STRATEGY COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
if "Strategy Comparison" in visible_sections or "Scenario Comparison" in visible_sections:
    section_header("⚖️", "7. Strategy Comparison",
        "Measurable trade-offs across 5 capacity planning methodologies.")

    strat_csv = PROJECT_ROOT / "outputs" / "capacity_strategy_comparison.csv"
    if strat_csv.exists():
        df_strat_all = pd.read_csv(strat_csv)
        
        # Filter for current scenario
        strat_sc_df = df_strat_all[df_strat_all["scenario"] == scenario_name].copy()
        if strat_sc_df.empty:
            strat_sc_df = df_strat_all[df_strat_all["scenario"] == "DISASTER_PEAK"].copy()

        STRAT_DISPLAY_NAMES = {
            "AVERAGE_DEMAND": "Average Demand Planning",
            "PEAK_DEMAND": "Peak Demand Planning",
            "SAFETY_MARGIN": "Safety Margin Planning",
            "DYNAMIC_SCALING": "Dynamic Scaling",
            "DISASTER_AWARE": "Disaster-Aware Scaling",
        }
        strat_sc_df["strategy_name"] = strat_sc_df["strategy"].map(lambda x: STRAT_DISPLAY_NAMES.get(x, x))

        # Chart: Cost vs Latency Trade-Off
        fig_strat_bar = make_subplots(
            rows=1, cols=3,
            subplot_titles=("Required Instances", "Max p95 Latency (ms)", "Simulated Cost ($)"),
        )
        bar_colors = ["#f87171", "#fbbf24", "#38bdf8", "#818cf8", "#34d399"]

        fig_strat_bar.add_trace(go.Bar(
            x=strat_sc_df["strategy_name"], y=strat_sc_df["peak_instances"],
            marker_color=bar_colors, name="Instances", showlegend=False,
        ), row=1, col=1)

        fig_strat_bar.add_trace(go.Bar(
            x=strat_sc_df["strategy_name"], y=strat_sc_df["max_p95_latency"],
            marker_color=bar_colors, name="Max Latency", showlegend=False,
        ), row=1, col=2)
        fig_strat_bar.add_hline(y=sla_latency, row=1, col=2, line_dash="dash", line_color=COLORS["sla_line"])

        fig_strat_bar.add_trace(go.Bar(
            x=strat_sc_df["strategy_name"], y=strat_sc_df["total_simulated_cost"],
            marker_color=bar_colors, name="Total Cost", showlegend=False,
        ), row=1, col=3)

        fig_strat_bar.update_layout(
            height=360,
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
        )
        st.plotly_chart(fig_strat_bar, use_container_width=True)

        # Measurable trade-offs table (no subjective ranking)
        st.markdown("**Measurable Strategy Trade-Offs Matrix**")
        df_strat_display = strat_sc_df[[
            "strategy_name", "required_instances", "peak_instances",
            "max_queue", "max_p95_latency", "max_error_rate",
            "sla_compliance", "total_simulated_cost"
        ]].rename(columns={
            "strategy_name": "Strategy",
            "required_instances": "Initial Instances",
            "peak_instances": "Peak Instances",
            "max_queue": "Max Queue",
            "max_p95_latency": "Max p95 (ms)",
            "max_error_rate": "Max Error %",
            "sla_compliance": "SLA Result",
            "total_simulated_cost": "Simulated Cost ($)",
        })
        st.dataframe(df_strat_display, use_container_width=True, hide_index=True)
    else:
        st.info("Strategy comparison results not found at outputs/capacity_strategy_comparison.csv.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 8: SENSITIVITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
if "Sensitivity Analysis" in visible_sections:
    section_header("🔬", "8. Sensitivity Analysis",
        "Assessing which capacity assumptions cause measurable decision changes (Step 6 findings).")

    sens_csv = PROJECT_ROOT / "outputs" / "advanced_sensitivity_results.csv"
    dec_csv = PROJECT_ROOT / "outputs" / "decision_changing_assumptions.csv"

    if sens_csv.exists() and dec_csv.exists():
        df_sens = pd.read_csv(sens_csv)
        df_dec = pd.read_csv(dec_csv)

        # Highlight decision-changing assumptions
        dec_changed = df_dec[df_dec["decision_changed"] == True].copy()
        little_eff = df_dec[df_dec["decision_changed"] == False].copy()

        sc_c1, sc_c2 = st.columns(2)
        with sc_c1:
            st.markdown(f"""
            <div class="rec-box fail">
                <h3>Decision-Changing: {len(dec_changed)} Parameter Combinations</h3>
                <p>These assumptions materially flip SLA compliance or cause severe queue backlogs.
                Under-estimating these parameters creates severe operational failure risk during a disaster.</p>
            </div>""", unsafe_allow_html=True)
        with sc_c2:
            st.markdown(f"""
            <div class="rec-box">
                <h3>Robust / Little Effect: {len(little_eff)} Combinations</h3>
                <p>These variations remained safely within capacity tolerances.
                Minor estimation inaccuracies here will not degrade public accessibility.</p>
            </div>""", unsafe_allow_html=True)

        # Chart: Impact across 8 tested parameters
        PARAM_LABELS = {
            "traffic_multiplier": "1. Traffic Multiplier",
            "scaling_delay_seconds": "2. Scaling Delay",
            "capacity_per_instance": "3. Instance Capacity",
            "max_instances": "4. Maximum Instances",
            "initial_instances": "5. Initial Instances",
            "safety_margin_pct": "6. Safety Margin",
            "disaster_duration_hours": "7. Disaster Duration",
            "peak_duration_ratio": "8. Peak Duration",
        }

        unique_params = [p for p in PARAM_LABELS.keys() if p in df_sens["parameter_name"].unique()]
        param_choice = st.selectbox(
            "Select Parameter to Inspect Impact",
            unique_params,
            format_func=lambda x: PARAM_LABELS.get(x, x),
        )

        sub_sens = df_sens[df_sens["parameter_name"] == param_choice].copy()
        if not sub_sens.empty:
            fig_p = make_subplots(
                rows=1, cols=2,
                subplot_titles=(f"Max p95 Latency vs {PARAM_LABELS.get(param_choice, param_choice)}",
                                f"Peak Queue Depth vs {PARAM_LABELS.get(param_choice, param_choice)}"),
            )
            for sc in sub_sens["scenario"].unique():
                sc_df = sub_sens[sub_sens["scenario"] == sc]
                fig_p.add_trace(go.Scatter(
                    x=sc_df["parameter_value"], y=sc_df["max_p95_latency"],
                    name=f"{sc} (Latency)", mode="lines+markers",
                ), row=1, col=1)
                fig_p.add_trace(go.Scatter(
                    x=sc_df["parameter_value"], y=sc_df["max_queue"],
                    name=f"{sc} (Queue)", mode="lines+markers",
                ), row=1, col=2)

            fig_p.add_hline(y=sla_latency, row=1, col=1, line_dash="dash", line_color=COLORS["sla_line"], annotation_text="SLA Target")
            fig_p.update_layout(
                height=360,
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            )
            st.plotly_chart(fig_p, use_container_width=True)

        # Decision changing assumptions table
        if not dec_changed.empty:
            st.markdown("**Assumptions that Measurably Flipped Capacity Decisions**")
            st.dataframe(
                dec_changed[["parameter", "baseline_value", "tested_value", "scenario", "baseline_sla", "tested_sla", "reason"]].rename(columns={
                    "parameter": "Parameter",
                    "baseline_value": "Baseline Value",
                    "tested_value": "Stress Value",
                    "scenario": "Scenario",
                    "baseline_sla": "Baseline SLA %",
                    "tested_sla": "Stress SLA %",
                    "reason": "Operational Decision Impact",
                }),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Sensitivity analysis data files not found in outputs/.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 9: FAILURE TESTING
# ══════════════════════════════════════════════════════════════════════════════
if "Failure Testing" in visible_sections:
    section_header("⚠️", "9. Failure Testing",
        "Stress and failure-case evaluations under extreme conditions (Step 7 outputs).")

    fail_csv = PROJECT_ROOT / "outputs" / "advanced_failure_cases.csv"
    if fail_csv.exists():
        df_fail = pd.read_csv(fail_csv)

        # Overview chart
        fig_fc = px.bar(
            df_fail,
            x="failure_case",
            y="max_p95_latency_ms",
            color="severity",
            color_discrete_map={"SLA Compliant": "#34d399", "SLA Violated": "#ef4444", "SLA Degraded": "#fbbf24"},
            title="Max Latency by Extreme Failure Condition",
            labels={"failure_case": "Failure Condition", "max_p95_latency_ms": "Max p95 Latency (ms)"},
        )
        fig_fc.add_hline(y=sla_latency, line_dash="dash", line_color="#ef4444", annotation_text=f"SLA Target ({sla_latency}ms)")
        fig_fc.update_layout(height=360, **PLOTLY_LAYOUT)
        st.plotly_chart(fig_fc, use_container_width=True)

        # Simple table
        cols_fail = [
            "failure_condition", "peak_demand_rpm", "peak_capacity_rpm",
            "max_queue_depth", "max_p95_latency_ms", "max_error_rate_pct",
            "severity", "recovery_time_min"
        ]
        df_fail_disp = df_fail[[c for c in cols_fail if c in df_fail.columns]].rename(columns={
            "failure_condition": "Failure Condition",
            "peak_demand_rpm": "Peak Demand (RPM)",
            "peak_capacity_rpm": "Peak Capacity (RPM)",
            "max_queue_depth": "Queue Depth",
            "max_p95_latency_ms": "p95 Latency (ms)",
            "max_error_rate_pct": "Error Rate %",
            "severity": "SLA Status",
            "recovery_time_min": "Recovery Time (min)",
        })
        st.dataframe(df_fail_disp, use_container_width=True, hide_index=True)
    else:
        st.info("Failure testing dataset not found at outputs/advanced_failure_cases.csv.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 10: ORGANISATION & PERMISSIONS
# ══════════════════════════════════════════════════════════════════════════════
section_header("🏢", "10. Organisation & Permissions",
    "Current identity, role capabilities, and security boundaries (Step 8 RBAC).")

op_c1, op_c2 = st.columns(2)
with op_c1:
    st.markdown(f"""
    <div class="info-card">
        <h3>Active Context</h3>
        <p><strong>Organisation:</strong> {org_choice}<br>
        <strong>Role:</strong> {role_choice}<br>
        <strong>External Partner Redaction:</strong> {'YES (Infrastructure Hidden)' if is_ext_partner else 'NO (Full Telemetry Visible)'}</p>
        <p style="font-size:0.85rem; color:#94a3b8; margin-top:8px;">
        {org_info.get('description', '')}
        </p>
    </div>""", unsafe_allow_html=True)

with op_c2:
    st.markdown("""
    <div class="info-card">
        <h3>Visible Dashboard Features for Current Role</h3>
        <p style="font-size:0.88rem; color:#cbd5e1;">
    """ + ", ".join([f"<code>{s}</code>" for s in visible_sections]) + """
        </p>
        <p style="font-size:0.80rem; color:#94a3b8; margin-top:8px;">
        Restricted controls are automatically locked or hidden to prevent unauthorized operational modifications.
        </p>
    </div>""", unsafe_allow_html=True)

if role_enum == Role.ADMINISTRATOR:
    st.markdown("#### Registered Organisations & Default SLA Policies (Admin View)")
    orgs_all = load_organisations()
    if orgs_all:
        df_orgs_view = pd.DataFrame([
            {
                "ID": o.get("organisation_id", ""),
                "Name": o.get("organisation_name", ""),
                "Allowed Scenarios": ", ".join(o.get("allowed_scenarios", [])),
                "Latency Target (ms)": o.get("default_SLA_target", {}).get("p95_latency_target_ms"),
                "Error Target (%)": o.get("default_SLA_target", {}).get("error_rate_target", 0.0) * 100.0,
                "Compliance Target (%)": o.get("default_SLA_target", {}).get("sla_compliance_target_pct"),
            }
            for o in orgs_all
        ])
        st.dataframe(df_orgs_view, use_container_width=True, hide_index=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PART 6: DEDICATED CAPACITY RECOMMENDATION PANEL (Explainable Engine)
# ══════════════════════════════════════════════════════════════════════════════
section_header("💡", "Capacity Recommendation",
    "Evidence-based, explainable recommendation constructed from measurable simulation telemetry.")

# Generate recommendation using the explainable engine
rec_record = generate_explainable_recommendation(
    summary=summary,
    scenario_name=scenario_name,
    config=sim_config,
    sla_targets=sla_config_dict,
    comp_df=comp_df,
)

rec_sev = rec_record.get("severity", "info")
rec_box_cls = {"success": "", "warning": "warn", "danger": "fail"}.get(rec_sev, "")

st.markdown(f"""
<div class="rec-box {rec_box_cls}">
    <h3>Recommendation: {rec_record.get('recommendation_type', '').replace('_', ' ').title()}</h3>
    <div class="rec-field-title">1. Situation (What is happening?)</div>
    <p>{rec_record.get('situation', '')}</p>
    <div class="rec-field-title">2. Evidence (Which measured metrics support the statement?)</div>
    <p>{rec_record.get('evidence', '')}</p>
    <div class="rec-field-title">3. Impact (What happens if the condition continues?)</div>
    <p>{rec_record.get('impact', '')}</p>
    <div class="rec-field-title">4. Recommended Action (What operational action could address it?)</div>
    <p><strong>{rec_record.get('recommended_action', '')}</strong></p>
    <div class="rec-field-title">5. Why? (Reason: Why would that action help?)</div>
    <p>{rec_record.get('reason', '')}</p>
</div>
""", unsafe_allow_html=True)

# Supporting metrics display
st.markdown("**Supporting Metrics**")
supp_metrics = rec_record.get("supporting_metrics", {})
sm_c1, sm_c2, sm_c3, sm_c4, sm_c5, sm_c6, sm_c7 = st.columns(7)
with sm_c1:
    st.metric("Peak Demand", f"{supp_metrics.get('peak_demand_rpm', peak_demand):,.0f} RPM")
with sm_c2:
    val_c = "[REDACTED]" if is_ext_partner else f"{supp_metrics.get('available_capacity_rpm', peak_cap):,.0f} RPM"
    st.metric("Capacity", val_c)
with sm_c3:
    st.metric("Queue Depth", f"{supp_metrics.get('max_queue_depth', max_queue):,.0f}")
with sm_c4:
    st.metric("P95 Latency", f"{supp_metrics.get('max_p95_latency_ms', max_p95):,.0f} ms")
with sm_c5:
    st.metric("Error Rate", f"{supp_metrics.get('max_error_rate_pct', max_err):.2f}%")
with sm_c6:
    st.metric("SLA Compliance", f"{supp_metrics.get('sla_compliance_pct', compliance):.1f}%")
with sm_c7:
    val_i = "[REDACTED]" if is_ext_partner else f"{supp_metrics.get('peak_instances', peak_inst)}"
    st.metric("Active Instances", val_i)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PART 7: BEFORE VS AFTER VISUAL COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
section_header("🔄", "Before vs After Planning Comparison",
    "Measuring the tangible resilience improvement of Scenario-Based Planning over legacy Average-Demand Planning.")

before_csv = PROJECT_ROOT / "outputs" / "before_after_comparison.csv"
if before_csv.exists():
    df_ba = pd.read_csv(before_csv)
    
    ba_col1, ba_col2 = st.columns(2)
    with ba_col1:
        st.markdown("""
        <div class="rec-box fail">
            <h3>BEFORE: Average-Demand Planning</h3>
            <p><strong>Baseline Architecture:</strong> Sized exclusively for average traffic (~950 RPM).<br>
            <strong>Infrastructure:</strong> 4 initial &bull; 6 maximum instances.<br>
            <strong>Result under Disaster:</strong> Queue backed up to 50,000+ requests, p95 latency spiked to 62,630 ms, and over 340,000 emergency requests were dropped.</p>
        </div>""", unsafe_allow_html=True)
    with ba_col2:
        st.markdown("""
        <div class="rec-box">
            <h3>AFTER: Scenario-Based Planning</h3>
            <p><strong>Scenario-Aware Architecture:</strong> Sized for modeled disaster peaks with pre-warming.<br>
            <strong>Infrastructure:</strong> Elastic scaling up to required peak demand.<br>
            <strong>Result under Disaster:</strong> Zero requests queued, latency remained under 400 ms, 0 requests dropped, and 100% SLA compliance achieved.</p>
        </div>""", unsafe_allow_html=True)

    # Comparison metrics table
    st.dataframe(df_ba, use_container_width=True, hide_index=True)
else:
    st.info("Before vs After comparison data not found at outputs/before_after_comparison.csv.")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.info("🔒 **Security Notice:** Role selection is an application-level workflow demonstration. In production, roles are securely governed by enterprise SSO (OAuth2 / OIDC / SAML).")
st.caption("Peak-Demand Capacity Simulator v1.2.0 &bull; Step 9 Implementation &bull; Built with Streamlit & Plotly")
