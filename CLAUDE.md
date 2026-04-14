# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a technical analysis system that monitors S&P 500 stocks and low-cost ETFs, calculating their proximity to the 200-week Simple Moving Average (SMA) and 21-week RSI values. The system processes hundreds of securities, ranks them by technical indicators, and exports results to timestamped CSV files.

**Two Parallel Systems:**
1. **S&P 500 Stock Monitor** - Analyzes ~500 stocks from the S&P 500 index
2. **Low-Cost ETF Monitor** - Analyzes ~150 ETFs filtered by expense ratio

## Architecture

### S&P 500 Stock Pipeline

1. **ticker_fetcher.py** - Scrapes Wikipedia for current S&P 500 ticker list
2. **data_fetcher.py** - Fetches weekly historical data via yfinance API, calculates 200-week SMA, 21-week RSI, computes proximity percentages
3. **options_fetcher.py** - Fetches monthly put options data for top-ranked securities
4. **polygon_options_historical.py** - Fetches 7-day historical options data from Massive.com (formerly Polygon.io) API
5. **main.py** - Orchestrates the pipeline and saves results to CSV
6. **config.py** - Centralized configuration loaded from environment variables

### ETF Pipeline

1. **etf_ticker_fetcher.py** - Fetches ~150 ETFs from major providers (Vanguard, SPDR, iShares, Schwab, Invesco) and retrieves expense ratios
2. **etf_data_fetcher.py** - Calculates 200-week SMA, 21-week RSI, and proximity metrics for ETFs
3. **options_fetcher.py** - Fetches monthly put options data for top-ranked ETFs
4. **polygon_options_historical.py** - Fetches 7-day historical options data from Massive.com API
5. **main_etf.py** - Orchestrates ETF analysis and saves results to CSV
6. **config.py** - Shared configuration

### Data Flow

**Stock Pipeline:**
```
Wikipedia → S&P 500 Tickers → Yahoo Finance API →
200-week SMA + 21-week RSI → Dual Sorting → Top 10: Options Data (yfinance) →
Top 10: 7-Day Historical Options (Massive.com API) → CSV Export (./output/)
```

**ETF Pipeline:**
```
ETF List (~150 ETFs) → Expense Ratio Fetch → Top N by Expense Ratio →
200-week SMA + 21-week RSI → Dual Sorting → Top 10: Options Data (yfinance) →
Top 10: 7-Day Historical Options (Massive.com API) → CSV Export (./etf_output/)
```

### Key Technical Details

- **200-Week SMA Proximity**: `((current_price - sma_200) / sma_200) * 100`
  - Positive values = above SMA
  - Negative values = below SMA

- **21-Week RSI**: Calculated using Wilder's smoothing method
  - Stocks: Target RSI of 20 (oversold threshold)
  - ETFs: Target RSI of 40 (moderate level)

- **Dual Sorting Logic**:
  1. Primary: Sort by proximity_pct (most negative to most positive)
  2. Secondary: Sort by RSI proximity (tiebreaker - closest to target first)

- **Data Requirements**:
  - Requires 200+ weeks of historical data
  - Uses 10-year period fetch to ensure sufficient data
  - Gracefully handles missing/insufficient data by skipping securities

- **Monthly Put Options** (Top 10 only):
  - Fetched for top 10 ranked securities only to optimize performance
  - Identifies next 2 monthly expiration dates (3rd Friday of each month)
  - Fetches 3 categories of puts for each expiry:
    1. **Highest strike** below min(current_price, sma_200) - Closest protection level
    2. **Lowest strike** below min(current_price, sma_200) - Furthest downside protection
    3. **Highest strike below 52-week low** - Protection at deeper technical support level
  - Premium selection: Uses lastPrice if available, otherwise bid/ask midpoint
  - Column naming: Dynamic based on actual expiry month (e.g., `march_2026_highest_strike`, `march_2026_below_52wk_low_strike`)

- **7-Day Historical Options Data** (Top 10 only - requires Massive.com/Polygon API key):
  - Fetches last 7 calendar days (5 trading days) of EOD (End of Day) options data
  - Uses Massive.com REST API (formerly Polygon.io) - **Free tier** for EOD data
  - Calculates for each put premium:
    - **7day_high** - Highest premium in last 7 days
    - **7day_low** - Lowest premium in last 7 days
    - **7day_avg** - Mean premium over 7 days
    - **pct_vs_7day_high** ← **KEY METRIC** for put selling decisions
  - OCC format: `O:AAPL260320P00235000` (Underlying, YYMMDD, P/C, Strike×1000)
  - Rate limiting: 5 calls/min (free tier) = ~12 seconds between requests
  - Can be disabled via `FETCH_HISTORICAL_OPTIONS=False` for faster runs

