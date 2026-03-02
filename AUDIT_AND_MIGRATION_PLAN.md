# Wall Street Analyst — Critical Audit & Database Migration Plan

**Date:** March 2, 2026  
**Version:** 2.1.0 Analysis  
**Purpose:** Identify structural holes, design persistent database, plan accuracy improvements

---

## 1. CRITICAL STRUCTURAL HOLES IDENTIFIED

### 🔴 HOLE #1: Hardcoded Decision Thresholds (High Severity)
**Location:** `decision_engine.py:181-195`
```python
if composite >= 72: action = "STRONG_BUY"
elif composite >= 60: action = "BUY"
elif composite >= 42: action = "HOLD"
elif composite >= 30: action = "SELL"
else: action = "STRONG_SELL"
```

**Problem:**
- Thresholds (72, 60, 42, 30) are arbitrary magic numbers with no empirical justification
- No sector-specific adjustments (Tech vs Banking have different volatility profiles)
- No market regime awareness (bull vs bear markets need different thresholds)
- Learning engine adapts weights but thresholds stay static

**Impact:** False signals, poor hit rate, inconsistent performance across sectors

**Proposed Fix:**
- Make thresholds adaptive per sector
- Calibrate thresholds empirically from historical hit rates
- Add regime detection (bull/bear/sideways) to shift thresholds dynamically

---

### 🔴 HOLE #2: Volume/Delivery Score is Synthetic (High Severity)
**Location:** `decision_engine.py:158-169`
```python
vol_score = 50.0
vs = vol_signal.get("signal", "neutral")
if vs == "strong_accumulation": vol_score = 80
elif vs == "accumulation": vol_score = 65
```

**Problem:**
- Volume signal derived from price change direction is too simplistic
- No actual delivery % data (NSE provides this but not fetched)
- "Accumulation" vs "distribution" logic is naive (vol_ratio > 1.5 + price_change)
- No institutional flow tracking

**Impact:** Misses institutional buying/selling, weak conviction on signals

**Proposed Fix:**
- Integrate NSE BhavCopy data for actual delivery %
- Add FII/DII flow tracking via NSE archives
- Use delivery % > 50% as strong accumulation signal

---

### 🔴 HOLE #3: Fundamental Analysis Missing Key Ratios (Medium-High Severity)
**Location:** `fundamental_analysis.py:261-303`

**Missing Critical Metrics:**
- Price-to-Sales (P/S) — critical for growth stocks
- EV/EBITDA — better than P/E for leveraged companies
- Altman Z-Score — bankruptcy risk
- Cash conversion cycle — working capital efficiency
- Insider ownership % — skin in the game
- Promoter pledge % — distress signal (India-specific!)

**Impact:** Incomplete fundamental picture, missing red flags (high promoter pledge = sell signal)

**Proposed Fix:** Add these metrics, fetch from yfinance + NSE corporate announcements API

---

### 🔴 HOLE #4: No Backtesting / Validation Loop (Critical Severity)
**Location:** Entire system

**Problem:**
- Decisions are saved but never systematically backtested
- `report_generator.py:evaluate_decision()` evaluates outcomes but learning is superficial
- No walk-forward validation
- No stratified testing (sector, market cap, volatility buckets)
- No performance attribution (which factor contributed most to wins/losses?)

**Impact:** Cannot prove system works, no feedback loop to improve

**Proposed Fix:**
- Build backtesting engine that simulates decisions on historical data
- Track hit rate, Sharpe ratio, max drawdown by sector/timeframe
- Use results to calibrate thresholds and weights

---

### 🔴 HOLE #5: Target/Stop-Loss Logic is Oversimplified (Medium Severity)
**Location:** `decision_engine.py:54-92`
```python
if action == "STRONG_BUY":
    target = price + (2 * atr)
    stop = price - (1.5 * atr)
```

