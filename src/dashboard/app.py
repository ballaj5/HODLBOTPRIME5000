# src/dashboard/app.py
import streamlit as st
import pandas as pd
import os
import sys

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# --- Correctly import from src packages ---
from src.data.database import get_live_signals
from src.telegram.send_alert import send_test_alert
from src.dashboard.performance_metrics import render_performance_metrics
from src.config import config # Import the central config object

# --- Page Configuration & Styling ---
st.set_page_config(layout="wide", page_title="HODLBot-V1.F Dashboard")

# Custom CSS for a modern look
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    h1, h2, h3 { font-weight: 700; }
    .stButton>button { border-color: #4A90E2; color: #4A90E2; }
    .stButton>button:hover { background-color: #4A90E2; color: #FFFFFF; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 1rem; }
    .signal-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; align-items: center; background-color: #161B22; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; border: 1px solid #30363D; }
    .coin-info { display: flex; align-items: center; gap: 1rem; }
    .coin-info img { width: 40px; height: 40px; }
    .confidence-text { font-size: 1.5rem; font-weight: bold; text-align: right; }
</style>
""", unsafe_allow_html=True)


# --- Header & Controls ---
st.title("📈 HODLBot-V1.F Dashboard")

# Use session state to keep the confidence value
if 'confidence_threshold' not in st.session_state:
    st.session_state.confidence_threshold = 70.0

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("⚙️ Controls")

    # Confidence Threshold Slider
    st.session_state.confidence_threshold = st.slider(
        "Confidence Threshold (%)",
        min_value=0.0, max_value=100.0,
        value=st.session_state.confidence_threshold,
        step=1.0,
        help="Filter signals displayed below by their minimum confidence level."
    )

    st.subheader("Telegram Alerts")
    # CORRECTED: Use the path from the central config file
    ALERT_FLAG_PATH = config.ALERT_FLAG_PATH

    def toggle_alerts_state():
        if st.session_state.alerts_enabled:
            if not os.path.exists(os.path.dirname(ALERT_FLAG_PATH)):
                 os.makedirs(os.path.dirname(ALERT_FLAG_PATH))
            if not os.path.exists(ALERT_FLAG_PATH):
                open(ALERT_FLAG_PATH, 'a').close()
                st.toast("Alerts enabled!", icon="🔔")
        else:
            if os.path.exists(ALERT_FLAG_PATH):
                os.remove(ALERT_FLAG_PATH)
                st.toast("Alerts disabled.", icon="🔕")

    st.toggle(
        "Enable Alerts",
        value=os.path.exists(ALERT_FLAG_PATH),
        key="alerts_enabled",
        on_change=toggle_alerts_state
    )

    if st.button("Send Test Alert"):
        send_test_alert()
        st.toast("Test alert sent!", icon="✅")

# --- Live Signals Display ---
st.header(f"Live Signals (Confidence ≥ {st.session_state.confidence_threshold:.0f}%)")
live_signals = get_live_signals(st.session_state.confidence_threshold)

if not live_signals:
    st.info("No signals meet the current criteria.")
else:
    # Display Header
    st.markdown("""
        <div class="signal-row" style="background-color: transparent; border: none; font-weight: bold; color: #A0AEC0;">
            <div>Coin</div>
            <div>Signal</div>
            <div>Timeframe</div>
            <div>Price at Alert</div>
            <div style="text-align: right;">Confidence</div>
        </div>
    """, unsafe_allow_html=True)

    for signal in live_signals:
        signal_dict = dict(signal)
        icon_symbol = signal_dict['symbol'].lower().replace('1000', '')
        icon_url = f"https://cdn.jsdelivr.net/gh/atomiclabs/cryptocurrency-icons@1a63530be6e374711a8554f31b17e4cb92c25659/32/color/{icon_symbol}.png"
        signal_color = "#2ECC71" if signal_dict['signal'] == 'UP' else "#E74C3C"

        st.markdown(f"""
            <div class="signal-row">
                <div class="coin-info">
                    <img src="{icon_url}" alt="{signal_dict['symbol']}">
                    <span>{signal_dict['symbol']}/USDT</span>
                </div>
                <div style="color: {signal_color}; font-weight: bold;">{signal_dict['signal']}</div>
                <div>{signal_dict['timeframe']}</div>
                <div>${float(signal_dict.get('price_at_prediction', 0)):,.4f}</div>
                <div class="confidence-text" style="color: {signal_color};">{signal_dict['confidence']:.2f}%</div>
            </div>
        """, unsafe_allow_html=True)


# --- Accuracy Stats Section ---
st.markdown("---")
# This now calls the corrected, Streamlit-native performance module
render_performance_metrics()