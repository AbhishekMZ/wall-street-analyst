"""
Database Layer - PostgreSQL with SQLAlchemy
Provides persistent storage for decisions, agent state, learning state, and portfolio.
Falls back to JSON if DATABASE_URL is not set (local development).
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, TIMESTAMP, Text, ARRAY, Boolean, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
from contextlib import contextmanager

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Render uses postgres://, SQLAlchemy 1.4+ needs postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine only if DATABASE_URL exists
engine = None
SessionLocal = None
DB_ENABLED = False

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=False  # Set to True for SQL debugging
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DB_ENABLED = True
        print("✅ Database connection established")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("📁 Falling back to JSON file storage")
        DB_ENABLED = False
else:
    print("📁 DATABASE_URL not set, using JSON file storage")

Base = declarative_base()


# ─── Models ───

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    name = Column(String(200))
    sector = Column(String(100), index=True)
    action = Column(String(20), nullable=False, index=True)
    confidence = Column(Integer, CheckConstraint('confidence BETWEEN 0 AND 100'))
    composite_score = Column(DECIMAL(5, 2))
    price = Column(DECIMAL(12, 2))
    target_price = Column(DECIMAL(12, 2))
    stop_loss = Column(DECIMAL(12, 2))
    risk_reward_ratio = Column(DECIMAL(5, 2))
    time_horizon = Column(String(20))
    risk_rating = Column(Integer, CheckConstraint('risk_rating BETWEEN 1 AND 10'))
    
    # Score breakdown
    technical_score = Column(DECIMAL(5, 2))
    fundamental_score = Column(DECIMAL(5, 2))
    momentum_score = Column(DECIMAL(5, 2))
    macro_score = Column(DECIMAL(5, 2))
    
    # Full analysis as JSON
    analysis_json = Column(JSONB)
    reasoning = Column(ARRAY(Text))
    
    # Metadata
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)
    data_quality_score = Column(Integer)
    
    # Evaluation (populated later)
    evaluated_at = Column(TIMESTAMP)
    current_price = Column(DECIMAL(12, 2))
    pnl_pct = Column(DECIMAL(8, 2))
    outcome = Column(String(20), index=True)
    
    __table_args__ = (
        UniqueConstraint('ticker', 'timestamp', name='unique_ticker_timestamp'),
    )


class AgentState(Base):
    __tablename__ = "agent_state"

    id = Column(Integer, primary_key=True)
    state_key = Column(String(100), unique=True, nullable=False)
    state_data = Column(JSONB, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentActivityLog(Base):
    __tablename__ = "agent_activity_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)
    action = Column(String(50), nullable=False)
    detail = Column(Text, nullable=False)
    category = Column(String(20), index=True)
    metadata = Column(JSONB)
    
    __table_args__ = (
        CheckConstraint("category IN ('scan', 'signal', 'learning', 'error', 'system')", name='check_category'),
    )


class LearningState(Base):
    __tablename__ = "learning_state"

    id = Column(Integer, primary_key=True)
    version = Column(Integer, nullable=False, unique=True, default=1)
    factor_accuracy = Column(JSONB, nullable=False)
    confidence_calibration = Column(JSONB, nullable=False)
    adapted_weights = Column(JSONB, nullable=False)
    regime_state = Column(String(20))
    total_decisions_evaluated = Column(Integer, default=0)
    avg_hit_rate = Column(DECIMAL(5, 2))
    sharpe_ratio = Column(DECIMAL(5, 2))
    max_drawdown = Column(DECIMAL(5, 2))
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False, unique=True)
    qty = Column(DECIMAL(12, 4), nullable=False, CheckConstraint('qty > 0'))
    avg_price = Column(DECIMAL(12, 2), nullable=False, CheckConstraint('avg_price > 0'))
    buy_date = Column(TIMESTAMP, nullable=False)
    sector = Column(String(100), index=True)
    current_price = Column(DECIMAL(12, 2))
    current_value = Column(DECIMAL(12, 2))
    pnl = Column(DECIMAL(12, 2))
    pnl_pct = Column(DECIMAL(8, 2))
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)


class WeightHistory(Base):
    __tablename__ = "weight_history"

    id = Column(Integer, primary_key=True)
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True)
    weights = Column(JSONB, nullable=False)
    hit_rate = Column(DECIMAL(5, 2))
    avg_return = Column(DECIMAL(8, 2))
    decisions_count = Column(Integer)
    reason = Column(String(200))


# ─── Helper Functions ───

@contextmanager
def get_db() -> Session:
    """Context manager for database sessions."""
    if not DB_ENABLED or not SessionLocal:
        raise RuntimeError("Database not enabled")
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables and default data."""
    if not DB_ENABLED:
        print("⚠️ Skipping DB initialization (not enabled)")
        return
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Insert default agent state if not exists
        with get_db() as db:
            existing = db.query(AgentState).filter_by(state_key='global').first()
            if not existing:
                default_state = AgentState(
                    state_key='global',
                    state_data={
                        "agent_started_at": None,
                        "total_scans_completed": 0,
                        "total_stocks_analyzed": 0,
                        "total_decisions_saved": 0,
                        "last_scan": {},
                        "learning_cycles": 0
                    }
                )
                db.add(default_state)
                print("✅ Default agent state initialized")
            
            # Insert default learning state if not exists
            existing_learning = db.query(LearningState).filter_by(version=1).first()
            if not existing_learning:
                default_learning = LearningState(
                    version=1,
                    factor_accuracy={"technical": 0.5, "fundamental": 0.5, "momentum": 0.5, "macro": 0.5},
                    confidence_calibration={},
                    adapted_weights={
                        "technical": 0.30,
                        "fundamental": 0.25,
                        "momentum": 0.20,
                        "macro": 0.15,
                        "volume_delivery": 0.10
                    }
                )
                db.add(default_learning)
                print("✅ Default learning state initialized")
                
    except Exception as e:
        print(f"❌ Database initialization error: {e}")


