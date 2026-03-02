"""
Autonomous Agent System
Runs background scheduled tasks:
- Auto-scan all stock universes periodically
- Save every BUY/SELL decision as a mock paper trade
- Auto-evaluate past decisions and trigger learning cycles
- Maintain an activity log for the frontend to display
"""

import json
import os
import threading
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from .config import DATA_DIR, NIFTY50, NIFTY_NEXT50, MIDCAP_GEMS, SMALLCAP_HIDDEN, ALL_UNIVERSES
from .decision_engine import analyze_stock, save_decision, load_decisions
from .data_fetcher import fetch_index_data, fetch_global_indicators
from .learning_engine import evaluate_and_learn, get_learning_summary
from .report_generator import evaluate_decision
from .database import get_agent_state_db, update_agent_state_db, log_activity_db, get_activity_logs_db, DB_ENABLED

# How long between scans before we consider it "overdue" (in seconds)
SCAN_OVERDUE_THRESHOLD = 3 * 3600  # 3 hours
WARMUP_STOCKS = 5  # Number of stocks to scan on startup warmup

AGENT_LOG_FILE = DATA_DIR / "agent_log.json"
AGENT_STATE_FILE = DATA_DIR / "agent_state.json"
BACKGROUND_RESULTS_FILE = DATA_DIR / "background_results.json"

# Thread pool for background analysis
_agent_executor = ThreadPoolExecutor(max_workers=2)
_agent_lock = threading.Lock()


# ─── Activity Log ───

def get_agent_logs(limit: int = 50) -> list:
    """Retrieve recent activity logs from database or file."""
    # Try database first
    if DB_ENABLED:
        db_logs = get_activity_logs_db(limit=limit)
        if db_logs:
            return db_logs
    
    # Fallback to JSON file
    if not AGENT_LOG_FILE.exists():
        return []
    try:
        with open(AGENT_LOG_FILE, "r") as f:
            logs = json.load(f)
            return logs[-limit:]
    except (json.JSONDecodeError, IOError):
        return []
    return []


def _save_log(log: list):
    with open(AGENT_LOG_FILE, "w") as f:
        json.dump(log[-500:], f, indent=2, default=str)


def log_activity(action: str, detail: str, category: str = "system"):
    """Log an agent activity."""
    log_activity_db(action, detail, category)
    log = get_agent_logs()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "detail": detail,
        "category": category,
    })
    _save_log(log)


def get_activity_log(limit: int = 50) -> list:
    """Get recent agent activity."""
    return get_agent_logs(limit)


# ─── Agent State ───

def _load_state() -> dict:
    """Load the persistent agent state from database or disk."""
    # Try database first
    if DB_ENABLED:
        db_state = get_agent_state_db()
        if db_state:
            return db_state
    
    # Fallback to JSON file
    if not AGENT_STATE_FILE.exists():
        return {
            "last_scan": {},
            "next_scan": {},
            "scan_in_progress": False,
            "current_scan_universe": None,
            "total_scans_completed": 0,
            "total_stocks_analyzed": 0,
            "total_decisions_saved": 0,
            "agent_started_at": None,
            "learning_cycles": 0,
        }
    try:
        with open(AGENT_STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"last_scan": {}, "next_scan": {}}


