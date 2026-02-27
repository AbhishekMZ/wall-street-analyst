"""
Data fetching module for Indian stock market data.
Uses Yahoo Finance for NSE/BSE stocks.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from .config import LOOKBACK_DAYS


def fetch_stock_data(ticker: str, period_days: int = LOOKBACK_DAYS) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data for an Indian stock from Yahoo Finance."""
    for attempt in range(2):
        try:
            end = datetime.now()
            start = end - timedelta(days=period_days)
            stock = yf.Ticker(ticker)
            df = stock.history(start=start, end=end)
            if df.empty:
                # Try with period parameter as fallback
                period_map = {30: "1mo", 90: "3mo", 365: "1y"}
                period_str = period_map.get(period_days, "1y")
                df = stock.history(period=period_str)
            if df.empty:
                return None
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume"
            })
            return df
        except Exception as e:
            print(f"Error fetching {ticker} (attempt {attempt+1}): {e}")
            if attempt == 0:
                import time
                time.sleep(1)
    return None


def fetch_stock_info(ticker: str) -> dict:
    """Fetch fundamental info for a stock."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        if not info or len(info) < 5:
            print(f"Warning: minimal info returned for {ticker}: {list(info.keys())[:5]}")
        return {
            "name": info.get("longName", ticker.replace(".NS", "")),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "forward_pe": info.get("forwardPE", None),
            "pb_ratio": info.get("priceToBook", None),
            "dividend_yield": info.get("dividendYield", 0) or 0,
            "roe": info.get("returnOnEquity", None),
            "roa": info.get("returnOnAssets", None),
            "debt_to_equity": info.get("debtToEquity", None),
            "current_ratio": info.get("currentRatio", None),
            "revenue_growth": info.get("revenueGrowth", None),
            "earnings_growth": info.get("earningsGrowth", None),
            "profit_margin": info.get("profitMargins", None),
            "operating_margin": info.get("operatingMargins", None),
            "free_cash_flow": info.get("freeCashflow", None),
            "total_revenue": info.get("totalRevenue", None),
            "total_debt": info.get("totalDebt", None),
            "total_cash": info.get("totalCash", None),
            "beta": info.get("beta", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "50d_avg": info.get("fiftyDayAverage", None),
            "200d_avg": info.get("twoHundredDayAverage", None),
            "avg_volume": info.get("averageVolume", None),
            "shares_outstanding": info.get("sharesOutstanding", None),
            "book_value": info.get("bookValue", None),
            "eps": info.get("trailingEps", None),
            "forward_eps": info.get("forwardEps", None),
            "peg_ratio": info.get("pegRatio", None),
        }
    except Exception as e:
        print(f"Error fetching info for {ticker}: {e}")
        return {"name": ticker, "sector": "Unknown"}


def fetch_index_data(index: str = "^NSEI", period_days: int = LOOKBACK_DAYS) -> Optional[pd.DataFrame]:
    """Fetch index data (Nifty 50, Sensex, etc.)."""
    return fetch_stock_data(index, period_days)


def fetch_global_indicators(period_days: int = 90) -> dict:
    """Fetch global correlation indicators relevant to Indian market."""
    indicators = {}
    tickers = {
        "nifty": "^NSEI",
        "sensex": "^BSESN",
        "sp500": "^GSPC",
        "dxy": "DX-Y.NYB",
        "crude_oil": "CL=F",
        "gold": "GC=F",
        "usdinr": "INR=X",
        "us10y": "^TNX",
        "vix_india": "^INDIAVIX",
    }
    for name, ticker in tickers.items():
        try:
            df = fetch_stock_data(ticker, period_days)
            if df is not None and not df.empty:
                current = df["close"].iloc[-1]
                prev_week = df["close"].iloc[-5] if len(df) >= 5 else current
                prev_month = df["close"].iloc[-22] if len(df) >= 22 else current
                indicators[name] = {
                    "current": round(float(current), 2),
                    "week_change_pct": round(((current - prev_week) / prev_week) * 100, 2),
                    "month_change_pct": round(((current - prev_month) / prev_month) * 100, 2),
                }
        except Exception:
            pass
    return indicators
