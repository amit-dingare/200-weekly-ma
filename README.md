# S&P 500 & ETF 200-Week SMA Technical Analysis System

Comprehensive technical analysis system that monitors S&P 500 stocks and low-cost ETFs, identifying securities approaching their 200-week Simple Moving Average (SMA) with advanced options analysis and premium benchmarking.

## Overview

This system provides automated technical analysis and options intelligence for two parallel asset classes:

1. **S&P 500 Stocks** - Analyzes ~500 stocks from the S&P 500 index
2. **Low-Cost ETFs** - Analyzes ~150 ETFs filtered by expense ratio

For each security, the system calculates:
- 200-week SMA proximity
- 21-week RSI values
- Monthly put options data (3 expiries)
- 7-day historical premium benchmarking
- Multiple protection strike levels

## Key Features

### Technical Indicators
- **200-Week SMA Analysis** - Identifies securities near long-term support/resistance levels
- **21-Week RSI** - Momentum indicator with custom targets (20 for stocks, 40 for ETFs)
- **Dual Sorting Logic** - Primary by SMA proximity, secondary by RSI proximity
- **52-Week Low Tracking** - Identifies key support levels

### Options Intelligence (Top 15 Securities)
- **3 Monthly Expiries** - Next 3rd Friday monthly expirations
- **4 Strike Price Categories**:
  1. Highest strike below min(current_price, sma_200)
  2. Lowest strike below min(current_price, sma_200)
  3. Highest strike below 52-week low
  4. Highest strike below (52-week low - 1 std dev) ← **NEW**
- **7-Day Premium Benchmarking** - Compare current premiums vs. 7-day high/low/avg
- **Put Selling Signals** - Identify optimal premium collection opportunities

### Data Sources
- **Yahoo Finance** - Price data, SMA/RSI calculations, current options prices
- **Massive.com API** (formerly Polygon.io) - 7-day historical options data (Free tier)
- **Wikipedia** - Current S&P 500 ticker list

## Architecture

### S&P 500 Stock Pipeline

```
Wikipedia → S&P 500 Tickers → Yahoo Finance API →
200-week SMA + 21-week RSI + 52-week std dev → Dual Sorting →
Top 15: Options Data (3 monthly expiries × 4 strike categories) →
Top 15: 7-Day Historical Premium Data (Massive.com API) →
CSV Export (./output/)
```

**Key Files:**
- `ticker_fetcher.py` - Scrapes Wikipedia for S&P 500 tickers
- `data_fetcher.py` - Fetches weekly data, calculates SMA/RSI/std dev
- `options_fetcher.py` - Fetches options data for 3 monthly expiries
- `polygon_options_historical.py` - Fetches 7-day historical premiums
- `main.py` - Orchestrates stock pipeline
- `config.py` - Centralized configuration

### ETF Pipeline

```
ETF List (~150 ETFs) → Expense Ratio Fetch → Top N by Expense Ratio →
200-week SMA + 21-week RSI + 52-week std dev → Dual Sorting →
Top 15: Options Data (3 monthly expiries × 4 strike categories) →
Top 15: 7-Day Historical Premium Data (Massive.com API) →
CSV Export (./etf_output/)
```

**Key Files:**
- `etf_ticker_fetcher.py` - Fetches ETFs from major providers with expense ratios
- `etf_data_fetcher.py` - Calculates SMA/RSI/std dev for ETFs
- `main_etf.py` - Orchestrates ETF pipeline
- Shared: `options_fetcher.py`, `polygon_options_historical.py`, `config.py`

## Technical Details

### 200-Week SMA Proximity

**Calculation:**
```python
proximity_pct = ((current_price - sma_200) / sma_200) * 100
```

- **Positive values** = Price above SMA (bullish)
- **Negative values** = Price below SMA (bearish/opportunity)
- Securities are sorted by proximity (most negative to most positive)

### 21-Week RSI

**Method:** Wilder's smoothing method
- **Stock Target:** RSI = 20 (oversold threshold)
- **ETF Target:** RSI = 40 (moderate level)
- Used as tiebreaker in sorting (closest to target first)

### 52-Week Statistics

**52-Week Low:** Minimum of daily low prices over 252 trading days
**52-Week Std Dev:** Standard deviation of daily closing prices over 252 trading days

These metrics identify key support levels for protective put strikes.

### Monthly Put Options Data (Top 15 Securities)

For each of the next **3 monthly expiries** (3rd Friday of each month), the system fetches **4 categories** of put options:

#### 1. Highest Strike Below Min(Price, SMA)
**Strike:** Closest protection level below current price or 200-week SMA (whichever is lower)
**Use Case:** Near-the-money downside protection

#### 2. Lowest Strike Below Min(Price, SMA)
**Strike:** Furthest OTM protection available
**Use Case:** Maximum capital efficiency, lower premium collection

