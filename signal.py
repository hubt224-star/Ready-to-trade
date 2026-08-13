import streamlit as st
import pandas as pd
import yfinance as yf

# Page Configuration
st.set_page_config(page_title="Pro Buy/Sell Signal Engine", layout="centered")

st.title("🎯 Direct Buy / Sell Signal Engine")

# Asset Selection Dropdown (Nifty 50 & Sensex)
selected_asset = st.selectbox(
    "Select Asset / Index:",
    ["Nifty 50", "Sensex"]
)

# Map selected asset to Yahoo Finance Ticker Symbols
ticker_map = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN"
}

ticker_symbol = ticker_map[selected_asset]

st.divider()

# Function to fetch live data and calculate EMA
@st.cache_data(ttl=15)  # Refresh cache every 15 seconds
def get_live_signal(symbol):
    # Fetch recent intraday 5-minute data
    df = yf.download(tickers=symbol, period="1d", interval="5m", progress=False)
    
    if df.empty:
        return None, None, None
    
    # Calculate Fast EMA (9) and Slow EMA (21)
    df['EMA_Fast'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    latest_price = float(df['Close'].iloc[-1])
    ema_fast = float(df['EMA_Fast'].iloc[-1])
    ema_slow = float(df['EMA_Slow'].iloc[-1])
    
    return latest_price, ema_fast, ema_slow

# Main Execution
try:
    live_price, ema_fast, ema_slow = get_live_signal(ticker_symbol)

    if live_price is not None:
        st.metric(label=f"Live Price ({selected_asset})", value=f"₹{live_price:,.2f}")
        
        col1, col2 = st.columns(2)
        col1.caption(f"EMA Fast (9): {ema_fast:,.2f}")
        col2.caption(f"EMA Slow (21): {ema_slow:,.2f}")

        st.divider()

        # Direct Buy / Sell Logic
        if ema_fast > ema_slow:
            st.success("🟢 SIGNAL: BUY CALL (CE)")
            st.markdown(f"**Action:** {selected_asset} Bullish trend me hai. Call Option (CE) Buy karein.")
        else:
            st.error("🔴 SIGNAL: BUY PUT (PE)")
            st.markdown(f"**Action:** {selected_asset} Bearish trend me hai. Put Option (PE) Buy karein.")
    else:
        st.warning("Market data load nahi ho pa raha hai. Re-try karein ya market hours ka wait karein.")

except Exception as e:
    st.error(f"Data fetch me error aaya: {e}")
