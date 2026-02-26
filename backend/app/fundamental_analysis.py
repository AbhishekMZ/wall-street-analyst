"""
Fundamental Analysis Module
Scores stocks based on valuation, profitability, growth, and financial health.
Tailored for Indian market with sector-aware benchmarks.
"""

from typing import Optional


# Sector average P/E ratios for Indian market (approximate benchmarks)
SECTOR_PE_BENCHMARKS = {
    "Technology": 28,
    "Financial Services": 18,
    "Consumer Defensive": 45,
    "Consumer Cyclical": 35,
    "Healthcare": 30,
    "Energy": 12,
    "Industrials": 25,
    "Basic Materials": 15,
    "Communication Services": 20,
    "Utilities": 14,
    "Real Estate": 20,
    "Unknown": 22,
}


def _safe_float(val, default=None) -> Optional[float]:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def score_valuation(info: dict) -> dict:
    """Score based on P/E, P/B, PEG, and relative valuation."""
    score = 50.0
    details = {}

    pe = _safe_float(info.get("pe_ratio"))
    forward_pe = _safe_float(info.get("forward_pe"))
    pb = _safe_float(info.get("pb_ratio"))
    peg = _safe_float(info.get("peg_ratio"))
    sector = info.get("sector", "Unknown")
    sector_pe = SECTOR_PE_BENCHMARKS.get(sector, 22)

    # P/E vs sector average
    if pe is not None and pe > 0:
        pe_ratio_to_sector = pe / sector_pe
        if pe_ratio_to_sector < 0.6:
            score += 15  # Significantly undervalued
        elif pe_ratio_to_sector < 0.8:
            score += 10
        elif pe_ratio_to_sector < 1.0:
            score += 5
        elif pe_ratio_to_sector > 1.5:
            score -= 10  # Overvalued
        elif pe_ratio_to_sector > 1.2:
            score -= 5
        details["pe"] = round(pe, 2)
        details["sector_pe"] = sector_pe
        details["pe_vs_sector"] = f"{round(pe_ratio_to_sector, 2)}x"

    # Forward P/E improvement
    if pe is not None and forward_pe is not None and pe > 0 and forward_pe > 0:
        if forward_pe < pe * 0.85:
            score += 8  # Earnings expected to grow significantly
        elif forward_pe < pe:
            score += 4
        details["forward_pe"] = round(forward_pe, 2)

    # P/B ratio
    if pb is not None and pb > 0:
        if pb < 1.0:
            score += 8  # Trading below book value
        elif pb < 2.0:
            score += 4
        elif pb > 5.0:
            score -= 5
        details["pb"] = round(pb, 2)

    # PEG ratio (growth-adjusted valuation)
    if peg is not None and peg > 0:
        if peg < 0.8:
            score += 10  # Undervalued relative to growth
        elif peg < 1.0:
            score += 5
        elif peg > 2.0:
            score -= 8
        elif peg > 1.5:
            score -= 4
        details["peg"] = round(peg, 2)

    return {"score": max(0, min(100, score)), "details": details}


def score_profitability(info: dict) -> dict:
    """Score based on ROE, margins, and earnings quality."""
    score = 50.0
    details = {}

    roe = _safe_float(info.get("roe"))
    profit_margin = _safe_float(info.get("profit_margin"))
    operating_margin = _safe_float(info.get("operating_margin"))

    # ROE
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 25:
            score += 15
        elif roe_pct > 18:
            score += 10
        elif roe_pct > 12:
            score += 5
        elif roe_pct < 5:
            score -= 10
        elif roe_pct < 8:
            score -= 5
        details["roe"] = f"{round(roe_pct, 1)}%"

    # Profit margin
    if profit_margin is not None:
        pm_pct = profit_margin * 100
        if pm_pct > 20:
            score += 10
        elif pm_pct > 12:
            score += 5
        elif pm_pct < 3:
            score -= 10
        elif pm_pct < 7:
            score -= 5
        details["profit_margin"] = f"{round(pm_pct, 1)}%"

    # Operating margin
    if operating_margin is not None:
        om_pct = operating_margin * 100
        if om_pct > 25:
            score += 8
        elif om_pct > 15:
            score += 4
        elif om_pct < 5:
            score -= 8
        details["operating_margin"] = f"{round(om_pct, 1)}%"

    return {"score": max(0, min(100, score)), "details": details}


