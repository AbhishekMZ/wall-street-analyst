"""
Portfolio Manager Module
Manages user's equity portfolio, tracks holdings, calculates performance,
and generates portfolio-level recommendations.
"""

import json
import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import DATA_DIR
from .data_fetcher import fetch_stock_data, fetch_stock_info

PORTFOLIO_DB = DATA_DIR / "portfolio.json"

DEFAULT_PORTFOLIO = {
    "holdings": [],
    "transactions": [],
    "last_updated": None,
    "total_invested": 0,
    "metadata": {},
}


def load_portfolio() -> dict:
    if PORTFOLIO_DB.exists():
        with open(PORTFOLIO_DB) as f:
            return json.load(f)
    return {**DEFAULT_PORTFOLIO}


def save_portfolio(portfolio: dict):
    portfolio["last_updated"] = datetime.now().isoformat()
    with open(PORTFOLIO_DB, "w") as f:
        json.dump(portfolio, f, indent=2, default=str)


def add_holding(ticker: str, qty: float, avg_price: float, buy_date: Optional[str] = None) -> dict:
    """Add or update a holding."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = ticker.upper() + ".NS"

    portfolio = load_portfolio()
    existing = next((h for h in portfolio["holdings"] if h["ticker"] == ticker), None)

    if existing:
        # Average up/down
        total_qty = existing["qty"] + qty
        existing["avg_price"] = round(
            (existing["avg_price"] * existing["qty"] + avg_price * qty) / total_qty, 2
        )
        existing["qty"] = total_qty
        existing["last_modified"] = datetime.now().isoformat()
    else:
        portfolio["holdings"].append({
            "ticker": ticker,
            "qty": qty,
            "avg_price": avg_price,
            "buy_date": buy_date or datetime.now().strftime("%Y-%m-%d"),
            "added_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
        })

    portfolio["transactions"].append({
        "type": "BUY",
        "ticker": ticker,
        "qty": qty,
        "price": avg_price,
        "date": buy_date or datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
    })

    portfolio["total_invested"] = sum(h["avg_price"] * h["qty"] for h in portfolio["holdings"])
    save_portfolio(portfolio)
    return {"status": "ok", "holding": existing or portfolio["holdings"][-1]}


def remove_holding(ticker: str, qty: Optional[float] = None) -> dict:
    """Remove or reduce a holding."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = ticker.upper() + ".NS"

    portfolio = load_portfolio()
    holding = next((h for h in portfolio["holdings"] if h["ticker"] == ticker), None)

    if not holding:
        return {"error": f"No holding found for {ticker}"}

    if qty is None or qty >= holding["qty"]:
        portfolio["holdings"] = [h for h in portfolio["holdings"] if h["ticker"] != ticker]
        sold_qty = holding["qty"]
    else:
        holding["qty"] -= qty
        holding["last_modified"] = datetime.now().isoformat()
        sold_qty = qty

    portfolio["transactions"].append({
        "type": "SELL",
        "ticker": ticker,
        "qty": sold_qty,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
    })

    portfolio["total_invested"] = sum(h["avg_price"] * h["qty"] for h in portfolio["holdings"])
    save_portfolio(portfolio)
    return {"status": "ok", "sold_qty": sold_qty}