**Problem:**
- ATR-based targets ignore actual support/resistance levels
- No consideration of volatility regime (high VIX = wider stops needed)
- Fixed 2x ATR for all stocks (small cap needs tighter, large cap looser)
- No trailing stop logic

**Impact:** Stops too tight (whipsawed out) or too loose (large losses)

**Proposed Fix:**
- Use actual S/R levels from technical analysis
- Adjust stop width by ATR percentile (high vol = wider)
- Add position sizing guidance (risk % per trade)

---

### 🔴 HOLE #6: Macro Analysis is Static Mapping (Medium Severity)
**Location:** `macro_analysis.py:10-82`

**Problem:**
- Sector sensitivities are hardcoded constants (e.g., IT/INR = 0.8)
- No dynamic correlation calculation from actual data
- Assumes linear relationships (crude ↑ always hurts airlines by same amount)
- No lag consideration (rate changes affect banks with 2-3 month lag)

**Impact:** Macro signals are directionally correct but magnitudes are wrong

**Proposed Fix:**
- Calculate rolling correlations from historical data
- Use regime-dependent sensitivities (correlation changes in crisis)

---

### 🔴 HOLE #7: Learning Engine Adapts Weights Without Constraints (Medium Severity)
**Location:** `learning_engine.py:239-280` (_adapt_weights function)

**Problem:**
- Weight adaptation can drift too far from priors (technical weight could go to 0.01)
- No regularization / bounds enforcement
- Overfitting risk if only 10-20 decisions in history
- No ensemble approach (single model = brittle)

**Impact:** Weights become unstable, performance degrades on new data

**Proposed Fix:**
- Add L2 regularization to keep weights near defaults
- Require minimum sample size (50+ decisions) before adapting
- Use Bayesian updating instead of direct optimization

---

### 🟡 HOLE #8: No Data Quality Checks (Medium Severity)
**Problem:**
- `yfinance` data can be stale, missing, or incorrect
- No validation that fetched data is fresh (e.g., last price is from today)
- No outlier detection (stock price = $0.01 should trigger error)
- No cross-validation with alternative data sources

**Impact:** Analysis on bad data = garbage signals

**Proposed Fix:**
- Add data freshness checks (reject if last date < today - 7 days)
- Outlier filters (flag if price change > 50% in 1 day without news)
- Fallback to NSE API if yfinance fails

---

### 🟡 HOLE #9: No Position Sizing / Portfolio Management (Medium Severity)
**Location:** Missing entirely

**Problem:**
- System gives BUY/SELL signals but no guidance on how much to buy
- No portfolio-level risk management
- No correlation awareness (buying 5 IT stocks = concentrated bet)
- No rebalancing logic

**Impact:** Users don't know how to act on signals safely

**Proposed Fix:**
- Add Kelly Criterion position sizing based on confidence + historical hit rate
- Portfolio optimizer that caps sector exposure at 25%
- Rebalancing triggers (rebalance if drift > 10%)

---

## 2. ACCURACY IMPROVEMENT OPPORTUNITIES (Feasibility Analysis)

### Priority 1: High ROI, Low Effort

| Improvement | Expected Accuracy Gain | Implementation Effort | Priority |
|-------------|------------------------|----------------------|----------|
| **Adaptive thresholds per sector** | +8-12% hit rate | 2-3 days (empirical calibration) | **HIGHEST** |
| **Add promoter pledge % check** | +5-8% (avoid disasters) | 1 day (NSE scraping) | **HIGHEST** |
| **Data quality filters** | +3-5% (garbage prevention) | 1 day | **HIGH** |
| **Use actual S/R for targets** | +10-15% R:R improvement | 1 day (already computed) | **HIGH** |
| **Delivery % integration** | +5-8% conviction accuracy | 2 days (NSE BhavCopy) | **HIGH** |

### Priority 2: High ROI, Medium Effort