#### 3. Highest Strike Below 52-Week Low
**Strike:** Protection at established technical support level
**Use Case:** Selling puts at historical support levels

#### 4. Highest Strike Below (52-Week Low - 1 Std Dev) ← **NEW**
**Strike:** Protection at deeper support level (52-week low minus 1 standard deviation)
**Use Case:** More conservative protection for volatile securities

### 7-Day Historical Premium Benchmarking

For each put option, the system calculates:
- **7day_high** - Highest premium in last 7 calendar days
- **7day_low** - Lowest premium in last 7 calendar days
- **7day_avg** - Mean premium over 7 days
- **pct_vs_7day_high** ← **KEY METRIC** - Current premium as % of 7-day high

**Put Selling Decision Guide:**
- **90-100%** - Current at/near 7-day high → **EXCELLENT** time to sell
- **75-89%** - Current above average → **GOOD** time to sell
- **50-74%** - Current moderate → **FAIR**, assess market conditions
- **<50%** - Current below recent levels → **WAIT** for better premiums

## Installation

### 1. Install Dependencies

```bash
cd /home/adinga01/PythonCode/Misc/200-weekly-ma
pip install -r requirements.txt
```

### 2. Configure Massive.com API Key (Optional but Recommended)

Create `.env` file:

```bash
POLYGON_API_KEY=your_api_key_here
```

**To get a free API key:**
1. Visit https://massive.com/ (formerly polygon.io)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes EOD (End of Day) options data - perfect for this use case

**Without API key:** System will skip historical options data but still fetch current prices.

**To disable historical data entirely:**
```bash
FETCH_HISTORICAL_OPTIONS=False
```

### 3. Output Directories

Created automatically:
- `./output/` - S&P 500 stock results
- `./etf_output/` - ETF results

## Usage

### Manual Execution

**S&P 500 Stock Analysis:**
```bash
python main.py
```
- Output: `./output/sma_alerts_YYYY-MM-DD.csv`
- Console: Displays top 50 stocks (configurable)

**Low-Cost ETF Analysis:**
```bash
python main_etf.py
```
- Output: `./etf_output/etf_sma_alerts_YYYY-MM-DD.csv`
- Console: Displays top 50 ETFs (configurable)

### Testing Individual Modules

```bash
# Test S&P 500 ticker fetching
python ticker_fetcher.py

# Test stock data fetching
python data_fetcher.py

# Test ETF ticker and expense ratio fetching
python etf_ticker_fetcher.py

# Test ETF data fetching
python etf_data_fetcher.py

# Test RSI calculation
python test_rsi.py

# Test options data fetching
python options_fetcher.py

# Test full integration with options
python test_options_integration.py
```

### Automated Scheduling (Cron)

**S&P 500 Stocks - Daily at 6:00 PM:**
```bash
0 18 * * * cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main.py >> /home/adinga01/logs/sma_stocks.log 2>&1
```

**ETFs - Weekly on Sunday at 8:00 PM:**
```bash
0 20 * * 0 cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main_etf.py >> /home/adinga01/logs/sma_etfs.log 2>&1
```

**Both Systems - Weekdays after market close (4:30 PM ET):**
```bash
30 16 * * 1-5 cd /home/adinga01/PythonCode/Misc/200-weekly-ma && /usr/bin/python3 main.py && /usr/bin/python3 main_etf.py >> /home/adinga01/logs/sma_all.log 2>&1
```

Create log directory:
```bash
mkdir -p /home/adinga01/logs
```

## Configuration

All settings in `config.py` (can be overridden via environment variables):

### Output Settings
- `TOP_N_STOCKS` (default: 50) - Number of stocks to display
- `TOP_N_ETFS` (default: 50) - Number of ETFs to display
- `CSV_OUTPUT_DIR` (default: './output') - Stock CSV output directory
- `ETF_CSV_OUTPUT_DIR` (default: './etf_output') - ETF CSV output directory

### Technical Analysis Settings
- `SMA_PERIOD` (default: 200) - Moving average window in weeks
- `DATA_INTERVAL` (default: '1wk') - Price data frequency
- `RSI_PERIOD` (default: 21) - RSI calculation period in weeks
- `RSI_TARGET` (default: 20) - Target RSI for stocks (oversold threshold)
- `RSI_TARGET_ETF` (default: 40) - Target RSI for ETFs (moderate level)

### API Rate Limiting
- `REQUEST_DELAY` (default: 1.5) - Delay between Yahoo Finance calls (seconds)
- `MAX_RETRIES` (default: 3) - Maximum retry attempts
- `RETRY_DELAY` (default: 5.0) - Initial retry delay (exponential backoff)