def _save_state(state: dict):
    update_agent_state_db(state)
    with open(AGENT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_agent_status() -> dict:
    """Get current agent status for the frontend."""
    state = _load_state()
    log = get_activity_log(10)
    return {
        "state": state,
        "recent_activity": log,
        "is_running": state.get("scan_in_progress", False),
    }


# ─── Background Results Store ───

def _load_bg_results() -> dict:
    if BACKGROUND_RESULTS_FILE.exists():
        try:
            with open(BACKGROUND_RESULTS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"pending": {}, "completed": {}}


def _save_bg_results(results: dict):
    # Keep only last 100 completed
    if len(results.get("completed", {})) > 100:
        keys = sorted(results["completed"].keys())
        for k in keys[:-100]:
            del results["completed"][k]
    with open(BACKGROUND_RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)


def submit_background_analysis(ticker: str) -> str:
    """Submit a stock for background analysis. Returns a task ID."""
    task_id = f"{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    bg = _load_bg_results()
    bg["pending"][task_id] = {
        "ticker": ticker,
        "submitted_at": datetime.now().isoformat(),
        "status": "queued",
    }
    _save_bg_results(bg)

    # Submit to thread pool
    _agent_executor.submit(_run_background_analysis, task_id, ticker)
    log_activity("ANALYSIS_QUEUED", f"Background analysis queued for {ticker}", "analysis")
    return task_id


def _run_background_analysis(task_id: str, ticker: str):
    """Execute analysis in background thread."""
    try:
        bg = _load_bg_results()
        if task_id in bg["pending"]:
            bg["pending"][task_id]["status"] = "running"
            _save_bg_results(bg)

        result = analyze_stock(ticker)

        bg = _load_bg_results()
        if task_id in bg["pending"]:
            del bg["pending"][task_id]

        if "error" not in result:
            save_decision(result)
            bg["completed"][task_id] = {
                "ticker": ticker,
                "result": result,
                "completed_at": datetime.now().isoformat(),
                "status": "done",
            }
            log_activity(
                "ANALYSIS_COMPLETE",
                f"{ticker}: {result['action']} (score: {result.get('composite_score', 0):.1f}, confidence: {result.get('confidence', 0)}%)",
                "analysis",
            )
        else:
            bg["completed"][task_id] = {
                "ticker": ticker,
                "error": result["error"],
                "completed_at": datetime.now().isoformat(),
                "status": "error",
            }
            log_activity("ANALYSIS_ERROR", f"{ticker}: {result['error']}", "error")

        _save_bg_results(bg)

    except Exception as e:
        log_activity("ANALYSIS_ERROR", f"{ticker}: {str(e)}", "error")


def get_background_results() -> dict:
    """Get all pending and completed background analysis results."""
    return _load_bg_results()


def get_completed_result(task_id: str) -> Optional[dict]:
    """Get a specific completed result."""
    bg = _load_bg_results()
    return bg.get("completed", {}).get(task_id)


# ─── Scheduled Auto-Scanner ───

def run_auto_scan(universe_key: str = "nifty50", max_stocks: int = 0):
    """Run an automated scan of a stock universe. Saves all decisions."""
    state = _load_state()
    if state.get("scan_in_progress"):
        log_activity("SCAN_SKIPPED", f"Scan already in progress for {state.get('current_scan_universe')}", "scan")
        return {"skipped": True, "reason": "scan_in_progress"}

    tickers = ALL_UNIVERSES.get(universe_key, NIFTY50)
    if max_stocks > 0:
        tickers = tickers[:max_stocks]

    state["scan_in_progress"] = True
    state["current_scan_universe"] = universe_key
    _save_state(state)

    log_activity("SCAN_STARTED", f"Auto-scanning {universe_key} ({len(tickers)} stocks)", "scan")

    # Pre-fetch shared data ONCE for the entire scan (saves ~450 API calls per 50-stock scan)
    try:
        cached_index_df = fetch_index_data("^NSEI")
        cached_global_ind = fetch_global_indicators()
        log_activity("SCAN_PREFETCH", f"Cached Nifty index + {len(cached_global_ind)} global indicators", "scan")
    except Exception as e:
        log_activity("SCAN_PREFETCH_ERROR", f"Failed to pre-fetch shared data: {e}", "error")
        cached_index_df = None
        cached_global_ind = None

    results = []
    errors = 0
    error_details = []

    for i, ticker in enumerate(tickers):
        try:
            result = analyze_stock(ticker, cached_index_df=cached_index_df, cached_global_ind=cached_global_ind)
            if "error" not in result:
                save_decision(result)
                results.append(result)
                action = result.get("action", "HOLD")
                if action in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL"):
                    log_activity(
                        f"SIGNAL_{action}",
                        f"{ticker}: {action} (score: {result.get('composite_score', 0):.1f})",
                        "signal",
                    )
            else:
                errors += 1
                error_details.append(f"{ticker}: {result.get('error', 'unknown')}")
        except Exception as e:
            errors += 1
            error_details.append(f"{ticker}: {str(e)}")
            print(f"Auto-scan error for {ticker}: {e}")

        # Small delay to avoid rate limiting
        if i < len(tickers) - 1:
            time.sleep(1)

    # Update state
    state = _load_state()
    state["scan_in_progress"] = False
    state["current_scan_universe"] = None
    state["total_scans_completed"] = state.get("total_scans_completed", 0) + 1
    state["total_stocks_analyzed"] = state.get("total_stocks_analyzed", 0) + len(results)
    state["total_decisions_saved"] = state.get("total_decisions_saved", 0) + len(results)
    state["last_scan"][universe_key] = datetime.now().isoformat()
    _save_state(state)

    buys = [r for r in results if r["action"] in ("STRONG_BUY", "BUY")]
    sells = [r for r in results if r["action"] in ("STRONG_SELL", "SELL")]

    summary = f"{universe_key}: {len(results)} analyzed, {len(buys)} buys, {len(sells)} sells, {errors} errors"
    if error_details:
        summary += f" | First errors: {'; '.join(error_details[:3])}"
    log_activity("SCAN_COMPLETE", summary, "scan")

    return {
        "universe": universe_key,
        "total_scanned": len(results),
        "buys": len(buys),
        "sells": len(sells),
        "errors": errors,
        "top_buys": sorted(buys, key=lambda x: x.get("composite_score", 0), reverse=True)[:5],
        "top_sells": sorted(sells, key=lambda x: x.get("composite_score", 0))[:5],
    }


def run_full_scan():
    """Scan all universes sequentially. Called by scheduler."""
    log_activity("FULL_SCAN_STARTED", "Starting full scan of all universes", "scan")

    all_results = {}
    for universe_key in ALL_UNIVERSES:
        try:
            result = run_auto_scan(universe_key)
            all_results[universe_key] = result
            # Wait between universes
            time.sleep(2)
        except Exception as e:
            log_activity("SCAN_ERROR", f"Error scanning {universe_key}: {e}", "error")
            all_results[universe_key] = {"error": str(e)}

    log_activity("FULL_SCAN_COMPLETE", f"All universes scanned: {list(all_results.keys())}", "scan")
    return all_results


# ─── Auto-Learning ───

def run_auto_learning():
    """Evaluate recent decisions and trigger learning cycle."""
    log_activity("LEARNING_STARTED", "Auto-learning cycle started", "learning")

    decisions = load_decisions()
    if not decisions:
        log_activity("LEARNING_SKIPPED", "No decisions to learn from", "learning")
        return {"skipped": True}

    # Only evaluate decisions from last 30 days that haven't been evaluated
    recent = []
    cutoff = datetime.now() - timedelta(days=30)
    for d in decisions:
        ts = d.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts) if ts else datetime.min
            if dt > cutoff and d.get("action") in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL"):
                recent.append(d)
        except Exception:
            pass

    if not recent:
        log_activity("LEARNING_SKIPPED", "No recent actionable decisions to evaluate", "learning")
        return {"skipped": True}

    evaluated = 0
    for d in recent[-30:]:  # Limit to 30 to avoid timeouts
        try:
            outcome = evaluate_decision(d)
            evaluate_and_learn(d, outcome)
            evaluated += 1
        except Exception as e:
            print(f"Learning error for {d.get('ticker')}: {e}")

    state = _load_state()
    state["learning_cycles"] = state.get("learning_cycles", 0) + 1
    _save_state(state)

    log_activity("LEARNING_COMPLETE", f"Evaluated {evaluated} decisions", "learning")
    return {"evaluated": evaluated}


