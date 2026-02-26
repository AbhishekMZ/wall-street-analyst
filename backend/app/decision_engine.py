"""
Decision Engine
Combines all analysis modules into a weighted composite score
and generates actionable trading decisions.
"""

import json
import os
from datetime import datetime
from typing import Optional

from .config import WEIGHTS, DB_PATH
from .data_fetcher import fetch_stock_data, fetch_stock_info, fetch_index_data, fetch_global_indicators
from .technical_analysis import run_technical_analysis
from .fundamental_analysis import run_fundamental_analysis
from .momentum_analysis import run_momentum_analysis
from .macro_analysis import analyze_macro_impact
from .learning_engine import get_adapted_weights


def compute_target_and_stoploss(price: float, atr: float, signal: str, sr: dict) -> dict:
    """Compute target price and stop-loss based on ATR and support/resistance."""
    if signal in ("STRONG_BUY", "BUY"):
        stop_loss = max(price - (2.5 * atr), sr.get("support_1", price * 0.95))
        target = min(price + (4 * atr), sr.get("resistance_2", price * 1.15))
        risk = price - stop_loss
        reward = target - price
    elif signal in ("STRONG_SELL", "SELL"):
        stop_loss = min(price + (2.5 * atr), sr.get("resistance_1", price * 1.05))
        target = max(price - (4 * atr), sr.get("support_2", price * 0.85))
        risk = stop_loss - price
        reward = price - target
    else:
        stop_loss = price - (2 * atr)
        target = price + (2 * atr)
        risk = atr * 2
        reward = atr * 2

    rr_ratio = round(reward / risk, 2) if risk > 0 else 0

    return {
        "target_price": round(target, 2),
        "stop_loss": round(stop_loss, 2),
        "risk_reward_ratio": rr_ratio,
    }


def determine_time_horizon(adx: float, atr_pct: float) -> str:
    """Estimate appropriate time horizon based on trend strength and volatility."""
    if adx > 30 and atr_pct < 2:
        return "2-4 weeks"
    elif adx > 25:
        return "1-3 weeks"
    elif atr_pct > 3:
        return "3-7 days"
    else:
        return "1-2 weeks"


def generate_reasoning(tech: dict, fund: dict, momentum: dict, macro: dict) -> list[str]:
    """Generate human-readable reasoning for the decision."""
    reasons = []

    # Technical reasons
    ts = tech.get("score", 50)
    td = tech.get("details", {})
    if ts >= 70:
        reasons.append(f"Strong technical setup with RSI at {td.get('rsi', 'N/A')} and positive MACD crossover")
    elif ts >= 60:
        reasons.append(f"Favorable technical indicators with RSI at {td.get('rsi', 'N/A')}")
    elif ts <= 30:
        reasons.append(f"Weak technical picture with RSI at {td.get('rsi', 'N/A')} signaling bearish momentum")
    elif ts <= 40:
        reasons.append(f"Technical indicators showing caution with RSI at {td.get('rsi', 'N/A')}")

    # Trend
    trend = td.get("trend", {})
    bullish_count = sum(1 for k in ["short_term", "medium_term", "long_term"] if trend.get(k) == "bullish")
    if bullish_count == 3:
        reasons.append("All timeframe trends aligned bullish (20/50/200 DMA)")
    elif bullish_count == 0:
        reasons.append("All timeframe trends bearish — trading below all major moving averages")

    # Volume
    vol = td.get("volume", {})
    if vol.get("signal") == "strong_accumulation":
        reasons.append(f"Heavy accumulation detected — volume {vol.get('volume_ratio', 1)}x average on up move")
    elif vol.get("signal") == "strong_distribution":
        reasons.append("Distribution pattern — high volume selling pressure")

    # Fundamental reasons
    fs = fund.get("score", 50)
    fb = fund.get("breakdown", {})
    if fs >= 65:
        val_d = fb.get("valuation", {}).get("details", {})
        if val_d.get("pe"):
            reasons.append(f"Fundamentally attractive — P/E of {val_d['pe']} vs sector avg {val_d.get('sector_pe', 'N/A')}")
    elif fs <= 35:
        reasons.append("Fundamental concerns — weak valuation or financial health metrics")

    # Growth
    gd = fb.get("growth", {}).get("details", {})
    if gd.get("revenue_growth"):
        reasons.append(f"Revenue growth at {gd['revenue_growth']}")
    if gd.get("earnings_growth"):
        reasons.append(f"Earnings growth at {gd['earnings_growth']}")

    # Momentum
    ms = momentum.get("score", 50)
    md = momentum.get("details", {})
    rs = md.get("relative_strength_vs_nifty")
    if rs is not None and rs > 5:
        reasons.append(f"Outperforming Nifty 50 by {rs}% over 3 months")
    elif rs is not None and rs < -5:
        reasons.append(f"Underperforming Nifty 50 by {abs(rs)}% over 3 months")

    mr = md.get("mean_reversion", {})
    if mr.get("signal") == "strongly_oversold":
        reasons.append(f"Trading {abs(mr.get('deviation_pct', 0))}% below 50-DMA — mean reversion opportunity")

    # Macro
    macro_s = macro.get("score", 50)
    if macro_s >= 60:
        reasons.append(f"Macro environment favorable for {macro.get('sector', 'this sector')}")
    elif macro_s <= 40:
        reasons.append(f"Macro headwinds for {macro.get('sector', 'this sector')}")

    return reasons


