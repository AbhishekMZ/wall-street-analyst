"""
Wall Street Analyst — FastAPI Backend
Indian Market Decision System with multi-factor analysis.
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import io

from .config import NIFTY50, NIFTY_NEXT50, MIDCAP_GEMS, SMALLCAP_HIDDEN, ALL_UNIVERSES
from .decision_engine import analyze_stock, save_decision, load_decisions
from .data_fetcher import fetch_global_indicators, fetch_stock_info
from .report_generator import generate_weekly_report, generate_cumulative_report
from .learning_engine import get_learning_summary, evaluate_and_learn, batch_learn_from_decisions
from .portfolio_manager import (
    load_portfolio, add_holding, remove_holding, import_from_csv,
    get_portfolio_performance, get_portfolio_recommendations,
)
from .agent import (
    start_scheduler, stop_scheduler, get_agent_status, get_activity_log,
    get_scheduler_jobs, submit_background_analysis, get_background_results,
    get_completed_result, run_auto_scan, run_auto_learning, log_activity,
)

app = FastAPI(
    title="Wall Street Analyst API",
    description="Indian Market Decision System with autonomous agent pipeline",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)


@app.on_event("startup")
async def startup_event():
    """Start the autonomous agent scheduler on server boot."""
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()


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
        "version": "2.1.0",
        "status": "running",
        "agent": "autonomous",
        "endpoints": [
            "/api/analyze/{ticker}",
            "/api/analyze/background/{ticker}",
            "/api/scan",
            "/api/agent/status",
            "/api/agent/trigger/{universe}",
            "/api/decisions",
            "/api/decisions/mock",
            "/api/reports/weekly",
            "/api/macro",
            "/api/learning",
            "/api/portfolio",
        ],
    }


# ------- AGENT -------

@app.get("/api/agent/status")
async def agent_status():
    """Get autonomous agent status, scheduled jobs, and recent activity."""
    status = get_agent_status()
    status["scheduled_jobs"] = get_scheduler_jobs()
    return status


@app.get("/api/agent/activity")
async def agent_activity(limit: int = Query(50, ge=1, le=200)):
    """Get agent activity log."""
    return {"activities": get_activity_log(limit)}


@app.post("/api/agent/trigger/{universe}")
async def trigger_scan(universe: str):
    """Manually trigger a background scan of a specific universe."""
    if universe not in ALL_UNIVERSES and universe != "all":
        raise HTTPException(status_code=400, detail=f"Unknown universe: {universe}. Options: {list(ALL_UNIVERSES.keys()) + ['all']}")

    loop = asyncio.get_event_loop()
    if universe == "all":
        # Run full scan in background thread
        _future = loop.run_in_executor(executor, run_full_scan if universe == "all" else lambda: run_auto_scan(universe))
    else:
        _future = loop.run_in_executor(executor, run_auto_scan, universe)

    return {"status": "triggered", "universe": universe, "message": f"Background scan started for {universe}. Check /api/agent/status for progress."}


@app.post("/api/agent/learn")
async def trigger_learning():
    """Manually trigger a learning cycle."""
    loop = asyncio.get_event_loop()
    _future = loop.run_in_executor(executor, run_auto_learning)
    return {"status": "triggered", "message": "Learning cycle started in background."}


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


@app.get("/api/analyze/background/{ticker}")
async def analyze_background(ticker: str):
    """Submit stock for background analysis. Returns immediately with a task ID."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = ticker.upper() + ".NS"
    task_id = submit_background_analysis(ticker)
    return {"task_id": task_id, "ticker": ticker, "status": "queued"}


@app.get("/api/analyze/results")
async def get_bg_results():
    """Get all background analysis results (pending + completed)."""
    return get_background_results()


@app.get("/api/analyze/result/{task_id}")
async def get_bg_result(task_id: str):
    """Get a specific background analysis result."""
    result = get_completed_result(task_id)
    if not result:
        bg = get_background_results()
        if task_id in bg.get("pending", {}):
            return {"status": "pending", **bg["pending"][task_id]}
        raise HTTPException(status_code=404, detail="Task not found")
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
async def get_universe(category: str = Query("all")):
    """Get stock universe by category."""
    if category == "all":
        all_tickers = NIFTY50 + NIFTY_NEXT50 + MIDCAP_GEMS + SMALLCAP_HIDDEN
        # deduplicate
        seen = set()
        unique = []
        for t in all_tickers:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return {
            "tickers": unique,
            "count": len(unique),
            "categories": {
                "nifty50": len(NIFTY50),
                "nifty_next50": len(NIFTY_NEXT50),
                "midcap_gems": len(MIDCAP_GEMS),
                "smallcap_hidden": len(SMALLCAP_HIDDEN),
            },
        }
    universes = ALL_UNIVERSES
    tickers = universes.get(category, NIFTY50)
    return {"tickers": tickers, "count": len(tickers), "category": category}