- **Performance**:
  - S&P 500: ~5-15 minutes for all stocks + ~30-60 seconds for options (top 10) + ~2-4 minutes for historical (top 10)
  - ETFs: ~3-8 minutes for 50 ETFs + ~20-40 seconds for options (top 10) + ~2-4 minutes for historical (top 10)
  - API rate limiting via configurable delays:
    - yfinance: 1.5s between requests (default)
    - Options: 2.0s between requests (default)
    - Historical: 12s between requests (Massive.com free tier: 5 calls/min)

## Running the System

### Manual Execution

**S&P 500 Stock Analysis:**
```bash
python main.py
```
- Outputs to: `./output/sma_alerts_YYYY-MM-DD.csv`
- Console displays top N stocks (default: 50)

**Low-Cost ETF Analysis:**
```bash
python main_etf.py
```
- Outputs to: `./etf_output/etf_sma_alerts_YYYY-MM-DD.csv`
- Console displays top N ETFs (default: 50)

### Testing Individual Modules

```bash
# Test S&P 500 ticker fetching
python ticker_fetcher.py

# Test stock data fetching with sample stocks
python data_fetcher.py

# Test ETF ticker and expense ratio fetching
python etf_ticker_fetcher.py

# Test ETF data fetching with sample ETFs
python etf_data_fetcher.py

# Test RSI calculation on specific ticker
python test_rsi.py

# Test options data fetching
python options_fetcher.py

# Test full integration with options (stocks + ETFs)
python test_options_integration.py
```

### Setup Requirements

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Massive.com API key for 7-day historical options data (optional but recommended):

Create or edit `.env` file:
```bash
POLYGON_API_KEY=your_api_key_here
```

**To get a free Massive.com API key:**
- Visit: https://massive.com/ (formerly polygon.io)
- Sign up for a free account
- Get your API key from the dashboard
- Free tier includes EOD (End of Day) options data - perfect for this use case

**Note:** Without this key, the system will skip historical options data but will still fetch current options prices.

To disable historical data fetching entirely (faster runs):
```bash
FETCH_HISTORICAL_OPTIONS=False
```

3. Output directories are created automatically:
   - `./output/` - S&P 500 stock results
   - `./etf_output/` - ETF results

### Optional: Automated Scheduling

Example cron configurations for periodic analysis:

```bash
# S&P 500 stocks - Daily at 6:00 PM
0 18 * * * cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main.py >> /home/adinga01/logs/sma_stocks.log 2>&1

# ETFs - Weekly on Sunday at 8:00 PM
0 20 * * 0 cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main_etf.py >> /home/adinga01/logs/sma_etfs.log 2>&1

# Both systems - Weekdays after market close (4:30 PM ET)
30 16 * * 1-5 cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main.py && /usr/bin/python3 main_etf.py >> /home/adinga01/logs/sma_all.log 2>&1
```

## Configuration

All configurable parameters in `config.py`:

**Output Settings:**
- `TOP_N_STOCKS` (default: 50) - Number of stocks to display and analyze
- `TOP_N_ETFS` (default: 50) - Number of ETFs to analyze (filtered by expense ratio)
- `CSV_OUTPUT_DIR` (default: './output') - S&P 500 CSV output directory
- `ETF_CSV_OUTPUT_DIR` (default: './etf_output') - ETF CSV output directory

**Technical Analysis Settings:**
- `SMA_PERIOD` (default: 200) - Moving average window in weeks
- `DATA_INTERVAL` (default: '1wk') - Price data frequency
- `LOOKBACK_PERIODS` (default: 250) - Historical data fetch period (not actively used, uses '10y' period)

**RSI Settings:**
- `RSI_PERIOD` (default: 21) - RSI calculation period in weeks
- `RSI_TARGET` (default: 20) - Target RSI for stock proximity (oversold threshold)
- `RSI_TARGET_ETF` (default: 40) - Target RSI for ETF proximity (moderate level)

**API Rate Limiting:**
- `REQUEST_DELAY` (default: 1.5) - Delay between Yahoo Finance API calls in seconds
- `MAX_RETRIES` (default: 3) - Maximum retry attempts for failed requests
- `RETRY_DELAY` (default: 5.0) - Initial delay between retries (exponential backoff)

