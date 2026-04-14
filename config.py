"""Configuration settings for S&P 500 Weekly 200 SMA Alert System."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Output Settings
CSV_OUTPUT_DIR = os.getenv('CSV_OUTPUT_DIR', './output')
ETF_CSV_OUTPUT_DIR = os.getenv('ETF_CSV_OUTPUT_DIR', './etf_output')

# Alert Settings
TOP_N_STOCKS = int(os.getenv('TOP_N_STOCKS', 50))
TOP_N_ETFS = int(os.getenv('TOP_N_ETFS', 50))

# Data Settings
SMA_PERIOD = 200  # 200-week simple moving average
DATA_INTERVAL = '1wk'  # Weekly data
LOOKBACK_PERIODS = 250  # Fetch extra data to ensure we have enough for SMA calculation

# RSI Settings
RSI_PERIOD = 21  # 21-week RSI period (matches weekly timeframe of 200-week SMA)
RSI_TARGET = 20  # Target RSI value for proximity calculation (oversold threshold) - for stocks
RSI_TARGET_ETF = 40  # Target RSI value for ETF proximity calculation (moderate level)

# API Settings
# Increased delays to prevent Yahoo Finance rate limiting (429 errors)
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', 1.5))  # Delay between API calls in seconds (1.5s = ~40 stocks/min)
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))  # Maximum number of retries for failed requests
RETRY_DELAY = float(os.getenv('RETRY_DELAY', 5.0))  # Initial delay between retries in seconds

# Options Settings
TOP_N_OPTIONS = int(os.getenv('TOP_N_OPTIONS', 15))  # Fetch options data for top N securities only
OPTIONS_DELAY = float(os.getenv('OPTIONS_DELAY', 2.0))  # Additional delay for options API calls (slower endpoint)
FETCH_HISTORICAL_OPTIONS = os.getenv('FETCH_HISTORICAL_OPTIONS', 'True').lower() in ('true', '1', 'yes')  # Enable 7-day historical data from Massive.com
