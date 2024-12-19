import pandas as pd
import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

# Load data
full_tab = pd.read_excel('trading_pairs_klines.xlsx')
initial_capital = 5000
top_n = 30

# Unique days
unique_dates = full_tab['openTime'].drop_duplicates().sort_values()

# Initialize variables
portfolio = defaultdict(float)  # crypto -> unitsHeld
cash = initial_capital

# Results table
results = pd.DataFrame(columns=['openTime', 'name', 'Action', 'close', 'Units', 'Value'])
portfolio_history = pd.DataFrame(columns=['openTime', 'PortfolioValue'])

# Iterate through unique dates
for i, current_date in enumerate(unique_dates):
    if i >= 1:
        # Data for the current day
        day_data = full_tab[full_tab['openTime'] == current_date]

        # Sort cryptocurrencies by 'cumulativeOC' descending
        day_data = day_data.sort_values('cumulativeOC', ascending=False)
        
        # Select top N cryptocurrencies
        top_n_cryptos = day_data.head(top_n)

        # Sell all holdings
        for crypto_name in list(portfolio.keys()):
            sell_data = day_data[day_data['name'] == crypto_name]
            if not sell_data.empty:
                sell_price = sell_data['close'].iloc[0] * (1 - 0.0005)
                units_held = portfolio[crypto_name]
                sell_value = units_held * sell_price

                # Record the sale
                results = pd.concat([
                    results,
                    pd.DataFrame({
                        'openTime': [current_date],
                        'name': [crypto_name],
                        'Action': ['Sell'],
                        'close': [sell_price],
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
                buy_price = row['close'] * (1 + 0.0005)
                units_to_buy = capital_per_crypto / buy_price
                buy_value = units_to_buy * buy_price

                # Record the purchase
                results = pd.concat([
                    results,
                    pd.DataFrame({
                        'openTime': [current_date],
                        'name': [crypto_name],
                        'Action': ['Buy'],
                        'close': [buy_price],
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
                current_price = current_data['close'].iloc[0]
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

# Plot results
plt.figure(figsize=(12, 6))
plt.bar(portfolio_history['openTime'], portfolio_history['PortfolioValue'], alpha=0.5, label='Top 30')

# BTC-specific calculations
btc_data = full_tab[full_tab['name'] == 'BTCUSDT']
sum_oc_btc = btc_data['cumulativeOC'] * 0.01 * 5000 + 5000
plt.bar(btc_data['openTime'], sum_oc_btc, color=[0.9290, 0.6940, 0.1250], alpha=0.5, label='BTC')

# EMA of portfolio value
portfolio_history['EMA14'] = portfolio_history['PortfolioValue'].ewm(span=14, adjust=False).mean()
plt.plot(portfolio_history['openTime'], portfolio_history['EMA14'], label=top_n)

# Finalize plot
plt.xlabel('Weeks')
plt.ylabel('Portfolio Value (USD)')
plt.legend()
plt.grid(True)
plt.show()
#portfolio_history.to_excel("portfolio_history.xlsx", index=False)
#results.to_excel("results.xlsx", index=False)
