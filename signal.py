import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

# Streamlit Page Setup
st.set_page_config(page_title="Institutional Options Engine", layout="wide")

st.title("⚡ Institutional Options Signal Engine (NIFTY & SENSEX)")
st.caption("Advanced Confluence Engine: Trend + Momentum + Bollinger Squeeze + Scoring System")

# Sidebar
st.sidebar.header("⚙️ Execution Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h"], index=1)
min_score = st.sidebar.slider("Min Signal Confidence Threshold (%)", 50, 90, 75)

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN"
}

@st.cache_data(ttl=60)
def fetch_advanced_data(symbol, timeframe="15m"):
    try:
        df = yf.download(tickers=symbol, period="5d", interval=timeframe, progress=False)
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 1. Trend Indicators
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        df['EMA_200'] = ta.ema(df['Close'], length=200)

        # 2. Momentum Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
            df['MACD_Hist'] = macd['MACDh_12_26_9']

        # 3. Volatility & Breakout (Bollinger Bands)
        bbands = ta.bbands(df['Close'], length=20, std=2)
        if bbands is not None:
            df['BBL'] = bbands['BBL_20_2.0']
            df['BBU'] = bbands['BBU_20_2.0']
            df['BBM'] = bbands['BBM_20_2.0']
            df['Bandwidth'] = (df['BBU'] - df['BBL']) / df['BBM']

        # 4. Volatility / Stoploss
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

        return df
    except Exception as e:
        return None

def calculate_confidence_score(df):
    if df is None or len(df) < 50:
        return 0, "NO DATA", "NEUTRAL", 0, 0, 0, 0, 0

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = round(latest['Close'], 2)
    rsi = round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else 50
    atr = round(latest['ATR'], 2) if not pd.isna(latest['ATR']) else 10

    bull_score = 0
    bear_score = 0

    # Test 1: Trend Alignment (25 Points)
    if price > latest['EMA_50'] and latest['EMA_20'] > latest['EMA_50']:
        bull_score += 25
    elif price < latest['EMA_50'] and latest['EMA_20'] < latest['EMA_50']:
        bear_score += 25

    # Test 2: Major Trend / Institutional Direction (20 Points)
    if price > latest['EMA_200']:
        bull_score += 20
    else:
        bear_score += 20

    # Test 3: RSI Momentum Zone (20 Points)
    if 55 <= rsi <= 70:
        bull_score += 20
    elif 30 <= rsi <= 45:
        bear_score += 20

    # Test 4: MACD Histogram Acceleration (20 Points)
    if latest['MACD_Hist'] > 0 and latest['MACD_Hist'] > prev['MACD_Hist']:
        bull_score += 20
    elif latest['MACD_Hist'] < 0 and latest['MACD_Hist'] < prev['MACD_Hist']:
        bear_score += 20

    # Test 5: Volatility / Bollinger Expansion (15 Points)
    if latest['Bandwidth'] > prev['Bandwidth'] and price > latest['BBU']:
        bull_score += 15
    elif latest['Bandwidth'] > prev['Bandwidth'] and price < latest['BBL']:
        bear_score += 15

    # Final Signal Determination
    signal = "NEUTRAL (WAIT FOR BREAKOUT) ⏳"
    confidence = max(bull_score, bear_score)
    trade_type = "NEUTRAL"
    sl, target = 0.0, 0.0

    if bull_score >= min_score:
        signal = f"STRONG CALL BUY (CE) 🔥 [{bull_score}% Match]"
        trade_type = "CALL"
        sl = round(price - (1.5 * atr), 2)
        target = round(price + (3.0 * atr), 2)
    elif bear_score >= min_score:
        signal = f"STRONG PUT BUY (PE) ⚡ [{bear_score}% Match]"
        trade_type = "PUT"
        sl = round(price + (1.5 * atr), 2)
        target = round(price - (3.0 * atr), 2)

    return confidence, signal, trade_type, price, rsi, atr, sl, target

def render_index_card(name, symbol):
    df = fetch_advanced_data(symbol, timeframe)
    
    if df is not None and not df.empty:
        confidence, signal, trade_type, price, rsi, atr, sl, target = calculate_confidence_score(df)
        
        st.subheader(f"📌 {name}")
        
        # Top Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Live Price", f"₹{price}")
        m2.metric("RSI (14)", f"{rsi}")
        m3.metric("ATR Volatility", f"₹{atr}")

        # Signal Display Box
        if trade_type == "CALL":
            st.success(f"**SIGNAL:** {signal}")
        elif trade_type == "PUT":
            st.error(f"**SIGNAL:** {signal}")
        else:
            st.warning(f"**SIGNAL:** {signal}")

        # Risk Management Card
        if sl > 0 and target > 0:
            st.markdown("##### 🛡️ Trade Execution & Risk Management")
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Suggested Stop-Loss", f"₹{sl}")
            rc2.metric("Target (1:2 R:R)", f"₹{target}")
            rc3.metric("Risk-Reward Ratio", "1 : 2.0")

        # Deep Breakdown Expander
        with st.expander("🔍 View Technical Indicator Matrix"):
            latest = df.iloc[-1]
            st.write(f"- **20 EMA vs 50 EMA:** {'Bullish 🟢' if latest['EMA_20'] > latest['EMA_50'] else 'Bearish 🔴'}")
            st.write(f"- **200 EMA Trend:** {'Above 200 EMA (Uptrend)' if price > latest['EMA_200'] else 'Below 200 EMA (Downtrend)'}")
            st.write(f"- **MACD Histogram:** {'Positive Acceleration 🟢' if latest['MACD_Hist'] > 0 else 'Negative Acceleration 🔴'}")
            st.dataframe(df[['Close', 'EMA_20', 'EMA_50', 'EMA_200', 'RSI', 'MACD', 'ATR']].tail(5), use_container_width=True)
    else:
        st.error(f"{name} data stream connection failed.")

# Main Layout
col_nifty, col_sensex = st.columns(2)

with col_nifty:
    render_index_card("NIFTY 50", INDICES["NIFTY 50"])

with col_sensex:
    render_index_card("SENSEX", INDICES["SENSEX"])
