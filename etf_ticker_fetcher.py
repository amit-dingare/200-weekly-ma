"""Fetch low-cost ETF tickers and their expense ratios."""
import yfinance as yf
import time


def get_low_cost_etfs(top_n=50):
    """
    Fetch low-cost ETFs sorted by expense ratio.

    Fetches expense ratios for a comprehensive list of popular ETFs from major providers
    (Vanguard, SPDR, iShares, Schwab, Invesco, etc.) and returns the top N with lowest
    expense ratios.

    Args:
        top_n (int): Number of lowest-cost ETFs to return (default: 50)

    Returns:
        dict: Dictionary mapping ticker symbols to expense ratios {ticker: expense_ratio}
              Sorted by expense ratio (lowest first)
    """
    # Comprehensive list of popular ETFs from major providers
    # ~150 ETFs covering: broad market, sectors, international, bonds, commodities
    candidate_etfs = [
        # Vanguard - Broad Market
        'VOO', 'VTI', 'VTV', 'VUG', 'VEA', 'VWO', 'VXUS', 'VT',
        'VO', 'VB', 'VIG', 'VYM', 'VONG', 'VONV', 'VTWO', 'VIOO',

        # Vanguard - Sector
        'VFH', 'VHT', 'VGT', 'VCR', 'VDC', 'VDE', 'VIS', 'VAW',
        'VNQ', 'VOX',

        # Vanguard - Fixed Income
        'BND', 'BNDX', 'BSV', 'BIV', 'BLV', 'VGIT', 'VGLT', 'VCIT',
        'VCLT', 'VTIP', 'VMBS',

        # SPDR - Broad Market
        'SPY', 'SPLG', 'SPYG', 'SPYV', 'SPTM', 'SPMB', 'SPMD', 'SPSM',
        'SPEM', 'SPDW', 'SPGM',

        # SPDR - Sector Select
        'XLK', 'XLF', 'XLV', 'XLE', 'XLY', 'XLP', 'XLI', 'XLU', 'XLB',
        'XLRE', 'XLC',

        # iShares Core
        'IVV', 'IVW', 'IVE', 'IEMG', 'IEFA', 'ITOT', 'IXUS', 'IJH', 'IJR',
        'AGG', 'IGSB', 'IGIB', 'IUSB', 'IAGG',

        # iShares - Sector & Specialty
        'IYW', 'IYF', 'IYH', 'IYE', 'IYC', 'IYK', 'IYJ', 'IDU', 'IYM',
        'IYR', 'IYZ',

        # iShares - International
        'EFA', 'EEM', 'EFAV', 'EEMV', 'ACWI', 'ACWX',

        # Schwab
        'SCHB', 'SCHX', 'SCHA', 'SCHM', 'SCHF', 'SCHE', 'SCHD', 'SCHV',
        'SCHG', 'SCHI', 'SCHR', 'SCHZ', 'SCHP',

        # Invesco (PowerShares)
        'QQQ', 'QQQM', 'QQQJ', 'PSI', 'PBW', 'PXE', 'PHO',

        # Other Popular Low-Cost
        'DIA', 'IWM', 'IWF', 'IWD', 'IWB', 'IWV', 'RSP', 'MDY',
        'LQD', 'HYG', 'TLT', 'IEF', 'SHY', 'TIP',

        # Thematic & Growth
        'ARKK', 'VGK', 'VPL', 'VGG', 'VOOG', 'VOOV',

        # Dividend & Value
        'SCHD', 'DVY', 'VYM', 'DGRO', 'NOBL', 'SDY',

        # Commodity & Real Estate
        'GLD', 'SLV', 'DBC', 'USCI', 'VNQ', 'XLRE', 'IYR', 'SCHH',

        # Small/Mid Cap
        'VBK', 'VBR', 'IJJ', 'IJS', 'VXF', 'SLYG', 'SLYV'
    ]

    print(f"Fetching expense ratios for {len(candidate_etfs)} candidate ETFs...")
    print("This may take a few minutes...\n")

    etf_expense_ratios = {}
    successful = 0
    failed = 0

    for i, ticker in enumerate(candidate_etfs, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(candidate_etfs)} ETFs processed")

        try:
            etf = yf.Ticker(ticker)
            info = etf.info

            # Try to get expense ratio (may be under different keys)
            # Note: Yahoo Finance changed API - now uses 'netExpenseRatio'
            expense_ratio = None
            if 'netExpenseRatio' in info and info['netExpenseRatio'] is not None:
                expense_ratio = info['netExpenseRatio']
            elif 'expenseRatio' in info and info['expenseRatio'] is not None:
                expense_ratio = info['expenseRatio']
            elif 'annualReportExpenseRatio' in info and info['annualReportExpenseRatio'] is not None:
                expense_ratio = info['annualReportExpenseRatio']

            if expense_ratio is not None and expense_ratio > 0:
                # Yahoo Finance returns values already in percentage form (e.g., 0.03 = 0.03%)
                # No conversion needed - values are already correct
                etf_expense_ratios[ticker] = round(expense_ratio, 4)
                successful += 1
            else:
                print(f"  Warning: No expense ratio data for {ticker}")
                failed += 1

            # Delay to avoid rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")
            failed += 1
            continue

    print(f"\nSuccessfully fetched expense ratios for {successful} ETFs")
    print(f"Failed to fetch {failed} ETFs\n")

    if not etf_expense_ratios:
        raise ValueError("No ETF expense ratios could be fetched. Please check your internet connection.")

    # Sort by expense ratio (lowest first)
    sorted_etfs = dict(sorted(etf_expense_ratios.items(), key=lambda x: x[1]))

    # Return top N
    top_etfs = dict(list(sorted_etfs.items())[:top_n])

    print(f"Selected top {len(top_etfs)} ETFs with lowest expense ratios:")
    print(f"  Expense ratio range: {min(top_etfs.values()):.4f}% - {max(top_etfs.values()):.4f}%")

    # Display top 10 for verification
    print("\nTop 10 lowest-cost ETFs:")
    for i, (ticker, er) in enumerate(list(top_etfs.items())[:10], 1):
        print(f"  {i:2d}. {ticker:6s} - {er:.4f}%")

    return top_etfs


if __name__ == "__main__":
    # Test the function
    etfs = get_low_cost_etfs(top_n=50)
    print(f"\nTotal ETFs selected: {len(etfs)}")
