"""
Report Generator Module
Generates weekly performance reports by comparing decisions against actual prices.
Tracks hit rate, P&L, and builds trust metrics over time.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from .config import REPORTS_DIR
from .data_fetcher import fetch_stock_data
from .decision_engine import load_decisions


def evaluate_decision(decision: dict) -> dict:
    """Evaluate a past decision against current/actual price."""
    ticker = decision["ticker"]
    entry_price = decision["price"]
    target = decision["target_price"]
    stop_loss = decision["stop_loss"]
    action = decision["action"]
    timestamp = decision["timestamp"]

    df = fetch_stock_data(ticker, period_days=30)
    if df is None or df.empty:
        return {**decision, "evaluation": "data_unavailable"}

    current_price = float(df["close"].iloc[-1])
    high_since = float(df["high"].max())
    low_since = float(df["low"].min())

    if action in ("STRONG_BUY", "BUY"):
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        hit_target = high_since >= target
        hit_stoploss = low_since <= stop_loss
        if hit_target:
            outcome = "TARGET_HIT"
            realized_pnl = ((target - entry_price) / entry_price) * 100
        elif hit_stoploss:
            outcome = "STOPLOSS_HIT"
            realized_pnl = ((stop_loss - entry_price) / entry_price) * 100
        else:
            outcome = "OPEN"
            realized_pnl = pnl_pct
    elif action in ("STRONG_SELL", "SELL"):
        pnl_pct = ((entry_price - current_price) / entry_price) * 100
        hit_target = low_since <= target
        hit_stoploss = high_since >= stop_loss
        if hit_target:
            outcome = "TARGET_HIT"
            realized_pnl = ((entry_price - target) / entry_price) * 100
        elif hit_stoploss:
            outcome = "STOPLOSS_HIT"
            realized_pnl = ((entry_price - stop_loss) / entry_price) * 100
        else:
            outcome = "OPEN"
            realized_pnl = pnl_pct
    else:
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        outcome = "HOLD"
        realized_pnl = pnl_pct

    return {
        **decision,
        "current_price": round(current_price, 2),
        "high_since": round(high_since, 2),
        "low_since": round(low_since, 2),
        "pnl_pct": round(pnl_pct, 2),
        "realized_pnl_pct": round(realized_pnl, 2),
        "outcome": outcome,
        "evaluated_at": datetime.now().isoformat(),
    }


def generate_weekly_report() -> dict:
    """Generate a weekly performance report."""
    decisions = load_decisions()
    if not decisions:
        return {"error": "No decisions to evaluate", "decisions": []}

    # Filter decisions from last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    recent = []
    for d in decisions:
        try:
            dt = datetime.fromisoformat(d["timestamp"])
            if dt >= week_ago:
                recent.append(d)
        except (ValueError, KeyError):
            pass

    if not recent:
        # Evaluate all decisions if none from this week
        recent = decisions[-20:]  # Last 20 decisions

    # Evaluate each decision
    evaluated = []
    for d in recent:
        try:
            result = evaluate_decision(d)
            evaluated.append(result)
        except Exception as e:
            evaluated.append({**d, "evaluation_error": str(e)})

    # Aggregate stats
    total = len(evaluated)
    winners = sum(1 for e in evaluated if e.get("pnl_pct", 0) > 0)
    losers = sum(1 for e in evaluated if e.get("pnl_pct", 0) < 0)
    targets_hit = sum(1 for e in evaluated if e.get("outcome") == "TARGET_HIT")
    stoplosses_hit = sum(1 for e in evaluated if e.get("outcome") == "STOPLOSS_HIT")

    pnl_values = [e.get("pnl_pct", 0) for e in evaluated if "pnl_pct" in e]
    avg_pnl = sum(pnl_values) / len(pnl_values) if pnl_values else 0
    total_pnl = sum(pnl_values)
    best_trade = max(pnl_values) if pnl_values else 0
    worst_trade = min(pnl_values) if pnl_values else 0
    hit_rate = (winners / total * 100) if total > 0 else 0

    # Sector breakdown
    sector_pnl: dict[str, list[float]] = {}
    for e in evaluated:
        sector = e.get("sector", "Unknown")
        if sector not in sector_pnl:
            sector_pnl[sector] = []
        sector_pnl[sector].append(e.get("pnl_pct", 0))

    sector_summary = {}
    for sector, pnls in sector_pnl.items():
        sector_summary[sector] = {
            "count": len(pnls),
            "avg_pnl": round(sum(pnls) / len(pnls), 2),
            "total_pnl": round(sum(pnls), 2),
        }

    report = {
        "report_date": datetime.now().isoformat(),
        "period": "weekly",
        "summary": {
            "total_decisions": total,
            "winners": winners,
            "losers": losers,
            "hit_rate_pct": round(hit_rate, 1),
            "targets_hit": targets_hit,
            "stoplosses_hit": stoplosses_hit,
            "avg_pnl_pct": round(avg_pnl, 2),
            "total_pnl_pct": round(total_pnl, 2),
            "best_trade_pnl_pct": round(best_trade, 2),
            "worst_trade_pnl_pct": round(worst_trade, 2),
        },
        "sector_breakdown": sector_summary,
        "decisions": evaluated,
    }

    # Save report
    report_file = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return report


def generate_cumulative_report() -> dict:
    """Generate cumulative performance across all time."""
    decisions = load_decisions()
    if not decisions:
        return {"error": "No decisions to evaluate"}

    evaluated = []
    for d in decisions:
        try:
            result = evaluate_decision(d)
            evaluated.append(result)
        except Exception:
            pass

    total = len(evaluated)
    if total == 0:
        return {"error": "No decisions could be evaluated"}

    winners = sum(1 for e in evaluated if e.get("pnl_pct", 0) > 0)
    pnl_values = [e.get("pnl_pct", 0) for e in evaluated]

    # Group by week
    weekly_pnl: dict[str, list[float]] = {}
    for e in evaluated:
        try:
            dt = datetime.fromisoformat(e["timestamp"])
            week_key = dt.strftime("%Y-W%U")
            if week_key not in weekly_pnl:
                weekly_pnl[week_key] = []
            weekly_pnl[week_key].append(e.get("pnl_pct", 0))
        except (ValueError, KeyError):
            pass

    weekly_summary = {}
    for week, pnls in sorted(weekly_pnl.items()):
        weekly_summary[week] = {
            "decisions": len(pnls),
            "avg_pnl": round(sum(pnls) / len(pnls), 2),
            "total_pnl": round(sum(pnls), 2),
            "hit_rate": round(sum(1 for p in pnls if p > 0) / len(pnls) * 100, 1),
        }

    return {
        "report_date": datetime.now().isoformat(),
        "period": "cumulative",
        "total_decisions": total,
        "hit_rate_pct": round(winners / total * 100, 1),
        "avg_pnl_pct": round(sum(pnl_values) / len(pnl_values), 2),
        "total_pnl_pct": round(sum(pnl_values), 2),
        "best_trade_pnl_pct": round(max(pnl_values), 2),
        "worst_trade_pnl_pct": round(min(pnl_values), 2),
        "weekly_breakdown": weekly_summary,
    }
