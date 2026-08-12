import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="High-Accuracy Trading Dashboard", layout="wide")

st.title("🎯 Institutional Options Signal Engine (NIFTY & SENSEX)")
st.caption("Pure Engine: EMA 9/21/50/200 + RSI + MACD + ATR (Zero Deployment Error)")

# Sidebar Settings
st.sidebar.header("⚙️ Execution Settings")
timeframe = st.sidebar.selectbox("Select Timeframe", ["5m", "15m", "1h"], index=1)
min_score = st.sidebar.slider("Min Signal Confidence Threshold (%)", 50, 90, 70)

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN"
}

# --- Pure Pandas Technical Indicators (No External TA Library Needed) ---
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

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

@st.cache_data(ttl=60)
def fetch_and_calculate_data(symbol, timeframe="15m"):
    try:
        df = yf.download(tickers=symbol, period="5d", interval=timeframe, progress=False)
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Pure Indicators Calculation
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        df['RSI'] = calculate_rsi(df['Close'], 14)
        df['ATR'] = calculate_atr(df, 14)
        
        macd_line, signal_line, macd_hist = calculate_macd(df['Close'])
        df['MACD_Hist'] = macd_hist

        return df
    except Exception as e:
        return None

def calculate_signal_score(df):
    if df is None or len(df) < 50:
        return 0, "DATA LOADING...", "NEUTRAL", 0, 0, 0, 0, 0

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = round(float(latest['Close']), 2)
    rsi = round(float(latest['RSI']), 2) if not pd.isna(latest['RSI']) else 50
    atr = round(float(latest['ATR']), 2) if not pd.isna(latest['ATR']) else 10

    bull_score = 0
    bear_score = 0

    # 1. Short-Term Crossover (25 Pts)
    if latest['EMA_9'] > latest['EMA_21']:
        bull_score += 25
    else:
        bear_score += 25

    # 2. Medium Trend (25 Pts)
    if price > latest['EMA_50']:
        bull_score += 25
    else:
        bear_score += 25

    # 3. Institutional Trend (20 Pts)
    if price > latest['EMA_200']:
        bull_score += 20
    else:
        bear_score += 20

    # 4. RSI Momentum (15 Pts)
    if 52 <= rsi <= 70:
        bull_score += 15
    elif 30 <= rsi <= 48:
        bear_score += 15

    # 5. MACD Momentum (15 Pts)
    if latest['MACD_Hist'] > 0:
        bull_score += 15
    else:
        bear_score += 15

    # Verdict
    signal = "NEUTRAL / NO CLEAR BREAKOUT ⏹️"
    trade_type = "NEUTRAL"
    sl, target = 0.0, 0.0

    if bull_score >= min_score:
        signal = f"STRONG CALL BUY (CE) 🟢 [{bull_score}% Match]"
        trade_type = "CALL"
        sl = round(price - (1.5 * atr), 2)
        target = round(price + (3.0 * atr), 2)
    elif bear_score >= min_score:
        signal = f"STRONG PUT BUY (PE) 🔴 [{bear_score}% Match]"
        trade_type = "PUT"
        sl = round(price + (1.5 * atr), 2)
        target = round(price - (3.0 * atr), 2)

    return max(bull_score, bear_score), signal, trade_type, price, rsi, atr, sl, target

def display_index_card(name, symbol):
    df = fetch_and_calculate_data(symbol, timeframe)
    
    if df is not None and not df.empty:
        score, signal, trade_type, price, rsi, atr, sl, target = calculate_signal_score(df)
        
        st.subheader(f"📌 {name}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Live Price", f"₹{price}")
        m2.metric("RSI (14)", f"{rsi}")
        m3.metric("ATR Volatility", f"₹{atr}")

        if trade_type == "CALL":
            st.success(f"**SIGNAL:** {signal}")
        elif trade_type == "PUT":
            st.error(f"**SIGNAL:** {signal}")
        else:
            st.warning(f"**SIGNAL:** {signal}")

        if sl > 0 and target > 0:
            st.markdown("##### 🛡️ Execution Risk Parameters")
            rc1, rc2 = st.columns(2)
            rc1.metric("Suggested Stop-Loss", f"₹{sl}")
            rc2.metric("Target (1:2 R:R)", f"₹{target}")

        with st.expander(f"Detailed Matrix for {name}"):
            latest = df.iloc[-1]
            st.write(f"- **EMA 9 vs 21:** {'Bullish 🟢' if latest['EMA_9'] > latest['EMA_21'] else 'Bearish 🔴'}")
            st.write(f"- **50 EMA Filter:** {'Price Above 50 EMA' if price > latest['EMA_50'] else 'Price Below 50 EMA'}")
            st.write(f"- **200 EMA Filter:** {'Price Above 200 EMA' if price > latest['EMA_200'] else 'Price Below 200 EMA'}")
            st.dataframe(df[['Close', 'EMA_9', 'EMA_21', 'EMA_50', 'RSI', 'ATR']].tail(5), use_container_width=True)
    else:
        st.error(f"{name} stream currently unavailable.")

# Main Display
col1, col2 = st.columns(2)

with col1:
    display_index_card("NIFTY 50", INDICES["NIFTY 50"])

with col2:
    display_index_card("SENSEX", INDICES["SENSEX"])