**Options Data Settings:**
- `TOP_N_OPTIONS` (default: 10) - Number of top-ranked securities to fetch options data for
- `OPTIONS_DELAY` (default: 2.0) - Additional delay for options API calls (slower endpoint)
- `FETCH_HISTORICAL_OPTIONS` (default: True) - Enable 7-day historical premium data from Massive.com
- `POLYGON_API_KEY` - API key for Massive.com (formerly Polygon.io) - Required for historical data

## CSV Output Format

### S&P 500 Stock CSV (`./output/sma_alerts_YYYY-MM-DD.csv`)

**Base Columns:**
- `ticker` - Stock symbol
- `date` - Date of data (YYYY-MM-DD)
- `sma_200` - 200-week simple moving average
- `current_price` - Most recent price (daily open or last close)
- `52_week_low` - Lowest price in the last 52 weeks (252 trading days)
- `proximity_pct` - Percentage distance from SMA (negative = below, positive = above)
- `rsi_21week` - 21-week RSI value (0-100)
- `rsi_proximity_to_20` - Absolute distance from RSI target of 20

**Options Columns (Top 10 stocks only):**

For each of the next 2 monthly expiries (dynamically named, e.g., `march_2026`, `april_2026`):

*Current Premium (from yfinance):*
- `{month}_{year}_expiry` - Expiration date (YYYY-MM-DD)
- `{month}_{year}_highest_strike` - Highest strike price where strike < min(current_price, sma_200)
- `{month}_{year}_highest_put_price` - **Current** premium for highest strike put
- `{month}_{year}_lowest_strike` - Lowest strike price meeting criteria
- `{month}_{year}_lowest_put_price` - **Current** premium for lowest strike put

*7-Day Historical (from Massive.com - if FETCH_HISTORICAL_OPTIONS=True):*
- `{month}_{year}_highest_put_7day_high` - Highest premium in last 7 days
- `{month}_{year}_highest_put_7day_low` - Lowest premium in last 7 days
- `{month}_{year}_highest_put_7day_avg` - Average premium in last 7 days
- `{month}_{year}_highest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**
- `{month}_{year}_lowest_put_7day_high` - Highest premium in last 7 days
- `{month}_{year}_lowest_put_7day_low` - Lowest premium in last 7 days
- `{month}_{year}_lowest_put_7day_avg` - Average premium in last 7 days
- `{month}_{year}_lowest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

*Below 52-Week Low Protection:*
- `{month}_{year}_below_52wk_low_strike` - Highest strike below 52-week low (deeper support level)
- `{month}_{year}_below_52wk_low_put_price` - **Current** premium for this put
- `{month}_{year}_below_52wk_low_put_7day_high` - Highest premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_7day_low` - Lowest premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_7day_avg` - Average premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high** (if historical enabled)

Example column names: `march_2026_highest_strike`, `april_2026_highest_put_pct_vs_7day_high`, `march_2026_below_52wk_low_strike`

**Put Selling Benchmark Guide:**
- **90-100%**: Current premium is at/near 7-day high → **EXCELLENT** time to sell
- **75-89%**: Current premium is above average → **GOOD** time to sell
- **50-74%**: Current premium is moderate → **FAIR**, assess market conditions
- **<50%**: Current premium is below recent levels → **WAIT** for better premiums

**Sorting:** Primary by proximity_pct (most negative to positive), secondary by rsi_proximity_to_20 (closest to 20 first)

**Note:** Stocks ranked 11+ will have empty/null values for options columns

### ETF CSV (`./etf_output/etf_sma_alerts_YYYY-MM-DD.csv`)

**Base Columns:**
- `ticker` - ETF symbol
- `date` - Date of data (YYYY-MM-DD)
- `sma_200` - 200-week simple moving average
- `current_price` - Most recent price (daily open or last close)
- `52_week_low` - Lowest price in the last 52 weeks (252 trading days)
- `proximity_pct` - Percentage distance from SMA (negative = below, positive = above)
- `rsi_21week` - 21-week RSI value (0-100)
- `rsi_proximity_to_40` - Absolute distance from RSI target of 40
- `expense_ratio_pct` - Annual expense ratio percentage

**Options Columns (Top 10 ETFs only):**

For each of the next 2 monthly expiries (dynamically named, e.g., `march_2026`, `april_2026`):

