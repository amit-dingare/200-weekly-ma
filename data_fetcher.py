"""Fetch stock data and calculate 200-week SMA proximity."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import config
from options_fetcher import get_highest_lowest_put_premiums

# yfinance 1.1.0+ uses curl_cffi internally and handles sessions automatically


def calculate_rsi(prices, period=21):
    """
    Calculate RSI using the standard Wilder's smoothing method.

    Args:
        prices (pd.Series): Series of closing prices (weekly data)
        period (int): RSI period (default 21 weeks)

    Returns:
        float: RSI value (0-100), or None if insufficient data
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


def calculate_200week_sma(ticker):
    """
    Calculate 200-week simple moving average, proximity, and 21-week RSI for a ticker.

    Args:
        ticker (str): Stock ticker symbol

    Returns:
        dict: Dictionary containing ticker, current_price, 52_week_low, sma_200, proximity, direction,
              rsi (21-week), and rsi_proximity (distance from RSI target of 20)
              Returns None if data cannot be fetched or calculated
    """
    # Retry logic with exponential backoff
    for attempt in range(config.MAX_RETRIES):
        try:
            # Download weekly data - use '10y' instead of '250wk' as yfinance doesn't support week-based periods
            # 10 years = ~520 weeks, which is more than enough for 200-week SMA
            # yfinance 1.1.0+ handles sessions and rate limiting internally via curl_cffi
            stock = yf.Ticker(ticker)
            hist = stock.history(period="10y", interval=config.DATA_INTERVAL)

            if hist.empty or len(hist) < config.SMA_PERIOD:
                print(f"Warning: Insufficient data for {ticker} (got {len(hist)} weeks, need {config.SMA_PERIOD})")
                return None

            # Calculate 200-week SMA using closing prices
            hist['SMA_200'] = hist['Close'].rolling(window=config.SMA_PERIOD).mean()

            # Get the 200-week SMA from the most recent weekly data point
            latest_weekly = hist.iloc[-1]
            sma_200 = latest_weekly['SMA_200']

            # Fetch latest daily data to get current day's opening price or last close
            # This ensures we use the most recent price available
            daily_hist = stock.history(period="5d", interval="1d")

            if daily_hist.empty:
                print(f"Warning: Could not fetch daily data for {ticker}, using weekly close")
                current_price = latest_weekly['Close']
            else:
                # Get the most recent daily data
                latest_daily = daily_hist.iloc[-1]

                # Check if we have today's opening price
                if pd.notna(latest_daily['Open']) and latest_daily['Open'] > 0:
                    current_price = latest_daily['Open']
                else:
                    # Fall back to most recent closing price
                    current_price = latest_daily['Close']

            # Calculate 52-week low and standard deviation from 1 year of daily data
            daily_hist_1y = stock.history(period="1y", interval="1d")
            if daily_hist_1y.empty:
                print(f"Warning: Could not fetch 1-year daily data for {ticker}, 52-week low and std dev will be None")
                week_52_low = None
                week_52_std_dev = None
            else:
                week_52_low = daily_hist_1y['Low'].min()
                # Calculate standard deviation of closing prices over 52 weeks
                week_52_std_dev = daily_hist_1y['Close'].std()

            # Check if SMA is valid (not NaN)
            if pd.isna(sma_200):
                print(f"Warning: Could not calculate SMA for {ticker}")
                return None

            # Calculate proximity percentage
            # Positive = above SMA, Negative = below SMA
            proximity = ((current_price - sma_200) / sma_200) * 100

            # Determine direction
            direction = "Above" if proximity > 0 else "Below"

            # Calculate 21-week RSI using weekly closing prices
            rsi = calculate_rsi(hist['Close'], period=config.RSI_PERIOD)

            # Check if RSI is valid
            if rsi is None or pd.isna(rsi):
                print(f"Warning: Could not calculate RSI for {ticker}")
                return None

            # Calculate proximity to RSI target (20)
            rsi_proximity = abs(rsi - config.RSI_TARGET)

            return {
                'ticker': ticker,
                'current_price': round(current_price, 2),
                '52_week_low': round(week_52_low, 2) if week_52_low and pd.notna(week_52_low) else None,
                '52_week_std_dev': round(week_52_std_dev, 2) if week_52_std_dev and pd.notna(week_52_std_dev) else None,
                'sma_200': round(sma_200, 2),
                'proximity_pct': round(proximity, 2),
                'abs_proximity': round(abs(proximity), 2),
                'direction': direction,
                'rsi': round(rsi, 2),
                'rsi_proximity': round(rsi_proximity, 2),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except json.JSONDecodeError as e:
            # Handle JSON parsing errors from Yahoo Finance API
            if attempt < config.MAX_RETRIES - 1:
                wait_time = config.RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                print(f"JSON decode error for {ticker}, retrying in {wait_time}s (attempt {attempt + 1}/{config.MAX_RETRIES})")
                time.sleep(wait_time)
                continue
            else:
                print(f"Failed to fetch {ticker} after {config.MAX_RETRIES} attempts: JSON decode error")
                return None

        except Exception as e:
            # Handle other errors
            if attempt < config.MAX_RETRIES - 1:
                wait_time = config.RETRY_DELAY * (2 ** attempt)
                print(f"Error fetching {ticker}, retrying in {wait_time}s (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                time.sleep(wait_time)
                continue
            else:
                print(f"Failed to fetch {ticker} after {config.MAX_RETRIES} attempts: {e}")
                return None

    return None


def get_top_stocks_near_sma(tickers, top_n=5):
    """
    Get top N stocks sorted by their proximity to 200-week SMA, with RSI proximity as tiebreaker.
    Fetches options data for top TOP_N_OPTIONS stocks only.

    Args:
        tickers (list): List of ticker symbols
        top_n (int): Number of top stocks to return

    Returns:
        pd.DataFrame: DataFrame with top N stocks sorted by:
                      1) Proximity % to 200-week SMA (primary - most negative to most positive)
                      2) Proximity to RSI target of 20 (secondary/tiebreaker - closest to 20 first)
                      Includes options data for top TOP_N_OPTIONS stocks
    """
    results = []
    total = len(tickers)

    print(f"Processing {total} tickers...")

    for i, ticker in enumerate(tickers, 1):
        if i % 50 == 0:
            print(f"Progress: {i}/{total} tickers processed")

        result = calculate_200week_sma(ticker)
        if result:
            results.append(result)

        # Add delay between API calls to avoid rate limiting
        # Skip delay for the last ticker
        if i < total:
            time.sleep(config.REQUEST_DELAY)

    print(f"\nSuccessfully processed {len(results)} out of {total} tickers")

    # Convert to DataFrame
    df = pd.DataFrame(results)

    if df.empty:
        print("Warning: No valid data retrieved")
        return df

    # Sort by:
    # 1) Proximity % to 200-week SMA (primary - most negative to most positive)
    # 2) RSI proximity to target of 20 (secondary - tiebreaker, closest to 20 first)
    df_sorted = df.sort_values(['proximity_pct', 'rsi_proximity'], ascending=[True, True])

    # Fetch options data for top TOP_N_OPTIONS stocks
    top_n_options = min(config.TOP_N_OPTIONS, len(df_sorted))
    if top_n_options > 0:
        print(f"\nFetching options data for top {top_n_options} stocks...")

        for idx in range(top_n_options):
            row = df_sorted.iloc[idx]
            ticker = row['ticker']
            current_price = row['current_price']
            sma_200 = row['sma_200']
            week_52_low = row['52_week_low']
            week_52_std_dev = row['52_week_std_dev']

            print(f"  Fetching options for {ticker} (rank {idx + 1})...")

            options_data = get_highest_lowest_put_premiums(ticker, current_price, sma_200, week_52_low, week_52_std_dev)

            if options_data:
                # Merge options data into the row
                for key, value in options_data.items():
                    df_sorted.loc[df_sorted['ticker'] == ticker, key] = value

            # Add delay for options API calls
            if idx < top_n_options - 1:
                time.sleep(config.OPTIONS_DELAY)

        print(f"Options data fetched for {top_n_options} stocks")

    # Return top N
    return df_sorted.head(top_n)


if __name__ == "__main__":
    # Test with a few tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    print("Testing with sample tickers...")
    results = get_top_stocks_near_sma(test_tickers, top_n=5)
    print("\nResults:")
    print(results)
