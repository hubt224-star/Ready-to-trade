import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Pro Buy-Sell Signal Engine", layout="wide")

st.title("🎯 Institutional Buy / Sell Trading Signal Engine")
st.caption("Multi-Indicator Filtered Strategy: Trend + EMA Crossover + Wilder's RSI + ATR Risk Engine")

# ---------------------------------------------------------
# 2. Asset & Timeframe Selection
# ---------------------------------------------------------
ASSETS = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "Crude Oil (Futures)": "CL=F",
    "Gold (Futures)": "GC=F",
    "Silver (Futures)": "SI=F",
    "Natural Gas (Futures)": "NG=F"
}

st.sidebar.header("⚙️ Control Panel")
selected_asset = st.sidebar.selectbox("Select Asset", list(ASSETS.keys()))
ticker = ASSETS[selected_asset]
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h", "1d"], index=1)

# ---------------------------------------------------------
# 3. Data Fetching & Technical Indicators Engine
# ---------------------------------------------------------
@st.cache_data(ttl=30)
def load_market_data(symbol, tf):
    try:
        period_map = {"5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "1y"}
        df = yf.download(symbol, period=period_map[tf], interval=tf)
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Indicators Calculation
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # Wilder's RSI Smoothing
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        loss = -delta.where(delta < 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

        # Average True Range (ATR)
        tr = pd.DataFrame({
            'hl': df['High'] - df['Low'],
            'hc': abs(df['High'] - df['Close'].shift()),
            'lc': abs(df['Low'] - df['Close'].shift())
        }).max(axis=1)
        df['ATR'] = tr.ewm(span=14, adjust=False).mean()

        return df
    except Exception:
        return None

# ---------------------------------------------------------
# 4. Strict Buy/Sell Signal Logic
# ---------------------------------------------------------
def generate_buy_sell_signal(df):
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(float(curr['Close']), 2)
    rsi = round(float(curr['RSI']), 2)
    atr = round(float(curr['ATR']), 2)

    # Bullish Setup:
    # 1. Price > EMA 200 (Uptrend)
    # 2. EMA 9 crosses above EMA 21 (Bullish Crossover)
    # 3. RSI between 45 and 68 (Strong momentum, not overbought)
    bullish_trend = curr['Close'] > curr['EMA_200']
    bullish_cross = curr['EMA_9'] > curr['EMA_21']
    bullish_rsi = 45 <= curr['RSI'] < 68

    # Bearish Setup:
    # 1. Price < EMA 200 (Downtrend)
    # 2. EMA 9 crosses below EMA 21 (Bearish Crossover)
    # 3. RSI between 32 and 55 (Strong drop momentum, not oversold)
    bearish_trend = curr['Close'] < curr['EMA_200']
    bearish_cross = curr['EMA_9'] < curr['EMA_21']
    bearish_rsi = 32 < curr['RSI'] <= 55

    # Buy Signal Execution
    if bullish_trend and bullish_cross and bullish_rsi:
        sl = round(price - (1.5 * atr), 2)
        target = round(price + (3.0 * atr), 2) # 1:2 R:R
        return "BUY SIGNAL 🟢", "success", price, sl, target, "Bullish Trend + EMA Crossover Confirmed"

    # Sell Signal Execution
    elif bearish_trend and bearish_cross and bearish_rsi:
        sl = round(price + (1.5 * atr), 2)
        target = round(price - (3.0 * atr), 2) # 1:2 R:R
        return "SELL SIGNAL 🔴", "error", price, sl, target, "Bearish Trend + EMA Crossover Confirmed"

    # Protection Guards
    elif curr['RSI'] <= 30:
        return "WAIT (NO TRADE) ⚠️", "warning", price, 0, 0, "Market Oversold (RSI < 30). Reversal possible, do NOT Sell."

    elif curr['RSI'] >= 70:
        return "WAIT (NO TRADE) ⚠️", "warning", price, 0, 0, "Market Overbought (RSI > 70). Pullback possible, do NOT Buy."

    else:
        return "NEUTRAL / WAIT ⚪", "info", price, 0, 0, "No clear trend breakout. Wait for strong confirmation."

# ---------------------------------------------------------
# 5. UI Rendering & Output
# ---------------------------------------------------------
df = load_market_data(ticker, timeframe)

if df is not None:
    signal, status, price, sl, target, reason = generate_buy_sell_signal(df)
    latest = df.iloc[-1]

    # Live Dashboard Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Asset Price", f"{price}")
    col2.metric("RSI (14)", f"{latest['RSI']:.2f}")
    col3.metric("EMA 200 (Trend)", f"{latest['EMA_200']:.2f}")
    col4.metric("ATR Volatility", f"{latest['ATR']:.2f}")

    st.markdown("---")

    # Clear Signal Display
    st.subheader(f"Asset: {selected_asset} ({timeframe})")
    
    if status == "success":
        st.success(f"### 🔥 PRO SIGNAL: {signal}")
    elif status == "error":
        st.error(f"### 🔥 PRO SIGNAL: {signal}")
    elif status == "warning":
        st.warning(f"### ⚠️ PRO SIGNAL: {signal}")
    else:
        st.info(f"### ⚪ PRO SIGNAL: {signal}")

    st.write(f"**Reason:** {reason}")

    # Execution Parameters Display (Entry, SL, Target)
    if "BUY" in signal or "SELL" in signal:
        st.markdown("---")
        st.subheader("🛡️ Trade Execution Plan (1:2 Risk-Reward)")
        
        p1, p2, p3 = st.columns(3)
        p1.metric("Entry Price", f"{price}")
        p2.metric("Stop-Loss (SL)", f"{sl}")
        p3.metric("Target Price (TP)", f"{target}")

    # Price Chart
    st.markdown("---")
    st.subheader("📈 Trend Line Chart (Price & EMAs)")
    st.line_chart(df[['Close', 'EMA_9', 'EMA_21', 'EMA_200']])

else:
    st.error("Market Data load nahi ho pa raha. Kripya Asset ya Network Check karein.")
