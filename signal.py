import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Institutional Signal Engine", page_icon="📈", layout="centered")

st.title("⚡ Multi-Indicator Buy/Sell Engine")
st.caption("Note: Combined indicator model (EMA + RSI + MACD + Bollinger Bands)")

# -------------------------------------------------------------
# 1. Segment & Asset Selection
# -------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    category = st.selectbox(
        "Select Segment",
        ["Indices & F&O", "Commodities (MCX)", "Equity Stocks"]
    )

symbols_data = {
    "Indices & F&O": {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Fin Nifty": "NIFTY_FIN_SERVICE.NS"
    },
    "Commodities (MCX)": {
        "Crude Oil": "CL=F",
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Natural Gas": "NG=F"
    },
    "Equity Stocks": {
        "Reliance": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "Tata Motors": "TATAMOTORS.NS"
    }
}

with col2:
    selected_asset = st.selectbox("Select Asset", list(symbols_data[category].keys()))

ticker_symbol = symbols_data[category][selected_asset]

# -------------------------------------------------------------
# 2. Technical Analysis Calculation
# -------------------------------------------------------------
def calculate_indicators(df):
    # 1. Exponential Moving Averages (EMA)
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # 2. Relative Strength Index (RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3. MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 4. Bollinger Bands
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['Lower_Band'] = df['SMA_20'] - (df['STD_20'] * 2)

    return df

# -------------------------------------------------------------
# 3. Fetch Data & Display Signal
# -------------------------------------------------------------
try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="5d", interval="5m") # 5-Min Timeframe for F&O/Intraday

    if len(df) > 30:
        df = calculate_indicators(df)
        
        latest = df.iloc[-1]
        live_price = latest['Close']

        # Multi-Condition Logic Scoring
        bullish_score = 0
        bearish_score = 0

        # Condition 1: EMA Trend
        if latest['EMA_9'] > latest['EMA_21']:
            bullish_score += 1
        else:
            bearish_score += 1

        # Condition 2: RSI Level
        if 50 < latest['RSI'] < 70:
            bullish_score += 1
        elif 30 < latest['RSI'] < 50:
            bearish_score += 1

        # Condition 3: MACD Crossover
        if latest['MACD'] > latest['Signal_Line']:
            bullish_score += 1
        else:
            bearish_score += 1

        # Condition 4: Bollinger Band Breakout
        if live_price > latest['SMA_20']:
            bullish_score += 1
        else:
            bearish_score += 1

        # Display Live Price & Metrics
        st.markdown("---")
        st.metric(label=f"Live Price ({selected_asset})", value=f"{live_price:,.2f}")
        
        # Display Indicators Breakdown
        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14)", f"{latest['RSI']:.1f}")
        c2.metric("EMA 9 vs 21", "Bullish" if latest['EMA_9'] > latest['EMA_21'] else "Bearish")
        c3.metric("MACD", "Bullish" if latest['MACD'] > latest['Signal_Line'] else "Bearish")

        st.markdown("---")

        # Decision Engine (Requires Strong Confluence)
        if bullish_score >= 3:
            st.success("🟢 STRONG BUY CALL (CE) / LONG SIGNAL")
            st.write(f"**Confluence Score:** {bullish_score}/4 Indicators Bullish.")
            st.write("**Action:** Uptrend Confirmed. Strictly target 1:2 Risk-Reward with strict Stop Loss.")
            
        elif bearish_score >= 3:
            st.error("🔴 STRONG BUY PUT (PE) / SHORT SIGNAL")
            st.write(f"**Confluence Score:** {bearish_score}/4 Indicators Bearish.")
            st.write("**Action:** Downtrend Confirmed. Strictly target 1:2 Risk-Reward with strict Stop Loss.")
            
        else:
            st.warning("⚠️ NEUTRAL / NO SIGNAL (SIDEWAYS MARKET)")
            st.write("**Action:** Indicators contradictory hain (No clear trend). Trading avoid karein.")

    else:
        st.warning("Data load ho raha hai, thoda wait karein ya market opening timing check karein.")

except Exception as e:
    st.error(f"Error loading live data: {e}")
