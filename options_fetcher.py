"""Fetch options data for stocks and ETFs."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import calendar
import time
import config
from polygon_options_historical import enrich_options_with_7day_history


def get_next_monthly_expiries(n=2):
    """
    Get the next N monthly option expiration dates (3rd Friday of each month).

    Args:
        n (int): Number of monthly expiries to return (default: 2)

    Returns:
        list: List of datetime objects representing expiration dates
    """
    expiries = []
    today = datetime.now()
    current_month = today.month
    current_year = today.year

    # Start from current month
    month = current_month
    year = current_year

    while len(expiries) < n:
        # Find 3rd Friday of the month
        # Get first day of month
        first_day = datetime(year, month, 1)

        # Find first Friday (weekday 4 = Friday)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)

        # 3rd Friday is 2 weeks after first Friday
        third_friday = first_friday + timedelta(weeks=2)

        # Only include if it's in the future
        if third_friday > today:
            expiries.append(third_friday)

        # Move to next month
        month += 1
        if month > 12:
            month = 1
            year += 1

    return expiries[:n]


def get_put_options_for_strike_range(ticker, expiry_date, max_strike):
    """
    Fetch put options with strike prices below max_strike for a given expiry.

    Args:
        ticker (str): Stock/ETF ticker symbol
        expiry_date (datetime): Option expiration date
        max_strike (float): Maximum strike price (exclusive upper bound)

    Returns:
        pd.DataFrame: DataFrame of put options, or None if unavailable
    """
    try:
        stock = yf.Ticker(ticker)

        # Format expiry date as string (YYYY-MM-DD)
        expiry_str = expiry_date.strftime('%Y-%m-%d')

        # Get available expiration dates
        available_expiries = stock.options

        if not available_expiries or len(available_expiries) == 0:
            return None

        # Find the closest matching expiry date
        # Convert available expiries to datetime for comparison
        expiry_dates = [datetime.strptime(exp, '%Y-%m-%d') for exp in available_expiries]

        # Find expiry within ±7 days of target date (to handle slight variations)
        matching_expiry = None
        min_diff = timedelta(days=365)  # Start with large difference

        for i, exp_date in enumerate(expiry_dates):
            diff = abs(exp_date - expiry_date)
            if diff < min_diff and diff <= timedelta(days=7):
                min_diff = diff
                matching_expiry = available_expiries[i]

        if not matching_expiry:
            # If no close match, try to find monthly expiry in that month
            target_month = expiry_date.month
            target_year = expiry_date.year
            for exp in available_expiries:
                exp_dt = datetime.strptime(exp, '%Y-%m-%d')
                if exp_dt.month == target_month and exp_dt.year == target_year:
                    matching_expiry = exp
                    break

        if not matching_expiry:
            return None

        # Get option chain for the matched expiry
        option_chain = stock.option_chain(matching_expiry)
        puts = option_chain.puts

        if puts.empty:
            return None

        # Filter for strikes below max_strike
        puts_filtered = puts[puts['strike'] < max_strike].copy()

        # Add the actual expiry date used
        puts_filtered['expiry_date'] = matching_expiry

        return puts_filtered if not puts_filtered.empty else None

    except Exception as e:
        print(f"  Warning: Could not fetch options for {ticker} expiry {expiry_date.strftime('%Y-%m-%d')}: {e}")
        return None


def get_highest_lowest_put_premiums(ticker, current_price, sma_200, week_52_low=None, week_52_std_dev=None):
    """
    Get highest and lowest put premiums for next 3 monthly expiries.

    Only considers puts with strike < min(current_price, sma_200).
    Also fetches put with highest strike below 52-week low if week_52_low is provided.
    Also fetches put with highest strike below (52-week low - 1 std dev) if both week_52_low and week_52_std_dev are provided.
    Returns highest and lowest strike puts (by strike price) and their premiums.

    Args:
        ticker (str): Stock/ETF ticker symbol
        current_price (float): Current stock/ETF price
        sma_200 (float): 200-week simple moving average
        week_52_low (float, optional): 52-week low price. If provided, also fetches put below this level.
        week_52_std_dev (float, optional): 52-week standard deviation. If provided along with week_52_low, also fetches put below (52-week low - 1 std dev).

    Returns:
        dict: Dictionary with options data for 3 monthly expiries, or None if unavailable
              Format: {
                  'month1_name_year_expiry': 'YYYY-MM-DD',
                  'month1_name_year_highest_strike': float,
                  'month1_name_year_highest_put_price': float,
                  'month1_name_year_lowest_strike': float,
                  'month1_name_year_lowest_put_price': float,
                  'month1_name_year_below_52wk_low_strike': float,  # if week_52_low provided
                  'month1_name_year_below_52wk_low_put_price': float,  # if week_52_low provided
                  ... (same for month2)
              }
    """
    try:
        # Calculate max strike: min(current_price, sma_200)
        max_strike = min(current_price, sma_200)

        # Get next 3 monthly expiries
        expiries = get_next_monthly_expiries(n=3)

        if len(expiries) < 3:
            print(f"  Warning: Could not calculate 3 monthly expiries for {ticker}")
            return None

        result = {}

        for i, expiry in enumerate(expiries, 1):
            # Get month name and year for column naming (e.g., "april_2026")
            month_name = expiry.strftime('%B').lower()  # e.g., "april"
            year = expiry.strftime('%Y')  # e.g., "2026"
            prefix = f"{month_name}_{year}"

            # Fetch put options for this expiry
            puts = get_put_options_for_strike_range(ticker, expiry, max_strike)

            if puts is None or puts.empty:
                print(f"  Warning: No put options found for {ticker} {month_name} {year} with strike < {max_strike:.2f}")
                # Set all values to None for this expiry
                result[f"{prefix}_expiry"] = None
                result[f"{prefix}_highest_strike"] = None
                result[f"{prefix}_highest_put_price"] = None
                result[f"{prefix}_lowest_strike"] = None
                result[f"{prefix}_lowest_put_price"] = None
                continue

            # Get actual expiry date used
            actual_expiry = puts['expiry_date'].iloc[0]
            result[f"{prefix}_expiry"] = actual_expiry

            # Sort by strike to find highest and lowest
            puts_sorted = puts.sort_values('strike')

            lowest_strike_put = puts_sorted.iloc[0]
            highest_strike_put = puts_sorted.iloc[-1]

            # Get premium (prefer lastPrice, fallback to bid/ask midpoint)
            def get_premium(row):
                if pd.notna(row.get('lastPrice')) and row.get('lastPrice', 0) > 0:
                    return row['lastPrice']
                elif pd.notna(row.get('bid')) and pd.notna(row.get('ask')):
                    return (row['bid'] + row['ask']) / 2
                elif pd.notna(row.get('bid')):
                    return row['bid']
                elif pd.notna(row.get('ask')):
                    return row['ask']
                return None

            lowest_premium = get_premium(lowest_strike_put)
            highest_premium = get_premium(highest_strike_put)

            # Store results
            result[f"{prefix}_highest_strike"] = round(highest_strike_put['strike'], 2)
            result[f"{prefix}_highest_put_price"] = round(highest_premium, 2) if highest_premium else None
            result[f"{prefix}_lowest_strike"] = round(lowest_strike_put['strike'], 2)
            result[f"{prefix}_lowest_put_price"] = round(lowest_premium, 2) if lowest_premium else None

            # Fetch put with highest strike below 52-week low (if week_52_low is provided)
            if week_52_low and pd.notna(week_52_low):
                puts_below_52wk = get_put_options_for_strike_range(ticker, expiry, week_52_low)

                if puts_below_52wk is not None and not puts_below_52wk.empty:
                    # Sort by strike and get the highest strike below 52-week low
                    puts_below_52wk_sorted = puts_below_52wk.sort_values('strike')
                    highest_below_52wk_put = puts_below_52wk_sorted.iloc[-1]

                    below_52wk_premium = get_premium(highest_below_52wk_put)

                    result[f"{prefix}_below_52wk_low_strike"] = round(highest_below_52wk_put['strike'], 2)
                    result[f"{prefix}_below_52wk_low_put_price"] = round(below_52wk_premium, 2) if below_52wk_premium else None
                else:
                    print(f"  Warning: No put options found for {ticker} {month_name} {year} with strike < {week_52_low:.2f} (52-week low)")
                    result[f"{prefix}_below_52wk_low_strike"] = None
                    result[f"{prefix}_below_52wk_low_put_price"] = None
            else:
                # If 52-week low not provided, set to None
                result[f"{prefix}_below_52wk_low_strike"] = None
                result[f"{prefix}_below_52wk_low_put_price"] = None

            # Fetch put with highest strike below (52-week low - 1 std dev) (if both week_52_low and week_52_std_dev are provided)
            if week_52_low and pd.notna(week_52_low) and week_52_std_dev and pd.notna(week_52_std_dev):
                # Calculate threshold: 52-week low minus 1 standard deviation
                threshold_minus_1std = week_52_low - week_52_std_dev
                puts_below_minus_1std = get_put_options_for_strike_range(ticker, expiry, threshold_minus_1std)

                if puts_below_minus_1std is not None and not puts_below_minus_1std.empty:
                    # Sort by strike and get the highest strike below threshold
                    puts_below_minus_1std_sorted = puts_below_minus_1std.sort_values('strike')
                    highest_below_minus_1std_put = puts_below_minus_1std_sorted.iloc[-1]

                    below_minus_1std_premium = get_premium(highest_below_minus_1std_put)

                    result[f"{prefix}_below_52wk_minus_1std_strike"] = round(highest_below_minus_1std_put['strike'], 2)
                    result[f"{prefix}_below_52wk_minus_1std_put_price"] = round(below_minus_1std_premium, 2) if below_minus_1std_premium else None
                else:
                    print(f"  Warning: No put options found for {ticker} {month_name} {year} with strike < {threshold_minus_1std:.2f} (52-week low - 1 std dev)")
                    result[f"{prefix}_below_52wk_minus_1std_strike"] = None
                    result[f"{prefix}_below_52wk_minus_1std_put_price"] = None
            else:
                # If 52-week low or std dev not provided, set to None
                result[f"{prefix}_below_52wk_minus_1std_strike"] = None
                result[f"{prefix}_below_52wk_minus_1std_put_price"] = None

        # Enrich with 7-day historical data from Massive.com (Polygon.io) if enabled
        if config.FETCH_HISTORICAL_OPTIONS:
            print(f"  Enriching {ticker} options with 7-day historical data...")
            result = enrich_options_with_7day_history(result, ticker)
        else:
            print(f"  Skipping historical data (FETCH_HISTORICAL_OPTIONS=False)")

        return result

    except Exception as e:
        print(f"  Error fetching options for {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Test the functions
    print("Testing options fetcher...")
    print("=" * 80)

    # Test 1: Get next monthly expiries
    print("\nTest 1: Next 3 monthly expiries")
    expiries = get_next_monthly_expiries(n=3)
    for i, exp in enumerate(expiries, 1):
        print(f"  Month {i}: {exp.strftime('%Y-%m-%d (%B %Y)')}")

    # Test 2: Test with AAPL (liquid stock with options)
    print("\n" + "=" * 80)
    print("Test 2: AAPL options")
    print("=" * 80)

    # Get current price and mock SMA
    aapl = yf.Ticker("AAPL")
    hist = aapl.history(period="5d")
    current_price = hist['Close'].iloc[-1]
    sma_200 = current_price * 0.95  # Mock SMA slightly below current price

    print(f"Current Price: ${current_price:.2f}")
    print(f"Mock SMA 200: ${sma_200:.2f}")
    print(f"Max Strike: ${min(current_price, sma_200):.2f}")

    options_data = get_highest_lowest_put_premiums("AAPL", current_price, sma_200)

    if options_data:
        print("\nOptions Data:")
        for key, value in options_data.items():
            print(f"  {key}: {value}")
    else:
        print("\nNo options data available")

    # Test 3: Test with a stock that may not have options
    print("\n" + "=" * 80)
    print("Test 3: Testing with potential non-options ticker")
    print("=" * 80)

    test_ticker = "VTI"  # Popular ETF, likely has options
    etf = yf.Ticker(test_ticker)
    hist = etf.history(period="5d")
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        sma_200 = current_price * 0.98
        print(f"{test_ticker} Current Price: ${current_price:.2f}")
        print(f"Mock SMA 200: ${sma_200:.2f}")

        options_data = get_highest_lowest_put_premiums(test_ticker, current_price, sma_200)

        if options_data:
            print("\nOptions Data:")
            for key, value in options_data.items():
                print(f"  {key}: {value}")
        else:
            print("\nNo options data available")
