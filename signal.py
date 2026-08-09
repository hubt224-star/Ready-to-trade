import pandas as pd
import numpy as np

def generate_signals(df, short_window=9, long_window=21):
    """
    Options Trading Strategy: Exponential Moving Average (EMA) Crossover
    - Buy Call (CE) when Short EMA crosses above Long EMA
    - Buy Put (PE) when Short EMA crosses below Long EMA
    """
    # Calculate Short and Long EMAs
    df['EMA_Short'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['EMA_Long'] = df['close'].ewm(span=long_window, adjust=False).mean()

    # Generate Signal (1 = BUY CALL, -1 = BUY PUT / SHORT, 0 = HOLD)
    df['Signal'] = 0
    df['Signal'] = np.where(df['EMA_Short'] > df['EMA_Long'], 1, -1)
    
    # Identify Signal Crossover points
    df['Position'] = df['Signal'].diff()

    return df

if __name__ == "__main__":
    # Dummy Nifty / BankNifty Sample Data
    data = {
        'timestamp': pd.date_range(start='2026-08-01', periods=10, freq='5min'),
        'close': [24100, 24120, 24115, 24150, 24180, 24170, 24140, 24110, 24090, 24080]
    }
    
    df = pd.DataFrame(data)
    result = generate_signals(df)

    print("--- Strategy Signal Output ---")
    print(result[['timestamp', 'close', 'EMA_Short', 'EMA_Long', 'Position']])
