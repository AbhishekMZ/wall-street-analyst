"""
Technical Analysis Module
Computes RSI, MACD, Bollinger Bands, Moving Averages, support/resistance,
volume trends, and chart pattern signals for Indian stocks.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    pct_b = (series - lower) / (upper - lower)
    return upper, sma, lower, pct_b


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    plus_dm = df["high"].diff()
    minus_dm = -df["low"].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    atr = compute_atr(df, period)
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    adx = dx.rolling(period).mean()
    return adx


def find_support_resistance(df: pd.DataFrame, window: int = 20) -> dict:
    """Find key support and resistance levels using pivot points and recent extremes."""
    recent = df.tail(window)
    high = recent["high"].max()
    low = recent["low"].min()
    close = df["close"].iloc[-1]

    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)

    return {
        "pivot": round(float(pivot), 2),
        "resistance_1": round(float(r1), 2),
        "resistance_2": round(float(r2), 2),
        "support_1": round(float(s1), 2),
        "support_2": round(float(s2), 2),
        "52w_high": round(float(df["high"].tail(252).max()), 2),
        "52w_low": round(float(df["low"].tail(252).min()), 2),
    }


def detect_trend(df: pd.DataFrame) -> dict:
    """Detect current trend using multiple timeframes."""
    close = df["close"]
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    current = close.iloc[-1]
    trends = {}

    # Short-term trend (20-day)
    if len(ma20.dropna()) > 0:
        trends["short_term"] = "bullish" if current > ma20.iloc[-1] else "bearish"
        trends["ma20"] = round(float(ma20.iloc[-1]), 2)

    # Medium-term trend (50-day)
    if len(ma50.dropna()) > 0:
        trends["medium_term"] = "bullish" if current > ma50.iloc[-1] else "bearish"
        trends["ma50"] = round(float(ma50.iloc[-1]), 2)

    # Long-term trend (200-day)
    if len(ma200.dropna()) > 0:
        trends["long_term"] = "bullish" if current > ma200.iloc[-1] else "bearish"
        trends["ma200"] = round(float(ma200.iloc[-1]), 2)

    # Golden/Death cross
    if len(ma50.dropna()) > 1 and len(ma200.dropna()) > 1:
        if ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2]:
            trends["cross"] = "golden_cross"
        elif ma50.iloc[-1] < ma200.iloc[-1] and ma50.iloc[-2] >= ma200.iloc[-2]:
            trends["cross"] = "death_cross"
        else:
            trends["cross"] = "none"

    return trends


def detect_volume_signal(df: pd.DataFrame, window: int = 20) -> dict:
    """Analyze volume patterns for signals."""
    vol = df["volume"]
    avg_vol = vol.rolling(window).mean()

    current_vol = vol.iloc[-1]
    avg = avg_vol.iloc[-1] if not pd.isna(avg_vol.iloc[-1]) else current_vol
    vol_ratio = current_vol / avg if avg > 0 else 1.0

    # Volume trend (5-day)
    recent_avg = vol.tail(5).mean()
    prior_avg = vol.tail(10).head(5).mean()
    vol_trend = "increasing" if recent_avg > prior_avg * 1.1 else (
        "decreasing" if recent_avg < prior_avg * 0.9 else "stable"
    )

    # Delivery estimation (volume spike on up day = accumulation)
    last_row = df.iloc[-1]
    price_change = last_row["close"] - last_row["open"]
    if vol_ratio > 1.5 and price_change > 0:
        signal = "strong_accumulation"
    elif vol_ratio > 1.5 and price_change < 0:
        signal = "strong_distribution"
    elif vol_ratio > 1.2 and price_change > 0:
        signal = "accumulation"
    elif vol_ratio > 1.2 and price_change < 0:
        signal = "distribution"
    else:
        signal = "neutral"

    return {
        "current_volume": int(current_vol),
        "avg_volume": int(avg),
        "volume_ratio": round(float(vol_ratio), 2),
        "volume_trend": vol_trend,
        "signal": signal,
    }


def run_technical_analysis(df: pd.DataFrame) -> dict:
    """Run full technical analysis and return a score (0-100) plus details."""
    if df is None or len(df) < 50:
        return {"score": 50, "details": {}, "signal": "insufficient_data"}

    close = df["close"]
    current_price = float(close.iloc[-1])

    # RSI
    rsi = compute_rsi(close)
    rsi_val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    # MACD
    macd_line, signal_line, histogram = compute_macd(close)
    macd_val = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0
    macd_signal = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0
    macd_hist = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower, bb_pct = compute_bollinger(close)
    bb_pct_val = float(bb_pct.iloc[-1]) if not pd.isna(bb_pct.iloc[-1]) else 0.5

    # ATR for volatility
    atr = compute_atr(df)
    atr_val = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
    atr_pct = (atr_val / current_price) * 100

    # ADX for trend strength
    adx = compute_adx(df)
    adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 25.0

    # Trend detection
    trend = detect_trend(df)

    # Support/Resistance
    sr = find_support_resistance(df)

    # Volume
    vol_signal = detect_volume_signal(df)

    # --- SCORING ---
    score = 50.0  # Start neutral

    # RSI scoring (oversold = bullish, overbought = bearish)
    if rsi_val < 30:
        score += 15  # Oversold — buy signal
    elif rsi_val < 40:
        score += 8
    elif rsi_val > 70:
        score -= 15  # Overbought — sell signal
    elif rsi_val > 60:
        score -= 5

    # MACD scoring
    if macd_val > macd_signal and macd_hist > 0:
        score += 10  # Bullish crossover
        if macd_hist > abs(macd_val * 0.1):
            score += 5  # Strong momentum
    elif macd_val < macd_signal and macd_hist < 0:
        score -= 10  # Bearish crossover

    # Bollinger Band position
    if bb_pct_val < 0.1:
        score += 10  # Near lower band — potential bounce
    elif bb_pct_val < 0.3:
        score += 5
    elif bb_pct_val > 0.9:
        score -= 10  # Near upper band — potential pullback
    elif bb_pct_val > 0.7:
        score -= 5

    # Trend alignment
    bullish_trends = sum(1 for k in ["short_term", "medium_term", "long_term"]
                        if trend.get(k) == "bullish")
    score += (bullish_trends - 1.5) * 8  # -12 to +12

    # Golden/Death cross
    if trend.get("cross") == "golden_cross":
        score += 10
    elif trend.get("cross") == "death_cross":
        score -= 10

    # Volume confirmation
    if vol_signal["signal"] == "strong_accumulation":
        score += 8
    elif vol_signal["signal"] == "accumulation":
        score += 4
    elif vol_signal["signal"] == "strong_distribution":
        score -= 8
    elif vol_signal["signal"] == "distribution":
        score -= 4

    # ADX — strong trend confirmation
    if adx_val > 25:
        # Amplify the direction if trend is strong
        if bullish_trends >= 2:
            score += 5
        elif bullish_trends <= 1:
            score -= 5

    score = max(0, min(100, score))

    # Determine signal
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
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 2),
            "macd": {"line": round(macd_val, 2), "signal": round(macd_signal, 2), "histogram": round(macd_hist, 2)},
            "bollinger": {"upper": round(float(bb_upper.iloc[-1]), 2), "middle": round(float(bb_mid.iloc[-1]), 2),
                          "lower": round(float(bb_lower.iloc[-1]), 2), "pct_b": round(bb_pct_val, 3)},
            "atr": round(atr_val, 2),
            "atr_pct": round(atr_pct, 2),
            "adx": round(adx_val, 2),
            "trend": trend,
            "support_resistance": sr,
            "volume": vol_signal,
        },
    }
