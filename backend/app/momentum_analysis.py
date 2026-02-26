"""
Momentum & Trend Analysis Module
Computes relative strength, price momentum, and mean reversion signals.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_returns(close: pd.Series) -> dict:
    """Compute returns across multiple timeframes."""
    current = float(close.iloc[-1])
    returns = {}

    periods = {
        "1d": 1, "5d": 5, "1m": 22, "3m": 66, "6m": 132, "1y": 252,
    }
    for label, days in periods.items():
        if len(close) > days:
            prev = float(close.iloc[-(days + 1)])
            returns[label] = round(((current - prev) / prev) * 100, 2)

    return returns


def compute_relative_strength(stock_close: pd.Series, index_close: pd.Series, period: int = 66) -> Optional[float]:
    """Compute relative strength vs benchmark (Nifty 50)."""
    if len(stock_close) < period or len(index_close) < period:
        return None

    stock_return = (stock_close.iloc[-1] / stock_close.iloc[-period]) - 1
    index_return = (index_close.iloc[-1] / index_close.iloc[-period]) - 1

    if index_return == 0:
        return 0.0
    return round(float((stock_return - index_return) * 100), 2)


def compute_rate_of_change(close: pd.Series, period: int = 14) -> pd.Series:
    """Rate of change indicator."""
    return ((close - close.shift(period)) / close.shift(period)) * 100


def detect_momentum_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 30) -> str:
    """Detect bullish/bearish divergence between price and RSI."""
    if len(close) < lookback or len(rsi) < lookback:
        return "none"

    recent_close = close.tail(lookback)
    recent_rsi = rsi.tail(lookback)

    # Find price lows and RSI lows
    price_min_idx = recent_close.idxmin()
    price_min_2 = recent_close.loc[:price_min_idx].iloc[:-1].idxmin() if len(recent_close.loc[:price_min_idx]) > 1 else price_min_idx

    # Bullish divergence: price makes lower low, RSI makes higher low
    if price_min_idx != price_min_2:
        if recent_close[price_min_idx] < recent_close[price_min_2]:
            if recent_rsi[price_min_idx] > recent_rsi[price_min_2]:
                return "bullish"

    # Find price highs and RSI highs
    price_max_idx = recent_close.idxmax()
    price_max_2 = recent_close.loc[:price_max_idx].iloc[:-1].idxmax() if len(recent_close.loc[:price_max_idx]) > 1 else price_max_idx

    # Bearish divergence: price makes higher high, RSI makes lower high
    if price_max_idx != price_max_2:
        if recent_close[price_max_idx] > recent_close[price_max_2]:
            if recent_rsi[price_max_idx] < recent_rsi[price_max_2]:
                return "bearish"

    return "none"


def compute_mean_reversion_signal(close: pd.Series, period: int = 50) -> dict:
    """Check if stock is mean-reverting (deviation from moving average)."""
    ma = close.rolling(period).mean()
    if pd.isna(ma.iloc[-1]):
        return {"deviation_pct": 0, "signal": "neutral"}

    current = float(close.iloc[-1])
    ma_val = float(ma.iloc[-1])
    deviation = ((current - ma_val) / ma_val) * 100

    if deviation < -15:
        signal = "strongly_oversold"
    elif deviation < -8:
        signal = "oversold"
    elif deviation > 15:
        signal = "strongly_overbought"
    elif deviation > 8:
        signal = "overbought"
    else:
        signal = "neutral"

    return {
        "deviation_pct": round(deviation, 2),
        "ma_value": round(ma_val, 2),
        "signal": signal,
    }


def run_momentum_analysis(df: pd.DataFrame, index_df: Optional[pd.DataFrame] = None) -> dict:
    """Run full momentum analysis and return score (0-100)."""
    if df is None or len(df) < 30:
        return {"score": 50, "details": {}, "signal": "insufficient_data"}

    close = df["close"]
    score = 50.0

    # Returns
    returns = compute_returns(close)

    # Short-term momentum (1m)
    r1m = returns.get("1m", 0)
    if r1m > 10:
        score += 10
    elif r1m > 5:
        score += 5
    elif r1m < -10:
        score -= 8
    elif r1m < -5:
        score -= 4

    # Medium-term momentum (3m)
    r3m = returns.get("3m", 0)
    if r3m > 20:
        score += 12
    elif r3m > 10:
        score += 6
    elif r3m < -15:
        score -= 10
    elif r3m < -8:
        score -= 5

    # Relative strength vs Nifty
    rs = None
    if index_df is not None and len(index_df) > 66:
        rs = compute_relative_strength(close, index_df["close"])
        if rs is not None:
            if rs > 10:
                score += 10  # Outperforming significantly
            elif rs > 5:
                score += 5
            elif rs < -10:
                score -= 8
            elif rs < -5:
                score -= 4

    # Rate of change
    roc = compute_rate_of_change(close, 14)
    roc_val = float(roc.iloc[-1]) if not pd.isna(roc.iloc[-1]) else 0
    if roc_val > 8:
        score += 5
    elif roc_val < -8:
        score -= 5

    # Mean reversion
    mr = compute_mean_reversion_signal(close)
    if mr["signal"] == "strongly_oversold":
        score += 10  # Mean reversion opportunity
    elif mr["signal"] == "oversold":
        score += 5
    elif mr["signal"] == "strongly_overbought":
        score -= 8
    elif mr["signal"] == "overbought":
        score -= 4

    score = max(0, min(100, score))

    if score >= 75:
        signal = "STRONG_BUY"
    elif score >= 60:
        signal = "BUY"
    elif score >= 40:
        signal = "HOLD"
    elif score >= 25:
        signal = "SELL"
    else:
        signal = "STRONG_SELL"

    return {
        "score": round(score, 1),
        "signal": signal,
        "details": {
            "returns": returns,
            "relative_strength_vs_nifty": rs,
            "rate_of_change_14d": round(roc_val, 2),
            "mean_reversion": mr,
        },
    }
