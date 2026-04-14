"""Test options integration with stock and ETF pipelines."""
import sys
from datetime import datetime
import config
from data_fetcher import get_top_stocks_near_sma
from etf_data_fetcher import get_top_etfs_near_sma

print("=" * 80)
print("Testing Options Integration")
print("=" * 80)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test 1: Stock pipeline with a few liquid tickers
print("Test 1: Stock Pipeline")
print("=" * 80)

test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'UNH',
               'WMT', 'JNJ', 'PG', 'MA', 'HD']

print(f"Testing with {len(test_stocks)} stocks...")
print("This will fetch SMA/RSI for all, and options for top {}\n".format(config.TOP_N_OPTIONS))

try:
    results = get_top_stocks_near_sma(test_stocks, top_n=15)

    if not results.empty:
        print("\nResults Summary:")
        print("=" * 80)
        print(f"Total stocks processed: {len(results)}")

        # Check which stocks have options data
        options_columns = [col for col in results.columns if 'expiry' in col or 'strike' in col or 'put_price' in col]

        if options_columns:
            print(f"Options columns found: {len(options_columns)}")
            print(f"Sample columns: {options_columns[:5]}")

            # Show which tickers have options data
            print("\nTickers with options data:")
            for idx, row in results.iterrows():
                ticker = row['ticker']
                # Check if any options column has non-null data for this ticker
                has_options = any(row[col] is not None and str(row[col]) != 'nan' for col in options_columns if col in row)
                if has_options:
                    print(f"  {ticker}")
        else:
            print("No options columns found in results!")

        # Display top 5 with basic info
        print("\nTop 5 Stocks (Basic Info):")
        print(results[['ticker', 'current_price', 'sma_200', 'proximity_pct', 'rsi']].head().to_string(index=False))

    else:
        print("ERROR: No results returned!")

except Exception as e:
    print(f"ERROR in stock pipeline: {e}")
    import traceback
    traceback.print_exc()

# Test 2: ETF pipeline
print("\n\n" + "=" * 80)
print("Test 2: ETF Pipeline")
print("=" * 80)

test_etfs_dict = {
    'VOO': 0.03,
    'VTI': 0.03,
    'SPY': 0.09,
    'IVV': 0.03,
    'QQQ': 0.20,
    'VEA': 0.05,
    'VWO': 0.08,
    'AGG': 0.03,
    'BND': 0.03,
    'VTV': 0.04,
    'VUG': 0.04,
    'IWM': 0.19
}

print(f"Testing with {len(test_etfs_dict)} ETFs...")
print("This will fetch SMA/RSI for all, and options for top {}\n".format(config.TOP_N_OPTIONS))

try:
    results = get_top_etfs_near_sma(test_etfs_dict, top_n=12)

    if not results.empty:
        print("\nResults Summary:")
        print("=" * 80)
        print(f"Total ETFs processed: {len(results)}")

        # Check which ETFs have options data
        options_columns = [col for col in results.columns if 'expiry' in col or 'strike' in col or 'put_price' in col]

        if options_columns:
            print(f"Options columns found: {len(options_columns)}")
            print(f"Sample columns: {options_columns[:5]}")

            # Show which tickers have options data
            print("\nTickers with options data:")
            for idx, row in results.iterrows():
                ticker = row['ticker']
                # Check if any options column has non-null data for this ticker
                has_options = any(row[col] is not None and str(row[col]) != 'nan' for col in options_columns if col in row)
                if has_options:
                    print(f"  {ticker}")
        else:
            print("No options columns found in results!")

        # Display top 5 with basic info
        print("\nTop 5 ETFs (Basic Info):")
        print(results[['ticker', 'current_price', 'sma_200', 'proximity_pct', 'rsi', 'expense_ratio']].head().to_string(index=False))

    else:
        print("ERROR: No results returned!")

except Exception as e:
    print(f"ERROR in ETF pipeline: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print(f"Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
