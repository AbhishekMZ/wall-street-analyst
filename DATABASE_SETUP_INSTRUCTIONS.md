# PostgreSQL Database Setup Instructions

## What Changed (v2.2.0)

**Database migration complete** — all JSON file storage now has PostgreSQL fallback for production persistence.

### Files Modified:
- ✅ `backend/requirements.txt` — Added `psycopg2-binary` and `sqlalchemy`
- ✅ `backend/app/database.py` — **NEW** SQLAlchemy models and DB layer
- ✅ `backend/app/decision_engine.py` — Uses DB with JSON fallback
- ✅ `backend/app/agent.py` — Uses DB for state/logs with JSON fallback
- ✅ `backend/app/learning_engine.py` — Uses DB with JSON fallback
- ✅ `backend/app/main.py` — Calls `init_db()` on startup

### System Behavior:
- **Without `DATABASE_URL`**: Works exactly as before (JSON files in `backend/data/`)
- **With `DATABASE_URL`**: All persistence goes to PostgreSQL, JSON files become backups

---

## Step-by-Step: Provision PostgreSQL on Render

### 1. Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `wall-street-analyst-db`
   - **Database**: `wsa_db` (or auto-generated)
   - **User**: `wsa_user` (or auto-generated)
   - **Region**: Same as your backend (e.g., Singapore)
   - **Plan**: **Free** (0 GB storage, expires after 90 days but data persists)
4. Click **Create Database**
5. Wait ~2 minutes for provisioning

### 2. Get Database Connection String

1. Once created, go to the database's **Info** tab
2. Find **Internal Database URL** (use this if backend is on same Render account)
   - Format: `postgresql://user:password@hostname:5432/dbname`
3. Copy the entire URL

**IMPORTANT:** The free tier URL starts with `postgres://` but SQLAlchemy needs `postgresql://`. The code auto-fixes this, but be aware.

### 3. Add DATABASE_URL to Backend Service

1. Go to your backend service: https://dashboard.render.com/web/srv-xxxxx (your wsa-api service)
2. Navigate to **Environment** tab
3. Click **Add Environment Variable**
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the Internal Database URL from step 2
4. Click **Save Changes**
5. Render will **automatically redeploy** your backend

### 4. Verify Database Initialization

After redeploy completes (~5 minutes):

1. Check Render logs for:
   ```
   ✅ Database connection established
   ✅ Database tables created/verified
   ✅ Default agent state initialized
   ✅ Default learning state initialized
   ```

2. If you see these, database is ready!

3. If you see `⚠️ Database connection failed`, check:
   - DATABASE_URL is correct (no typos)
   - Database is in "Available" status on Render dashboard
   - Internal URL matches your backend's region

---

## Testing Database Persistence

### Test 1: Trigger a Scan
```bash
curl -X POST https://wsa-api.onrender.com/api/agent/trigger/nifty50
```

Check response — should see scan start.

### Test 2: Check Agent Status
```bash
curl https://wsa-api.onrender.com/api/agent/status
```

Should see `total_scans_completed > 0` and `total_decisions_saved > 0`.

### Test 3: **CRITICAL** — Restart Backend
1. Go to Render dashboard → your backend service
2. Click **Manual Deploy** → **Clear build cache & deploy**
3. Wait for redeploy
4. Check status again:
   ```bash
   curl https://wsa-api.onrender.com/api/agent/status
   ```
5. **If `total_scans_completed` is still > 0**, database persistence works! 🎉
6. **If it reset to 0**, check logs for DB connection errors

---

## Database Schema

Tables created automatically on first startup:

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `decisions` | All stock analysis decisions | ticker, action, composite_score, timestamp, pnl_pct, outcome |
| `agent_state` | Agent's global state | state_key='global', state_data (JSONB) |
| `agent_activity_log` | All agent activities | timestamp, action, detail, category |
| `learning_state` | Learning engine weights/accuracy | version, adapted_weights, factor_accuracy |
| `portfolio_holdings` | User portfolio (if used) | ticker, qty, avg_price, pnl_pct |
| `weight_history` | Weight changes over time | timestamp, weights, hit_rate |