### Options Data Settings
- `TOP_N_OPTIONS` (default: 15) - Number of top-ranked securities to fetch options for
- `OPTIONS_DELAY` (default: 2.0) - Delay for options API calls (seconds)
- `FETCH_HISTORICAL_OPTIONS` (default: True) - Enable 7-day historical data
- `POLYGON_API_KEY` - API key for Massive.com (required for historical data)

## CSV Output Format

### S&P 500 Stock CSV (`./output/sma_alerts_YYYY-MM-DD.csv`)

#### Base Columns
- `ticker` - Stock symbol
- `date` - Data date (YYYY-MM-DD)
- `current_price` - Most recent price (daily open or last close)
- `52_week_low` - Lowest price in last 52 weeks (252 trading days)
- `52_week_std_dev` - Standard deviation of closing prices over 52 weeks ← **NEW**
- `sma_200` - 200-week simple moving average
- `proximity_pct` - Percentage distance from SMA (negative = below, positive = above)
- `rsi_21week` - 21-week RSI value (0-100)
- `rsi_proximity_to_20` - Absolute distance from RSI target of 20

#### Options Columns (Top 15 Stocks Only)

For each of the next **3 monthly expiries** (dynamically named: `april_2026`, `may_2026`, `june_2026`):

**Expiry Date:**
- `{month}_{year}_expiry` - Expiration date (YYYY-MM-DD)

**Strike Category 1: Highest Strike Below Min(Price, SMA)**
- `{month}_{year}_highest_strike` - Strike price
- `{month}_{year}_highest_put_price` - Current premium
- `{month}_{year}_highest_put_7day_high` - 7-day high premium
- `{month}_{year}_highest_put_7day_low` - 7-day low premium
- `{month}_{year}_highest_put_7day_avg` - 7-day average premium
- `{month}_{year}_highest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

**Strike Category 2: Lowest Strike Below Min(Price, SMA)**
- `{month}_{year}_lowest_strike` - Strike price
- `{month}_{year}_lowest_put_price` - Current premium
- `{month}_{year}_lowest_put_7day_high` - 7-day high premium
- `{month}_{year}_lowest_put_7day_low` - 7-day low premium
- `{month}_{year}_lowest_put_7day_avg` - 7-day average premium
- `{month}_{year}_lowest_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

