"""Main script to run Low-Cost ETF Weekly 200 SMA Alert System."""
import sys
import os
from datetime import datetime
import config
from etf_ticker_fetcher import get_low_cost_etfs
from etf_data_fetcher import get_top_etfs_near_sma


def main():
    """Main function to orchestrate the ETF alert system."""
    print("=" * 80)
    print("Low-Cost ETF Weekly 200 SMA Alert System")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Step 1: Fetch low-cost ETFs with expense ratios
        print("Step 1: Fetching low-cost ETFs ranked by expense ratio...")
        top_n_etfs = getattr(config, 'TOP_N_ETFS', 50)
        etf_expense_dict = get_low_cost_etfs(top_n=top_n_etfs)
        print(f"Selected {len(etf_expense_dict)} ETFs for analysis\n")

        # Step 2: Calculate 200-week SMA, proximity, and RSI for all ETFs
        print(f"Step 2: Analyzing {len(etf_expense_dict)} ETFs for 200-week SMA proximity and 21-week RSI ~40...")
        print("This may take several minutes...\n")

        # Analyze all ETFs (not just top N for display)
        all_etfs = get_top_etfs_near_sma(etf_expense_dict, top_n=len(etf_expense_dict))

        if all_etfs.empty:
            print("Error: No valid ETF data retrieved. Exiting...")
            sys.exit(1)

        # Step 3: Display results (show top stocks for TOP_N_STOCKS)
        display_n = config.TOP_N_STOCKS
        print("\n" + "=" * 80)
        print(f"Top {display_n} ETFs Closest to 200-Week SMA (Sorted by RSI Proximity to 40)")
        print("=" * 80)
        display_df = all_etfs.head(display_n)
        print(display_df[['ticker', 'current_price', 'sma_200', 'proximity_pct', 'rsi', 'expense_ratio', 'direction']].to_string(index=False))
        print("=" * 80 + "\n")

        # Step 4: Save results to CSV
        print("Step 3: Saving results to CSV...")

        # Create output directory if it doesn't exist
        csv_output_dir = getattr(config, 'ETF_CSV_OUTPUT_DIR', './etf_output')
        os.makedirs(csv_output_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y-%m-%d')
        csv_filename = f"etf_sma_alerts_{timestamp}.csv"
        csv_path = os.path.join(csv_output_dir, csv_filename)

        # Prepare CSV data - include all columns
        csv_data = all_etfs.copy()

        # Rename base columns
        column_renames = {
            'last_updated': 'date',
            'rsi': 'rsi_21week',
            'rsi_proximity': 'rsi_proximity_to_40',
            'expense_ratio': 'expense_ratio_pct'
        }
        csv_data.rename(columns=column_renames, inplace=True)

        # Extract just the date part (remove time)
        csv_data['date'] = csv_data['date'].str.split(' ').str[0]

        # Remove internal columns not needed in CSV
        columns_to_drop = ['abs_proximity', 'direction']
        csv_data.drop(columns=[col for col in columns_to_drop if col in csv_data.columns], inplace=True)

        # Reorder columns: base columns first, then options columns
        base_columns = ['ticker', 'date', 'sma_200', 'current_price', '52_week_low', 'proximity_pct', 'rsi_21week', 'rsi_proximity_to_40', 'expense_ratio_pct']

        # Get all options columns (those not in base_columns)
        options_columns = [col for col in csv_data.columns if col not in base_columns]

        # Sort options columns chronologically by month/year (not alphabetically)
        # Extract month/year from column names like "april_2026_highest_strike"
        def get_month_year_sort_key(col):
            """Extract month and year for chronological sorting."""
            parts = col.split('_')
            if len(parts) >= 2:
                try:
                    # Try to parse month name and year
                    month_name = parts[0]
                    year = parts[1]
                    # Convert month name to number for sorting
                    from datetime import datetime
                    month_num = datetime.strptime(month_name.capitalize(), '%B').month
                    # Return tuple (year, month, original_column) for sorting
                    return (int(year), month_num, col)
                except (ValueError, IndexError):
                    pass
            # If parsing fails, sort by column name (fallback)
            return (9999, 99, col)

        options_columns.sort(key=get_month_year_sort_key)

        # Reorder columns
        final_columns = base_columns + options_columns
        csv_data = csv_data[final_columns]

        # Save to CSV (sorted by proximity_pct absolute value - already sorted from etf_data_fetcher)
        csv_data.to_csv(csv_path, index=False)

        print(f"CSV file saved: {csv_path}")
        print(f"Total records: {len(csv_data)}")

        # Display expense ratio statistics
        print(f"\nExpense Ratio Statistics:")
        print(f"  Average: {csv_data['expense_ratio_pct'].mean():.4f}%")
        print(f"  Range: {csv_data['expense_ratio_pct'].min():.4f}% - {csv_data['expense_ratio_pct'].max():.4f}%")

        print("\n" + "=" * 80)
        print("SUCCESS: ETF Analysis complete!")
        print("=" * 80)

    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"FATAL ERROR: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
