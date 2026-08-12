import streamlit as st
import pandas as pd
import numpy as np
import pyotp
from streamlit_autorefresh import st_autorefresh
from SmartApi import SmartConnect

st.set_page_config(page_title="Angel One Trading Signal", layout="wide")

# Har 2 second me live auto-refresh
st_autorefresh(interval=2000, limit=None, key="live_refresh")

st.title("📈 Live Options Trading Signal Dashboard")

# Sidebar - Angel One Login Inputs
st.sidebar.header("Angel One API Login")
api_key = st.sidebar.text_input("API Key", type="password")
client_id = st.sidebar.text_input("Client ID / User ID")
password = st.sidebar.text_input("MPIN / Password", type="password")
totp_secret = st.sidebar.text_input("TOTP Secret Key (e.g. 6WTKYR...)")

if st.sidebar.button("Fetch Live Signal"):
    if api_key and client_id and password and totp_secret:
        try:
            # Auto Generate 6-Digit TOTP using Secret Key
            totp = pyotp.TOTP(totp_secret.replace(" ", "")).now()

            # Angel One Connection Setup
            smartApi = SmartConnect(api_key=api_key)
            data = smartApi.generateSession(client_id, password, totp)
            
            # Fetching Nifty 50 Spot LTP (Token: 99926000, Exchange: NSE)
            ltp_data = smartApi.ltpData("NSE", "NIFTY", "99926000")
            latest_price = float(ltp_data['data']['ltp'])

            # Maintaining last 30 prices in session state for EMA
            if 'price_history' not in st.session_state:
                st.session_state['price_history'] = [latest_price] * 30
            else:
                st.session_state['price_history'].append(latest_price)
                if len(st.session_state['price_history']) > 50:
                    st.session_state['price_history'].pop(0)

            df = pd.DataFrame({'price': st.session_state['price_history']})
            df['EMA_9'] = df['price'].ewm(span=9, adjust=False).mean()
            df['EMA_21'] = df['price'].ewm(span=21, adjust=False).mean()

            short_ema = df['EMA_9'].iloc[-1]
            long_ema = df['EMA_21'].iloc[-1]

            # Display Live Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Latest Price", f"₹{latest_price:.2f}")
            col2.metric("Short EMA (9)", f"₹{short_ema:.2f}")
            col3.metric("Long EMA (21)", f"₹{long_ema:.2f}")

            # Signal Logic
            if short_ema > long_ema:
                st.success("🟢 SIGNAL: BUY CALL (CE) - Short EMA crossed above Long EMA")
            elif short_ema < long_ema:
                st.error("🔻 SIGNAL: BUY PUT (PE) - Short EMA crossed below Long EMA")
            else:
                st.warning("⚡ SIGNAL: NEUTRAL - No Crossover")

            st.line_chart(df[['price', 'EMA_9', 'EMA_21']])

        except Exception as e:
            st.error(f"Angel One Login Error: {e}")
    else:
        st.warning("Please enter all Angel One Login Details in Sidebar.")
else:
    st.info("Sidebar me Apni Angel API details bhar kar 'Fetch Live Signal' par click karein.")