# ─── Startup Warmup & Overdue Detection ───

def _check_and_run_overdue():
    """Check if any scan is overdue and run immediately. Handles Render free tier wake-ups."""
    state = _load_state()
    last_scans = state.get("last_scan", {})
    universe_keys = list(ALL_UNIVERSES.keys())
    now = datetime.now()

    # Find the most overdue universe
    most_overdue_key = None
    most_overdue_secs = 0

    for key in universe_keys:
        last = last_scans.get(key)
        if last is None:
            # Never scanned — most overdue
            most_overdue_key = key
            most_overdue_secs = float('inf')
            break
        try:
            last_dt = datetime.fromisoformat(last)
            elapsed = (now - last_dt).total_seconds()
            if elapsed > SCAN_OVERDUE_THRESHOLD and elapsed > most_overdue_secs:
                most_overdue_key = key
                most_overdue_secs = elapsed
        except Exception:
            most_overdue_key = key
            most_overdue_secs = float('inf')
            break

    if most_overdue_key:
        log_activity(
            "WARMUP_SCAN",
            f"Overdue scan detected for {most_overdue_key} — running immediately on wake-up",
            "scan",
        )
        try:
            run_auto_scan(most_overdue_key, max_stocks=WARMUP_STOCKS)
        except Exception as e:
            log_activity("WARMUP_ERROR", f"Warmup scan failed: {e}", "error")
            print(f"Warmup scan error: {e}")
    else:
        log_activity("WARMUP_SKIP", "All universes scanned recently, no warmup needed", "system")


