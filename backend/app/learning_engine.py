"""
Self-Learning Engine
Tracks prediction accuracy, adapts scoring weights, identifies which factors
are most predictive in different market conditions, and auto-corrects over time.

This is the "cheatcode" — it gets smarter with every decision it evaluates.
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import DATA_DIR, WEIGHTS

LEARNING_DB = DATA_DIR / "learning_state.json"
WEIGHT_HISTORY = DATA_DIR / "weight_history.json"

DEFAULT_STATE = {
    "version": 1,
    "created_at": None,
    "last_updated": None,
    "total_decisions_evaluated": 0,
    "current_weights": dict(WEIGHTS),
    "factor_accuracy": {
        "technical": {"correct": 0, "total": 0, "accuracy": 0.5},
        "fundamental": {"correct": 0, "total": 0, "accuracy": 0.5},
        "momentum": {"correct": 0, "total": 0, "accuracy": 0.5},
        "macro": {"correct": 0, "total": 0, "accuracy": 0.5},
    },
    "market_regime": "unknown",
    "regime_history": [],
    "sector_performance": {},
    "confidence_calibration": {
        "buckets": {
            "30-50": {"predicted": 0, "correct": 0},
            "50-65": {"predicted": 0, "correct": 0},
            "65-80": {"predicted": 0, "correct": 0},
            "80-95": {"predicted": 0, "correct": 0},
        }
    },
    "action_accuracy": {
        "STRONG_BUY": {"total": 0, "correct": 0},
        "BUY": {"total": 0, "correct": 0},
        "HOLD": {"total": 0, "correct": 0},
        "SELL": {"total": 0, "correct": 0},
        "STRONG_SELL": {"total": 0, "correct": 0},
    },
    "lessons_learned": [],
    "adaptation_log": [],
}


def load_learning_state() -> dict:
    if LEARNING_DB.exists():
        with open(LEARNING_DB) as f:
            return json.load(f)
    state = {**DEFAULT_STATE, "created_at": datetime.now().isoformat()}
    save_learning_state(state)
    return state


def save_learning_state(state: dict):
    state["last_updated"] = datetime.now().isoformat()
    with open(LEARNING_DB, "w") as f:
        json.dump(state, f, indent=2, default=str)


def _save_weight_snapshot(state: dict, reason: str):
    history = []
    if WEIGHT_HISTORY.exists():
        with open(WEIGHT_HISTORY) as f:
            history = json.load(f)
    history.append({
        "timestamp": datetime.now().isoformat(),
        "weights": state["current_weights"],
        "reason": reason,
        "total_evaluated": state["total_decisions_evaluated"],
    })
    with open(WEIGHT_HISTORY, "w") as f:
        json.dump(history[-200:], f, indent=2)


def evaluate_and_learn(decision: dict, actual_outcome: dict) -> dict:
    """
    Core learning loop. Takes a past decision and its actual outcome,
    updates factor accuracy, calibrates confidence, and adapts weights.

    Returns a learning summary.
    """
    state = load_learning_state()
    state["total_decisions_evaluated"] += 1

    action = decision.get("action", "HOLD")
    pnl = actual_outcome.get("pnl_pct", 0)
    outcome = actual_outcome.get("outcome", "OPEN")

    # --- 1. Track action accuracy ---
    was_correct = _was_decision_correct(action, pnl)
    if action in state["action_accuracy"]:
        state["action_accuracy"][action]["total"] += 1
        if was_correct:
            state["action_accuracy"][action]["correct"] += 1

    # --- 2. Track per-factor accuracy ---
    scores = decision.get("scores", {})
    for factor, score in scores.items():
        if factor not in state["factor_accuracy"]:
            state["factor_accuracy"][factor] = {"correct": 0, "total": 0, "accuracy": 0.5}

        fa = state["factor_accuracy"][factor]
        factor_was_right = _factor_aligned_with_outcome(factor, score, pnl)
        fa["total"] += 1
        if factor_was_right:
            fa["correct"] += 1
        fa["accuracy"] = fa["correct"] / fa["total"] if fa["total"] > 0 else 0.5

    # --- 3. Confidence calibration ---
    confidence = decision.get("confidence", 50)
    bucket = _get_confidence_bucket(confidence)
    if bucket in state["confidence_calibration"]["buckets"]:
        state["confidence_calibration"]["buckets"][bucket]["predicted"] += 1
        if was_correct:
            state["confidence_calibration"]["buckets"][bucket]["correct"] += 1

    # --- 4. Sector tracking ---
    sector = decision.get("sector", "Unknown")
    if sector not in state["sector_performance"]:
        state["sector_performance"][sector] = {"decisions": 0, "correct": 0, "total_pnl": 0}
    sp = state["sector_performance"][sector]
    sp["decisions"] += 1
    if was_correct:
        sp["correct"] += 1
    sp["total_pnl"] += pnl

    # --- 5. Adapt weights every 10 evaluations ---
    lessons = []
    if state["total_decisions_evaluated"] % 10 == 0 and state["total_decisions_evaluated"] >= 10:
        lessons = _adapt_weights(state)
        _save_weight_snapshot(state, f"Auto-adaptation after {state['total_decisions_evaluated']} evaluations")

    # --- 6. Detect market regime ---
    _detect_regime(state, actual_outcome)

    # --- 7. Record lesson ---
    if lessons:
        for lesson in lessons:
            state["lessons_learned"].append({
                "timestamp": datetime.now().isoformat(),
                "lesson": lesson,
                "evaluation_count": state["total_decisions_evaluated"],
            })
        state["lessons_learned"] = state["lessons_learned"][-100:]

    save_learning_state(state)

    return {
        "decision_correct": was_correct,
        "pnl_pct": pnl,
        "factor_accuracy": {k: v["accuracy"] for k, v in state["factor_accuracy"].items()},
        "current_weights": state["current_weights"],
        "lessons": lessons,
        "total_evaluated": state["total_decisions_evaluated"],
    }


def _was_decision_correct(action: str, pnl: float) -> bool:
    if action in ("STRONG_BUY", "BUY"):
        return pnl > 0
    elif action in ("STRONG_SELL", "SELL"):
        return pnl < 0
    else:  # HOLD
        return abs(pnl) < 3  # within 3% is fine for HOLD


def _factor_aligned_with_outcome(factor: str, score: float, pnl: float) -> bool:
    """Did this factor's signal align with what actually happened?"""
    if score > 60 and pnl > 0:
        return True
    if score < 40 and pnl < 0:
        return True
    if 40 <= score <= 60 and abs(pnl) < 5:
        return True
    return False