| Improvement | Expected Accuracy Gain | Implementation Effort | Priority |
|-------------|------------------------|----------------------|----------|
| **Backtesting engine** | Validates entire system | 5-7 days | **CRITICAL** |
| **Dynamic macro correlations** | +4-6% macro timing | 3-4 days (rolling calc) | **MEDIUM** |
| **Add missing fundamental ratios** | +3-5% fundamental edge | 2-3 days | **MEDIUM** |
| **Position sizing module** | +20-30% portfolio returns | 3-4 days | **MEDIUM** |

### Priority 3: Medium ROI, High Effort

| Improvement | Expected Accuracy Gain | Implementation Effort | Priority |
|-------------|------------------------|----------------------|----------|
| **Regime detection (ML)** | +8-12% (context-aware) | 7-10 days (ML model) | **MEDIUM** |
| **Sentiment analysis (news)** | +5-8% (catalyst timing) | 10-14 days (NLP pipeline) | **LOW** |
| **Options flow tracking** | +10-15% (smart money) | 14+ days (complex scraping) | **LOW** |

**Recommendation:** Focus on Priority 1 items first (2 weeks), then build backtesting engine, then Priority 2.

---

## 3. DATABASE SCHEMA DESIGN (PostgreSQL)

### Table 1: `decisions`
```sql
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(200),
    sector VARCHAR(100),
    action VARCHAR(20) NOT NULL, -- STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence INT CHECK (confidence BETWEEN 0 AND 100),
    composite_score DECIMAL(5,2),
    price DECIMAL(12,2),
    target_price DECIMAL(12,2),
    stop_loss DECIMAL(12,2),
    risk_reward_ratio DECIMAL(5,2),
    time_horizon VARCHAR(20),
    risk_rating INT CHECK (risk_rating BETWEEN 1 AND 10),
    
    -- Scores breakdown
    technical_score DECIMAL(5,2),
    fundamental_score DECIMAL(5,2),
    momentum_score DECIMAL(5,2),
    macro_score DECIMAL(5,2),
    
    -- Full analysis JSON (for detailed review)
    analysis_json JSONB,
    reasoning TEXT[],
    
    -- Metadata
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    data_quality_score INT, -- 0-100, based on data freshness/completeness
    
    -- Evaluation (populated later by evaluate_decision)
    evaluated_at TIMESTAMP,
    current_price DECIMAL(12,2),
    pnl_pct DECIMAL(8,2),
    outcome VARCHAR(20), -- TARGET_HIT, STOPLOSS_HIT, OPEN, HOLD
    
    CONSTRAINT unique_ticker_timestamp UNIQUE(ticker, timestamp)
);

CREATE INDEX idx_decisions_ticker ON decisions(ticker);
CREATE INDEX idx_decisions_timestamp ON decisions(timestamp DESC);
CREATE INDEX idx_decisions_action ON decisions(action);
CREATE INDEX idx_decisions_sector ON decisions(sector);
CREATE INDEX idx_decisions_outcome ON decisions(outcome);
```

### Table 2: `agent_state`
```sql
CREATE TABLE agent_state (
    id SERIAL PRIMARY KEY,
    state_key VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'global', 'nifty50_scan', etc.
    state_data JSONB NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Single-row global state
INSERT INTO agent_state (state_key, state_data) VALUES ('global', '{
    "agent_started_at": null,
    "total_scans_completed": 0,
    "total_stocks_analyzed": 0,
    "total_decisions_saved": 0,
    "last_scan": {},
    "learning_cycles": 0
}') ON CONFLICT (state_key) DO NOTHING;
```

### Table 3: `agent_activity_log`
```sql
CREATE TABLE agent_activity_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    action VARCHAR(50) NOT NULL,
    detail TEXT NOT NULL,
    category VARCHAR(20), -- scan, signal, learning, error, system
    metadata JSONB,
    
    CONSTRAINT check_category CHECK (category IN ('scan', 'signal', 'learning', 'error', 'system'))
);

CREATE INDEX idx_activity_timestamp ON agent_activity_log(timestamp DESC);
CREATE INDEX idx_activity_category ON agent_activity_log(category);
```

