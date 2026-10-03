from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="TITAN Master Reconciliation Dashboard",
    page_icon="⚡",
    layout="wide",
)

# Static Engine Base Weights (\alpha_i)
ENGINE_BASE_WEIGHTS = {
    "Engine 1 (Directional Core)": 0.15,
    "Engine 2 (Yield Acceleration)": 0.15,
    "Engine 3 (Macro Vector)": 0.15,
    "Engine 4 (Range Expansion)": 0.10,
    "Engine 5 (Order Flow Ledger)": 0.10,
    "Engine 6 (Volatility DNA)": 0.10,
    "Engine 7 (Liquidity Pools)": 0.10,
    "Engine 8 (Cross-Asset Correl)": 0.08,
    "Engine 9 (Option Magnet Clamps)": 0.07,
}

# --- Core Execution Functions ---


def compute_structural_drift(S_day, S_week):
    delta_S = float(np.linalg.norm(np.array(S_day) - np.array(S_week)))

    if delta_S < 0.95:
        status, trust, mult = "PASSIVE DRIFT", "SAFE", 1.00
    elif 0.95 <= delta_S < 1.10:
        status, trust, mult = "HIGH ALERT", "CAUTION", 0.50
    elif 1.10 <= delta_S < 1.25:
        status, trust, mult = (
            "HARD TRIGGER - INTRAWEEK RECALIBRATION",
            "CAUTION",
            0.25,
        )
    else:
        status, trust, mult = "HARD FAIL - SYSTEM LOCK", "HARD FAIL", 0.00

    return delta_S, status, trust, mult


def apply_confidence_gating(raw_confidences):
    gated = {}
    for engine, c_i in raw_confidences.items():
        if c_i >= 0.80:
            gated[engine] = c_i
        elif 0.50 <= c_i < 0.80:
            gated[engine] = 0.50 * c_i
        else:
            gated[engine] = 0.0
    return gated


def calculate_master_weights(gated_confidences):
    weighted_scores = {}
    total_weight = 0.0
    for engine, phi_c in gated_confidences.items():
        alpha = ENGINE_BASE_WEIGHTS[engine]
        weighted_scores[engine] = alpha * phi_c
        total_weight += weighted_scores[engine]

    if total_weight == 0:
        return {engine: 0.0 for engine in ENGINE_BASE_WEIGHTS}

    return {
        engine: score / total_weight for engine, score in weighted_scores.items()
    }


# --- UI Layout ---

st.title("⚡ TITAN 9-Engine Master Reconciliation Suite")
st.markdown("---")

# Sidebar - Live Telemetry Input Controls
st.sidebar.header("🕹️ Session Telemetry Inputs")
symbol = st.sidebar.selectbox("Active Symbol", ["EURUSD", "GBPUSD"])

st.sidebar.subheader("Sub-Engine Confidence Scores ($c_i$)")
conf_e1 = st.sidebar.slider(
    "Engine 1 (Directional Core)", 0.0, 1.0, 0.88, 0.01
)
conf_e2 = st.sidebar.slider(
    "Engine 2 (Yield Acceleration)", 0.0, 1.0, 0.86, 0.01
)
conf_e3 = st.sidebar.slider("Engine 3 (Macro Vector)", 0.0, 1.0, 0.90, 0.01)
conf_e4 = st.sidebar.slider("Engine 4 (Range Expansion)", 0.0, 1.0, 0.75, 0.01)
conf_e5 = st.sidebar.slider("Engine 5 (Order Flow Ledger)", 0.0, 1.0, 0.82, 0.01)
conf_e6 = st.sidebar.slider("Engine 6 (Volatility DNA)", 0.0, 1.0, 0.60, 0.01)
conf_e7 = st.sidebar.slider("Engine 7 (Liquidity Pools)", 0.0, 1.0, 0.45, 0.01)
conf_e8 = st.sidebar.slider(
    "Engine 8 (Cross-Asset Correl)", 0.0, 1.0, 0.81, 0.01
)
conf_e9 = st.sidebar.slider(
    "Engine 9 (Option Magnet Clamps)", 0.0, 1.0, 0.92, 0.01
)

raw_confidences = {
    "Engine 1 (Directional Core)": conf_e1,
    "Engine 2 (Yield Acceleration)": conf_e2,
    "Engine 3 (Macro Vector)": conf_e3,
    "Engine 4 (Range Expansion)": conf_e4,
    "Engine 5 (Order Flow Ledger)": conf_e5,
    "Engine 6 (Volatility DNA)": conf_e6,
    "Engine 7 (Liquidity Pools)": conf_e7,
    "Engine 8 (Cross-Asset Correl)": conf_e8,
    "Engine 9 (Option Magnet Clamps)": conf_e9,
}

# Run Calculations
S_week = [1.0820, 1.0880, 1.0790, 1.0835, 0.02]
S_day = [1.0850, 1.0890, 1.0810, 1.0850, 0.04]

delta_S, status, trust, size_mult = compute_structural_drift(S_day, S_week)
gated_conf = apply_confidence_gating(raw_confidences)
weights = calculate_master_weights(gated_conf)

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Structural Drift ($\Delta S$)", f"{delta_S:.4f}")
col2.metric("System Status", status)
col3.metric("Trust Level", trust)
col4.metric("Position Sizing Multiplier", f"{int(size_mult * 100)}%")

st.markdown("---")

# Main Section 1: Engine Weights Chart
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 Normalized Engine Weights ($\phi(c_i)$-Gated)")
    df_weights = pd.DataFrame(
        list(weights.items()), columns=["Engine", "Weight"]
    )
    st.bar_chart(df_weights.set_index("Engine"))

with col_right:
    st.subheader("⚙️ Directional Override Audit")
    if conf_e1 >= 0.85 and conf_e2 >= 0.85 and conf_e3 >= 0.85:
        st.success("🔒 HARD-LOCKED DIRECTIONAL OVERRIDE ACTIVE")
        st.markdown("**Master Bias:** BULLISH")
    else:
        st.info("🔄 DYNAMIC MATRIX FUSION ACTIVE")
        st.markdown("**Master Bias:** BALANCED / NEUTRAL")

    st.markdown("---")
    st.subheader("🎯 Option Magnet (Engine 9)")
    if conf_e9 >= 0.80:
        st.warning("🧲 Active Magnet Lock (SCD ≥ 2.50)")
        st.markdown("**Clamped Strike Node:** 1.0850")
    else:
        st.write("No magnet lock active.")

st.markdown("---")

# Main Section 2: Next-Day GPS Coordinates Table
st.subheader("📍 Next-Day Target Price GPS Coordinates")

gps_data = {
    "Boundary Target": [
        "First Extreme (E1)",
        "Expected Midpoint (M)",
        "Second Extreme (E2)",
        "Expected Close (C)",
    ],
    "Target Price": ["1.0815", "1.0852", "1.0895", "1.0880"],
    "Timing Window / Session Phase": [
        "08:00–09:30 CEST (Phase AL)",
        "Session Median Anchor",
        "15:30–17:00 CEST (Phase NY)",
        "21:30–22:00 CEST (Session Close)",
    ],
    "Execution Protocol": [
        "Session Low / Long Entry Validation Node",
        "Pivot Confirmation Threshold",
        "Session High / Primary Take-Profit Target",
        "Terminal Range Settlement",
    ],
}

st.table(pd.DataFrame(gps_data))
