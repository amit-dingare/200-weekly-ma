"""Test full pipeline with historical options data."""
import sys
import os
from datetime import datetime
import pandas as pd
import config
from data_fetcher import get_top_stocks_near_sma

print("=" * 80)
print("Testing Full Pipeline with Historical Options Data")
print("=" * 80)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test with just 5 liquid stocks to keep it fast
test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

print(f"Testing with {len(test_stocks)} stocks...")
print("This will:")
print("  1. Fetch SMA/RSI for all stocks")
print("  2. Sort by proximity")
print("  3. Fetch current options data for top stocks")
print("  4. Enrich with 7-day historical data from Massive.com")
print("\n" + "=" * 80)

try:
    # Run the pipeline (will fetch options for top 5 since we only have 5 stocks)
    results = get_top_stocks_near_sma(test_stocks, top_n=5)

    if not results.empty:
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"\nTotal stocks processed: {len(results)}")

        # Check what columns we have
        print(f"\nTotal columns: {len(results.columns)}")
        print("\nColumn names:")
        for col in sorted(results.columns):
            print(f"  - {col}")

        # Display basic info
        print("\n" + "=" * 80)
        print("Basic Stock Info (Top 5)")
        print("=" * 80)
        display_cols = ['ticker', 'current_price', 'sma_200', 'proximity_pct', 'rsi']
        print(results[display_cols].to_string(index=False))

        # Check for historical columns
        historical_cols = [col for col in results.columns if '7day' in col or 'pct_vs' in col]

        if historical_cols:
            print("\n" + "=" * 80)
            print("Historical Options Columns Found:")
            print("=" * 80)
            for col in sorted(historical_cols):
                print(f"  ✓ {col}")

            # Show sample data for first ticker with options data
            print("\n" + "=" * 80)
            print(f"Sample Historical Data - {results.iloc[0]['ticker']}")
            print("=" * 80)

            ticker = results.iloc[0]['ticker']
            row = results.iloc[0]

            # Find all month prefixes
            expiry_cols = [col for col in results.columns if '_expiry' in col]

            for expiry_col in expiry_cols:
                prefix = expiry_col.replace('_expiry', '')
                print(f"\n{prefix.upper()}:")

                # Highest strike put
                print(f"  Highest Strike Put:")
                print(f"    Strike: ${row.get(f'{prefix}_highest_strike', 'N/A')}")
                print(f"    Current: ${row.get(f'{prefix}_highest_put_price', 'N/A')}")
                print(f"    7-Day High: ${row.get(f'{prefix}_highest_put_7day_high', 'N/A')}")
                print(f"    7-Day Low: ${row.get(f'{prefix}_highest_put_7day_low', 'N/A')}")
                print(f"    7-Day Avg: ${row.get(f'{prefix}_highest_put_7day_avg', 'N/A')}")
                pct = row.get(f'{prefix}_highest_put_pct_vs_7day_high', 'N/A')
                print(f"    % of 7-Day High: {pct}%")

                if pct != 'N/A' and pct is not None:
                    if pct >= 90:
                        print(f"    → EXCELLENT time to sell (near recent high)")
                    elif pct >= 75:
                        print(f"    → GOOD time to sell")
                    elif pct >= 50:
                        print(f"    → FAIR - consider market conditions")
                    else:
                        print(f"    → WAIT - premiums below recent highs")

        else:
            print("\n⚠️ WARNING: No historical options columns found!")

        # Save to CSV for inspection
        csv_output_dir = './test_output'
        os.makedirs(csv_output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        csv_path = os.path.join(csv_output_dir, f'test_with_historical_{timestamp}.csv')

        results.to_csv(csv_path, index=False)
        print("\n" + "=" * 80)
        print(f"CSV saved: {csv_path}")
        print("=" * 80)

    else:
        print("❌ ERROR: No results returned!")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
