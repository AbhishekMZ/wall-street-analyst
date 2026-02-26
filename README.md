# Wall Street Analyst — Indian Market Decision System

An institutional-grade, multi-factor stock analysis engine for the Indian market (NSE/BSE).
Combines technical, fundamental, momentum, and macro analysis to generate actionable
buy/sell decisions with confidence scores, targets, stop-losses, and reasoning.

## Quick Start

### 1. Start the Backend (Python FastAPI)
```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend (React + Vite)
```powershell
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## System Architecture

```
Frontend (React Dashboard)  ←→  Backend (FastAPI + Python)  ←→  Data (Yahoo Finance, NSE)
```

### Analysis Modules (15 Factors)
| # | Module | Weight | Source |
|---|--------|--------|--------|
| 1 | Technical Analysis (RSI, MACD, Bollinger, MA) | 25% | Price data |
| 2 | Fundamental Analysis (P/E, ROE, D/E, growth) | 20% | Financial data |
| 3 | Momentum & Relative Strength | 15% | Price vs Nifty 50 |
| 4 | Volume & Delivery Analysis | 10% | Volume data |
| 5 | Macro Impact (RBI, INR, crude, VIX) | 10% | Global indicators |
| 6 | Sentiment | 5% | News APIs (planned) |
| 7 | Seasonal Patterns | 5% | Historical data |
| 8 | Global Correlations | 5% | DXY, S&P, crude |
| 9 | Options Flow (PCR, max pain) | 5% | NSE options chain |

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze/{ticker}` | GET | Full analysis of a single stock |
| `/api/scan` | POST | Scan Nifty 50 for top buy/sell signals |
| `/api/scan/quick` | POST | Scan a custom watchlist |
| `/api/decisions` | GET | View decision history |
| `/api/reports/weekly` | GET | Weekly performance report |
| `/api/reports/cumulative` | GET | Cumulative performance report |
| `/api/macro` | GET | Current macro indicators |
| `/api/universe` | GET | Default stock universe (Nifty 50) |

### Decision Output
Each analysis generates:
- **Action**: STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL
- **Confidence**: 30-95%
- **Target Price** & **Stop Loss** (ATR + support/resistance based)
- **Risk-Reward Ratio**
- **Time Horizon** (based on ADX + volatility)
- **Score Breakdown** (technical, fundamental, momentum, macro)
- **Reasoning** (human-readable explanations)

## Trust-Building Process (3-4 Month Plan)
1. **Week 1-2**: Run daily analyses, log all decisions
2. **Week 3-4**: Generate first weekly reports, compare vs Nifty
3. **Month 2**: Review hit rate, refine weights, add more factors
4. **Month 3-4**: Track cumulative alpha, adjust risk parameters
5. **After validation**: Use for real decision support

## Disclaimer
This is for **educational and research purposes only**. Not financial advice.
Always do your own due diligence before making investment decisions.
