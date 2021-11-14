import os
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

trade_mode = os.environ.get('TRADE_MODE')
PLATFORMS = ["ALPACA", "COINBASE", "BINANCEUS"]

if trade_mode == "LIVE":
    ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY')
    ALPACA_API_SECRET = os.environ.get('ALPACA_API_SECRET')
    ALPACA_BASE_URL = "https://api.alpaca.markets"

    CB_API_KEY = os.environ.get('CB_API_KEY')
    CB_API_SECRET = os.environ.get('CB_API_SECRET')
    CB_PASS_PHRASE = os.environ.get('CB_PASS_PHRASE')
    CB_API_URL="https://api.pro.coinbase.com"

    BN_API_KEY = os.environ.get("BN_API_KEY")
    BN_API_SECRET = os.environ.get("BN_API_SECRET")
else:
    ALPACA_API_KEY = os.environ.get('ALPACA_PAPER_API_KEY')
    ALPACA_API_SECRET = os.environ.get('ALPACA_PAPER_API_SECRET')
    ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

    CB_API_KEY = os.environ.get('CB_SANBOX_API_KEY')
    CB_API_SECRET = os.environ.get('CB_SANBOX_API_SECRET')
    CB_PASS_PHRASE = os.environ.get('CB_SANBOX_PASS_PHRASE')
    CB_API_URL="https://api-public.sandbox.pro.coinbase.com"

    BN_API_KEY = os.environ.get("BN_API_KEY")
    BN_API_SECRET = os.environ.get("BN_API_SECRET")

CB_MARKETS = pd.read_csv("main/CB_MARKET.csv")
