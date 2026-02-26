"""
Wall Street Analyst — FastAPI Backend
Indian Market Decision System with multi-factor analysis.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .config import NIFTY50
from .decision_engine import analyze_stock, save_decision, load_decisions
from .data_fetcher import fetch_global_indicators, fetch_stock_info
from .report_generator import generate_weekly_report, generate_cumulative_report
from .learning_engine import get_learning_summary, evaluate_and_learn, batch_learn_from_decisions
from .portfolio_manager import (
    load_portfolio, add_holding, remove_holding, import_from_csv,
    get_portfolio_performance, get_portfolio_recommendations,
)

app = FastAPI(
    title="Wall Street Analyst API",
    description="Indian Market Decision System with institutional-grade analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


class AnalyzeRequest(BaseModel):
    ticker: str
    save: bool = True


class ScanRequest(BaseModel):
    tickers: Optional[list[str]] = None
    top_n: int = 10


class WatchlistRequest(BaseModel):
    tickers: list[str]


class HoldingRequest(BaseModel):
    ticker: str
    qty: float
    avg_price: float
    buy_date: Optional[str] = None


class RemoveHoldingRequest(BaseModel):
    ticker: str
    qty: Optional[float] = None


class CSVImportRequest(BaseModel):
    csv_content: str


# ------- HEALTH -------

@app.get("/")
async def root():
    return {
        "service": "Wall Street Analyst",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/analyze/{ticker}",
            "/api/scan",
            "/api/decisions",
            "/api/reports/weekly",
            "/api/reports/cumulative",
            "/api/macro",
            "/api/learning",
            "/api/portfolio",
        ],
    }


# ------- ANALYSIS -------

@app.get("/api/analyze/{ticker}")
async def analyze_single_stock(ticker: str, save: bool = Query(True)):
    """Run full analysis pipeline on a single stock."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = ticker.upper() + ".NS"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, analyze_stock, ticker)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    if save:
        await loop.run_in_executor(executor, save_decision, result)

    return result


@app.post("/api/scan")
async def scan_market(request: ScanRequest):
    """Scan multiple stocks and return top recommendations."""
    tickers = request.tickers or NIFTY50
    loop = asyncio.get_event_loop()

    results = []
    for ticker in tickers:
        try:
            result = await loop.run_in_executor(executor, analyze_stock, ticker)
            if "error" not in result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    # Sort by composite score descending
    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

    # Top buys and sells
    buys = [r for r in results if r["action"] in ("STRONG_BUY", "BUY")][:request.top_n]
    sells = [r for r in results if r["action"] in ("STRONG_SELL", "SELL")][:request.top_n]
    holds = [r for r in results if r["action"] == "HOLD"]

    return {
        "total_scanned": len(results),
        "top_buys": buys,
        "top_sells": sells,
        "holds": holds,
        "all_results": results,
    }


@app.post("/api/scan/quick")
async def quick_scan(request: WatchlistRequest):
    """Quick scan a custom watchlist."""
    loop = asyncio.get_event_loop()
    results = []
    for ticker in request.tickers:
        if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
            ticker = ticker.upper() + ".NS"
        try:
            result = await loop.run_in_executor(executor, analyze_stock, ticker)
            if "error" not in result:
                results.append(result)
        except Exception:
            pass

    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return {"results": results}


# ------- DECISIONS -------

@app.get("/api/decisions")
async def get_decisions(limit: int = Query(50, ge=1, le=500)):
    """Get saved decisions history."""
    decisions = load_decisions()
    return {
        "total": len(decisions),
        "decisions": decisions[-limit:],
    }


# ------- REPORTS -------

@app.get("/api/reports/weekly")
async def weekly_report():
    """Generate weekly performance report."""
    loop = asyncio.get_event_loop()
    report = await loop.run_in_executor(executor, generate_weekly_report)
    return report


@app.get("/api/reports/cumulative")
async def cumulative_report():
    """Generate cumulative performance report."""
    loop = asyncio.get_event_loop()
    report = await loop.run_in_executor(executor, generate_cumulative_report)
    return report


# ------- MACRO -------