def import_from_csv(csv_content: str) -> dict:
    """
    Import portfolio from CSV. Expected columns (flexible matching):
    ticker/symbol/stock, qty/quantity/shares, avg_price/price/buy_price, date/buy_date
    Handles broker statement formats with metadata rows.
    """
    # Clean CSV: skip metadata rows, find header row
    lines = csv_content.strip().split('\n')
    header_idx = 0
    
    # Look for the header row - must contain multiple expected column keywords
    for i, line in enumerate(lines):
        lower_line = line.lower()
        # Count how many expected column keywords are in this line
        keyword_count = sum(1 for keyword in ['scrip', 'ticker', 'symbol', 'quantity', 'qty', 'price', 'isin', 'company'] 
                          if keyword in lower_line)
        # Header row should have at least 3 expected keywords
        if keyword_count >= 3:
            header_idx = i
            break
    
    # Reconstruct CSV from header onwards
    clean_csv = '\n'.join(lines[header_idx:])
    
    reader = csv.DictReader(io.StringIO(clean_csv))
    if not reader.fieldnames:
        return {"error": "Empty or invalid CSV"}
    
    # Debug: log what we found
    if len(reader.fieldnames) < 3 or all(f.strip() == '' for f in reader.fieldnames):
        return {"error": f"Invalid header row detected. Found: {reader.fieldnames}. Please ensure your file has proper column headers."}

    # Flexible column mapping
    ticker_col = next((f for f in reader.fieldnames if f.lower().strip() in
                       ("ticker", "symbol", "stock", "scrip", "scrip/contract", "name", "instrument")), None)
    qty_col = next((f for f in reader.fieldnames if f.lower().strip() in
                    ("qty", "quantity", "shares", "units", "no. of shares")), None)
    price_col = next((f for f in reader.fieldnames if f.lower().strip() in
                      ("avg_price", "price", "buy_price", "average price", "avg price",
                       "avg. price", "avg trading price", "purchase price", "cost")), None)
    date_col = next((f for f in reader.fieldnames if f.lower().strip() in
                     ("date", "buy_date", "purchase date", "purchase_date")), None)

    if not ticker_col:
        return {"error": f"Could not find ticker column. Found: {reader.fieldnames}"}
    
    if not qty_col:
        return {"error": f"Could not find quantity column. Found: {reader.fieldnames}"}
    
    if not price_col:
        return {"error": f"Could not find price column. Found: {reader.fieldnames}"}

    imported = 0
    errors = []
    skipped = 0
    
    for row in reader:
        try:
            ticker_raw = row.get(ticker_col, "").strip().upper()
            if not ticker_raw or len(ticker_raw) < 2:
                skipped += 1
                continue

            # Extract ticker symbol (handle formats like "MARINE" or "HDFCBANK")
            ticker = ticker_raw.split()[0] if ' ' in ticker_raw else ticker_raw
            
            # Get quantity and price with better error handling
            qty_str = row.get(qty_col, "0").replace(",", "").strip()
            price_str = row.get(price_col, "0").replace(",", "").strip()
            
            qty = float(qty_str) if qty_str and qty_str != "" else 0
            price = float(price_str) if price_str and price_str != "" else 0
            
            date = row.get(date_col, "").strip() if date_col else None

            if qty > 0 and price > 0:
                # Add .NS suffix for NSE stocks if not present
                if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
                    ticker = f"{ticker}.NS"
                add_holding(ticker, qty, price, date)
                imported += 1
            else:
                errors.append(f"{ticker_raw}: Invalid qty ({qty}) or price ({price})")
        except Exception as e:
            errors.append(f"{ticker_raw if 'ticker_raw' in locals() else 'unknown'}: {str(e)}")

    return {
        "imported": imported, 
        "errors": errors, 
        "skipped": skipped,
        "total_rows": imported + len(errors) + skipped,
        "columns_found": {
            "ticker": ticker_col,
            "quantity": qty_col,
            "price": price_col,
            "date": date_col
        }
    }


