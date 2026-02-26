import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "decisions.json"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Default universe — Nifty 50 + high-volume mid-caps
NIFTY50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "HCLTECH.NS", "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "ONGC.NS", "JSWSTEEL.NS", "COALINDIA.NS",
    "BAJAJFINSV.NS", "TECHM.NS", "NESTLEIND.NS", "DIVISLAB.NS", "DRREDDY.NS",
    "GRASIM.NS", "CIPLA.NS", "BRITANNIA.NS", "HEROMOTOCO.NS", "EICHERMOT.NS",
    "APOLLOHOSP.NS", "SBILIFE.NS", "HDFCLIFE.NS", "TATACONSUM.NS", "BPCL.NS",
    "INDUSINDBK.NS", "HINDALCO.NS", "UPL.NS", "LTIM.NS", "SHRIRAMFIN.NS",
]

# Scoring weights for the decision engine
WEIGHTS = {
    "technical": 0.25,
    "fundamental": 0.20,
    "momentum": 0.15,
    "volume_delivery": 0.10,
    "macro": 0.10,
    "sentiment": 0.05,
    "seasonal": 0.05,
    "global_correlation": 0.05,
    "options_flow": 0.05,
}

# Analysis lookback periods
LOOKBACK_DAYS = 365
SHORT_MA = 20
MEDIUM_MA = 50
LONG_MA = 200
