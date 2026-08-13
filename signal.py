import streamlit as st
import pandas as pd

st.set_page_config(page_title="Buy Sell Signal", layout="centered")
st.title("🎯 Direct Buy / Sell Signal Engine")

# Sample data parameters (In production, replace with live broker data/yfinance)
live_price = 77798.65
ema_fast = 77850.00   # 9 EMA
ema_slow = 77700.00   # 21 EMA

st.metric(label="Live Price", value=live_price)
st.divider()

# Direct Buy / Sell Logic
if ema_fast > ema_slow:
    st.success("🟢 SIGNAL: BUY CALL (CE)")
    st.markdown("**Action:** Market Bullish hai. Call Option Buy karein.")
else:
    st.error("🔴 SIGNAL: BUY PUT (PE)")
    st.markdown("**Action:** Market Bearish hai. Put Option Buy karein.")
