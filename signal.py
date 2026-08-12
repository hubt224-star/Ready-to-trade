import streamlit as st
import pandas as pd
import numpy as np
import pyotp
import time
from streamlit_autorefresh import st_autorefresh
from SmartApi import SmartConnect

st.set_page_config(page_title="Angel One Trading Signal", layout="wide")

st.title("📈 Live Options Trading Signal Dashboard")

# Session State Initialization
if "connected" not in st.session_state:
    st.session_state.connected = False
if "smartApi" not in st.session_state:
    st.session_state.smartApi = None
if "price_history" not in st.session_state:
    st.session_state.price_history = []

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

# Live Data Fetch & Logic
if st.session_state.connected:
    st_autorefresh(interval=5000, key="data_refresh") # Har 5 sec me refresh
    st.success("Live Connection Active!")
    
    st.subheader("📊 Live Market Signal")
    
    try:
        smartApi = st.session_state.smartApi
        ltp_data = smartApi.ltpData("NSE", "NIFTY-EQ", "99926000")
        
        if ltp_data and ltp_data.get('status'):
            price = float(ltp_data['data']['ltp'])
            
            # Store price history for EMA Calculation
            st.session_state.price_history.append(price)
            if len(st.session_state.price_history) > 50:
                st.session_state.price_history.pop(0)

            # Round off to nearest ATM Strike Price (Nifty 50 Step size = 50)
            atm_strike = round(price / 50) * 50

            col1, col2, col3 = st.columns(3)
            col1.metric("NIFTY 50 Live Price", f"₹{price}")

            # Trading Logic (Minimum 5 data points required)
            if len(st.session_state.price_history) >= 5:
                df = pd.DataFrame(st.session_state.price_history, columns=['Price'])
                ema_short = df['Price'].ewm(span=3, adjust=False).mean().iloc[-1]
                ema_long = df['Price'].ewm(span=8, adjust=False).mean().iloc[-1]

                # CALL (CE) Signal
                if ema_short > ema_long:
                    signal = "BUY CALL (CE)"
                    strike_suggested = f"NIFTY {atm_strike} CE"
                    stoploss = round(price - 25, 2)
                    target = round(price + 50, 2)
                    status_color = "green"

                # PUT (PE) Signal
                elif ema_short < ema_long:
                    signal = "BUY PUT (PE)"
                    strike_suggested = f"NIFTY {atm_strike} PE"
                    stoploss = round(price + 25, 2)
                    target = round(price - 50, 2)
                    status_color = "red"

                # NEUTRAL Signal
                else:
                    signal = "WAIT / NO SIGNAL"
                    strike_suggested = "N/A"
                    stoploss = 0
                    target = 0
                    status_color = "orange"

                col2.metric("Signal Status", signal)
                col3.metric("Recommended Strike", strike_suggested)

                st.markdown("---")
                
                # Trade Details Table
                st.subheader("🎯 Trade Levels")
                st.write(f"**Current Trend:** {signal}")
                st.write(f"**Stop Loss (SL):** ₹{stoploss}")
                st.write(f"**Target Price:** ₹{target}")

            else:
                st.info("Market data collect ho raha hai... 5-10 second me signal update hoga.")
        else:
            st.info("Market close hai ya data fetch nahi ho raha hai.")

    except Exception as e:
        st.error(f"Data Fetching Error: {e}")
else:
    st.info("Sidebar me details bhar kar 'Connect & Start Live Fetch' par click karein.")
