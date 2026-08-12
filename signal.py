import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="High-Accuracy Signal Engine")

st.title("🎯 Institutional Options Signal Engine")
st.caption("Pure Engine: EMA 9/21/50/200 + RSI + ATR")

# Sidebar Settings
st.sidebar.header("⚙️ Execution Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "1d"])
min_score = st.sidebar.slider("Min Signal Confidence", 0, 100, 70)

# Updated Dictionary with Indices & Commodities
INDICES = {
    # Equity Indices
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    
    # Commodities (Yahoo Finance Futures Tickers)
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
    "Copper": "HG=F"
}

# --- Pure Pandas Technical Indicators (No External Libs) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()
