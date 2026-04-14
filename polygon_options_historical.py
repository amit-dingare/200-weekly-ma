"""Fetch historical options data from Massive.com (formerly Polygon.io) for 7-day premium benchmarking."""
import requests
import os
from datetime import datetime, timedelta
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

# Try both base URLs since Massive.com is a rebrand of Polygon.io
# The API structure appears to be the same
POLYGON_BASE_URLS = [
    "https://api.polygon.io",  # Original
    "https://api.massive.com"   # New brand
]


def format_occ_ticker(underlying, expiry_date, option_type, strike):
    """
    Convert option parameters to OCC (Options Clearing Corporation) format.

    Format: O:{underlying}{YYMMDD}{C/P}{strike_padded}
    Example: O:AAPL260320P00235000 = AAPL Put expiring Mar 20, 2026, strike 235

    Args:
        underlying (str): Stock/ETF ticker (e.g., "AAPL")
        expiry_date (str): Expiration date in YYYY-MM-DD format
        option_type (str): "C" for Call, "P" for Put
        strike (float): Strike price (e.g., 235.0)

    Returns:
        str: OCC-formatted options ticker
    """
    # Parse expiry date
    exp_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
    exp_str = exp_dt.strftime('%y%m%d')  # YYMMDD format

    # Format strike: 8 digits with 3 decimal places, padded with zeros
    # Example: 235.0 -> 00235000, 1234.5 -> 01234500
    strike_int = int(strike * 1000)
    strike_str = f"{strike_int:08d}"

    # Construct OCC ticker
    occ_ticker = f"O:{underlying.upper()}{exp_str}{option_type.upper()}{strike_str}"

    return occ_ticker


def get_7day_options_history(occ_ticker, days=7):
    """
    Fetch last N days of EOD (End of Day) data for an options contract from Massive.com API.

    Uses endpoint: GET /v2/aggs/ticker/{optionsTicker}/range/{multiplier}/{timespan}/{from}/{to}

    Args:
        occ_ticker (str): OCC-formatted options ticker (e.g., "O:AAPL260320P00235000")
        days (int): Number of calendar days to look back (default: 7)

    Returns:
        dict: Statistics including 7day_high, 7day_low, 7day_avg, 7day_stdev
              Returns None if insufficient data or error
    """
    if not POLYGON_API_KEY:
        print("  ERROR: POLYGON_API_KEY not found in environment variables")
        return None

    try:
        # Calculate date range (7 calendar days back to today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')

        # Massive.com (Polygon.io) aggregates endpoint for daily bars
        # /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        endpoint = f"/v2/aggs/ticker/{occ_ticker}/range/1/day/{from_date}/{to_date}"

        params = {
            'apiKey': POLYGON_API_KEY,
            'adjusted': 'true',  # Adjust for splits/dividends
            'sort': 'asc'
        }

        # Try both base URLs
        response = None
        for base_url in POLYGON_BASE_URLS:
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code in [200, 429]:
                    break  # Found working URL
            except:
                continue

        if not response:
            print(f"  ERROR: Could not connect to Massive.com API")
            return None

        if response.status_code == 429:
            print(f"  WARNING: Rate limit hit for {occ_ticker}. Waiting...")
            time.sleep(15)  # Wait 15 seconds and retry once
            response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  WARNING: API returned status {response.status_code} for {occ_ticker}")
            return None

        data = response.json()

        # Check if we have results
        if data.get('resultsCount', 0) == 0 or 'results' not in data:
            print(f"  WARNING: No historical data found for {occ_ticker}")
            return None

        results = data['results']

        # Extract close prices from daily bars
        # results format: [{'o': open, 'h': high, 'l': low, 'c': close, 'v': volume, 'vw': vwap, 't': timestamp}, ...]
        close_prices = [bar['c'] for bar in results if 'c' in bar and bar['c'] > 0]

        if len(close_prices) == 0:
            print(f"  WARNING: No valid close prices for {occ_ticker}")
            return None

        # Calculate statistics
        close_array = np.array(close_prices)

        stats = {
            '7day_high': round(float(np.max(close_array)), 2),
            '7day_low': round(float(np.min(close_array)), 2),
            '7day_avg': round(float(np.mean(close_array)), 2),
            '7day_stdev': round(float(np.std(close_array)), 2),
            'data_points': len(close_prices)
        }

        return stats

    except requests.exceptions.Timeout:
        print(f"  ERROR: Timeout fetching data for {occ_ticker}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed for {occ_ticker}: {e}")
        return None
    except Exception as e:
        print(f"  ERROR: Failed to process {occ_ticker}: {e}")
        return None


