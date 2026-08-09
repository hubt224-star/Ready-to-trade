import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Options Trading Dashboard", layout="wide")

st.title("📈 Options Trading Signal Dashboard")

# Sidebar inputs
st.sidebar.header("Strategy Settings")
short_window = st.sidebar.slider("Short EMA Period", 5, 20, 9)
long_window = st.sidebar.slider("Long EMA Period", 15, 50, 21)

# Sample Data Generator
@st.cache_data
def load_data():
    dates = pd.date_range(start='2026-08-01', periods=50, freq='15min')
    prices = 24000 + np.random.randn(50).cumsum() * 25
    return pd.DataFrame({'timestamp': dates, 'close': prices})

df = load_data().copy()

# Strategy Calculation
df['EMA_Short'] = df['close'].ewm(span=short_window, adjust=False).mean()
df['EMA_Long'] = df['close'].ewm(span=long_window, adjust=False).mean()

# Latest Signal Alert
latest_short = df['EMA_Short'].iloc[-1]
latest_long = df['EMA_Long'].iloc[-1]

st.subheader("Current Market Status")
col1, col2, col3 = st.columns(3)
col1.metric("Latest Price", f"₹{df['close'].iloc[-1]:.2f}")
col2.metric(f"Short EMA ({short_window})", f"₹{latest_short:.2f}")
col3.metric(f"Long EMA ({long_window})", f"₹{latest_long:.2f}")

if latest_short > latest_long:
    st.success("🔥 SIGNAL: **BUY CALL (CE)** - Short EMA crossed above Long EMA")
else:
    st.error("🔻 SIGNAL: **BUY PUT (PE)** - Short EMA crossed below Long EMA")

# Price & EMA Chart
st.subheader("Price & EMA Chart")
st.line_chart(df.set_index('timestamp')[['close', 'EMA_Short', 'EMA_Long']])

# Raw Data Table
with st.expander("View Raw Signal Data"):
    st.dataframe(df)