@app.post("/api/scan/universe")
async def scan_universe(category: str = Query("nifty50"), top_n: int = Query(10)):
    """Scan a specific stock universe for opportunities."""
    universes = ALL_UNIVERSES
    tickers = universes.get(category, NIFTY50)
    loop = asyncio.get_event_loop()

    results = []
    for ticker in tickers:
        try:
            result = await loop.run_in_executor(executor, analyze_stock, ticker)
            if "error" not in result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")

    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    buys = [r for r in results if r["action"] in ("STRONG_BUY", "BUY")][:top_n]
    sells = [r for r in results if r["action"] in ("STRONG_SELL", "SELL")][:top_n]
    holds = [r for r in results if r["action"] == "HOLD"]

    return {
        "category": category,
        "total_scanned": len(results),
        "top_buys": buys,
        "top_sells": sells,
        "holds": holds,
        "all_results": results,
    }


@app.get("/api/decisions/mock")
async def get_mock_investments(limit: int = Query(50, ge=1, le=500)):
    """Get mock investment decisions with current P&L tracking."""
    from .report_generator import evaluate_decision
    loop = asyncio.get_event_loop()
    decisions = load_decisions()
    if not decisions:
        return {"total": 0, "decisions": [], "summary": {}}

    # Evaluate recent decisions with current prices
    evaluated = []
    actionable = [d for d in decisions if d.get("action") in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL")]
    for d in actionable[-limit:]:
        try:
            result = await loop.run_in_executor(executor, evaluate_decision, d)
            evaluated.append(result)
        except Exception:
            evaluated.append({**d, "outcome": "evaluation_error"})

    # Summary stats
    pnl_values = [e.get("pnl_pct", 0) for e in evaluated if "pnl_pct" in e]
    winners = sum(1 for p in pnl_values if p > 0)
    total = len(pnl_values)

    return {
        "total": total,
        "decisions": evaluated,
        "summary": {
            "total_trades": total,
            "winners": winners,
            "losers": total - winners,
            "hit_rate": round(winners / total * 100, 1) if total > 0 else 0,
            "avg_pnl": round(sum(pnl_values) / len(pnl_values), 2) if pnl_values else 0,
            "total_pnl": round(sum(pnl_values), 2),
            "best_trade": round(max(pnl_values), 2) if pnl_values else 0,
            "worst_trade": round(min(pnl_values), 2) if pnl_values else 0,
        },
    }


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


@app.post("/api/portfolio/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """Upload portfolio from Excel (.xlsx/.xls) or CSV file.
    Handles Angel One and other broker statement formats with metadata rows."""
    try:
        contents = await file.read()
        
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            # Read Excel with NO assumed header to inspect all rows
            raw_df = pd.read_excel(io.BytesIO(contents), header=None)
            
            # Find the actual header row by looking for broker column keywords
            header_keywords = ['scrip', 'ticker', 'symbol', 'company', 'quantity', 'isin', 'instrument']
            header_row = None
            for idx, row in raw_df.iterrows():
                row_text = ' '.join(str(v).lower() for v in row.values if pd.notna(v))
                matches = sum(1 for kw in header_keywords if kw in row_text)
                if matches >= 3:
                    header_row = idx
                    break
            
            if header_row is None:
                return {"error": f"Could not find holding data header in Excel. First rows: {raw_df.head(10).to_string()}"}
            
            # Re-read with correct header row
            df = pd.read_excel(io.BytesIO(contents), header=header_row)
            # Drop any fully empty rows
            df = df.dropna(how='all')
            csv_content = df.to_csv(index=False)
        elif file.filename.endswith('.csv'):
            csv_content = contents.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="File must be .xlsx, .xls, or .csv")
        
        result = import_from_csv(csv_content)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
