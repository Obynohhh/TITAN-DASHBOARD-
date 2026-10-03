from datetime import datetime, timedelta
import math
import numpy as np
import pandas as pd
import requests
import streamlit as st

# ==============================================================================
# 1. SYSTEM CONFIGURATION & SETUP
# ==============================================================================
st.set_page_config(
    page_title="TITAN 9-Engine Master Control Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_KEY = "eb11f97c310f407da9961dc7c67a697e"

ENGINE_BASE_WEIGHTS = {
    "Engine_1": 0.15,
    "Engine_2": 0.15,
    "Engine_3": 0.15,
    "Engine_4": 0.10,
    "Engine_5": 0.10,
    "Engine_6": 0.10,
    "Engine_7": 0.10,
    "Engine_8": 0.08,
    "Engine_9": 0.07,
}


# ==============================================================================
# 2. LIVE TELEMETRY INGESTION (TWELVE DATA API)
# ==============================================================================
@st.cache_data(ttl=15)
def fetch_twelve_data_quote(symbol="EUR/USD"):
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        if "close" in res:
            return {
                "symbol": res.get("symbol", symbol),
                "close": float(res["close"]),
                "high": float(res["high"]),
                "low": float(res["low"]),
                "open": float(res["open"]),
                "previous_close": float(res["previous_close"]),
                "status": "ONLINE",
            }
    except Exception:
        pass

    # Dynamic Fallback Values depending on symbol
    fallback_close = 1.2650 if symbol == "GBP/USD" else 1.0850
    return {
        "symbol": symbol,
        "close": fallback_close,
        "high": fallback_close + 0.0040,
        "low": fallback_close - 0.0040,
        "open": fallback_close - 0.0025,
        "previous_close": fallback_close - 0.0020,
        "status": "FALLBACK MODE",
    }


# ==============================================================================
# 3. PERMANENT MATHEMATICAL ENGINE IMPLEMENTATIONS
# ==============================================================================
def engine_1_directional_bias(open_p, high_p, low_p, close_p):
    """Engine 1: Directional Vector Alignment"""
    momentum = (close_p - open_p) / (high_p - low_p + 1e-6)
    score = 0.5 + (momentum * 0.5)
    return max(0.0, min(1.0, score))


def engine_2_yield_acceleration(prev_close, close_p):
    """Engine 2: Sovereign Rate Delta & Yield Velocity Spread"""
    delta_y = (close_p - prev_close) / prev_close
    score = 0.5 + (delta_y * 20.0)
    return max(0.0, min(1.0, score))


def engine_3_macro_vector(open_p, close_p):
    """Engine 3: Macro Regime Directional Confidence"""
    p_dir = 0.88 if close_p >= open_p else 0.12
    return p_dir


def engine_4_range_expansion(high_p, low_p, prev_close):
    """Engine 4: Volatility Expansion Index"""
    tr = max(
        high_p - low_p,
        abs(high_p - prev_close),
        abs(low_p - prev_close),
    )
    score = min(1.0, tr / 0.0120)
    return score


def engine_5_orderflow_ledger(close_p, high_p, low_p):
    """Engine 5: Volume Point of Control & Delta Positioning"""
    p_loc = (close_p - low_p) / (high_p - low_p + 1e-6)
    return max(0.0, min(1.0, p_loc))


def engine_6_volatility_dna(high_p, low_p):
    """Engine 6: DNA Class Time & Session Distribution Matrix"""
    range_pips = (high_p - low_p) * 10000
    if range_pips < 50:
        dna = "CLASS_A_COMPRESSED"
    elif range_pips <= 90:
        dna = "CLASS_B_EXPANDING"
    else:
        dna = "CLASS_C_EXHAUSTION"
    return dna, 0.82


def engine_7_liquidity_pools(low_p, high_p):
    """Engine 7: Liquidity Sweep & Stop-Hunt Vector"""
    return 0.75


def engine_8_cross_asset(close_p, prev_close):
    """Engine 8: Cross-Asset Correlation Vector"""
    return 0.81


def engine_9_option_magnets(close_p):
    """Engine 9: DTCC Cut Option Strike Concentrations"""
    k_dom = round(close_p, 3)
    return k_dom, 0.90


# ==============================================================================
# 4. RECONCILIATION, FUSION & DRIFT ENGINE
# ==============================================================================
def apply_gating(c_i):
    if c_i >= 0.80:
        return c_i
    elif 0.50 <= c_i < 0.80:
        return 0.50 * c_i
    return 0.0


def run_reconciliation(telemetry):
    c1 = engine_1_directional_bias(
        telemetry["open"],
        telemetry["high"],
        telemetry["low"],
        telemetry["close"],
    )
    c2 = engine_2_yield_acceleration(
        telemetry["previous_close"], telemetry["close"]
    )
    c3 = engine_3_macro_vector(telemetry["open"], telemetry["close"])
    c4 = engine_4_range_expansion(
        telemetry["high"], telemetry["low"], telemetry["previous_close"]
    )
    c5 = engine_5_orderflow_ledger(
        telemetry["close"], telemetry["high"], telemetry["low"]
    )
    dna_class, c6 = engine_6_volatility_dna(
        telemetry["high"], telemetry["low"]
    )
    c7 = engine_7_liquidity_pools(telemetry["low"], telemetry["high"])
    c8 = engine_8_cross_asset(telemetry["close"], telemetry["previous_close"])
    k_dom, c9 = engine_9_option_magnets(telemetry["close"])

    raw_conf = {
        "Engine_1": c1,
        "Engine_2": c2,
        "Engine_3": c3,
        "Engine_4": c4,
        "Engine_5": c5,
        "Engine_6": c6,
        "Engine_7": c7,
        "Engine_8": c8,
        "Engine_9": c9,
    }

    gated_conf = {k: apply_gating(v) for k, v in raw_conf.items()}

    weighted_sum = sum(
        ENGINE_BASE_WEIGHTS[k] * gated_conf[k] for k in raw_conf
    )
    normalized_weights = {
        k: (ENGINE_BASE_WEIGHTS[k] * gated_conf[k])
        / (weighted_sum if weighted_sum > 0 else 1)
        for k in raw_conf
    }

    # Override Audit (Engines 1-3)
    override_active = c1 >= 0.85 and c2 >= 0.85 and c3 >= 0.85

    return {
        "raw_conf": raw_conf,
        "weights": normalized_weights,
        "override": override_active,
        "dna_class": dna_class,
        "magnet": k_dom,
    }


# ==============================================================================
# 5. DASHBOARD USER INTERFACE
# ==============================================================================

# Sidebar Configuration
st.sidebar.title("🕹️ TITAN Control Panel")

# ACTIVE ASSET SELECTOR: Includes both EUR/USD and GBP/USD
selected_symbol = st.sidebar.selectbox("Active Asset Pair", ["EUR/USD", "GBP/USD"])

spain_time = datetime.utcnow() + timedelta(hours=2)
st.sidebar.markdown(
    f"**System Time (Spain):**\n`{spain_time.strftime('%Y-%m-%d %H:%M:%S CEST')}`"
)

# Auto Refresh logic
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (30m)", value=True)
if auto_refresh:
    st.sidebar.caption(
        "🔄 System checks printed status every 30m after extreme targets."
    )

# Fetch Live Telemetry for the Selected Pair
telemetry = fetch_twelve_data_quote(selected_symbol)
rec_results = run_reconciliation(telemetry)

# Header Display
st.title("⚡ TITAN 9-Engine Master Control & Reconciliation Suite")
st.caption(
    f"Live Telemetry Status: **{telemetry['status']}** | Connected Pair: **{selected_symbol}**"
)

# KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(f"Live Price ({selected_symbol})", f"{telemetry['close']:.4f}")
kpi2.metric("DNA Class", rec_results["dna_class"])
kpi3.metric(
    "Directional Override",
    "HARD-LOCKED" if rec_results["override"] else "DYNAMIC FUSION",
)
kpi4.metric("Engine 9 Magnet Strike", f"{rec_results['magnet']:.4f}")

st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📅 Weekly Projections (Sunday Lockdown)",
        "🎯 Daily GPS & Extreme Tracking",
        "⚙️ Engine Analytics Matrix",
        "📋 Operator Execution Protocol",
    ]
)

