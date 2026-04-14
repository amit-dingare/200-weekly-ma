"""Test script to verify chronological sorting of month columns."""
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


def test_month_sorting():
    """Test that month columns are sorted chronologically."""
    print("=" * 80)
    print("Testing Chronological Month Sorting")
    print("=" * 80)

    # Create sample column names (intentionally out of order - alphabetical)
    sample_columns = [
        'april_2026_expiry',
        'april_2026_highest_strike',
        'april_2026_highest_put_price',
        'april_2026_lowest_strike',
        'april_2026_lowest_put_price',
        'june_2026_expiry',
        'june_2026_highest_strike',
        'june_2026_highest_put_price',
        'june_2026_lowest_strike',
        'june_2026_lowest_put_price',
        'may_2026_expiry',
        'may_2026_highest_strike',
        'may_2026_highest_put_price',
        'may_2026_lowest_strike',
        'may_2026_lowest_put_price',
    ]

    print("\n1. Original (alphabetical) order:")
    print("-" * 80)
    for i, col in enumerate(sample_columns, 1):
        print(f"  {i:2d}. {col}")

    # Sort chronologically
    sorted_columns = sorted(sample_columns, key=get_month_year_sort_key)

    print("\n2. After chronological sorting:")
    print("-" * 80)
    for i, col in enumerate(sorted_columns, 1):
        print(f"  {i:2d}. {col}")

    # Verify expected order
    expected_order = [
        'april_2026_expiry',
        'april_2026_highest_strike',
        'april_2026_highest_put_price',
        'april_2026_lowest_strike',
        'april_2026_lowest_put_price',
        'may_2026_expiry',
        'may_2026_highest_strike',
        'may_2026_highest_put_price',
        'may_2026_lowest_strike',
        'may_2026_lowest_put_price',
        'june_2026_expiry',
        'june_2026_highest_strike',
        'june_2026_highest_put_price',
        'june_2026_lowest_strike',
        'june_2026_lowest_put_price',
    ]

    print("\n3. Verification:")
    print("-" * 80)
    if sorted_columns == expected_order:
        print("  ✓ SUCCESS! Columns are in correct chronological order:")
        print("    April 2026 → May 2026 → June 2026")
    else:
        print("  ✗ FAILED! Columns are not in expected order")
        print("\n  Expected:")
        for col in expected_order:
            print(f"    {col}")
        print("\n  Got:")
        for col in sorted_columns:
            print(f"    {col}")

    # Test with different years
    print("\n4. Testing multi-year sorting:")
    print("-" * 80)
    multi_year_columns = [
        'june_2026_expiry',
        'april_2026_expiry',
        'may_2026_expiry',
        'january_2027_expiry',
        'december_2026_expiry',
    ]

    sorted_multi_year = sorted(multi_year_columns, key=get_month_year_sort_key)
    print("  Original order:")
    for col in multi_year_columns:
        parts = col.split('_')
        print(f"    {col:30s} → {parts[0].capitalize()} {parts[1]}")

    print("\n  Sorted order:")
    for col in sorted_multi_year:
        parts = col.split('_')
        print(f"    {col:30s} → {parts[0].capitalize()} {parts[1]}")

    expected_multi_year = [
        'april_2026_expiry',
        'may_2026_expiry',
        'june_2026_expiry',
        'december_2026_expiry',
        'january_2027_expiry',
    ]

    if sorted_multi_year == expected_multi_year:
        print("\n  ✓ SUCCESS! Multi-year sorting works correctly")
    else:
        print("\n  ✗ FAILED! Multi-year sorting incorrect")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_month_sorting()
