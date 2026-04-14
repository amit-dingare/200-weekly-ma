# Setup Notes

## Python Environment

This project uses **system Python 3.10** with packages installed in the user location (`~/.local/lib/python3.10/site-packages`).

The old `.venv` directory has been renamed to `.venv.broken_old` because it was missing pip and using an outdated yfinance version.

## Running the System

Always use system Python explicitly:

```bash
# Run the main system
/usr/bin/python3 main.py

# Or use the default python3
python3 main.py
```

## Dependencies

All dependencies are installed in the user location. If you need to reinstall:

```bash
pip install --user -r requirements.txt
```

## Key Updates (February 11, 2026)

1. **yfinance upgraded** from 0.2.37 → 1.1.0
   - Now uses `curl_cffi` internally for better rate limiting handling
   - Fixed invalid period parameter: `"250wk"` → `"10y"`

2. **Added retry logic** with exponential backoff (3 retries, 5s initial delay)

3. **Added request delays** (1.5s between API calls) to prevent rate limiting

4. **Improved error handling** for JSON decode errors and API failures

## Configuration

Edit `.env` file to customize:
- `REQUEST_DELAY=1.5` - Delay between API calls (default: 1.5s)
- `MAX_RETRIES=3` - Maximum retry attempts (default: 3)
- `RETRY_DELAY=5.0` - Initial retry delay (default: 5s)
- `TOP_N_STOCKS=5` - Number of stocks in alert (default: 5)

## Performance

- Processing 500 S&P 500 stocks: ~12-13 minutes (with 1.5s delay)
- Reducing delay to 1.0s: ~8-9 minutes (may risk rate limiting)