### Table 4: `learning_state`
```sql
CREATE TABLE learning_state (
    id SERIAL PRIMARY KEY,
    version INT NOT NULL DEFAULT 1,
    factor_accuracy JSONB NOT NULL, -- {"technical": 0.65, "fundamental": 0.58, ...}
    confidence_calibration JSONB NOT NULL,
    adapted_weights JSONB NOT NULL,
    regime_state VARCHAR(20), -- bull, bear, sideways
    total_decisions_evaluated INT DEFAULT 0,
    avg_hit_rate DECIMAL(5,2),
    sharpe_ratio DECIMAL(5,2),
    max_drawdown DECIMAL(5,2),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_version UNIQUE(version)
);

-- Insert default learning state
INSERT INTO learning_state (version, factor_accuracy, confidence_calibration, adapted_weights) VALUES (
    1,
    '{"technical": 0.5, "fundamental": 0.5, "momentum": 0.5, "macro": 0.5}',
    '{}',
    '{"technical": 0.30, "fundamental": 0.25, "momentum": 0.20, "macro": 0.15, "volume_delivery": 0.10}'
) ON CONFLICT (version) DO NOTHING;
```

### Table 5: `portfolio_holdings`
```sql
CREATE TABLE portfolio_holdings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    qty DECIMAL(12,4) NOT NULL CHECK (qty > 0),
    avg_price DECIMAL(12,2) NOT NULL CHECK (avg_price > 0),
    buy_date DATE NOT NULL,
    sector VARCHAR(100),
    current_price DECIMAL(12,2),
    current_value DECIMAL(12,2),
    pnl DECIMAL(12,2),
    pnl_pct DECIMAL(8,2),
    last_updated TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_ticker_portfolio UNIQUE(ticker)
);

CREATE INDEX idx_portfolio_sector ON portfolio_holdings(sector);
```

### Table 6: `weight_history` (for learning engine)
```sql
CREATE TABLE weight_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    weights JSONB NOT NULL,
    hit_rate DECIMAL(5,2),
    avg_return DECIMAL(8,2),
    decisions_count INT,
    reason VARCHAR(200) -- "Auto-learning cycle", "Manual reset", etc.
);

CREATE INDEX idx_weight_history_timestamp ON weight_history(timestamp DESC);
```

### Table 7: `backtests`
```sql
CREATE TABLE backtests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    universe VARCHAR(50), -- nifty50, nifty_next50, etc.
    config JSONB NOT NULL, -- thresholds, weights used
    results JSONB NOT NULL, -- hit_rate, sharpe, max_dd, total_return, etc.
    trades_count INT,
    winners INT,
    losers INT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 4. MIGRATION PLAN

### Phase 1: Database Setup (Day 1)
1. **Create PostgreSQL on Render Free Tier**
   - Provision via Render dashboard
   - Note connection string (store in env var `DATABASE_URL`)
   - Verify connection with `psql`

2. **Install Dependencies**
   ```bash
   pip install psycopg2-binary sqlalchemy alembic
   ```

3. **Run Schema Creation**
   - Execute all CREATE TABLE statements
   - Verify with `\dt` in psql

### Phase 2: Create Database Layer (Day 2-3)
**File:** `backend/app/database.py`
```python
from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, TIMESTAMP, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Decision(Base):
    __tablename__ = "decisions"
    # ... (map to schema)

class AgentState(Base):
    __tablename__ = "agent_state"
    # ...

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_decision_db(decision: dict):
    db = next(get_db())
    # ... insert logic