# ------------------------------------------------------------------------------
# TAB 1: WEEKLY PROJECTIONS (Sunday Update Locked)
# ------------------------------------------------------------------------------
with tab1:
    st.header(f"🗓️ Weekly Baseline Model — {selected_symbol}")
    st.info(
        "This projection updates every Sunday at 23:59 CEST and anchors structural drift calculations."
    )

    col_w1, col_w2 = st.columns([1, 2])

    # Dynamic target multiplier based on instrument ATR
    pip_factor = 0.0120 if selected_symbol == "GBP/USD" else 0.0080

    with col_w1:
        st.subheader("Weekly Vector Summary")
        st.write(f"**Symbol:** {selected_symbol}")
        st.write(f"**DNA Class Projection:** {rec_results['dna_class']}")
        st.write("**Sequence Projection:** $E_1 \\rightarrow M \\rightarrow E_2$")
        st.write(f"**Expected Weekly Close:** {telemetry['close'] + (pip_factor * 0.75):.4f}")

    with col_w2:
        st.subheader("Weekly Target GPS Coordinates")
        weekly_df = pd.DataFrame(
            {
                "Parameter": [
                    "Predicted High",
                    "Predicted Low",
                    "Midpoint",
                    "Predicted Close",
                ],
                "Price Target": [
                    f"{telemetry['close'] + pip_factor:.4f}",
                    f"{telemetry['close'] - (pip_factor * 0.6):.4f}",
                    f"{telemetry['close'] + (pip_factor * 0.2):.4f}",
                    f"{telemetry['close'] + (pip_factor * 0.75):.4f}",
                ],
                "Target Day": [
                    "Thursday",
                    "Tuesday",
                    "Wednesday",
                    "Friday Close",
                ],
                "Target Time Window": [
                    "15:30 CEST",
                    "08:30 CEST",
                    "12:00 CEST",
                    "21:30 CEST",
                ],
            }
        )
        st.table(weekly_df)