# ─── Decision Storage Functions ───

def save_decision_db(decision: dict) -> bool:
    """Save decision to database. Returns True on success."""
    if not DB_ENABLED:
        return False
    
    try:
        with get_db() as db:
            db_decision = Decision(
                ticker=decision["ticker"],
                name=decision.get("name"),
                sector=decision.get("sector"),
                action=decision["action"],
                confidence=decision.get("confidence"),
                composite_score=decision.get("composite_score"),
                price=decision.get("price"),
                target_price=decision.get("target_price"),
                stop_loss=decision.get("stop_loss"),
                risk_reward_ratio=decision.get("risk_reward_ratio"),
                time_horizon=decision.get("time_horizon"),
                risk_rating=decision.get("risk_rating"),
                technical_score=decision.get("scores", {}).get("technical"),
                fundamental_score=decision.get("scores", {}).get("fundamental"),
                momentum_score=decision.get("scores", {}).get("momentum"),
                macro_score=decision.get("scores", {}).get("macro"),
                analysis_json=decision.get("analysis"),
                reasoning=decision.get("reasoning"),
                timestamp=datetime.fromisoformat(decision["timestamp"]) if isinstance(decision.get("timestamp"), str) else datetime.utcnow()
            )
            db.add(db_decision)
        return True
    except Exception as e:
        print(f"❌ Failed to save decision to DB: {e}")
        return False


def load_decisions_db(limit: int = 100, ticker: Optional[str] = None) -> List[dict]:
    """Load decisions from database."""
    if not DB_ENABLED:
        return []
    
    try:
        with get_db() as db:
            query = db.query(Decision)
            if ticker:
                query = query.filter(Decision.ticker == ticker)
            query = query.order_by(Decision.timestamp.desc()).limit(limit)
            decisions = query.all()
            
            return [
                {
                    "id": d.id,
                    "ticker": d.ticker,
                    "name": d.name,
                    "sector": d.sector,
                    "action": d.action,
                    "confidence": d.confidence,
                    "composite_score": float(d.composite_score) if d.composite_score else None,
                    "price": float(d.price) if d.price else None,
                    "target_price": float(d.target_price) if d.target_price else None,
                    "stop_loss": float(d.stop_loss) if d.stop_loss else None,
                    "risk_reward_ratio": float(d.risk_reward_ratio) if d.risk_reward_ratio else None,
                    "time_horizon": d.time_horizon,
                    "risk_rating": d.risk_rating,
                    "scores": {
                        "technical": float(d.technical_score) if d.technical_score else None,
                        "fundamental": float(d.fundamental_score) if d.fundamental_score else None,
                        "momentum": float(d.momentum_score) if d.momentum_score else None,
                        "macro": float(d.macro_score) if d.macro_score else None,
                    },
                    "analysis": d.analysis_json,
                    "reasoning": d.reasoning,
                    "timestamp": d.timestamp.isoformat(),
                    "outcome": d.outcome,
                    "pnl_pct": float(d.pnl_pct) if d.pnl_pct else None,
                }
                for d in decisions
            ]
    except Exception as e:
        print(f"❌ Failed to load decisions from DB: {e}")
        return []


