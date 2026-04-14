"""Send email alerts via Outlook SMTP."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import config


def create_html_table(df):
    """
    Create an HTML table from the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with stock data

    Returns:
        str: HTML string containing formatted table
    """
    if df.empty:
        return "<p>No data available at this time.</p>"

    html = """
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h2 {
                color: #2c3e50;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                max-width: 800px;
                margin-top: 20px;
            }
            th {
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }
            td {
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .positive {
                color: #27ae60;
            }
            .negative {
                color: #e74c3c;
            }
            .rsi-oversold {
                color: #e74c3c;
                font-weight: bold;
            }
            .rsi-neutral {
                color: #34495e;
            }
            .rsi-overbought {
                color: #27ae60;
            }
            .footer {
                margin-top: 20px;
                font-size: 12px;
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <h2>S&P 500 Stocks Closest to 200-Week SMA (Sorted by RSI Proximity to 20)</h2>
        <p>The following stocks are closest to their 200-week Simple Moving Average, with secondary sorting by RSI proximity to 20 (oversold):</p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Ticker</th>
                    <th>Current Price</th>
                    <th>200-Week SMA</th>
                    <th>Proximity (%)</th>
                    <th>21-Week RSI</th>
                    <th>Direction</th>
                </tr>
            </thead>
            <tbody>
    """

    for idx, row in df.iterrows():
        proximity_class = "positive" if row['proximity_pct'] >= 0 else "negative"
        rank = idx + 1 if isinstance(idx, int) else df.index.get_loc(idx) + 1

        # Determine RSI color class
        rsi_value = row['rsi']
        if rsi_value < 30:
            rsi_class = "rsi-oversold"
        elif rsi_value > 70:
            rsi_class = "rsi-overbought"
        else:
            rsi_class = "rsi-neutral"

        html += f"""
                <tr>
                    <td><strong>{rank}</strong></td>
                    <td><strong>{row['ticker']}</strong></td>
                    <td>${row['current_price']:.2f}</td>
                    <td>${row['sma_200']:.2f}</td>
                    <td class="{proximity_class}"><strong>{row['proximity_pct']:+.2f}%</strong></td>
                    <td class="{rsi_class}"><strong>{row['rsi']:.2f}</strong></td>
                    <td>{row['direction']}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
        <div class="footer">
            <p>Generated on: """ + df.iloc[0]['last_updated'] + """</p>
            <p><strong>Sorting:</strong> Primary by proximity to 200-week SMA, secondary by RSI proximity to 20 (oversold threshold).</p>
            <p><strong>Proximity:</strong> Percentage distance from 200-week SMA. Positive = above SMA, negative = below SMA.</p>
            <p><strong>RSI:</strong> 21-week Relative Strength Index. RSI < 30 (red) = oversold, RSI > 70 (green) = overbought, 30-70 = neutral.</p>
        </div>
    </body>
    </html>
    """

    return html


def send_email(df):
    """
    Send email with stock alert data.

    Args:
        df (pd.DataFrame): DataFrame with top stocks data

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Validate configuration
        config.validate_config()

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = config.EMAIL_SUBJECT
        msg['From'] = config.OUTLOOK_EMAIL
        msg['To'] = config.RECIPIENT_EMAIL

        # Create HTML content
        html_content = create_html_table(df)

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Connect to Outlook SMTP server
        print(f"Connecting to {config.SMTP_SERVER}:{config.SMTP_PORT}...")
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()

        # Login
        print(f"Logging in as {config.OUTLOOK_EMAIL}...")
        server.login(config.OUTLOOK_EMAIL, config.OUTLOOK_PASSWORD)

        # Send email
        print(f"Sending email to {config.RECIPIENT_EMAIL}...")
        server.send_message(msg)

        # Close connection
        server.quit()

        print("Email sent successfully!")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'current_price': [150.25, 380.50, 140.75],
        'sma_200': [148.30, 382.10, 139.90],
        'proximity_pct': [1.31, -0.42, 0.61],
        'abs_proximity': [1.31, 0.42, 0.61],
        'direction': ['Above', 'Below', 'Above'],
        'rsi': [25.50, 47.30, 19.80],
        'rsi_proximity': [5.50, 27.30, 0.20],
        'last_updated': ['2024-02-11 12:00:00'] * 3
    }

    test_df = pd.DataFrame(sample_data)
    print("Testing email with sample data...")
    print(test_df)
    print("\nNote: Email will only send if .env file is configured")
