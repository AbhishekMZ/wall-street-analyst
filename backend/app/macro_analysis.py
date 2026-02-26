"""
Macro & Global Correlation Analysis Module
Analyzes how macro factors (RBI policy, INR, crude, global indices)
affect individual stocks and sectors in the Indian market.
"""

from typing import Optional

# Sector sensitivity mapping to macro factors
# Positive = benefits from increase, Negative = hurt by increase
SECTOR_MACRO_SENSITIVITY = {
    "Technology": {
        "interest_rate": -0.3,  # Growth stocks hurt by rate hikes
        "inr_weakness": 0.8,   # IT exports benefit from weak INR
        "crude_oil": -0.1,
        "us_market": 0.7,      # Correlated to US tech spending
        "inflation": -0.2,
    },
    "Financial Services": {
        "interest_rate": 0.5,   # Banks benefit from rate hikes (NIM)
        "inr_weakness": -0.2,
        "crude_oil": -0.3,
        "us_market": 0.3,
        "inflation": -0.3,
    },
    "Energy": {
        "interest_rate": -0.2,
        "inr_weakness": -0.5,   # Oil imports costlier
        "crude_oil": 0.7,       # Oil companies benefit
        "us_market": 0.2,
        "inflation": 0.3,
    },
    "Consumer Defensive": {
        "interest_rate": -0.2,
        "inr_weakness": -0.3,
        "crude_oil": -0.4,      # Input costs rise
        "us_market": 0.1,
        "inflation": -0.5,      # Margin pressure
    },
    "Consumer Cyclical": {
        "interest_rate": -0.6,   # Rate-sensitive (auto loans etc.)
        "inr_weakness": -0.3,
        "crude_oil": -0.5,
        "us_market": 0.3,
        "inflation": -0.6,
    },
    "Healthcare": {
        "interest_rate": -0.1,
        "inr_weakness": 0.5,    # Pharma exports benefit
        "crude_oil": -0.2,
        "us_market": 0.5,       # US generics market
        "inflation": -0.1,
    },
    "Industrials": {
        "interest_rate": -0.4,
        "inr_weakness": -0.2,
        "crude_oil": -0.4,
        "us_market": 0.2,
        "inflation": -0.3,
    },
    "Basic Materials": {
        "interest_rate": -0.3,
        "inr_weakness": -0.3,
        "crude_oil": -0.2,
        "us_market": 0.3,
        "inflation": 0.4,       # Commodity prices rise with inflation
    },
    "Communication Services": {
        "interest_rate": -0.3,
        "inr_weakness": -0.1,
        "crude_oil": -0.2,
        "us_market": 0.2,
        "inflation": -0.2,
    },
    "Utilities": {
        "interest_rate": -0.5,   # Capital-intensive, rate-sensitive
        "inr_weakness": -0.3,
        "crude_oil": -0.6,       # Power generation costs
        "us_market": 0.1,
        "inflation": -0.2,
    },
}


def analyze_macro_impact(global_indicators: dict, sector: str) -> dict:
    """Analyze macro impact on a specific sector/stock."""
    score = 50.0
    details = {}
    sensitivity = SECTOR_MACRO_SENSITIVITY.get(sector, {})

    # Interest rate environment (using US 10Y as proxy for direction)
    us10y = global_indicators.get("us10y", {})
    if us10y:
        rate_change = us10y.get("month_change_pct", 0)
        rate_impact = rate_change * sensitivity.get("interest_rate", 0) * 2
        score += rate_impact
        details["interest_rate"] = {
            "us10y_current": us10y.get("current"),
            "month_change": rate_change,
            "impact": round(rate_impact, 2),
            "direction": "positive" if rate_impact > 0 else "negative",
        }

    # INR strength/weakness
    usdinr = global_indicators.get("usdinr", {})
    if usdinr:
        inr_change = usdinr.get("month_change_pct", 0)
        # Positive usdinr change = INR weakening
        inr_impact = inr_change * sensitivity.get("inr_weakness", 0) * 2
        score += inr_impact
        details["currency"] = {
            "usdinr_current": usdinr.get("current"),
            "month_change": inr_change,
            "impact": round(inr_impact, 2),
            "direction": "INR weakening" if inr_change > 0 else "INR strengthening",
        }

    # Crude oil
    crude = global_indicators.get("crude_oil", {})
    if crude:
        crude_change = crude.get("month_change_pct", 0)
        crude_impact = crude_change * sensitivity.get("crude_oil", 0) * 1.5
        score += crude_impact
        details["crude_oil"] = {
            "current": crude.get("current"),
            "month_change": crude_change,
            "impact": round(crude_impact, 2),
        }

    # US market correlation
    sp500 = global_indicators.get("sp500", {})
    if sp500:
        us_change = sp500.get("week_change_pct", 0)
        us_impact = us_change * sensitivity.get("us_market", 0) * 2
        score += us_impact
        details["us_market"] = {
            "sp500_week_change": us_change,
            "impact": round(us_impact, 2),
        }

    # India VIX (fear gauge)
    vix = global_indicators.get("vix_india", {})
    if vix:
        vix_current = vix.get("current", 15)
        if vix_current > 25:
            score -= 8  # High fear
            details["india_vix"] = {"current": vix_current, "signal": "high_fear"}
        elif vix_current > 20:
            score -= 4
            details["india_vix"] = {"current": vix_current, "signal": "elevated"}
        elif vix_current < 12:
            score += 5  # Complacency can also be a risk
            details["india_vix"] = {"current": vix_current, "signal": "low_complacent"}
        else:
            details["india_vix"] = {"current": vix_current, "signal": "normal"}

    # Nifty trend
    nifty = global_indicators.get("nifty", {})
    if nifty:
        nifty_week = nifty.get("week_change_pct", 0)
        nifty_month = nifty.get("month_change_pct", 0)
        if nifty_month > 5:
            score += 5
        elif nifty_month < -5:
            score -= 5
        details["nifty"] = {
            "current": nifty.get("current"),
            "week_change": nifty_week,
            "month_change": nifty_month,
        }

    score = max(0, min(100, score))

    if score >= 70:
        signal = "FAVORABLE"
    elif score >= 55:
        signal = "SLIGHTLY_FAVORABLE"
    elif score >= 45:
        signal = "NEUTRAL"
    elif score >= 30:
        signal = "SLIGHTLY_UNFAVORABLE"
    else:
        signal = "UNFAVORABLE"

    return {
        "score": round(score, 1),
        "signal": signal,
        "sector": sector,
        "details": details,
    }
