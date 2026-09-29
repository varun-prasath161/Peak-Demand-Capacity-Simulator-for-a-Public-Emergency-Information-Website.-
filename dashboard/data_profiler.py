"""
Data Profiler & Dataset Exploration Dashboard Page
===================================================
Provides interactive visualization and profiling for the synthetic
emergency workload dataset, featuring data cleaning audits, traffic time series,
disaster event breakdowns, and statistical distributions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as gg
import plotly.subplots as sp
from pathlib import Path

from src.data.loader import load_raw_data, load_processed_data
from src.data.cleaner import clean_dataset, process_and_save_dataset
from src.data.profiler import compute_dataset_profile, compute_event_breakdown
from src.data.generate_dataset import generate_dataset, SEED, START_DATE, END_DATE

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "emergency_load_raw.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "emergency_load_processed.csv"


def render_data_profiler_page():
    """Render the Data Ingestion & Profiling Dashboard Page in Streamlit."""
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #334155;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 2rem;">📊 Module 2: Data Ingestion, Profiling & Quality Audit</h1>
        <p style="color: #94a3b8; margin-top: 8px; font-size: 1.05rem;">
            Synthetic workload generation (~10 months, 3,800+ records, 33 features) capturing non-linear disaster spikes,
            queue dynamics, M/M/1-degraded latencies, auto-scaling delays, and automated data cleaning audits.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Ensure dataset exists ───────────────────────────────────────────────
    if not RAW_CSV.exists():
        st.warning("⚠️ Raw dataset not found. Generating dataset using seed=42...")
        with st.spinner("Generating 10-month realistic operational load dataset..."):
            generate_dataset()
        st.success("✅ Dataset generated successfully!")

    if not PROCESSED_CSV.exists():
        st.info("⚙️ Running automated data cleaning pipeline...")
        with st.spinner("Cleaning raw dataset anomalies..."):
            process_and_save_dataset()
        st.success("✅ Dataset cleaned and saved!")

    # ── Load Datasets ───────────────────────────────────────────────────────
    df_raw = load_raw_data()
    df_clean, audit = clean_dataset(df_raw)
    profile = compute_dataset_profile(df_clean)

    # ── Top KPI Metrics Bar ─────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Records", f"{profile['overview']['total_records']:,}", delta="3,800–3,900 target")
    with col2:
        st.metric("Peak Load (RPM)", f"{profile['traffic_statistics']['max_rpm']:,.0f}", delta=f"{profile['traffic_statistics']['burst_ratio']}x Burst Ratio")
    with col3:
        st.metric("Mean Load (RPM)", f"{profile['traffic_statistics']['mean_rpm']:,.0f}")
    with col4:
        st.metric("SLA Breach Rate", f"{profile['performance_and_sla']['sla_breach_rate_pct']}%", delta_color="inverse")
    with col5:
        st.metric("Anomalies Cleaned", f"{audit['missing_values_interpolated'] + audit['negative_values_fixed'] + audit['out_of_bounds_utils_clamped'] + audit['duplicates_removed']:,}")

    st.markdown("---")

    # ── Interactive Controls Bar ────────────────────────────────────────────
    st.sidebar.markdown("### ⚙️ Data Module Actions")
    if st.sidebar.button("🔄 Regenerate Synthetic Data"):
        with st.spinner("Regenerating dataset..."):
            generate_dataset()
            process_and_save_dataset()
            st.rerun()

    # ── Tabs Navigation ─────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Workload & Time-Series",
        "🧹 Quality & Audit Report",
        "📊 Statistical Distributions",
        "🚨 Disaster Event Analysis",
        "📋 Data Table & Export"
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: Workload & Time-Series
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("10-Month Workload & Infrastructure Performance Timeline")
        
        # Event type filter
        selected_events = st.multiselect(
            "Filter Event Types",
            options=["normal", "seasonal", "breaking_news", "disaster", "extreme_disaster"],
            default=["normal", "seasonal", "breaking_news", "disaster", "extreme_disaster"]
        )
        
        df_filtered = df_clean[df_clean["event_type"].isin(selected_events)]

        # Time series chart: Requests per Minute & Capacity
        fig = px.line(
            df_filtered,
            x="timestamp",
            y=["requests_per_minute", "total_capacity_rpm"],
            labels={"value": "Requests / Minute", "timestamp": "Timestamp", "variable": "Metric"},
            title="Traffic Demand vs Available Total System Capacity (RPM)",
            color_discrete_map={"requests_per_minute": "#38bdf8", "total_capacity_rpm": "#ef4444"}
        )
        fig.update_layout(template="plotly_dark", height=420, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # Multi-panel System Response: CPU %, Latency, and Queue Depth
        col_left, col_right = st.columns(2)
        with col_left:
            fig_cpu = px.line(
                df_filtered, x="timestamp", y="cpu_utilisation",
                title="CPU Utilisation (%) over Time",
                color_discrete_sequence=["#f59e0b"]
            )
            fig_cpu.add_hline(y=75, line_dash="dash", line_color="#ef4444", annotation_text="Autoscale Scale-Out Threshold (75%)")
            fig_cpu.update_layout(template="plotly_dark", height=320)
            st.plotly_chart(fig_cpu, use_container_width=True)

        with col_right:
            fig_lat = px.line(
                df_filtered, x="timestamp", y=["average_latency_ms", "p95_latency_ms"],
                title="Response Latency (Mean & p95 ms)",
                color_discrete_map={"average_latency_ms": "#a855f7", "p95_latency_ms": "#ec4899"}
            )
            fig_lat.add_hline(y=500, line_dash="dash", line_color="#ef4444", annotation_text="SLA Target (500ms)")
            fig_lat.update_layout(template="plotly_dark", height=320)
            st.plotly_chart(fig_lat, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: Quality & Audit Report
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("Data Quality & Automated Cleaning Audit Report")
        
        st.markdown("""
        The synthetic data generator intentionally embeds realistic operational telemetry flaws:
        missing records, duplicate timestamps, negative throughput inputs, illegal CPU/memory percentages (>100%),
        and capacity calculation inconsistencies. Below is the full audit of automated repairs performed by `src/data/cleaner.py`.
        """)

        audit_cols = st.columns(4)
        with audit_cols[0]:
            st.info(f"**Missing Values Interpolated:**\n### {audit['missing_values_interpolated']}")
        with audit_cols[1]:
            st.warning(f"**Negative Values Fixed:**\n### {audit['negative_values_fixed']}")
        with audit_cols[2]:
            st.error(f"**Utilisations Clamped (>100%):**\n### {audit['out_of_bounds_utils_clamped']}")
        with audit_cols[3]:
            st.success(f"**Duplicates Removed:**\n### {audit['duplicates_removed']}")

        st.markdown("#### Raw vs Cleaned Dataset Feature Comparison")
        comp_df = pd.DataFrame({
            "Metric": [
                "Total Row Count", "Missing Value Count", "Negative Count (Non-neg fields)",
                "Illegal Utilisation (>100%)", "Capacity Calculation Mismatches"
            ],
            "Raw Dataset": [
                len(df_raw), int(df_raw.isnull().sum().sum()),
                sum((df_raw[col] < 0).sum() for col in ["requests_per_minute", "concurrent_users", "queue_depth"] if col in df_raw.columns),
                sum((df_raw[col] > 100.0).sum() for col in ["cpu_utilisation", "memory_utilisation"] if col in df_raw.columns),
                int((df_raw["total_capacity_rpm"] != df_raw["available_instances"] * df_raw["instance_capacity_rpm"]).sum())
            ],
            "Cleaned Dataset": [
                len(df_clean), int(df_clean.isnull().sum().sum()),
                0, 0, 0
            ]
        })
        st.table(comp_df)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: Statistical Distributions
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("Workload Statistical Distributions & Non-Linear Degradation")
        
        col_hist1, col_hist2 = st.columns(2)
        with col_hist1:
            fig_hist = px.histogram(
                df_clean, x="requests_per_minute", nbins=50,
                title="Traffic Volume Distribution (RPM)",
                color="event_type",
                color_discrete_map={
                    "normal": "#38bdf8", "seasonal": "#2dd4bf",
                    "breaking_news": "#f59e0b", "disaster": "#f97316",
                    "extreme_disaster": "#ef4444"
                }
            )
            fig_hist.update_layout(template="plotly_dark", height=360)
            st.plotly_chart(fig_hist, use_container_width=True)

        with col_hist2:
            fig_scat = px.scatter(
                df_clean, x="normalised_load", y="average_latency_ms",
                color="event_type", size="queue_depth",
                title="Non-Linear Latency Degradation vs Normalised Load",
                labels={"normalised_load": "Normalised System Load (Demand / Capacity)", "average_latency_ms": "Average Latency (ms)"},
                color_discrete_map={
                    "normal": "#38bdf8", "seasonal": "#2dd4bf",
                    "breaking_news": "#f59e0b", "disaster": "#f97316",
                    "extreme_disaster": "#ef4444"
                }
            )
            fig_scat.add_vline(x=1.0, line_dash="dash", line_color="#ef4444", annotation_text="100% Saturation")
            fig_scat.update_layout(template="plotly_dark", height=360)
            st.plotly_chart(fig_scat, use_container_width=True)

        # Percentiles summary table
        st.markdown("#### Traffic Percentiles & Summary Statistics")
        stats_df = pd.DataFrame([profile["traffic_statistics"]])
        st.dataframe(stats_df, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4: Disaster Event Analysis
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("Operational Breakdown by Event Class")
        
        event_breakdown = compute_event_breakdown(df_clean)
        st.dataframe(event_breakdown, use_container_width=True)

        col_bar1, col_bar2 = st.columns(2)
        with col_bar1:
            fig_bar_rpm = px.bar(
                event_breakdown, x="event_type", y="max_rpm",
                title="Peak Requests / Min by Event Class",
                color="event_type",
                color_discrete_map={
                    "normal": "#38bdf8", "seasonal": "#2dd4bf",
                    "breaking_news": "#f59e0b", "disaster": "#f97316",
                    "extreme_disaster": "#ef4444"
                }
            )
            fig_bar_rpm.update_layout(template="plotly_dark", height=340)
            st.plotly_chart(fig_bar_rpm, use_container_width=True)

        with col_bar2:
            fig_bar_sla = px.bar(
                event_breakdown, x="event_type", y="sla_breach_rate_pct",
                title="SLA Breach Rate (%) by Event Class",
                color="event_type",
                color_discrete_map={
                    "normal": "#38bdf8", "seasonal": "#2dd4bf",
                    "breaking_news": "#f59e0b", "disaster": "#f97316",
                    "extreme_disaster": "#ef4444"
                }
            )
            fig_bar_sla.update_layout(template="plotly_dark", height=340)
            st.plotly_chart(fig_bar_sla, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 5: Data Table & Export
    # ════════════════════════════════════════════════════════════════════════
    with tab5:
        st.subheader("Explore Raw and Cleaned Data")
        
        data_choice = st.radio("Select View", ["Cleaned & Processed Data", "Raw Data (With Injected Anomalies)"], horizontal=True)
        display_df = df_clean if data_choice == "Cleaned & Processed Data" else df_raw
        
        search_term = st.text_input("Search dataset (e.g. disaster, extreme_disaster, central)", "")
        if search_term:
            display_df = display_df[display_df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)]

        st.dataframe(display_df, use_container_width=True)
        
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_data,
            file_name="emergency_load_export.csv",
            mime="text/csv"
        )
