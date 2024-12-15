import os
from binance.um_futures import UMFutures
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="config.env")
# Retrieve API keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
# Initialize client with API key and secret
client = UMFutures(key=API_KEY, secret=API_SECRET)

def check_account_status():
    print(client.account())

if __name__ == "__main__":
    check_account_status()