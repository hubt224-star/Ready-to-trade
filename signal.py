import streamlit as st
import pandas as pd
import numpy as np
import pyotp
from streamlit_autorefresh import st_autorefresh
from SmartApi import SmartConnect

st.set_page_config(page_title="Pro Trading Signal Dashboard", layout="wide")

st.title("📈 Pro Options Signal Dashboard (EMA + RSI Filter)")

# Session State Initialization
if "connected" not in st.session_state:
    st.session_state.connected = False
if "smartApi" not in st.session_state:
    st.session_state.smartApi = None
if "nifty_history" not in st.session_state:
    st.session_state.nifty_history = []
if "sensex_history" not in st.session_state:
    st.session_state.sensex_history = []

# Sidebar Form
with st.sidebar:
    st.header("Angel One API Login")
    with st.form("login_form"):
        api_key = st.text_input("API Key", type="password")
        client_id = st.text_input("Client ID / User ID")
        password = st.text_input("MPIN / Password", type="password")
        totp_secret = st.text_input("TOTP Secret Key")
        
        submit_btn = st.form_submit_button("Connect & Start Live Fetch")

if submit_btn:
    if api_key and client_id and password and totp_secret:
        try:
            totp = pyotp.TOTP(totp_secret.replace(" ", "")).now()
            smartApi = SmartConnect(api_key=api_key)
            data = smartApi.generateSession(client_id, password, totp)
            
            if data and data.get('status'):
                st.session_state.smartApi = smartApi
                st.session_state.connected = True
                st.sidebar.success("Connected Successfully!")
            else:
                msg = data.get('message', 'Login Failed') if data else 'No response'
                st.sidebar.error(f"Failed: {msg}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Kripya saare fields bharein.")

# High Accuracy Indicator Calculation
def calculate_advanced_signal(history, step_size, sl_pts, target_pts):
    # Minimum 14 data points required for accurate RSI
    if len(history) < 14:
        return "WAIT / COLLECTING DATA", "N/A", 0, 0, 0, "Neutral"
    
    current_price = history[-1]
    atm_strike = round(current_price / step_size) * step_size
    
    df = pd.DataFrame(history, columns=['Price'])
    
    # 1. Exponential Moving Averages (EMA 5 & EMA 20)
    ema_short = df['Price'].ewm(span=5, adjust=False).mean().iloc[-1]
    ema_long = df['Price'].ewm(span=20, adjust=False).mean().iloc[-1]
    
    # 2. Relative Strength Index (RSI 14)
    delta = df['Price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero
    loss_val = loss.iloc[-1] if loss.iloc[-1] != 0 else 0.001
    rs = gain.iloc[-1] / loss_val
    rsi = 100 - (100 / (1 + rs))
    rsi = round(rsi, 2)
    
    # 3. Multi-Condition Filtering Logic
    # Strong CALL Rule: EMA 5 > EMA 20 AND RSI > 55 (Momentum Building) AND RSI < 70 (Not Overbought)
    if (ema_short > ema_long) and (rsi > 55) and (rsi < 70):
        signal = "STRONG BUY CALL (CE)"
        strike = f"{atm_strike} CE"
        sl = round(current_price - sl_pts, 2)
        target = round(current_price + target_pts, 2)
        trend = "BULLISH 🚀"
        
    # Strong PUT Rule: EMA 5 < EMA 20 AND RSI < 45 (Bearish Momentum) AND RSI > 30 (Not Oversold)
    elif (ema_short < ema_long) and (rsi < 45) and (rsi > 30):
        signal = "STRONG BUY PUT (PE)"
        strike = f"{atm_strike} PE"
        sl = round(current_price + sl_pts, 2)
        target = round(current_price - target_pts, 2)
        trend = "BEARISH 🔻"
        
    # Sideways / Risk Zone Avoidance Filter
    else:
        signal = "NO SIGNAL (Sideways/Market Filtered)"
        strike = "N/A"
        sl, target = 0, 0
        trend = "SIDEWAYS ⏸️"
        
    return signal, strike, sl, target, rsi, trend

# Live Data Fetch & Logic
if st.session_state.connected:
    st_autorefresh(interval=5000, key="data_refresh") # 5 Sec Refresh
    st.success("Live High-Accuracy Feed Active!")
    
    try:
        smartApi = st.session_state.smartApi
        
        # 1. Fetch Nifty 50 Data
        nifty_data = smartApi.ltpData("NSE", "NIFTY-EQ", "99926000")
        # 2. Fetch Sensex Data
        sensex_data = smartApi.ltpData("BSE", "SENSEX-EQ", "1")
        
        # --- NIFTY SECTION ---
        st.subheader("📊 NIFTY 50 (High Accuracy Filter)")
        if nifty_data and nifty_data.get('status'):
            n_price = float(nifty_data['data']['ltp'])
            st.session_state.nifty_history.append(n_price)
            if len(st.session_state.nifty_history) > 100:
                st.session_state.nifty_history.pop(0)

            n_sig, n_strike, n_sl, n_tgt, n_rsi, n_trend = calculate_advanced_signal(
                st.session_state.nifty_history, step_size=50, sl_pts=20, target_pts=45
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("NIFTY Price", f"₹{n_price}")
            col2.metric("RSI (14)", f"{n_rsi}")
            col3.metric("Trend", n_trend)
            col4.metric("Recommended Strike", f"NIFTY {n_strike}")
            
            st.info(f"📌 **Signal:** {n_sig} | **SL:** ₹{n_sl} | **Target:** ₹{n_tgt}")
        else:
            st.info("Nifty data fetch ho raha hai...")

        st.markdown("---")

        # --- SENSEX SECTION ---
        st.subheader("📊 SENSEX (High Accuracy Filter)")
        if sensex_data and sensex_data.get('status'):
            s_price = float(sensex_data['data']['ltp'])
            st.session_state.sensex_history.append(s_price)
            if len(st.session_state.sensex_history) > 100:
                st.session_state.sensex_history.pop(0)

            s_sig, s_strike, s_sl, s_tgt, s_rsi, s_trend = calculate_advanced_signal(
                st.session_state.sensex_history, step_size=100, sl_pts=70, target_pts=140
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("SENSEX Price", f"₹{s_price}")
            col2.metric("RSI (14)", f"{s_rsi}")
            col3.metric("Trend", s_trend)
            col4.metric("Recommended Strike", f"SENSEX {s_strike}")
            
            st.info(f"📌 **Signal:** {s_sig} | **SL:** ₹{s_sl} | **Target:** ₹{s_tgt}")
        else:
            st.info("Sensex data fetch ho raha hai...")

    except Exception as e:
        st.error(f"Data Fetching Error: {e}")
else:
    st.info("Sidebar me details bhar kar 'Connect & Start Live Fetch' par click karein.")