def get_portfolio_performance() -> dict:
    """Calculate current portfolio performance with live prices."""
    portfolio = load_portfolio()
    if not portfolio["holdings"]:
        return {"error": "No holdings in portfolio", "holdings": []}

    enriched = []
    total_invested = 0
    total_current = 0

    for h in portfolio["holdings"]:
        ticker = h["ticker"]
        df = fetch_stock_data(ticker, period_days=30)

        current_price = 0
        day_change = 0
        week_change = 0
        month_change = 0

        if df is not None and not df.empty:
            current_price = float(df["close"].iloc[-1])
            if len(df) > 1:
                day_change = ((current_price - float(df["close"].iloc[-2])) / float(df["close"].iloc[-2])) * 100
            if len(df) >= 5:
                week_change = ((current_price - float(df["close"].iloc[-5])) / float(df["close"].iloc[-5])) * 100
            if len(df) >= 20:
                month_change = ((current_price - float(df["close"].iloc[-20])) / float(df["close"].iloc[-20])) * 100

        invested = h["avg_price"] * h["qty"]
        current_val = current_price * h["qty"]
        pnl = current_val - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        total_invested += invested
        total_current += current_val

        enriched.append({
            "ticker": ticker,
            "qty": h["qty"],
            "avg_price": h["avg_price"],
            "current_price": round(current_price, 2),
            "invested": round(invested, 2),
            "current_value": round(current_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "day_change_pct": round(day_change, 2),
            "week_change_pct": round(week_change, 2),
            "month_change_pct": round(month_change, 2),
            "buy_date": h.get("buy_date", ""),
            "weight_pct": 0,  # filled below
        })

    # Calculate weights
    for h in enriched:
        h["weight_pct"] = round(h["current_value"] / total_current * 100, 1) if total_current > 0 else 0

    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Sort by weight descending
    enriched.sort(key=lambda x: x["current_value"], reverse=True)

    # Sector diversification
    sector_map: dict[str, float] = {}
    for h in enriched:
        info = fetch_stock_info(h["ticker"])
        sector = info.get("sector", "Unknown")
        h["sector"] = sector
        sector_map[sector] = sector_map.get(sector, 0) + h["current_value"]

    sector_weights = {
        s: round(v / total_current * 100, 1) if total_current > 0 else 0
        for s, v in sorted(sector_map.items(), key=lambda x: x[1], reverse=True)
    }

    return {
        "summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "num_holdings": len(enriched),
        },
        "sector_diversification": sector_weights,
        "holdings": enriched,
        "last_updated": datetime.now().isoformat(),
    }


def get_portfolio_recommendations() -> dict:
    """
    Generate recommendations for the current portfolio:
    - Overweight/underweight sectors
    - Stocks to add/trim
    - Risk concentration warnings
    """
    perf = get_portfolio_performance()
    if "error" in perf:
        return perf

    holdings = perf["holdings"]
    sector_weights = perf["sector_diversification"]
    recommendations = []

    # 1. Concentration risk
    for h in holdings:
        if h["weight_pct"] > 25:
            recommendations.append({
                "type": "RISK",
                "severity": "high",
                "message": f"{h['ticker'].replace('.NS', '')} is {h['weight_pct']}% of portfolio — consider trimming to reduce concentration risk",
            })
        elif h["weight_pct"] > 15:
            recommendations.append({
                "type": "RISK",
                "severity": "medium",
                "message": f"{h['ticker'].replace('.NS', '')} is {h['weight_pct']}% — approaching high concentration",
            })

    # 2. Sector concentration
    for sector, weight in sector_weights.items():
        if weight > 35:
            recommendations.append({
                "type": "DIVERSIFICATION",
                "severity": "high",
                "message": f"{sector} sector at {weight}% — heavily overweight. Consider diversifying.",
            })

    # 3. Big losers
    losers = [h for h in holdings if h["pnl_pct"] < -15]
    for h in losers:
        recommendations.append({
            "type": "REVIEW",
            "severity": "medium",
            "message": f"{h['ticker'].replace('.NS', '')} is down {h['pnl_pct']}% — review thesis or set stop loss",
        })

    # 4. Big winners — lock profits
    winners = [h for h in holdings if h["pnl_pct"] > 30]
    for h in winners:
        recommendations.append({
            "type": "PROFIT_BOOKING",
            "severity": "low",
            "message": f"{h['ticker'].replace('.NS', '')} is up {h['pnl_pct']}% — consider partial profit booking",
        })

    # 5. Number of holdings
    if len(holdings) < 5:
        recommendations.append({
            "type": "DIVERSIFICATION",
            "severity": "medium",
            "message": "Portfolio has only {len(holdings)} stocks — consider 10-15 for proper diversification",
        })
    elif len(holdings) > 25:
        recommendations.append({
            "type": "COMPLEXITY",
            "severity": "low",
            "message": f"Portfolio has {len(holdings)} stocks — may be over-diversified, harder to monitor",
        })

    return {
        "portfolio_summary": perf["summary"],
        "recommendations": recommendations,
        "recommendations_count": len(recommendations),
    }