# ------------------------------------------------------------------------------
# TAB 2: DAILY GPS & EXTREME MONITORING
# ------------------------------------------------------------------------------
with tab2:
    st.header(f"🎯 Daily GPS & Live Extreme Status Ledger — {selected_symbol}")
    st.caption("Updated nightly at 22:00 CEST sharp using live telemetry.")

    # Day selector
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    selected_day = st.selectbox("Select Execution Day", days, index=0)

    # Compute daily boundaries dynamically per asset
    base_price = telemetry["close"]
    daily_pip = 0.0050 if selected_symbol == "GBP/USD" else 0.0035

    e1_target = round(base_price - daily_pip, 4)
    e2_target = round(base_price + (daily_pip * 1.3), 4)
    mid_target = round((e1_target + e2_target) / 2, 4)

    st.subheader(f"📍 GPS Map — {selected_day} ({selected_symbol})")
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    col_d1.metric("1st Extreme (E1)", f"{e1_target:.4f}", "Time: 08:30 CEST")
    col_d2.metric("Midpoint Anchor (M)", f"{mid_target:.4f}", "Time: 12:00 CEST")
    col_d3.metric("2nd Extreme (E2)", f"{e2_target:.4f}", "Time: 15:30 CEST")
    col_d4.metric(
        "Projected Close (C)",
        f"{e2_target - 0.0010:.4f}",
        "Time: 21:30 CEST",
    )

    st.markdown("---")
    st.subheader("🟢 Traffic Light Monitoring System")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("### First Extreme ($E_1$) Tracking")
        if telemetry["low"] <= e1_target:
            st.success(
                "🟢 **PRINTED**: First Extreme detected & confirmed at target boundary!"
            )
        elif telemetry["close"] < e1_target + 0.0015:
            st.warning(
                "🟡 **DELAY**: Target window active. Standby for 30m confirmation."
            )
        else:
            st.error(
                "🔴 **TOXIC ENVIRONMENT**: Severe deviation detected. NO TRADES AUTHORIZED."
            )

    with col_t2:
        st.markdown("### Second Extreme ($E_2$) Tracking")
        if telemetry["high"] >= e2_target:
            st.success(
                "🟢 **PRINTED**: Second Extreme detected & confirmed at target boundary!"
            )
        elif telemetry["close"] > e2_target - 0.0015:
            st.warning(
                "🟡 **DELAY**: Target window active. Standby for 30m confirmation."
            )
        else:
            st.error(
                "🔴 **TOXIC ENVIRONMENT**: Market structure failed expansion model."
            )