# ─── Agent State Functions ───

def get_agent_state_db() -> Optional[dict]:
    """Get global agent state from database."""
    if not DB_ENABLED:
        return None
    
    try:
        with get_db() as db:
            state = db.query(AgentState).filter_by(state_key='global').first()
            return state.state_data if state else None
    except Exception as e:
        print(f"❌ Failed to get agent state: {e}")
        return None


def update_agent_state_db(state_data: dict) -> bool:
    """Update global agent state in database."""
    if not DB_ENABLED:
        return False
    
    try:
        with get_db() as db:
            state = db.query(AgentState).filter_by(state_key='global').first()
            if state:
                state.state_data = state_data
                state.updated_at = datetime.utcnow()
            else:
                state = AgentState(state_key='global', state_data=state_data)
                db.add(state)
        return True
    except Exception as e:
        print(f"❌ Failed to update agent state: {e}")
        return False


def log_activity_db(action: str, detail: str, category: str = "system", metadata: Optional[dict] = None) -> bool:
    """Log agent activity to database."""
    if not DB_ENABLED:
        return False
    
    try:
        with get_db() as db:
            log_entry = AgentActivityLog(
                action=action,
                detail=detail,
                category=category,
                metadata=metadata
            )
            db.add(log_entry)
        return True
    except Exception as e:
        print(f"❌ Failed to log activity: {e}")
        return False


def get_activity_logs_db(limit: int = 50) -> List[dict]:
    """Get recent activity logs from database."""
    if not DB_ENABLED:
        return []
    
    try:
        with get_db() as db:
            logs = db.query(AgentActivityLog).order_by(AgentActivityLog.timestamp.desc()).limit(limit).all()
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "detail": log.detail,
                    "category": log.category,
                    "metadata": log.metadata
                }
                for log in logs
            ]
    except Exception as e:
        print(f"❌ Failed to get activity logs: {e}")
        return []


# ─── Learning State Functions ───

def get_learning_state_db() -> Optional[dict]:
    """Get latest learning state from database."""
    if not DB_ENABLED:
        return None
    
    try:
        with get_db() as db:
            state = db.query(LearningState).order_by(LearningState.version.desc()).first()
            if not state:
                return None
            return {
                "version": state.version,
                "factor_accuracy": state.factor_accuracy,
                "confidence_calibration": state.confidence_calibration,
                "adapted_weights": state.adapted_weights,
                "regime_state": state.regime_state,
                "total_decisions_evaluated": state.total_decisions_evaluated,
                "avg_hit_rate": float(state.avg_hit_rate) if state.avg_hit_rate else None,
                "sharpe_ratio": float(state.sharpe_ratio) if state.sharpe_ratio else None,
                "max_drawdown": float(state.max_drawdown) if state.max_drawdown else None,
                "updated_at": state.updated_at.isoformat()
            }
    except Exception as e:
        print(f"❌ Failed to get learning state: {e}")
        return None


def update_learning_state_db(learning_data: dict) -> bool:
    """Update learning state in database (creates new version)."""
    if not DB_ENABLED:
        return False
    
    try:
        with get_db() as db:
            # Get current max version
            max_version = db.query(LearningState).order_by(LearningState.version.desc()).first()
            new_version = (max_version.version + 1) if max_version else 1
            
            new_state = LearningState(
                version=new_version,
                factor_accuracy=learning_data.get("factor_accuracy", {}),
                confidence_calibration=learning_data.get("confidence_calibration", {}),
                adapted_weights=learning_data.get("adapted_weights", {}),
                regime_state=learning_data.get("regime_state"),
                total_decisions_evaluated=learning_data.get("total_decisions_evaluated", 0),
                avg_hit_rate=learning_data.get("avg_hit_rate"),
                sharpe_ratio=learning_data.get("sharpe_ratio"),
                max_drawdown=learning_data.get("max_drawdown")
            )
            db.add(new_state)
        return True
    except Exception as e:
        print(f"❌ Failed to update learning state: {e}")
        return False
