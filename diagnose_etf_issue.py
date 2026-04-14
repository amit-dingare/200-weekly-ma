"""Diagnostic script to check what data yfinance returns for ETFs."""
import yfinance as yf
import json

# Test with a few popular ETFs
test_tickers = ['VOO', 'SPY', 'VTI', 'IVV', 'QQQ']

print("Testing yfinance data retrieval for sample ETFs...")
print("=" * 80)

for ticker in test_tickers:
    print(f"\n{ticker}:")
    print("-" * 40)
    try:
        etf = yf.Ticker(ticker)
        info = etf.info

        # Check if we got any data
        if not info or len(info) == 0:
            print("  ERROR: No data returned from yfinance!")
            continue

        # Print all available keys
        print(f"  Total keys available: {len(info)}")

        # Look for expense ratio related keys
        expense_keys = [k for k in info.keys() if 'expense' in k.lower() or 'ratio' in k.lower()]
        print(f"  Expense/Ratio related keys: {expense_keys}")

        # Print expense ratio values if found
        for key in expense_keys:
            print(f"    {key}: {info[key]}")

        # Also check some specific keys we're looking for
        if 'expenseRatio' in info:
            print(f"  expenseRatio: {info['expenseRatio']}")
        if 'annualReportExpenseRatio' in info:
            print(f"  annualReportExpenseRatio: {info['annualReportExpenseRatio']}")

        # Print first 10 keys to see what data is available
        print(f"  First 10 keys: {list(info.keys())[:10]}")

    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 80)
print("Diagnostic complete!")