def analyze_stock(ticker: str) -> dict:
    """Run full analysis pipeline for a single stock."""
    # Fetch data
    df = fetch_stock_data(ticker)
    if df is None or df.empty:
        return {"error": f"Could not fetch data for {ticker}", "ticker": ticker}

    info = fetch_stock_info(ticker)
    index_df = fetch_index_data("^NSEI")
    global_ind = fetch_global_indicators()

    # Run analysis modules
    tech = run_technical_analysis(df)
    fund = run_fundamental_analysis(info)
    momentum = run_momentum_analysis(df, index_df)
    macro = analyze_macro_impact(global_ind, info.get("sector", "Unknown"))

    # Use self-adapted weights (learning engine) with fallback to defaults
    try:
        weights = get_adapted_weights()
    except Exception:
        weights = dict(WEIGHTS)

    # Weighted composite score
    composite = (
        tech["score"] * weights.get("technical", 0.25) +
        fund["score"] * weights.get("fundamental", 0.20) +
        momentum["score"] * weights.get("momentum", 0.15) +
        macro["score"] * weights.get("macro", 0.10) +
        50 * weights.get("volume_delivery", 0.10) +
        50 * weights.get("sentiment", 0.05) +
        50 * weights.get("seasonal", 0.05) +
        50 * weights.get("global_correlation", 0.05) +
        50 * weights.get("options_flow", 0.05)
    )

    # Determine final action
    if composite >= 72:
        action = "STRONG_BUY"
        confidence = min(95, int(composite + 10))
    elif composite >= 60:
        action = "BUY"
        confidence = int(composite + 5)
    elif composite >= 42:
        action = "HOLD"
        confidence = int(50 + abs(composite - 50))
    elif composite >= 30:
        action = "SELL"
        confidence = int(100 - composite + 5)
    else:
        action = "STRONG_SELL"
        confidence = min(95, int(100 - composite + 10))

    confidence = max(30, min(95, confidence))

    # Compute targets
    atr = tech["details"].get("atr", 0)
    sr = tech["details"].get("support_resistance", {})
    price = tech["details"].get("price", 0)
    targets = compute_target_and_stoploss(price, atr, action, sr)

    # Time horizon
    adx = tech["details"].get("adx", 25)
    atr_pct = tech["details"].get("atr_pct", 2)
    time_horizon = determine_time_horizon(adx, atr_pct)

    # Risk rating (1-10, where 10 = highest risk)
    risk_rating = 5
    if info.get("beta") is not None:
        beta = float(info["beta"])
        risk_rating = max(1, min(10, int(beta * 4 + atr_pct)))

    # Reasoning
    reasons = generate_reasoning(tech, fund, momentum, macro)

    return {
        "ticker": ticker,
        "name": info.get("name", ticker.replace(".NS", "")),
        "sector": info.get("sector", "Unknown"),
        "action": action,
        "confidence": confidence,
        "composite_score": round(composite, 1),
        "price": price,
        "target_price": targets["target_price"],
        "stop_loss": targets["stop_loss"],
        "risk_reward_ratio": targets["risk_reward_ratio"],
        "time_horizon": time_horizon,
        "risk_rating": risk_rating,
        "reasoning": reasons,
        "scores": {
            "technical": tech["score"],
            "fundamental": fund["score"],
            "momentum": momentum["score"],
            "macro": macro["score"],
        },
        "analysis": {
            "technical": tech,
            "fundamental": fund,
            "momentum": momentum,
            "macro": macro,
        },
        "timestamp": datetime.now().isoformat(),
    }


def save_decision(decision: dict):
    """Persist a decision to the JSON store for tracking."""
    decisions = []
    if DB_PATH.exists():
        try:
            with open(DB_PATH, "r") as f:
                decisions = json.load(f)
        except (json.JSONDecodeError, IOError):
            decisions = []

    decisions.append(decision)

    with open(DB_PATH, "w") as f:
        json.dump(decisions, f, indent=2, default=str)


def load_decisions() -> list:
    """Load all saved decisions."""
    if not DB_PATH.exists():
        return []
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
