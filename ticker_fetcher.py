"""Fetch S&P 500 ticker symbols from Wikipedia."""
import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_sp500_tickers():
    """
    Fetch the current list of S&P 500 ticker symbols from Wikipedia.

    Returns:
        list: List of ticker symbols
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

    try:
        # Fetch the page with proper headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table with S&P 500 companies (first wikitable)
        table = soup.find('table', {'class': 'wikitable'})

        # Read the table into pandas DataFrame
        df = pd.read_html(str(table))[0]

        # Extract ticker symbols (first column)
        tickers = df['Symbol'].tolist()

        # Clean tickers (remove any special characters)
        tickers = [ticker.replace('.', '-') for ticker in tickers]

        print(f"Successfully fetched {len(tickers)} S&P 500 tickers")
        return tickers

    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        raise


if __name__ == "__main__":
    # Test the function
    tickers = get_sp500_tickers()
    print(f"Sample tickers: {tickers[:10]}")