def _get_confidence_bucket(confidence: float) -> str:
    if confidence < 50:
        return "30-50"
    elif confidence < 65:
        return "50-65"
    elif confidence < 80:
        return "65-80"
    else:
        return "80-95"


def _adapt_weights(state: dict) -> list[str]:
    """
    The core self-improvement algorithm.
    Adjusts weights based on which factors have been most predictive.
    Uses a Bayesian-inspired approach with smoothing.
    """
    lessons = []
    factor_acc = state["factor_accuracy"]
    current_weights = state["current_weights"]

    # Calculate performance-adjusted weights
    total_accuracy = 0
    acc_map = {}
    for factor in current_weights:
        if factor in factor_acc and factor_acc[factor]["total"] >= 3:
            acc = factor_acc[factor]["accuracy"]
        else:
            acc = 0.5  # prior
        acc_map[factor] = acc
        total_accuracy += acc

    if total_accuracy == 0:
        return lessons

    # New weights proportional to accuracy, with smoothing toward original
    LEARNING_RATE = 0.15  # how fast to adapt (higher = faster but noisier)
    original_weights = dict(WEIGHTS)

    new_weights = {}
    for factor, current_w in current_weights.items():
        acc = acc_map.get(factor, 0.5)
        # Performance-based target weight
        target_w = acc / total_accuracy
        # Smooth toward target, anchored to original
        orig_w = original_weights.get(factor, current_w)
        blended_target = 0.5 * target_w + 0.5 * orig_w
        new_w = current_w + LEARNING_RATE * (blended_target - current_w)
        new_weights[factor] = max(0.02, new_w)  # minimum 2% weight

    # Normalize to sum to 1
    total = sum(new_weights.values())
    new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

    # Log significant changes
    for factor in new_weights:
        old_w = current_weights.get(factor, 0)
        new_w = new_weights[factor]
        change_pct = ((new_w - old_w) / old_w * 100) if old_w > 0 else 0
        if abs(change_pct) > 5:
            direction = "increased" if change_pct > 0 else "decreased"
            acc_str = f"{acc_map.get(factor, 0.5):.0%}"
            lessons.append(
                f"{factor.title()} weight {direction} to {new_w:.1%} "
                f"(accuracy: {acc_str}, was {old_w:.1%})"
            )

    state["current_weights"] = new_weights
    state["adaptation_log"].append({
        "timestamp": datetime.now().isoformat(),
        "old_weights": current_weights,
        "new_weights": new_weights,
        "accuracies": acc_map,
    })
    state["adaptation_log"] = state["adaptation_log"][-50:]

    return lessons


