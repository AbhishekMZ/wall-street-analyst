# Wall Street Analyst — Indian Market Decision System

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    React Dashboard                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Decisions │ │ Analysis │ │ Reports  │ │ Portfolio  │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────┴─────────────────────────────────┐
│                  Python FastAPI Backend                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Decision Engine (Weighted Scoring)     │  │
│  ├──────────┬──────────┬──────────┬──────────────────┤  │
│  │Technical │Fundament │ Momentum │ Volume/Delivery  │  │
│  │ Analysis │ Analysis │ & Trend  │   Analysis       │  │
│  ├──────────┼──────────┼──────────┼──────────────────┤  │
│  │ Options  │ FII/DII  │  Macro   │ Sector Rotation  │  │
│  │ Analysis │  Flows   │Indicators│   & Breadth      │  │
│  ├──────────┼──────────┼──────────┼──────────────────┤  │
│  │Sentiment │ Seasonal │ Insider  │ Global           │  │
│  │ Analysis │ Patterns │ Activity │ Correlations     │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │            Report Generator & Tracker              │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                    Data Sources                           │
│  Yahoo Finance (NSE/BSE) │ NSE India │ RBI │ News APIs   │
└──────────────────────────────────────────────────────────┘
```

## Analysis Factors (15 Modules)

### Core (Prompts 1-10)
1. **Technical Analysis** — MA, RSI, MACD, Bollinger, patterns
2. **DCF Valuation** — Revenue projections, WACC, fair value
3. **Risk Assessment** — Correlation, drawdown, tail risk
4. **Earnings Analysis** — Beat/miss, guidance, EPS revision
5. **Portfolio Allocation** — Asset mix, rebalancing
6. **Technical Charting** — Support/resistance, Fibonacci
7. **Dividend Analysis** — Yield, safety, growth
8. **Competitive Analysis** — Moat, market share, SWOT
9. **Pattern Recognition** — Seasonal, statistical edges
10. **Macro Impact** — RBI, inflation, GDP, INR

### Additional Edge Factors
11. **Delivery Volume %** — High delivery = institutional conviction
12. **FII/DII Flow** — Foreign & domestic institutional money flow
13. **Options Chain Intelligence** — PCR, max pain, OI buildup
14. **Block/Bulk Deals** — Smart money tracking
15. **Promoter Holding Changes** — Insider confidence signal

### Global Correlation Layer
- USD/INR, Crude Oil, US 10Y Yield, DXY Index
- Nikkei, S&P 500 overnight moves
- Gold price (MCX correlation)

## Decision Output Format
```json
{
  "ticker": "RELIANCE.NS",
  "action": "BUY",
  "confidence": 82,
  "target_price": 2850,
  "stop_loss": 2620,
  "time_horizon": "2-4 weeks",
  "risk_rating": 4,
  "reasoning": { ... },
  "scores": {
    "technical": 78,
    "fundamental": 85,
    "momentum": 72,
    "sentiment": 68,
    "macro": 75
  }
}
```

## Report Tracking
- **Daily**: Decision log with entry prices
- **Weekly**: P&L report, hit rate, best/worst calls
- **Monthly**: Aggregate performance, Sharpe ratio, alpha vs Nifty 50
