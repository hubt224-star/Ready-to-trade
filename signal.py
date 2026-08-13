import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="Institutional Signal Engine", page_icon="🎯", layout="centered")

st.title("🎯 Precision Signal Engine")
st.caption("Auto Strike Price, Entry, Target & Stop-Loss Calculator")

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
        "Nifty 50": {"ticker": "^NSEI", "step": 50},
        "Bank Nifty": {"ticker": "^NSEBANK", "step": 100},
        "Fin Nifty": {"ticker": "NIFTY_FIN_SERVICE.NS", "step": 50},
        "BSE Sensex": {"ticker": "BSESN", "step": 100},
        "BSE Bankex": {"ticker": "BSE-BANKEX", "step": 100}
    },
    "Commodities (MCX)": {
        "Crude Oil": {"ticker": "CL=F", "step": 50},
        "Gold": {"ticker": "GC=F", "step": 100},
        "Silver": {"ticker": "SI=F", "step": 500},
        "Natural Gas": {"ticker": "NG=F", "step": 5}
    },
    "Equity Stocks": {
        "Reliance": {"ticker": "RELIANCE.NS", "step": 20},
        "TCS": {"ticker": "TCS.NS", "step": 50},
        "HDFC Bank": {"ticker": "HDFCBANK.NS", "step": 20},
        "Tata Motors": {"ticker": "TATAMOTORS.NS", "step": 10},
        "State Bank of India": {"ticker": "SBIN.NS", "step": 10}
    }
}

with col2:
    selected_asset = st.selectbox("Select Asset", list(symbols_data[category].keys()))

asset_info = symbols_data[category][selected_asset]
ticker_symbol = asset_info["ticker"]
strike_step = asset_info["step"]

# -------------------------------------------------------------
# 2. Indicator Calculation Logic
# -------------------------------------------------------------
def calculate_indicators(df):
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD Calculation
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # ATR (Average True Range for Stop Loss calculation)
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.maximum(
            abs(df['High'] - df['Close'].shift(1)),
            abs(df['Low'] - df['Close'].shift(1))
        )
    )
    df['ATR'] = df['TR'].rolling(window=14).mean()

    return df

# Helper Function to get ATM Strike Price
def get_atm_strike(price, step):
    return round(price / step) * step

# -------------------------------------------------------------
# 3. Data Fetching & Trade Execution Details
# -------------------------------------------------------------
try:
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period="5d", interval="5m")

    if len(df) > 30:
        df = calculate_indicators(df)
        
        latest = df.iloc[-1]
        live_price = latest['Close']
        atr = latest['ATR'] if not np.isnan(latest['ATR']) else (live_price * 0.005)

        bullish_score = 0
        bearish_score = 0

        if latest['EMA_9'] > latest['EMA_21']: bullish_score += 1
        else: bearish_score += 1

        if 50 < latest['RSI'] < 70: bullish_score += 1
        elif 30 < latest['RSI'] < 50: bearish_score += 1

        if latest['MACD'] > latest['Signal_Line']: bullish_score += 1
        else: bearish_score += 1

        st.markdown("---")
        st.metric(label=f"Live Spot Price ({selected_asset})", value=f"{live_price:,.2f}")

        # ATM Strike Price Calculation
        atm_strike = get_atm_strike(live_price, strike_step)

        st.markdown("---")

        # ------------------- BULLISH SIGNAL (BUY CALL) -------------------
        if bullish_score >= 2:
            st.success(f"🟢 BUY SIGNAL: CALL OPTION (CE) - {selected_asset}")
            
            strike_name = f"{int(atm_strike)} CE" if category != "Commodities (MCX)" else f"{selected_asset} BUY FUT / LONG"
            entry_spot = live_price
            target_spot = live_price + (1.5 * atr)
            sl_spot = live_price - (0.8 * atr)

            st.subheader(f"📌 Recommended Strike: **{strike_name}**")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📍 Spot Entry", f"{entry_spot:,.2f}")
            c2.metric("🎯 Target Price", f"{target_spot:,.2f}", delta=f"+{1.5*atr:.2f}")
            c3.metric("🛑 Stop Loss (SL)", f"{sl_spot:,.2f}", delta=f"-{0.8*atr:.2f}")

            st.info("💡 **Trade Tip:** Direct Index me Entry level par Aati hi Position banayein. Premium me Target ~15-20% aur SL ~8-10% rakhein.")

        # ------------------- BEARISH SIGNAL (BUY PUT) -------------------
        elif bearish_score >= 2:
            st.error(f"🔴 BUY SIGNAL: PUT OPTION (PE) - {selected_asset}")
            
            strike_name = f"{int(atm_strike)} PE" if category != "Commodities (MCX)" else f"{selected_asset} SELL FUT / SHORT"
            entry_spot = live_price
            target_spot = live_price - (1.5 * atr)
            sl_spot = live_price + (0.8 * atr)

            st.subheader(f"📌 Recommended Strike: **{strike_name}**")

            c1, c2, c3 = st.columns(3)
            c1.metric("📍 Spot Entry", f"{entry_spot:,.2f}")
            c2.metric("🎯 Target Price", f"{target_spot:,.2f}", delta=f"-{1.5*atr:.2f}")
            c3.metric("🛑 Stop Loss (SL)", f"{sl_spot:,.2f}", delta=f"+{0.8*atr:.2f}")

            st.info("💡 **Trade Tip:** Target hitting par profit trailing SL ke sath book karein.")

        else:
            st.warning("⚠️ NEUTRAL / NO TRADE ZONE")
            st.write("Market range-bound hai. Exact signal nahi ban raha, trade avoid karein.")

    else:
        st.warning("Data fetch karne me problem ho rahi hai. Market Timings check karein.")

except Exception as e:
    st.error(f"Error: {e}")
