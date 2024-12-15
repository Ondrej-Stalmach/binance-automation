# Binance Automation Extension

This project is an extension to [binance-futures-connector-python](https://github.com/binance/binance-futures-connector-python). It provides additional functionalities to automate trading strategies on Binance Futures, including automated buying of multiple trading pairs, closing all open positions, and more.

## Installation

```bash
pip install binance-futures-connector
```
## RESTful APIs

Usage examples:

```bash

from binance.cm_futures import CMFutures

cm_futures_client = CMFutures()

# get server time
print(cm_futures_client.time())

cm_futures_client = CMFutures(key='<api_key>', secret='<api_secret>')

# Get account information
print(cm_futures_client.account())