def get_7day_stats_for_put(ticker, expiry_date, strike, current_price):
    """
    Get 7-day statistics for a put option and calculate benchmarking metrics.

    Args:
        ticker (str): Stock/ETF ticker (e.g., "AAPL")
        expiry_date (str): Expiration date in YYYY-MM-DD format
        strike (float): Strike price
        current_price (float): Current premium price from yfinance

    Returns:
        dict: Statistics including 7day metrics and pct_vs_7day_high
              Returns None if data unavailable
    """
    # Convert to OCC format
    occ_ticker = format_occ_ticker(ticker, expiry_date, "P", strike)

    # Get historical data from Massive.com
    stats = get_7day_options_history(occ_ticker, days=7)

    if not stats:
        return None

    # Calculate percentage vs 7-day high (key metric for selling decision)
    # If current is 95% of 7-day high, it's near the top (good time to sell)
    # If current is 50% of 7-day high, it's cheap (bad time to sell)
    if stats['7day_high'] > 0 and current_price is not None:
        pct_vs_high = round((current_price / stats['7day_high']) * 100, 1)
    else:
        pct_vs_high = None

    # Add the percentage metric
    stats['pct_vs_7day_high'] = pct_vs_high

    return stats


def enrich_options_with_7day_history(options_data, ticker):
    """
    Enrich existing options data with 7-day historical statistics from Massive.com API.

    Args:
        options_data (dict): Dictionary from get_highest_lowest_put_premiums()
                            Contains expiry dates, strikes, and current prices
        ticker (str): Stock/ETF ticker

    Returns:
        dict: Enriched options_data with additional 7-day columns
              Returns original dict if Massive.com data unavailable
    """
    if not options_data:
        return options_data

    enriched_data = options_data.copy()

    # Find all expiry prefixes (e.g., "march_2026", "april_2026")
    expiry_prefixes = set()
    for key in options_data.keys():
        if '_expiry' in key:
            prefix = key.replace('_expiry', '')
            expiry_prefixes.add(prefix)

    # For each expiry
    for prefix in expiry_prefixes:
        expiry_date = options_data.get(f"{prefix}_expiry")

        if not expiry_date or expiry_date is None:
            continue

        # Process highest strike put
        highest_strike = options_data.get(f"{prefix}_highest_strike")
        highest_price = options_data.get(f"{prefix}_highest_put_price")

        if highest_strike and highest_price:
            print(f"    Fetching 7-day history for {ticker} {prefix} highest strike ({highest_strike})...")
            stats = get_7day_stats_for_put(ticker, expiry_date, highest_strike, highest_price)

            if stats:
                enriched_data[f"{prefix}_highest_put_7day_high"] = stats['7day_high']
                enriched_data[f"{prefix}_highest_put_7day_low"] = stats['7day_low']
                enriched_data[f"{prefix}_highest_put_7day_avg"] = stats['7day_avg']
                enriched_data[f"{prefix}_highest_put_pct_vs_7day_high"] = stats['pct_vs_7day_high']
            else:
                enriched_data[f"{prefix}_highest_put_7day_high"] = None
                enriched_data[f"{prefix}_highest_put_7day_low"] = None
                enriched_data[f"{prefix}_highest_put_7day_avg"] = None
                enriched_data[f"{prefix}_highest_put_pct_vs_7day_high"] = None

            # Rate limiting: Free tier = 5 calls/min, so wait 12 seconds
            time.sleep(12)

        # Process lowest strike put
        lowest_strike = options_data.get(f"{prefix}_lowest_strike")
        lowest_price = options_data.get(f"{prefix}_lowest_put_price")

        if lowest_strike and lowest_price:
            print(f"    Fetching 7-day history for {ticker} {prefix} lowest strike ({lowest_strike})...")
            stats = get_7day_stats_for_put(ticker, expiry_date, lowest_strike, lowest_price)

            if stats:
                enriched_data[f"{prefix}_lowest_put_7day_high"] = stats['7day_high']
                enriched_data[f"{prefix}_lowest_put_7day_low"] = stats['7day_low']
                enriched_data[f"{prefix}_lowest_put_7day_avg"] = stats['7day_avg']
                enriched_data[f"{prefix}_lowest_put_pct_vs_7day_high"] = stats['pct_vs_7day_high']
            else:
                enriched_data[f"{prefix}_lowest_put_7day_high"] = None
                enriched_data[f"{prefix}_lowest_put_7day_low"] = None
                enriched_data[f"{prefix}_lowest_put_7day_avg"] = None
                enriched_data[f"{prefix}_lowest_put_pct_vs_7day_high"] = None

            # Rate limiting
            time.sleep(12)

        # Process below 52-week low strike put (if exists)
        below_52wk_strike = options_data.get(f"{prefix}_below_52wk_low_strike")
        below_52wk_price = options_data.get(f"{prefix}_below_52wk_low_put_price")

        if below_52wk_strike and below_52wk_price:
            print(f"    Fetching 7-day history for {ticker} {prefix} below-52wk-low strike ({below_52wk_strike})...")
            stats = get_7day_stats_for_put(ticker, expiry_date, below_52wk_strike, below_52wk_price)

            if stats:
                enriched_data[f"{prefix}_below_52wk_low_put_7day_high"] = stats['7day_high']
                enriched_data[f"{prefix}_below_52wk_low_put_7day_low"] = stats['7day_low']
                enriched_data[f"{prefix}_below_52wk_low_put_7day_avg"] = stats['7day_avg']
                enriched_data[f"{prefix}_below_52wk_low_put_pct_vs_7day_high"] = stats['pct_vs_7day_high']
            else:
                enriched_data[f"{prefix}_below_52wk_low_put_7day_high"] = None
                enriched_data[f"{prefix}_below_52wk_low_put_7day_low"] = None
                enriched_data[f"{prefix}_below_52wk_low_put_7day_avg"] = None
                enriched_data[f"{prefix}_below_52wk_low_put_pct_vs_7day_high"] = None

            # Rate limiting
            time.sleep(12)

        # Process below 52-week low minus 1 std dev strike put (if exists)
        below_52wk_minus_1std_strike = options_data.get(f"{prefix}_below_52wk_minus_1std_strike")
        below_52wk_minus_1std_price = options_data.get(f"{prefix}_below_52wk_minus_1std_put_price")

        if below_52wk_minus_1std_strike and below_52wk_minus_1std_price:
            print(f"    Fetching 7-day history for {ticker} {prefix} below-52wk-minus-1std strike ({below_52wk_minus_1std_strike})...")
            stats = get_7day_stats_for_put(ticker, expiry_date, below_52wk_minus_1std_strike, below_52wk_minus_1std_price)

            if stats:
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_high"] = stats['7day_high']
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_low"] = stats['7day_low']
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_avg"] = stats['7day_avg']
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_pct_vs_7day_high"] = stats['pct_vs_7day_high']
            else:
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_high"] = None
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_low"] = None
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_7day_avg"] = None
                enriched_data[f"{prefix}_below_52wk_minus_1std_put_pct_vs_7day_high"] = None

            # Rate limiting
            time.sleep(12)

    return enriched_data


