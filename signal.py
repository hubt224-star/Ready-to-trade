import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Configuration
st.set_page_config(page_title="Pro Quant Terminal v4.0", layout="wide")

# 2. Assets Configuration
ASSETS = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "Gold (Futures)": "GC=F",
    "Silver (Futures)": "SI=F",
    "Crude Oil (Futures)": "CL=F",
    "Natural Gas (Futures)": "NG=F"
}

st.title("🏛️ Institutional Quant Trading Engine v4.0")
st.sidebar.header("🛠️ Market Configuration")
selected_name = st.sidebar.selectbox("Select Asset", list(ASSETS.keys()))
ticker = ASSETS[selected_name]
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"], index=1)

# 3. Robust Data Processing
@st.cache_data(ttl=60)
def fetch_and_process(ticker, tf):
    try:
        period_map = {"5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "1y"}
        df = yf.download(ticker, period=period_map[tf], interval=tf)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Indicators
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        df['EMA200'] = df['Close'].ewm(span=200).mean()
        
        # RSI Wilder's
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).ewm(alpha=1/14).mean()
        loss = -delta.where(delta < 0, 0).ewm(alpha=1/14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        # ATR
        tr = pd.DataFrame({'a': df['High']-df['Low'], 'b': abs(df['High']-df['Close'].shift()), 'c': abs(df['Low']-df['Close'].shift())}).max(axis=1)
        df['ATR'] = tr.ewm(span=14).mean()
        
        return df
    except Exception as e:
        return None

# 4. Signal Engine Logic
def get_signal_status(df):
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Logic: Buy if Price > EMA200 & Price > EMA50 & RSI < 65 & Bullish Cross
    if curr['Close'] > curr['EMA200'] and curr['EMA20'] > curr['EMA50'] and 40 < curr['RSI'] < 65:
        return "STRONG BUY 🟢", "success", round(curr['Close'] - (curr['ATR']*1.5), 2), round(curr['Close'] + (curr['ATR']*3), 2)
    
    # Logic: Sell if Price < EMA200 & Price < EMA50 & RSI > 35 & Bearish Cross
    elif curr['Close'] < curr['EMA200'] and curr['EMA20'] < curr['EMA50'] and 35 < curr['RSI'] < 60:
        return "STRONG SELL 🔴", "error", round(curr['Close'] + (curr['ATR']*1.5), 2), round(curr['Close'] - (curr['ATR']*3), 2)
    
    return "NEUTRAL / HOLD ⚪", "info", 0, 0

# 5. UI Rendering
df = fetch_and_process(ticker, timeframe)

if df is not None:
    signal, color, sl, target = get_signal_status(df)
    
    # Layout
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Price", f"{df['Close'].iloc[-1]:.2f}")
    col2.metric("RSI", f"{df['RSI'].iloc[-1]:.2f}")
    col3.metric("ATR Volatility", f"{df['ATR'].iloc[-1]:.2f}")
    
    st.markdown("---")
    if color == "success": st.success(f"### {signal}")
    elif color == "error": st.error(f"### {signal}")
    else: st.info(f"### {signal}")
    
    if sl > 0:
        c1, c2 = st.columns(2)
        c1.metric("Suggested Stop Loss", f"{sl}")
        c2.metric("Target (1:2 R:R)", f"{target}")

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Data load failed. Check Asset selection or Network.")