def _detect_regime(state: dict, outcome: dict):
    """Detect current market regime (trending/mean-reverting/volatile)."""
    nifty_change = outcome.get("nifty_change_pct", None)
    vix = outcome.get("vix", None)

    if nifty_change is not None and vix is not None:
        if vix > 22:
            regime = "high_volatility"
        elif abs(nifty_change) > 3:
            regime = "trending"
        elif abs(nifty_change) < 1:
            regime = "range_bound"
        else:
            regime = "normal"

        state["market_regime"] = regime
        state["regime_history"].append({
            "timestamp": datetime.now().isoformat(),
            "regime": regime,
            "vix": vix,
            "nifty_change": nifty_change,
        })
        state["regime_history"] = state["regime_history"][-100:]


def get_adapted_weights() -> dict:
    """Get the current adapted weights for use by the decision engine."""
    state = load_learning_state()
    return state.get("current_weights", dict(WEIGHTS))


def get_learning_summary() -> dict:
    """Get a human-readable learning summary."""
    state = load_learning_state()

    # Overall accuracy
    total_correct = sum(
        v["correct"] for v in state["action_accuracy"].values()
    )
    total_decisions = sum(
        v["total"] for v in state["action_accuracy"].values()
    )
    overall_accuracy = total_correct / total_decisions if total_decisions > 0 else 0

    # Best and worst factors
    factor_rankings = sorted(
        state["factor_accuracy"].items(),
        key=lambda x: x[1]["accuracy"],
        reverse=True,
    )

    # Confidence calibration
    cal = state["confidence_calibration"]["buckets"]
    calibration = {}
    for bucket, data in cal.items():
        actual_rate = data["correct"] / data["predicted"] if data["predicted"] > 0 else 0
        calibration[bucket] = {
            "predicted_count": data["predicted"],
            "actual_accuracy": round(actual_rate * 100, 1),
        }

    # Best/worst sectors
    sector_rankings = sorted(
        state["sector_performance"].items(),
        key=lambda x: x[1]["correct"] / x[1]["decisions"] if x[1]["decisions"] > 0 else 0,
        reverse=True,
    )

    return {
        "total_evaluated": state["total_decisions_evaluated"],
        "overall_accuracy_pct": round(overall_accuracy * 100, 1),
        "market_regime": state["market_regime"],
        "current_weights": state["current_weights"],
        "factor_rankings": [
            {"factor": f, "accuracy": round(d["accuracy"] * 100, 1), "sample_size": d["total"]}
            for f, d in factor_rankings
        ],
        "action_accuracy": {
            k: {
                "accuracy": round(v["correct"] / v["total"] * 100, 1) if v["total"] > 0 else 0,
                "sample_size": v["total"],
            }
            for k, v in state["action_accuracy"].items()
        },
        "confidence_calibration": calibration,
        "sector_rankings": [
            {
                "sector": s,
                "accuracy": round(d["correct"] / d["decisions"] * 100, 1) if d["decisions"] > 0 else 0,
                "avg_pnl": round(d["total_pnl"] / d["decisions"], 2) if d["decisions"] > 0 else 0,
                "decisions": d["decisions"],
            }
            for s, d in sector_rankings[:10]
        ],
        "recent_lessons": state["lessons_learned"][-10:],
        "adaptations_count": len(state["adaptation_log"]),
        "created_at": state.get("created_at"),
        "last_updated": state.get("last_updated"),
    }


def batch_learn_from_decisions(decisions: list[dict], outcomes: list[dict]) -> dict:
    """Process a batch of decision-outcome pairs for learning."""
    results = []
    for decision, outcome in zip(decisions, outcomes):
        result = evaluate_and_learn(decision, outcome)
        results.append(result)

    state = load_learning_state()
    return {
        "processed": len(results),
        "current_weights": state["current_weights"],
        "overall_summary": get_learning_summary(),
    }
