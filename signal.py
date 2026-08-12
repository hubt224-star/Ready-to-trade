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

# Sidebar Form (Ye disconnect aur reset hone se rokega)
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
                msg = data.get('message', 'Login Failed') if data else 'No response from server'
                st.sidebar.error(f"Failed: {msg}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Kripya saare fields bharein.")

# Live Data Fetch logic tabhi chalega jab connect ho jaye
if st.session_state.connected:
    # Auto refresh 10 seconds me page update karega bina login reset kiye
    st_autorefresh(interval=10000, key="data_refresh")
    st.success("Live Connection Active!")
else:
    st.info("Sidebar me details bhar kar 'Connect & Start Live Fetch' par click karein.")
