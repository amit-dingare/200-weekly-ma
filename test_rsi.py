"""Test RSI calculation for FISV ticker."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_rsi(prices, period=21):
    """
    Calculate RSI using the standard Wilder's smoothing method.

    Args:
        prices (pd.Series): Series of closing prices
        period (int): RSI period (default 21)

    Returns:
        float: RSI value (0-100)
    """
    if len(prices) < period + 1:
        return None

    # Calculate price changes
    deltas = prices.diff()

    # Separate gains and losses
    gains = deltas.where(deltas > 0, 0)
    losses = -deltas.where(deltas < 0, 0)

    # Calculate initial averages using SMA for first value
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()

    # Apply Wilder's smoothing (exponential moving average)
    for i in range(period, len(prices)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]


def test_ticker(ticker, period=21):
    """Test RSI calculation for a specific ticker."""
    print(f"Testing RSI calculation for {ticker}")
    print("=" * 60)

    try:
        # Fetch daily data - get extra to ensure we have enough for RSI calculation
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo", interval="1d")

        if hist.empty:
            print(f"Error: No data retrieved for {ticker}")
            return

        print(f"Retrieved {len(hist)} days of data")
        print(f"Date range: {hist.index[0].date()} to {hist.index[-1].date()}")
        print(f"\nLast 5 closing prices:")
        print(hist['Close'].tail())

        # Calculate RSI
        rsi = calculate_rsi(hist['Close'], period=period)

        print(f"\n{'=' * 60}")
        print(f"{period}-day RSI for {ticker}: {rsi:.2f}")
        print(f"{'=' * 60}")

        # Show interpretation
        if rsi < 30:
            print("Interpretation: OVERSOLD (RSI < 30)")
        elif rsi > 70:
            print("Interpretation: OVERBOUGHT (RSI > 70)")
        else:
            print("Interpretation: NEUTRAL (30 <= RSI <= 70)")

        print(f"\nProximity to RSI=20: {abs(rsi - 20):.2f}")

        # Get current price
        current_price = hist['Close'].iloc[-1]
        print(f"\nCurrent price: ${current_price:.2f}")
        print(f"Last updated: {hist.index[-1].strftime('%Y-%m-%d %H:%M:%S %Z')}")

        return rsi

    except Exception as e:
        print(f"Error testing {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Test with FISV
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    rsi = test_ticker("FISV", period=21)

    # Test with a few more tickers for comparison
    print("\n\n" + "=" * 60)
    print("Testing additional tickers for comparison:")
    print("=" * 60 + "\n")

    for ticker in ["AAPL", "MSFT"]:
        print()
        test_ticker(ticker, period=21)
        print()
