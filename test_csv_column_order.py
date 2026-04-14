"""Test CSV column ordering with chronological month sorting."""
import pandas as pd
from datetime import datetime


def get_month_year_sort_key(col):
    """Extract month and year for chronological sorting."""
    parts = col.split('_')
    if len(parts) >= 2:
        try:
            # Try to parse month name and year
            month_name = parts[0]
            year = parts[1]
            # Convert month name to number for sorting
            month_num = datetime.strptime(month_name.capitalize(), '%B').month
            # Return tuple (year, month, original_column) for sorting
            return (int(year), month_num, col)
        except (ValueError, IndexError):
            pass
    # If parsing fails, sort by column name (fallback)
    return (9999, 99, col)


def test_csv_column_order():
    """Test that CSV columns are ordered correctly."""
    print("=" * 80)
    print("Testing CSV Column Order with Chronological Sorting")
    print("=" * 80)

    # Create sample data mimicking the actual structure
    sample_data = {
        'ticker': ['AAPL', 'MSFT'],
        'date': ['2026-04-06', '2026-04-06'],
        'sma_200': [150.0, 350.0],
        'current_price': [170.0, 400.0],
        '52_week_low': [140.0, 330.0],
        'proximity_pct': [13.33, 14.29],
        'rsi_21week': [55.0, 60.0],
        'rsi_proximity_to_20': [35.0, 40.0],
        # April 2026 columns
        'april_2026_expiry': ['2026-04-17', '2026-04-17'],
        'april_2026_highest_strike': [165.0, 390.0],
        'april_2026_highest_put_price': [5.5, 12.0],
        'april_2026_lowest_strike': [140.0, 320.0],
        'april_2026_lowest_put_price': [1.2, 3.5],
        # June 2026 columns (intentionally placed before May)
        'june_2026_expiry': ['2026-06-19', '2026-06-19'],
        'june_2026_highest_strike': [165.0, 390.0],
        'june_2026_highest_put_price': [8.5, 18.0],
        'june_2026_lowest_strike': [140.0, 320.0],
        'june_2026_lowest_put_price': [2.5, 6.0],
        # May 2026 columns (intentionally placed last - alphabetical order)
        'may_2026_expiry': ['2026-05-15', '2026-05-15'],
        'may_2026_highest_strike': [165.0, 390.0],
        'may_2026_highest_put_price': [7.0, 15.0],
        'may_2026_lowest_strike': [140.0, 320.0],
        'may_2026_lowest_put_price': [1.8, 4.5],
    }

    df = pd.DataFrame(sample_data)

    print("\n1. Current DataFrame columns (as created - alphabetical month order):")
    print("-" * 80)
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # Apply the sorting logic from main.py
    base_columns = ['ticker', 'date', 'sma_200', 'current_price', '52_week_low',
                    'proximity_pct', 'rsi_21week', 'rsi_proximity_to_20']

    # Get all options columns (those not in base_columns)
    options_columns = [col for col in df.columns if col not in base_columns]

    # Sort options columns chronologically
    options_columns.sort(key=get_month_year_sort_key)

    # Reorder columns
    final_columns = base_columns + options_columns
    df_sorted = df[final_columns]

    print("\n2. After applying chronological sorting:")
    print("-" * 80)
    for i, col in enumerate(df_sorted.columns, 1):
        print(f"  {i:2d}. {col}")

    # Extract just the month-year parts to show the order clearly
    print("\n3. Month sequence in sorted DataFrame:")
    print("-" * 80)
    month_cols = [col for col in df_sorted.columns if any(month in col for month in ['april', 'may', 'june'])]
    months_seen = []
    for col in month_cols:
        month_year = '_'.join(col.split('_')[:2])
        if month_year not in months_seen:
            months_seen.append(month_year)
            print(f"  → {month_year.replace('_', ' ').title()}")

    # Verify the order
    expected_month_order = ['april_2026', 'may_2026', 'june_2026']

    print("\n4. Verification:")
    print("-" * 80)
    if months_seen == expected_month_order:
        print("  ✓ SUCCESS! Months are in chronological order:")
        print("    April 2026 → May 2026 → June 2026")
    else:
        print("  ✗ FAILED! Incorrect month order")
        print(f"    Expected: {expected_month_order}")
        print(f"    Got: {months_seen}")

    # Save to CSV for visual inspection
    test_csv = '/home/adinga01/PythonCode/Misc/200-weekly-ma/test_output_chronological.csv'
    df_sorted.to_csv(test_csv, index=False)
    print(f"\n5. Test CSV saved to: {test_csv}")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_csv_column_order()