def score_growth(info: dict) -> dict:
    """Score based on revenue and earnings growth."""
    score = 50.0
    details = {}

    rev_growth = _safe_float(info.get("revenue_growth"))
    earn_growth = _safe_float(info.get("earnings_growth"))
    eps = _safe_float(info.get("eps"))
    forward_eps = _safe_float(info.get("forward_eps"))

    # Revenue growth
    if rev_growth is not None:
        rg_pct = rev_growth * 100
        if rg_pct > 25:
            score += 15
        elif rg_pct > 15:
            score += 10
        elif rg_pct > 8:
            score += 5
        elif rg_pct < 0:
            score -= 10
        elif rg_pct < 3:
            score -= 5
        details["revenue_growth"] = f"{round(rg_pct, 1)}%"

    # Earnings growth
    if earn_growth is not None:
        eg_pct = earn_growth * 100
        if eg_pct > 30:
            score += 15
        elif eg_pct > 18:
            score += 10
        elif eg_pct > 8:
            score += 5
        elif eg_pct < 0:
            score -= 12
        details["earnings_growth"] = f"{round(eg_pct, 1)}%"

    # EPS forward improvement
    if eps is not None and forward_eps is not None and eps > 0:
        eps_growth = ((forward_eps - eps) / abs(eps)) * 100
        if eps_growth > 20:
            score += 8
        elif eps_growth > 10:
            score += 4
        elif eps_growth < -10:
            score -= 8
        details["eps"] = round(eps, 2)
        details["forward_eps"] = round(forward_eps, 2)

    return {"score": max(0, min(100, score)), "details": details}


def score_financial_health(info: dict) -> dict:
    """Score based on debt levels, cash position, and liquidity."""
    score = 50.0
    details = {}

    de = _safe_float(info.get("debt_to_equity"))
    current_ratio = _safe_float(info.get("current_ratio"))
    fcf = _safe_float(info.get("free_cash_flow"))
    total_debt = _safe_float(info.get("total_debt"))
    total_cash = _safe_float(info.get("total_cash"))

    # Debt to equity
    if de is not None:
        if de < 30:
            score += 12  # Very low debt
        elif de < 60:
            score += 8
        elif de < 100:
            score += 3
        elif de > 200:
            score -= 15  # Heavily leveraged
        elif de > 150:
            score -= 10
        details["debt_to_equity"] = round(de, 1)

    # Current ratio
    if current_ratio is not None:
        if current_ratio > 2.0:
            score += 8
        elif current_ratio > 1.5:
            score += 5
        elif current_ratio < 0.8:
            score -= 10
        elif current_ratio < 1.0:
            score -= 5
        details["current_ratio"] = round(current_ratio, 2)

    # Cash vs Debt
    if total_cash is not None and total_debt is not None and total_debt > 0:
        cash_debt_ratio = total_cash / total_debt
        if cash_debt_ratio > 1.0:
            score += 8  # Net cash positive
        elif cash_debt_ratio > 0.5:
            score += 4
        elif cash_debt_ratio < 0.1:
            score -= 8
        details["cash_to_debt"] = round(cash_debt_ratio, 2)

    # Free cash flow
    if fcf is not None:
        if fcf > 0:
            score += 5
        else:
            score -= 8  # Negative FCF is a red flag
        details["free_cash_flow"] = fcf

    return {"score": max(0, min(100, score)), "details": details}


def run_fundamental_analysis(info: dict) -> dict:
    """Run full fundamental analysis and return composite score."""
    valuation = score_valuation(info)
    profitability = score_profitability(info)
    growth = score_growth(info)
    health = score_financial_health(info)

    # Weighted composite
    composite = (
        valuation["score"] * 0.30 +
        profitability["score"] * 0.25 +
        growth["score"] * 0.25 +
        health["score"] * 0.20
    )

    if composite >= 75:
        signal = "STRONG_BUY"
    elif composite >= 60:
        signal = "BUY"
    elif composite >= 40:
        signal = "HOLD"
    elif composite >= 25:
        signal = "SELL"
    else:
        signal = "STRONG_SELL"

    return {
        "score": round(composite, 1),
        "signal": signal,
        "breakdown": {
            "valuation": valuation,
            "profitability": profitability,
            "growth": growth,
            "financial_health": health,
        },
        "company_info": {
            "name": info.get("name", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("market_cap", 0),
        },
    }
