import os
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from dotenv import load_dotenv

config_logging(logging, logging.INFO, log_file="logs/binance.log") 

# Load environment variables from .env file
load_dotenv(dotenv_path="config.env")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize client with API key and secret
try:
    if not API_KEY or not API_SECRET:
        raise ValueError("API keys are not set.")
    client = UMFutures(key=API_KEY, secret=API_SECRET)
    logging.info("Binance Futures client initialized successfully.")
except ValueError as e:
    logging.error(f"Initialization Error: {e}")
    client = None # Set client to None to indicate initialization failure

def get_account_status():
    """
    Retrieves account status, including open positions and USDT balance.

    Returns:
        tuple: A tuple containing:
            - list: A list of open positions (list of dictionaries).
            - float: The available USDT balance.
        Returns None, None in case of an error.
    """
    if client is None: # Check if the client was initialized
        logging.error("Binance Futures client is not initialized. Cannot get account status.")
        return None, None
    try:

        account_info = client.account(recvWindow=6000)

        logging.info("Account information retrieved successfully.")
        # logging.debug(f"Account details: {account_info}")

        positions = account_info.get("positions", [])
        open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]

        formatted_positions = []
        for position in open_positions:
            formatted_positions.append({
                "symbol": position.get("symbol"),
                "positionAmt": float(position.get("positionAmt")),
                "unrealizedProfit": float(position.get("unrealizedProfit")),
            })

        balances = account_info.get("assets", [])
        usdt_balance = next((float(b.get("availableBalance", 0)) for b in balances if b.get("asset") == "BNFCR"), 0.0)

        return formatted_positions, usdt_balance

    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return None, None
    except Exception as e:
        logging.exception(f"Unexpected error while retrieving account information: {e}")
        return None, None

def sell_crypto_market(symbol, quantity):
    """
    Sells a specified quantity of a crypto asset at market price.

    Args:
        symbol (str): The symbol of the crypto asset (e.g., "BTCUSDT").
        quantity (float): The quantity to sell.

    Returns:
        dict: The order information in case of success, None in case of failure.
    """
    if client is None:
        logging.error("Binance Futures client is not initialized. Cannot execute sell order.")
        return None

    try:
        logging.info(f"Attempting to sell {quantity} {symbol} at market price.")

        order = client.new_order(
            symbol=symbol,
            side="SELL",
            positionSide='LONG',
            type="MARKET",
            quantity=quantity,
            recvWindow=6000
        )

        logging.info(f"Sell order successful: {order}")
        return order

    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return None
    except ValueError as e:
        logging.error(f"Validation Error: {e}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error during selling: {e}")
        return None


def buy_crypto_market(symbol, quantityUSD):
    """
    Buys a specified value of a crypto asset in USDT at market price.

    Args:
        symbol (str): The symbol of the crypto asset (e.g., "BTCUSDT").
        quantityUSD (float): The purchase value in USDT.

    Returns:
        dict: The order information on success, None on failure.
    """
    quantityUSD = int(quantityUSD)

    if client is None:
        logging.error("Binance Futures client is not initialized. Cannot execute buy order.")
        return None

    try:
        logging.info(f"Attempting to buy {symbol} with {quantityUSD} USDT at market price.")

        # Get the current price
        ticker = client.ticker_price(symbol=symbol)
        current_price = float(ticker["price"])

        logging.debug(f"Current price of {symbol}: {current_price}")
        quantity = quantityUSD / current_price

        # Calculate the quantity to buy
        if quantity >= 1:
            quantity = int(quantity)
        else:
            quantity_str = str(quantity)
            decimal_part = quantity_str.split('.')[1] if '.' in quantity_str else '0'
            first_nonzero_index = next((i for i, digit in enumerate(decimal_part) if digit != '0'), None)
            round_param = first_nonzero_index + 2
            quantity = round(quantity,round_param)

        
        # Create the order
        order = client.new_order(
            symbol=symbol,
            side="BUY",
            positionSide='LONG',
            type="MARKET",
            quantity=quantity,
            recvWindow=6000
        )

        logging.info(f"Buy order successful: {order}")
        return order

    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return None
    except ZeroDivisionError:
        logging.error(f"ZeroDivisionError: Current price of {symbol} is zero. Cannot calculate quantity.")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error during buying: {e}")
        return None

if __name__ == "__main__":
    open_positions, usdt_balance = get_account_status()
    # buy_crypto_market("ETHUSDT", 50)
    sell_crypto_market("ETHUSDT", 0.14)