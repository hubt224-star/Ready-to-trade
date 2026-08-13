import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="Multi-Indicator Signal Engine", page_icon="⚡", layout="centered")

st.title("⚡ Multi-Indicator Buy/Sell Engine")
st.caption("Includes NSE & BSE F&O, Commodities, and Equity Stocks")

# -------------------------------------------------------------
# 1. Segment & Asset Selection (Sensex & Bankex Added)
# -------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    category = st.selectbox(
        "Select Segment",
        ["Indices & F&O", "Commodities (MCX)", "Equity Stocks"]
    )

# Ticker Symbols Mapping (Yahoo Finance Format)
symbols_data = {
    "Indices & F&O": {
        "Nifty 50": "^NSEI",
        "Bank Nifty": "^NSEBANK",
        "Fin Nifty": "NIFTY_FIN_SERVICE.NS",
        "BSE Sensex": "BSESN",
        "BSE Bankex": "BSE-BANKEX"
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
        "Tata Motors": "TATAMOTORS.NS",
        "State Bank of India": "SBIN.NS"
    }
}

with col2:
    selected_asset = st.selectbox("Select Asset", list(symbols_data[category].keys()))

ticker_symbol = symbols_data[category][selected_asset]

# -------------------------------------------------------------
# 2. Technical Indicators Logic
# -------------------------------------------------------------
def calculate_indicators(df):
    # 1. EMA (9 & 21)
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # 2. RSI (14)
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
# 3. Data Fetching & Signal Execution
# -------------------------------------------------------------
try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="5d", interval="5m")

    if len(df) > 30:
        df = calculate_indicators(df)
        
        latest = df.iloc[-1]
        live_price = latest['Close']

        bullish_score = 0
        bearish_score = 0

        # Indicator 1: EMA
        if latest['EMA_9'] > latest['EMA_21']:
            bullish_score += 1
        else:
            bearish_score += 1

        # Indicator 2: RSI
        if 50 < latest['RSI'] < 70:
            bullish_score += 1
        elif 30 < latest['RSI'] < 50:
            bearish_score += 1

        # Indicator 3: MACD
        if latest['MACD'] > latest['Signal_Line']:
            bullish_score += 1
        else:
            bearish_score += 1

        # Indicator 4: Bollinger Band Midline
        if live_price > latest['SMA_20']:
            bullish_score += 1
        else:
            bearish_score += 1

        st.markdown("---")
        st.metric(label=f"Live Price ({selected_asset})", value=f"{live_price:,.2f}")
        
        # Breakdown Indicators
        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14)", f"{latest['RSI']:.1f}")
        c2.metric("EMA Trend", "Bullish" if latest['EMA_9'] > latest['EMA_21'] else "Bearish")
        c3.metric("MACD Status", "Bullish" if latest['MACD'] > latest['Signal_Line'] else "Bearish")

        st.markdown("---")

        # Confluence Signals
        if bullish_score >= 3:
            st.success("🟢 STRONG BUY CALL (CE) / LONG SIGNAL")
            st.write(f"**Score:** {bullish_score}/4 Technical Indicators Bullish hain.")
            st.write("**Action:** Call Option Buy karein (Strict Stop Loss ke saath).")
            
        elif bearish_score >= 3:
            st.error("🔴 STRONG BUY PUT (PE) / SHORT SIGNAL")
            st.write(f"**Score:** {bearish_score}/4 Technical Indicators Bearish hain.")
            st.write("**Action:** Put Option Buy karein (Strict Stop Loss ke saath).")
            
        else:
            st.warning("⚠️ NEUTRAL / SIDEWAYS MARKET (NO SIGNAL)")
            st.write("**Action:** Market me clear trend nahi hai. Trading avoid karein.")

    else:
        st.warning("Live data load nahi ho pa raha hai. Market timings/holidays check karein.")

except Exception as e:
    st.error(f"Error: {e}")