*Current Premium (from yfinance):*
- `{month}_{year}_expiry` - Expiration date (YYYY-MM-DD)
- `{month}_{year}_highest_strike` - Highest strike price where strike < min(current_price, sma_200)
- `{month}_{year}_highest_put_price` - **Current** premium for highest strike put
- `{month}_{year}_lowest_strike` - Lowest strike price meeting criteria
- `{month}_{year}_lowest_put_price` - **Current** premium for lowest strike put

*7-Day Historical (from Massive.com - if FETCH_HISTORICAL_OPTIONS=True):*
- `{month}_{year}_highest_put_7day_high` - Highest premium in last 7 days
- `{month}_{year}_highest_put_7day_low` - Lowest premium in last 7 days
- `{month}_{year}_highest_put_7day_avg` - Average premium in last 7 days
- `{month}_{year}_highest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**
- `{month}_{year}_lowest_put_7day_high` - Highest premium in last 7 days
- `{month}_{year}_lowest_put_7day_low` - Lowest premium in last 7 days
- `{month}_{year}_lowest_put_7day_avg` - Average premium in last 7 days
- `{month}_{year}_lowest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

*Below 52-Week Low Protection:*
- `{month}_{year}_below_52wk_low_strike` - Highest strike below 52-week low (deeper support level)
- `{month}_{year}_below_52wk_low_put_price` - **Current** premium for this put
- `{month}_{year}_below_52wk_low_put_7day_high` - Highest premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_7day_low` - Lowest premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_7day_avg` - Average premium in last 7 days (if historical enabled)
- `{month}_{year}_below_52wk_low_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high** (if historical enabled)

Example column names: `march_2026_highest_strike`, `april_2026_highest_put_pct_vs_7day_high`, `march_2026_below_52wk_low_strike`

**Put Selling Benchmark Guide:**
- **90-100%**: Current premium is at/near 7-day high → **EXCELLENT** time to sell
- **75-89%**: Current premium is above average → **GOOD** time to sell
- **50-74%**: Current premium is moderate → **FAIR**, assess market conditions
- **<50%**: Current premium is below recent levels → **WAIT** for better premiums

**Sorting:** Primary by proximity_pct (most negative to positive), secondary by rsi_proximity_to_40 (closest to 40 first)

**Note:** ETFs ranked 11+ will have empty/null values for options columns

## ETF Expense Ratio Selection

The ETF system fetches expense ratios from ~150 ETFs across major providers:
- **Vanguard**: VOO, VTI, VTV, VUG, VEA, VWO, sector ETFs, bond ETFs
- **SPDR**: SPY, SPLG, sector Select ETFs (XLK, XLF, XLV, etc.)
- **iShares**: IVV, IEMG, IEFA, sector and specialty ETFs
- **Schwab**: SCHB, SCHX, SCHA, SCHF, SCHE, SCHD
- **Invesco**: QQQ, QQQM, sector ETFs

Selection process:
1. Fetches expense ratios for all candidate ETFs via yfinance
2. Sorts by expense ratio (lowest first)
3. Selects top N ETFs (default: 50) with lowest expense ratios
4. Performs 200-week SMA and RSI analysis on selected ETFs

Typical expense ratio range: 0.03% - 0.20%

## Error Handling

The system is designed to be resilient:
- Securities with insufficient data are skipped with warnings
- Failed ticker fetches are logged but don't halt execution
- CSV output directories are created automatically if they don't exist
- API failures trigger exponential backoff retry logic (up to 3 attempts)
- JSON decode errors from Yahoo Finance API are handled gracefully
- **Options-specific handling:**
  - Securities without options availability return None gracefully
  - When no puts meet strike criteria (< min(current_price, sma_200)), columns are set to None
  - Missing monthly expiries are logged as warnings
  - Premium calculation falls back from lastPrice → bid/ask midpoint → bid → ask

## External Dependencies

- **yfinance**: Yahoo Finance API wrapper for stock/ETF data, expense ratios, and current options prices
- **Beautiful Soup**: Wikipedia scraping for S&P 500 ticker list
- **pandas/numpy**: Data manipulation, SMA calculation, RSI calculation, statistical analysis
- **python-dotenv**: Environment variable management
- **requests**: HTTP client for Massive.com (Polygon.io) API calls
- **Massive.com API** (formerly Polygon.io): Historical options premium data (Free tier for EOD data)
