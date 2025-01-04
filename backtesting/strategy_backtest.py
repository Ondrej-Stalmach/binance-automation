import os
import pandas as pd
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import mplcursors

# Load data
# file_path = os.path.join('backtesting', 'trading_pairs_klines.xlsx')
# df = pd.read_excel(file_path)

file_path = os.path.join('backtesting', 'coinmarketcap_historical_data.csv')
# Read the CSV file into a DataFrame
full_df = pd.read_csv(file_path)

# Convert the string-encoded "openTime" column to datetime objects
# The parameter 'format="%Y%m%d"' specifies the date format,
# e.g. "20130602" -> June 2, 2013
full_df["openTime"] = pd.to_datetime(full_df["openTime"], format="%Y%m%d")

# Define the range of dates you want to filter
# You can choose any date format recognized by pandas (e.g. "YYYY-MM-DD")

# Bullrun 2017
# start_date = "2017-02-19"
# end_date   = "2017-12-31"

# Bullrun 2021
start_date = "2020-12-13"
end_date   = "2021-12-31"

# Create a boolean mask to select rows where the "openTime" column
# falls within the specified range [start_date, end_date]
mask = (full_df["openTime"] >= start_date) & (full_df["openTime"] <= end_date)

# Filter the DataFrame using the mask
df = full_df.loc[mask]

# Calculate the cumulative percentage change for each cryptocurrency
# Compare each price to the FIRST price for that crypto
# The first day will show 0.0 (no change from itself),
# and subsequent days will show the percentage change from that first price
df["cumulativeOC"] = df.groupby("name")["price"].transform(
    lambda x: (x / x.iloc[0] - 1) * 100
)

initial_capital = 5000
top_n = 40

# Unique dates
unique_dates = (
    df['openTime']
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)  # vytvorí nový 0-based index
)

# Initialize variables
portfolio = defaultdict(float)  # crypto -> unitsHeld
cash = initial_capital

# Results dateFrame
results = pd.DataFrame(columns=['openTime', 'name', 'Action', 'price', 'Units', 'Value'])
portfolio_history = pd.DataFrame(columns=['openTime', 'PortfolioValue'])

# Iterate through unique dates
for i, current_date in enumerate(unique_dates):
    if i >= 1:
        # Data for the current date
        day_data = df[df['openTime'] == current_date]
        
        # Data for the previous date
        prev_day_data = df[df['openTime'] == unique_dates[i - 1]]
        # Sort cryptocurrencies by 'cumulativeOC' descending
        day_data = day_data.sort_values('cumulativeOC', ascending=False)
        
        # Select top N cryptocurrencies
        top_n_cryptos = day_data.head(top_n)

        # Sell all holdings
        for crypto_name in list(portfolio.keys()):
            sell_data = day_data[day_data['name'] == crypto_name]
            if not sell_data.empty:
                sell_price = sell_data['price'].iloc[0] * (1 - 0.0005)
                units_held = portfolio[crypto_name]
                sell_value = units_held * sell_price

                # Record the sale
                results = pd.concat([
                    results,
                    pd.DataFrame({
                        'openTime': [current_date],
                        'name': [crypto_name],
                        'Action': ['Sell'],
                        'price': [sell_price],
                        'Units': [units_held],
                        'Value': [sell_value]
                    })
                ])
            else:
                # Some cryptocurrencies are removed from the CoinMarketCap top 200 over time, 
                # so we calculate their value with a 20% reduction.
                sell_data = prev_day_data[prev_day_data['name'] == crypto_name]
                sell_price = sell_data['price'].iloc[0] * (0.8 - 0.0005)
                units_held = portfolio[crypto_name]
                sell_value = units_held * sell_price

                # Record the sale
                results = pd.concat([
                    results,
                    pd.DataFrame({
                        'openTime': [current_date],
                        'name': [crypto_name],
                        'Action': ['Sell'],
                        'price': [sell_price],
                        'Units': [units_held],
                        'Value': [sell_value]
                    })
                ])

                # Update cash
            cash += sell_value

        # Clear the portfolio
        portfolio.clear()

        # Buy top N cryptocurrencies
        if top_n > 0:
            capital_per_crypto = cash / top_n
            for _, row in top_n_cryptos.iterrows():
                crypto_name = row['name']
                buy_price = row['price'] * (1 + 0.0005)
                units_to_buy = capital_per_crypto / buy_price
                buy_value = units_to_buy * buy_price

                # Record the purchase
                results = pd.concat([
                    results,
                    pd.DataFrame({
                        'openTime': [current_date],
                        'name': [crypto_name],
                        'Action': ['Buy'],
                        'price': [buy_price],
                        'Units': [units_to_buy],
                        'Value': [buy_value]
                    })
                ])

                # Update cash and portfolio
                cash -= buy_value
                portfolio[crypto_name] += units_to_buy

        # Calculate portfolio value
        day_value = cash
        for crypto_name, units in portfolio.items():
            current_data = day_data[day_data['name'] == crypto_name]
            if not current_data.empty:
                current_price = current_data['price'].iloc[0]
                day_value += units * current_price

        portfolio_history = pd.concat([
            portfolio_history,
            pd.DataFrame({'openTime': [current_date], 'PortfolioValue': [day_value]})
        ])
    else:
        portfolio_history = pd.concat([
            portfolio_history,
            pd.DataFrame({'openTime': [current_date], 'PortfolioValue': [initial_capital]})
        ])

portfolio_history["PortfolioValue"] = pd.to_numeric(portfolio_history["PortfolioValue"], errors="coerce").round(0)

# Plot results
plt.figure(figsize=(12, 6))
bars = plt.bar(
    portfolio_history["openTime"], 
    portfolio_history["PortfolioValue"], 
    width=4.0,             
    alpha=0.5, 
    label="Top 40"
)
cursor = mplcursors.cursor(bars)

# BTC-specific calculations
btc_data = df[df['name'] == 'BTC']
sum_oc_btc = btc_data['cumulativeOC'] * 0.01 * 5000 + 5000
plt.bar(
    btc_data['openTime'], 
    sum_oc_btc, 
    color=[0.9290, 0.6940, 0.1250],
    width=4.0, 
    alpha=0.7, 
    label='BTC')

# EMA of portfolio value
portfolio_history['EMA14'] = portfolio_history['PortfolioValue'].ewm(span=14, adjust=False).mean()
plt.plot(portfolio_history['openTime'], portfolio_history['EMA14'], label='EMA14')
plt.xlabel('Weeks')
plt.ylabel('Portfolio Value (USD)')
plt.legend()
plt.grid(True)
plt.show()

#portfolio_history.to_excel("portfolio_history.xlsx", index=False)
#results.to_excel("results.xlsx", index=False)