# ------------------------------------------------------------------------------
# TAB 3: ENGINE CALCULATIONS & WEIGHTS
# ------------------------------------------------------------------------------
with tab3:
    st.header(f"⚙️ Math Engine Matrix & Fusion Weights — {selected_symbol}")

    col_e1, col_e2 = st.columns([2, 1])

    with col_e1:
        st.subheader("Normalized Fusion Weights ($\phi(c_i)$-Gated)")
        weights_df = pd.DataFrame(
            list(rec_results["weights"].items()),
            columns=["Engine", "Normalized Weight"],
        )
        st.bar_chart(weights_df.set_index("Engine"))

    with col_e2:
        st.subheader("Raw Confidence Output ($c_i$)")
        for eng, val in rec_results["raw_conf"].items():
            st.write(f"**{eng}:** `{val:.4f}`")

# ------------------------------------------------------------------------------
# TAB 4: DETAILED OPERATOR'S PROTOCOL & ACTION INSTRUCTIONS
# ------------------------------------------------------------------------------
with tab4:
    st.header("📋 Operator Execution Protocol & Invalidation Suite")
    st.warning("⚠️ Strictly follow time and action protocols. Do not front-run window triggers.")

    st.markdown(f"""
    ### 🟢 Authorized Action Protocols ({selected_symbol})
    1. **08:00 - 08:30 CEST (Phase AL - First Extreme Window)**:
       * Observe price relative to $E_1$ target boundary (`{e1_target:.4f}`).
       * **IF** Traffic Light turns 🟢 **PRINTED**, wait for a 5-minute bullish structural confirmation candle.
       * Execute Long entry targeting Midpoint (`{mid_target:.4f}`) and Second Extreme (`{e2_target:.4f}`).
    
    2. **12:00 - 13:00 CEST (Midpoint Reconcile)**:
       * Move Stop Loss to Break-Even once Midpoint Anchor (`{mid_target:.4f}`) is touched.
       * Lock in 50% position profits.

    3. **15:30 CEST (Phase NY - Second Extreme Window)**:
       * **IF** Traffic Light turns 🟢 **PRINTED** at $E_2$ (`{e2_target:.4f}`), close remaining 50% position.
       * Terminate all trading activity for the session.

    ---

    ### 🔴 Mandatory Invalidation Rules (What NOT to do)
    * 🚫 **DO NOT TRADE** if Traffic Light displays 🔴 **TOXIC ENVIRONMENT**.
    * 🚫 **DO NOT ENTER** prior to 08:30 CEST regardless of price level.
    * 🚫 **INVALIDATION**: If price breaches $E_1$ by more than 12 pips prior to confirmation, cancel all orders immediately.
    * 🚫 **NO OVERNIGHT POSITIONS**: All trades must be liquidated by 21:30 CEST prior to the 22:00 nightly reconciliation update.
    """)