if __name__ == "__main__":
    # Test the module
    print("Testing Massive.com (formerly Polygon.io) Historical Options Fetcher")
    print("=" * 80)

    # Test 1: OCC ticker formatting
    print("\nTest 1: OCC Ticker Formatting")
    print("-" * 80)

    test_cases = [
        ("AAPL", "2026-03-20", "P", 235.0, "O:AAPL260320P00235000"),
        ("SPY", "2025-12-19", "C", 580.0, "O:SPY251219C00580000"),
        ("TSLA", "2026-04-17", "P", 150.5, "O:TSLA260417P00150500"),
    ]

    for ticker, exp, opt_type, strike, expected in test_cases:
        result = format_occ_ticker(ticker, exp, opt_type, strike)
        status = "✓" if result == expected else "✗"
        print(f"{status} {ticker} {exp} {opt_type} {strike} -> {result}")
        if result != expected:
            print(f"  Expected: {expected}")

    # Test 2: Fetch real historical data (requires API key)
    if POLYGON_API_KEY:
        print("\n\nTest 2: Fetching Real Historical Data")
        print("-" * 80)

        # Use a recent, liquid option that likely has data
        # AAPL near-the-money put expiring in March 2026
        test_ticker = "AAPL"
        test_expiry = "2026-03-20"  # March 2026 monthly (this Friday!)
        test_strike = 235.0
        test_current_price = 5.0  # Mock current price

        print(f"\nTicker: {test_ticker}")
        print(f"Expiry: {test_expiry}")
        print(f"Strike: ${test_strike}")
        print(f"Current Price (mock): ${test_current_price}")

        occ = format_occ_ticker(test_ticker, test_expiry, "P", test_strike)
        print(f"OCC Format: {occ}")

        print("\nFetching 7-day history from Massive.com API...")
        stats = get_7day_stats_for_put(test_ticker, test_expiry, test_strike, test_current_price)

        if stats:
            print("\n7-Day Statistics:")
            print(f"  High:     ${stats['7day_high']}")
            print(f"  Low:      ${stats['7day_low']}")
            print(f"  Average:  ${stats['7day_avg']}")
            print(f"  StdDev:   ${stats['7day_stdev']}")
            print(f"  Data Points: {stats['data_points']} days")
            print(f"\n  Current vs 7-Day High: {stats['pct_vs_7day_high']}%")

            if stats['pct_vs_7day_high'] and stats['pct_vs_7day_high'] >= 90:
                print("  → Premium is NEAR 7-day high - GOOD time to sell!")
            elif stats['pct_vs_7day_high'] and stats['pct_vs_7day_high'] < 70:
                print("  → Premium is BELOW recent highs - consider waiting")
        else:
            print("  ERROR: Could not fetch historical data")
            print("  This could mean:")
            print("    - API key is invalid")
            print("    - Option contract has no trade history")
            print("    - Rate limit exceeded")
            print("    - Expiry is too close (this Friday)")
    else:
        print("\n\nTest 2: SKIPPED (No POLYGON_API_KEY found)")
        print("Add POLYGON_API_KEY to .env file to test with real data")

    print("\n" + "=" * 80)
