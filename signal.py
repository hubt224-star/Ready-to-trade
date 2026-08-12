import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="Institutional Trading Dashboard", layout="wide")

st.title("🎯 Institutional Trading & Signal Engine")
st.caption("Filtered Engine: Multi-EMA Trend + Wilder's RSI + MACD + Dynamic ATR Risk Engine")

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Execution Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "1d"], index=1)

ASSETS = {
    "Crude Oil (Futures)": "CL=F",
    "Gold (Futures)": "GC=F",
    "Silver (Futures)": "SI=F",
    "Natural Gas (Futures)": "NG=F",
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK"
}

selected_asset_name = st.sidebar.selectbox("Select Asset", list(ASSETS.keys()))
ticker = ASSETS[selected_asset_name]

# --- Accurate Indicator Functions ---

def calculate_rsi(series, period=14):
    """Accurate Wilder's Smoothing RSI"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    """Average True Range for Dynamic SL/Target"""
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    df_tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    return df_tr.ewm(alpha=1/period, adjust=False).mean()

# --- Data Fetching & Processing ---
@st.cache_data(ttl=60)
def fetch_data(symbol, tf):
    period_map = {"5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "1y"}
    df = yf.download(symbol, period=period_map[tf], interval=tf)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Technical Indicators
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['RSI'] = calculate_rsi(df['Close'])
    df['ATR'] = calculate_atr(df)
    
    # MACD Calculation
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

try:
    df = fetch_data(ticker, timeframe)
    latest = df.iloc[-1]
    
    price = round(float(latest['Close']), 2)
    rsi = round(float(latest['RSI']), 2)
    ema21 = round(float(latest['EMA_21']), 2)
    ema50 = round(float(latest['EMA_50']), 2)
    atr = round(float(latest['ATR']), 2)
    macd = float(latest['MACD'])
    macd_sig = float(latest['MACD_Signal'])

    # --- Strict Signal Generation Engine ---
    signal = "NEUTRAL ⚪"
    status_type = "info"
    sl = 0.0
    target = 0.0

    # Bullish Conditions
    bullish_trend = price > ema21 and ema21 > ema50
    bullish_macd = macd > macd_sig
    
    # Bearish Conditions
    bearish_trend = price < ema21 and ema21 < ema50
    bearish_macd = macd < macd_sig

    if bullish_trend and bullish_macd and (45 <= rsi < 70):
        signal = "STRONG BULLISH BUY 🟢"
        status_type = "success"
        sl = round(price - (1.5 * atr), 2)
        target = round(price + (3.0 * atr), 2)

    elif bearish_trend and bearish_macd and (30 < rsi <= 55):
        signal = "STRONG BEARISH SELL 🔴"
        status_type = "error"
        sl = round(price + (1.5 * atr), 2)
        target = round(price - (3.0 * atr), 2)

    # Oversold / Overbought Protection Blockers
    elif rsi <= 30:
        signal = "OVERSOLD - NO SELL (WAIT FOR REVERSAL) ⚠️"
        status_type = "warning"
    elif rsi >= 70:
        signal = "OVERBOUGHT - NO BUY (WAIT FOR PULLBACK) ⚠️"
        status_type = "warning"

    # --- UI Rendering ---
    st.subheader(f"Asset: {selected_asset_name} ({timeframe})")
    st.metric("Live Market Price", f"${price}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI (14)", rsi)
    c2.metric("EMA 21", ema21)
    c3.metric("EMA 50", ema50)
    c4.metric("ATR Volatility", atr)

    st.markdown("---")

    # Display Signal Box
    if status_type == "success":
        st.success(f"**SIGNAL:** {signal}")
    elif status_type == "error":
        st.error(f"**SIGNAL:** {signal}")
    elif status_type == "warning":
        st.warning(f"**SIGNAL:** {signal}")
    else:
        st.info(f"**SIGNAL:** {signal}")

    # Display Trade Execution Details
    if "BUY" in signal or "SELL" in signal:
        st.subheader("🛡️ Dynamic Risk Management (1:2 R:R Ratio)")
        res1, res2 = st.columns(2)
        res1.metric("Suggested Stop-Loss", f"${sl}")
        res2.metric("Target Price", f"${target}")

except Exception as e:
    st.error(f"Data load karne me problem hui. Details: {e}")
