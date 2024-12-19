from datetime import datetime
import pandas as pd
import requests
import pandas as pd


def get_USDT_trading_pairs():

    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(url)
    data = response.json()

    trading_pairs = [
        symbol["symbol"]
        for symbol in data["symbols"]
        if symbol["quoteAsset"] == "USDT" and "_" not in symbol["symbol"]
    ]
    return trading_pairs


def get_klines(symbol, interval, start_date, end_date):
    """
    Fetch kline data from Binance API for a specific symbol and interval.

    :param symbol: Trading pair symbol, e.g., 'BTCUSDT'
    :param interval: Kline interval, e.g., '1d'
    :param start_date: Start date in 'DD.MM.YYYY' format
    :param end_date: End date in 'DD.MM.YYYY' format
    :return: DataFrame containing kline data
    """
    base_url = "https://api.binance.com/api/v3/klines"
    start_timestamp = start_date
    end_timestamp = end_date

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_timestamp,
        "endTime": end_timestamp,
        "limit": 1000,  # Maximum number of records per request
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        # Create DataFrame from the received data
        df = pd.DataFrame(
            data,
            columns=[
                "openTime",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "closeTime",
                "quoteAssetVolume",
                "numberOfTrades",
                "takerBuyBaseAssetVolume",
                "takerBuyQuoteAssetVolume",
                "ignore",
            ],
        )

        # Convert timestamps to datetime objects
        df["openTime"] = pd.to_datetime(df["openTime"], unit="ms")
        df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms")
    except:
        df = []
    return df


def get_klines_futures(symbol, interval, start_date, end_date):

    base_url = "https://fapi.binance.com/fapi/v1/klines"
    start_timestamp = start_date
    end_timestamp = end_date

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_timestamp,
        "endTime": end_timestamp,
        "limit": 1000,
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        df = pd.DataFrame(
            data,
            columns=[
                "openTime",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "closeTime",
                "quoteAssetVolume",
                "numberOfTrades",
                "takerBuyBaseAssetVolume",
                "takerBuyQuoteAssetVolume",
                "ignore",
            ],
        )

        df["openTime"] = pd.to_datetime(df["openTime"], unit="ms")
        df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms")
    except:
        df = []

    return df


def download_data():

    # Bullrun 2021
    start_date = "16.12.2020"
    end_date = "31.12.2021"

    # Bullrun 2024
    #start_date = "05.11.2024"
    #end_date = datetime.now().strftime("%d.%m.%Y")

    # Convert dates to milliseconds
    start_time = int(datetime.strptime(start_date, "%d.%m.%Y").timestamp() * 1000)
    end_time = int(datetime.strptime(end_date, "%d.%m.%Y").timestamp() * 1000)

    # Fetch all trading pairs
    trading_pairs = get_USDT_trading_pairs()

    all_data = []

    for pair in trading_pairs:

        # 1st Try to fetch kline data from spot market
        klines = get_klines(pair, "1d", start_time, end_time)

        if klines.empty:
            # 2nd Try to fetch kline data from futures market
            klines = get_klines_futures(pair, "1d", start_time, end_time)

        if klines.empty or klines.shape[0] < 2:
            continue

        klines = klines.iloc[1:]
        first_close = klines.iat[0, 4]

        for row in klines.itertuples(index=False):
            all_data.append(
                {
                    "name": pair,
                    "openTime": row.openTime,
                    "open": float(row.open),
                    "close": float(row.close),
                    "openClose": round(
                        ((float(row.close) - float(row.open)) / float(row.open)) * 100,
                        2,
                    ),
                    "cumulativeOC": round(
                        ((float(row.close) - float(first_close)) / float(first_close))
                        * 100,
                        2,
                    ),
                }
            )

        print(pair)

    # Create DataFrame
    df = pd.DataFrame(all_data)

    # Save to Excel
    df.to_excel("trading_pairs_klines.xlsx", index=False)
    print("Data has been saved to trading_pairs_klines.xlsx")


if __name__ == "__main__":
    download_data()