@app.get("/api/macro")
async def macro_overview():
    """Get current macro indicators."""
    loop = asyncio.get_event_loop()
    indicators = await loop.run_in_executor(executor, fetch_global_indicators)
    return {
        "indicators": indicators,
        "analysis": _interpret_macro(indicators),
    }


def _interpret_macro(indicators: dict) -> dict:
    """Quick macro interpretation."""
    signals = []

    nifty = indicators.get("nifty", {})
    if nifty.get("month_change_pct", 0) > 3:
        signals.append({"factor": "Nifty 50", "signal": "bullish", "detail": f"+{nifty['month_change_pct']}% this month"})
    elif nifty.get("month_change_pct", 0) < -3:
        signals.append({"factor": "Nifty 50", "signal": "bearish", "detail": f"{nifty['month_change_pct']}% this month"})

    vix = indicators.get("vix_india", {})
    if vix.get("current", 15) > 22:
        signals.append({"factor": "India VIX", "signal": "fear", "detail": f"VIX at {vix['current']} — elevated fear"})
    elif vix.get("current", 15) < 13:
        signals.append({"factor": "India VIX", "signal": "greed", "detail": f"VIX at {vix['current']} — complacency"})

    crude = indicators.get("crude_oil", {})
    if crude.get("month_change_pct", 0) > 10:
        signals.append({"factor": "Crude Oil", "signal": "negative_for_india", "detail": f"Oil up {crude['month_change_pct']}% — inflationary pressure"})

    usdinr = indicators.get("usdinr", {})
    if usdinr.get("month_change_pct", 0) > 2:
        signals.append({"factor": "USD/INR", "signal": "inr_weakening", "detail": f"INR weakened {usdinr['month_change_pct']}% — benefits IT, hurts importers"})

    return {"signals": signals, "count": len(signals)}


# ------- STOCK INFO -------

@app.get("/api/info/{ticker}")
async def stock_info(ticker: str):
    """Get fundamental info for a stock."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = ticker.upper() + ".NS"

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(executor, fetch_stock_info, ticker)
    return info


# ------- NIFTY 50 LIST -------

@app.get("/api/universe")
async def get_universe():
    """Get the default stock universe (Nifty 50)."""
    return {"tickers": NIFTY50, "count": len(NIFTY50)}


# ------- LEARNING ENGINE -------

@app.get("/api/learning")
async def learning_summary():
    """Get the self-learning engine's current state and insights."""
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(executor, get_learning_summary)
    return summary


@app.post("/api/learning/evaluate")
async def trigger_learning():
    """Trigger a learning cycle — evaluate all past decisions and adapt weights."""
    from .report_generator import evaluate_decision
    loop = asyncio.get_event_loop()
    decisions = load_decisions()
    if not decisions:
        return {"error": "No decisions to learn from"}

    results = []
    for d in decisions[-50:]:
        try:
            outcome = await loop.run_in_executor(executor, evaluate_decision, d)
            result = await loop.run_in_executor(executor, evaluate_and_learn, d, outcome)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "ticker": d.get("ticker")})

    summary = await loop.run_in_executor(executor, get_learning_summary)
    return {
        "evaluated": len(results),
        "summary": summary,
    }


# ------- PORTFOLIO -------

@app.get("/api/portfolio")
async def portfolio_overview():
    """Get current portfolio holdings."""
    return load_portfolio()


@app.get("/api/portfolio/performance")
async def portfolio_perf():
    """Get portfolio performance with live prices."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_portfolio_performance)


@app.get("/api/portfolio/recommendations")
async def portfolio_recs():
    """Get portfolio-level recommendations."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_portfolio_recommendations)


@app.post("/api/portfolio/add")
async def add_portfolio_holding(req: HoldingRequest):
    """Add a holding to the portfolio."""
    return add_holding(req.ticker, req.qty, req.avg_price, req.buy_date)


@app.post("/api/portfolio/remove")
async def remove_portfolio_holding(req: RemoveHoldingRequest):
    """Remove or reduce a holding."""
    return remove_holding(req.ticker, req.qty)


@app.post("/api/portfolio/import")
async def import_portfolio(req: CSVImportRequest):
    """Import portfolio from CSV content."""
    return import_from_csv(req.csv_content)
