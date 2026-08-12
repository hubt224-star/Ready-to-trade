import streamlit as st
import pandas as pd
import numpy as np
import pyotp
from streamlit_autorefresh import st_autorefresh
from SmartApi import SmartConnect

st.set_page_config(page_title="Angel One Trading Signal", layout="wide")

st.title("📈 Live Options Trading Signal Dashboard")

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

# Signal Generator Helper Function
def calculate_signal(history, step_size, sl_pts, target_pts):
    if len(history) < 5:
        return "WAIT / FETCHING DATA", "N/A", 0, 0
    
    current_price = history[-1]
    atm_strike = round(current_price / step_size) * step_size
    
    df = pd.DataFrame(history, columns=['Price'])
    ema_short = df['Price'].ewm(span=3, adjust=False).mean().iloc[-1]
    ema_long = df['Price'].ewm(span=8, adjust=False).mean().iloc[-1]
    
    if ema_short > ema_long:
        signal = "BUY CALL (CE)"
        strike = f"{atm_strike} CE"
        sl = round(current_price - sl_pts, 2)
        target = round(current_price + target_pts, 2)
    elif ema_short < ema_long:
        signal = "BUY PUT (PE)"
        strike = f"{atm_strike} PE"
        sl = round(current_price + sl_pts, 2)
        target = round(current_price - target_pts, 2)
    else:
        signal = "WAIT / NO SIGNAL"
        strike = "N/A"
        sl, target = 0, 0
        
    return signal, strike, sl, target

# Live Data Fetch & Logic
if st.session_state.connected:
    st_autorefresh(interval=5000, key="data_refresh") # 5 Sec Refresh
    st.success("Live Connection Active!")
    
    try:
        smartApi = st.session_state.smartApi
        
        # 1. Fetch Nifty 50 Data (NSE, Token: 99926000)
        nifty_data = smartApi.ltpData("NSE", "NIFTY-EQ", "99926000")
        # 2. Fetch Sensex Data (BSE, Token: 1)
        sensex_data = smartApi.ltpData("BSE", "SENSEX-EQ", "1")
        
        # --- NIFTY SECTION ---
        st.subheader("📊 NIFTY 50 Live Signal")
        if nifty_data and nifty_data.get('status'):
            n_price = float(nifty_data['data']['ltp'])
            st.session_state.nifty_history.append(n_price)
            if len(st.session_state.nifty_history) > 50:
                st.session_state.nifty_history.pop(0)

            n_sig, n_strike, n_sl, n_tgt = calculate_signal(
                st.session_state.nifty_history, step_size=50, sl_pts=25, target_pts=50
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("NIFTY Live Price", f"₹{n_price}")
            col2.metric("Signal Status", n_sig)
            col3.metric("Recommended Strike", f"NIFTY {n_strike}")
            
            st.caption(f"🎯 **NIFTY Levels:** SL: ₹{n_sl} | Target: ₹{n_tgt}")
        else:
            st.info("Nifty data fetch nahi ho raha hai.")

        st.markdown("---")

        # --- SENSEX SECTION ---
        st.subheader("📊 SENSEX Live Signal")
        if sensex_data and sensex_data.get('status'):
            s_price = float(sensex_data['data']['ltp'])
            st.session_state.sensex_history.append(s_price)
            if len(st.session_state.sensex_history) > 50:
                st.session_state.sensex_history.pop(0)

            s_sig, s_strike, s_sl, s_tgt = calculate_signal(
                st.session_state.sensex_history, step_size=100, sl_pts=80, target_pts=150
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("SENSEX Live Price", f"₹{s_price}")
            col2.metric("Signal Status", s_sig)
            col3.metric("Recommended Strike", f"SENSEX {s_strike}")
            
            st.caption(f"🎯 **SENSEX Levels:** SL: ₹{s_sl} | Target: ₹{s_tgt}")
        else:
            st.info("Sensex data fetch nahi ho raha hai.")

    except Exception as e:
        st.error(f"Data Fetching Error: {e}")
else:
    st.info("Sidebar me details bhar kar 'Connect & Start Live Fetch' par click karein.")