```

### Phase 3: Migrate decision_engine.py (Day 3-4)
- Replace `save_decision()` JSON file logic with DB insert
- Replace `load_decisions()` with SQL query
- Keep backward compatibility (check if DB_URL exists, fallback to JSON)

### Phase 4: Migrate agent.py state/logs (Day 4-5)
- Replace JSON state files with `agent_state` table
- Replace activity log JSON with `agent_activity_log` table inserts
- Add connection pooling for background tasks

### Phase 5: Migrate learning_engine.py (Day 5-6)
- Store learning state in `learning_state` table
- Track weight history in `weight_history` table
- Load latest weights from DB on startup

### Phase 6: Migrate portfolio_manager.py (Day 6)
- Use `portfolio_holdings` table
- Add endpoints to sync CSV import → DB

### Phase 7: Testing & Deploy (Day 7)
- Test locally with PostgreSQL
- Run full scan → verify decisions persist across restarts
- Deploy to Render
- Verify DB connection works on Render
- Run smoke test scan

---

## 5. STRUCTURAL FIXES ROADMAP

### Week 1: Database + Critical Fixes
- [ ] Setup PostgreSQL on Render
- [ ] Migrate all JSON persistence to DB
- [ ] Add adaptive thresholds per sector
- [ ] Add promoter pledge % check (NSE scraping)
- [ ] Add data quality filters

### Week 2: Backtesting + Validation
- [ ] Build backtesting engine
- [ ] Run historical validation (6 months of data)
- [ ] Calibrate thresholds empirically
- [ ] Track hit rate by sector

### Week 3: Accuracy Improvements
- [ ] Add missing fundamental ratios (P/S, EV/EBITDA, Z-Score)
- [ ] Integrate delivery % from NSE BhavCopy
- [ ] Use actual S/R levels for targets
- [ ] Dynamic macro correlations

### Week 4: Portfolio Management
- [ ] Position sizing module (Kelly Criterion)
- [ ] Portfolio optimizer (sector caps)
- [ ] Rebalancing triggers
- [ ] Risk dashboard

---

## 6. COMPARISON: CURRENT vs IDEAL SYSTEM

| Aspect | Current (v2.1.0) | After Migration | After Fixes |
|--------|------------------|-----------------|-------------|
| **Data Persistence** | ❌ Ephemeral (lost on restart) | ✅ PostgreSQL permanent | ✅ Same |
| **Decision Thresholds** | ❌ Hardcoded magic numbers | ✅ DB-stored | ✅ Adaptive per sector |
| **Fundamental Coverage** | ⚠️ 60% (missing key ratios) | ✅ Same | ✅ 95% (all critical ratios) |
| **Volume Analysis** | ❌ Synthetic (fake delivery %) | ✅ Same | ✅ Real NSE delivery % |
| **Backtesting** | ❌ None | ✅ Same | ✅ Full engine with metrics |
| **Macro Analysis** | ⚠️ Static sensitivities | ✅ Same | ✅ Dynamic correlations |
| **Learning Stability** | ⚠️ Unbounded drift | ✅ Same | ✅ Regularized Bayesian |
| **Data Quality** | ❌ No validation | ✅ Same | ✅ Freshness + outlier checks |
| **Position Sizing** | ❌ Missing | ✅ Same | ✅ Kelly + portfolio optimizer |
| **Hit Rate (estimated)** | ~45-50% | ~45-50% | **~62-68%** |

---

## 7. IMMEDIATE NEXT STEPS

1. **PostgreSQL Setup** (2 hours)
   - Create Render PostgreSQL instance
   - Run schema SQL
   - Get connection string

2. **Create database.py** (4 hours)
   - SQLAlchemy models
   - Helper functions
   - Test connection

3. **Migrate decision_engine.py** (6 hours)
   - Replace save/load functions
   - Test with local DB
   - Deploy to Render

4. **Test End-to-End** (2 hours)
   - Trigger scan
   - Verify decisions persist
   - Restart backend
   - Verify state survives

**Total Estimate for DB Migration:** 2-3 days  
**Total Estimate for All Fixes:** 4 weeks

---

**END OF AUDIT**
