# Non-Technical User Guide: How to Run Simulations & Interpret Guidance

## Overview

Welcome to the **Peak-Demand Capacity Simulator**. This guide provides step-by-step instructions for non-technical leadership, emergency operations directors, and agency analysts to run disaster scenarios and understand capacity recommendations.

---

## Quick Start: Launching the Dashboard

1. Open your terminal or command prompt.
2. Navigate to the project folder and launch Streamlit:
   ```bash
   streamlit run dashboard/app.py
   ```
3. Open your web browser to **`http://localhost:8501`**.

---

## Step-by-Step Scenario Execution Guide

### Step 1: Select Your Organisation & Role (Sidebar)
- In the left sidebar under **Organisation & Access**, select your organisation (e.g. *Emergency Operations Centre*) and role (e.g. *Operator* or *Analyst*).
- Expanding the **🔑 Role Rights** box shows your permitted actions.

### Step 2: Choose a Workload Scenario (Sidebar)
- Under **Workload Scenario**, select a disaster surge profile:
  - **Normal Day**: Standard daily web traffic.
  - **Seasonal Peak**: Elevated holiday/weekend traffic (1.8x).
  - **Breaking News**: Rapid 2.5x surge for breaking events.
  - **Disaster Peak**: Major flood or hurricane surge (4.0x).
  - **Extreme Disaster**: Catastrophic disaster surge (6.5x).

### Step 3: Configure Infrastructure (Sidebar)
- Adjust the sliders for:
  - **Initial Instances**: Starting number of operational servers.
  - **Maximum Instances**: Cloud ceiling for auto-scaling.
  - **Scaling Delay**: Time in seconds for new servers to launch.

### Step 4: Run Simulation & Review Charts (Main Screen)
- Click the **🚀 Run Simulation** button.
- Examine Section 4 time-series graphs:
  - **Blue line**: Web traffic demand.
  - **Green line**: Server capacity available.
  - **Red line**: Queue depth (waiting users).
  - **Yellow line**: Response time (latency in ms).

---

## Understanding Executive Recommendations

Section 8 of the dashboard provides plain-language capacity recommendations:

- **🟢 Green Box (All Clear)**: Infrastructure is fully adequate to handle the selected scenario without SLA violations.
- **🟡 Yellow Box (Caution)**: Current scenario passes, but higher disaster tiers will overload the fleet. Recommendation will specify how many additional servers to add.
- **🔴 Red Box (Action Required)**: Current configuration fails under the selected scenario. The system will state the exact capacity shortfall in requests per minute and recommend server ceiling adjustments.

---

## Practical Example: Preparing for a Disaster Warning

When an emergency warning is issued (e.g., Category 4 Hurricane expected in 24 hours):
1. Select **Disaster Peak** scenario.
2. If the recommendation box shows a red or yellow alert, increase the **Initial Instances** slider (pre-warming servers) until the status turns **Green**.
3. Note the recommended server count for your infrastructure operations team.