**Strike Category 3: Highest Strike Below 52-Week Low**
- `{month}_{year}_below_52wk_low_strike` - Strike price
- `{month}_{year}_below_52wk_low_put_price` - Current premium
- `{month}_{year}_below_52wk_low_put_7day_high` - 7-day high premium
- `{month}_{year}_below_52wk_low_put_7day_low` - 7-day low premium
- `{month}_{year}_below_52wk_low_put_7day_avg` - 7-day average premium
- `{month}_{year}_below_52wk_low_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

**Strike Category 4: Highest Strike Below (52-Week Low - 1 Std Dev)** ← **NEW**
- `{month}_{year}_below_52wk_minus_1std_strike` - Strike price
- `{month}_{year}_below_52wk_minus_1std_put_price` - Current premium
- `{month}_{year}_below_52wk_minus_1std_put_7day_high` - 7-day high premium
- `{month}_{year}_below_52wk_minus_1std_put_7day_low` - 7-day low premium
- `{month}_{year}_below_52wk_minus_1std_put_7day_avg` - 7-day average premium
- `{month}_{year}_below_52wk_minus_1std_put_pct_vs_7day_high` ← **KEY: Current as % of 7-day high**

**Total Columns:** ~84 columns per stock (9 base + 25 options columns × 3 expiries)
  - 9 base columns
  - Per expiry: 1 expiry date + (4 strike categories × 6 data points) = 25 columns
  - 3 expiries × 25 = 75 options columns

**Sorting:** Primary by `proximity_pct` (most negative to positive), secondary by `rsi_proximity_to_20` (closest to 20 first)

**Note:** Stocks ranked 16+ will have empty/null values for options columns

### ETF CSV (`./etf_output/etf_sma_alerts_YYYY-MM-DD.csv`)

#### Base Columns
- `ticker` - ETF symbol
- `date` - Data date (YYYY-MM-DD)
- `current_price` - Most recent price (daily open or last close)
- `52_week_low` - Lowest price in last 52 weeks (252 trading days)
- `52_week_std_dev` - Standard deviation of closing prices over 52 weeks ← **NEW**
- `sma_200` - 200-week simple moving average
- `proximity_pct` - Percentage distance from SMA (negative = below, positive = above)
- `rsi_21week` - 21-week RSI value (0-100)
- `rsi_proximity_to_40` - Absolute distance from RSI target of 40
- `expense_ratio_pct` - Annual expense ratio percentage

#### Options Columns (Top 15 ETFs Only)

Same structure as stocks (see above) - 4 strike categories × 3 monthly expiries × 6 data points each

**Total Columns:** ~85 columns per ETF (10 base + 25 options columns × 3 expiries)
  - 10 base columns (includes expense_ratio_pct)
  - Per expiry: 1 expiry date + (4 strike categories × 6 data points) = 25 columns
  - 3 expiries × 25 = 75 options columns

**Sorting:** Primary by `proximity_pct` (most negative to positive), secondary by `rsi_proximity_to_40` (closest to 40 first)

**Note:** ETFs ranked 16+ will have empty/null values for options columns

## ETF Selection Process

The system analyzes ~150 ETFs from major providers:
- **Vanguard** - VOO, VTI, VTV, VUG, VEA, VWO, sector ETFs, bond ETFs
- **SPDR** - SPY, SPLG, sector Select ETFs (XLK, XLF, XLV, etc.)
- **iShares** - IVV, IEMG, IEFA, sector and specialty ETFs
- **Schwab** - SCHB, SCHX, SCHA, SCHF, SCHE, SCHD
- **Invesco** - QQQ, QQQM, sector ETFs

**Selection Process:**
1. Fetch expense ratios for all ~150 candidate ETFs
2. Sort by expense ratio (lowest first)
3. Select top 50 ETFs (configurable)
4. Perform 200-week SMA and RSI analysis
5. Fetch options data for top 15

**Typical Expense Ratio Range:** 0.03% - 0.20%

## Performance

**S&P 500 Pipeline:**
- Ticker fetching: ~5 seconds
- 500 stocks analysis: ~5-15 minutes
- Options data (top 15): ~30-60 seconds
- Historical data (top 15): ~4-8 minutes
  - Up to 12 API calls per security (3 expiries × 4 strike categories)
  - Actual calls vary based on available strikes
  - Rate limited: 12s/call @ 5 calls/min (Massive.com free tier)
- **Total:** ~10-24 minutes

**ETF Pipeline:**
- ETF list + expense ratios: ~2-3 minutes
- 50 ETFs analysis: ~3-8 minutes
- Options data (top 15): ~30-60 seconds
- Historical data (top 15): ~4-8 minutes
  - Up to 12 API calls per security (3 expiries × 4 strike categories)
  - Actual calls vary based on available strikes
- **Total:** ~10-20 minutes

## Error Handling

The system is designed for resilience:
- Securities with insufficient data are skipped with warnings
- Failed fetches trigger exponential backoff retry (up to 3 attempts)
- CSV output directories created automatically
- Options unavailability handled gracefully (columns set to None)
- Missing monthly expiries logged as warnings
- Premium calculation falls back: lastPrice → bid/ask midpoint → bid → ask

## Data Requirements

- **Minimum History:** 200+ weeks of data for SMA calculation
- **Fetch Period:** 10 years (~520 weeks) to ensure sufficient data
- **52-Week Stats:** 1 year (252 trading days) of daily data
- **Options:** At least 2 monthly expiries available
- **Historical Options:** Last 7 calendar days (~5 trading days) of EOD data

## OCC Options Ticker Format

Historical options use OCC (Options Clearing Corporation) format:

**Format:** `O:{underlying}{YYMMDD}{C/P}{strike_padded}`

**Example:** `O:AAPL260320P00235000`
- Underlying: AAPL
- Expiry: March 20, 2026 (260320)
- Type: Put (P)
- Strike: $235.00 (00235000 = strike × 1000, padded to 8 digits)

## External Dependencies

- **yfinance** - Yahoo Finance API wrapper (price data, SMA/RSI, current options)
- **Beautiful Soup** - Wikipedia scraping (S&P 500 ticker list)
- **pandas/numpy** - Data manipulation, statistical calculations
- **python-dotenv** - Environment variable management
- **requests** - HTTP client for Massive.com API
- **Massive.com API** (formerly Polygon.io) - Historical options premium data (Free tier)

## Files Structure

```
200-weekly-ma/
├── main.py                          # Stock pipeline orchestrator
├── main_etf.py                      # ETF pipeline orchestrator
├── config.py                        # Centralized configuration
├── ticker_fetcher.py                # S&P 500 ticker scraper
├── etf_ticker_fetcher.py            # ETF list + expense ratio fetcher
├── data_fetcher.py                  # Stock SMA/RSI/std dev calculator
├── etf_data_fetcher.py              # ETF SMA/RSI/std dev calculator
├── options_fetcher.py               # Options data fetcher (3 expiries, 4 strikes)
├── polygon_options_historical.py    # 7-day historical premium enrichment
├── test_rsi.py                      # RSI calculation tester
├── test_options_integration.py      # Full options integration tester
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (create from .env.example)
├── README.md                        # This file
├── CLAUDE.md                        # Claude Code instructions
├── output/                          # Stock CSV output directory
└── etf_output/                      # ETF CSV output directory
```

## Support

For issues or questions, contact amit.dingare@prgx.com

## License

This project is for personal use.