---

## Troubleshooting

### "Database connection failed"
- **Check**: DATABASE_URL env var is set correctly
- **Check**: Database status is "Available" on Render
- **Try**: Use External Database URL instead of Internal (less common issue)

### "Tables not created"
- **Check logs**: Look for SQL errors in Render logs
- **Possible cause**: PostgreSQL version mismatch (should auto-handle)
- **Fix**: Check if psycopg2-binary installed (run `pip list` in Render shell)

### "Data still resets after restart"
- **Verify**: DATABASE_URL is actually set (not just saved in dashboard but not applied)
- **Check logs**: Should see `DB_ENABLED = True` messages
- **Verify**: No errors during `init_db()`

### Local Development (Optional)

To test database locally:

1. Install PostgreSQL locally or use Docker:
   ```bash
   docker run --name wsa-postgres -e POSTGRES_PASSWORD=test -p 5432:5432 -d postgres:15
   ```

2. Create database:
   ```bash
   docker exec -it wsa-postgres psql -U postgres -c "CREATE DATABASE wsa_db;"
   ```

3. Set env var:
   ```bash
   # Windows PowerShell
   $env:DATABASE_URL="postgresql://postgres:test@localhost:5432/wsa_db"
   
   # Mac/Linux
   export DATABASE_URL="postgresql://postgres:test@localhost:5432/wsa_db"
   ```

4. Run backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

5. Check startup logs for `✅ Database connection established`

---

## Migration from JSON to PostgreSQL (Data Transfer)

If you have existing decisions in `backend/data/decisions.json` and want to migrate them:

**Option 1: Manual SQL Insert** (if < 100 decisions)
1. Read `decisions.json`
2. For each decision, INSERT into `decisions` table manually

**Option 2: Python Script** (recommended if > 100 decisions)
```python
# migration_script.py
import json
import os
from app.database import get_db, Decision
from datetime import datetime

# Set DATABASE_URL first
os.environ["DATABASE_URL"] = "postgresql://..."

# Load old JSON
with open("backend/data/decisions.json") as f:
    old_decisions = json.load(f)

# Insert into DB
with get_db() as db:
    for d in old_decisions:
        db_decision = Decision(
            ticker=d["ticker"],
            action=d["action"],
            # ... map all fields ...
        )
        db.add(db_decision)
    print(f"Migrated {len(old_decisions)} decisions")
```

**Option 3: Start Fresh** (recommended)
- Old JSON decisions stay in `backend/data/` as archive
- New decisions go to PostgreSQL
- Learning engine will re-train on new data

---

## Free Tier Limitations

**Render PostgreSQL Free Tier:**
- ✅ 1 GB storage (enough for ~1 million decisions)
- ✅ Shared CPU (fine for this workload)
- ❌ Database expires after 90 days (gets deleted, but you can create a new one)
- ❌ No automatic backups

**Recommended for Production:**
- Upgrade to **Starter ($7/month)** for persistent DB + backups
- OR export decisions to CSV weekly as backup

---

## What's Next After Database is Live?

See `AUDIT_AND_MIGRATION_PLAN.md` for:
1. **Priority 1 Accuracy Fixes** (~2 weeks work):
   - Adaptive thresholds per sector
   - Promoter pledge % integration (India-specific red flag)
   - Data quality filters
   - Real delivery % from NSE

2. **Backtesting Engine** (~1 week):
   - Validate hit rate empirically
   - Calibrate thresholds
   - Stratified testing by sector

3. **Advanced Features** (~4 weeks):
   - Regime detection (bull/bear/sideways)
   - Position sizing (Kelly Criterion)
   - Portfolio optimizer

---

**Current Status:** v2.2.0 — Database migration complete, ready to deploy ✅