# ─── Scheduler Setup ───

_scheduler = None


def start_scheduler():
    """Start the APScheduler for automated background tasks."""
    global _scheduler
    if _scheduler is not None:
        return  # Already running

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger

        _scheduler = BackgroundScheduler()

        # Scan one universe every 2 hours (rotates through them)
        _scan_rotation = {"idx": 0}
        universe_keys = list(ALL_UNIVERSES.keys())

        def rotating_scan():
            idx = _scan_rotation["idx"]
            key = universe_keys[idx % len(universe_keys)]
            _scan_rotation["idx"] = idx + 1
            try:
                print(f"🔄 Rotating scan starting: {key}")
                run_auto_scan(key)
            except Exception as e:
                log_activity("SCAN_ERROR", f"Scheduled scan error for {key}: {e}", "error")
                print(f"❌ Scheduled scan error for {key}: {e}")

        # Run first scan 30 seconds after startup (not wait 2 hours!)
        first_scan_time = datetime.now() + timedelta(seconds=30)

        _scheduler.add_job(
            rotating_scan,
            IntervalTrigger(hours=2),
            id="rotating_scan",
            name="Rotate through stock universes",
            next_run_time=first_scan_time,
            replace_existing=True,
        )

        # Auto-learning: first run 5 min after startup
        first_learn_time = datetime.now() + timedelta(minutes=5)

        _scheduler.add_job(
            run_auto_learning,
            IntervalTrigger(hours=6),
            id="auto_learning",
            name="Auto-learning cycle",
            next_run_time=first_learn_time,
            replace_existing=True,
        )

        # Full scan once daily at 10:00 AM IST (4:30 UTC)
        _scheduler.add_job(
            run_full_scan,
            CronTrigger(hour=4, minute=30),
            id="daily_full_scan",
            name="Daily full market scan (10 AM IST)",
            replace_existing=True,
        )

        # Self-ping every 10 min to prevent Render free tier from sleeping
        def _self_ping():
            import requests
            try:
                api_url = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
                requests.get(f"{api_url}/", timeout=10)
            except Exception:
                pass  # Best-effort, don't log noise

        _scheduler.add_job(
            _self_ping,
            IntervalTrigger(minutes=10),
            id="keep_alive",
            name="Keep-alive self-ping",
            replace_existing=True,
        )

        _scheduler.start()

        state = _load_state()
        state["agent_started_at"] = datetime.now().isoformat()
        _save_state(state)

        log_activity("AGENT_STARTED", "Autonomous agent started — first scan in 30s, learning in 5m, keep-alive every 10m", "system")
        print("✅ Agent scheduler started — first scan in 30s")

        # Immediately queue a warmup scan in background to check for overdue work
        _agent_executor.submit(_check_and_run_overdue)

    except Exception as e:
        print(f"❌ Failed to start agent scheduler: {e}")
        log_activity("AGENT_ERROR", f"Failed to start scheduler: {e}", "error")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log_activity("AGENT_STOPPED", "Autonomous agent stopped", "system")


def get_scheduler_jobs() -> list:
    """Get info about scheduled jobs."""
    if _scheduler is None:
        return []
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return jobs
