import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Loader2, RefreshCw, Target, AlertTriangle } from 'lucide-react';
import { api } from '../api';

interface MockTrade {
  ticker: string;
  name: string;
  sector: string;
  action: string;
  price: number;
  current_price: number;
  target_price: number;
  stop_loss: number;
  pnl_pct: number;
  outcome: string;
  confidence: number;
  timestamp: string;
}

interface MockSummary {
  total_trades: number;
  winners: number;
  losers: number;
  hit_rate: number;
  avg_pnl: number;
  total_pnl: number;
  best_trade: number;
  worst_trade: number;
}

export default function MockInvestmentsPanel() {
  const [trades, setTrades] = useState<MockTrade[]>([]);
  const [summary, setSummary] = useState<MockSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadMockData = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getMockInvestments(50) as any;
      setTrades(data.decisions || []);
      setSummary(data.summary || null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadMockData(); }, []);

  const outcomeColor: Record<string, string> = {
    TARGET_HIT: 'text-emerald-400',
    STOPLOSS_HIT: 'text-red-400',
    OPEN: 'text-cyan-400',
    HOLD: 'text-zinc-400',
  };

  const outcomeLabel: Record<string, string> = {
    TARGET_HIT: 'Target Hit',
    STOPLOSS_HIT: 'Stop Loss Hit',
    OPEN: 'Open',
    HOLD: 'Holding',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <DollarSign size={18} className="text-cyan-400" />
          <h3 className="text-white font-bold text-base">Mock Investments</h3>
          <span className="text-zinc-600 text-xs">— Paper trading tracker</span>
        </div>
        <button
          onClick={loadMockData}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-zinc-300 text-xs font-medium hover:bg-white/10 transition-colors cursor-pointer"
        >
          {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}

      {/* Summary Cards */}
      {summary && summary.total_trades > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Total Trades</p>
            <p className="text-white text-xl font-bold mt-1">{summary.total_trades}</p>
          </div>
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <p className="text-emerald-500 text-[10px] uppercase tracking-wider">Hit Rate</p>
            <p className="text-emerald-400 text-xl font-bold mt-1">{summary.hit_rate}%</p>
            <p className="text-zinc-600 text-[10px]">{summary.winners}W / {summary.losers}L</p>
          </div>
          <div className={`rounded-xl border p-4 ${summary.total_pnl >= 0 ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
            <p className={`text-[10px] uppercase tracking-wider ${summary.total_pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>Total P&L</p>
            <p className={`text-xl font-bold mt-1 ${summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {summary.total_pnl >= 0 ? '+' : ''}{summary.total_pnl}%
            </p>
            <p className="text-zinc-600 text-[10px]">Avg: {summary.avg_pnl >= 0 ? '+' : ''}{summary.avg_pnl}%</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Best / Worst</p>
            <p className="text-emerald-400 text-sm font-bold mt-1">+{summary.best_trade}%</p>
            <p className="text-red-400 text-sm font-bold">{summary.worst_trade}%</p>
          </div>
        </div>
      )}

      {/* Trade List */}
      {trades.length > 0 ? (
        <div className="space-y-2">
          {trades.map((t, i) => (
            <div key={`${t.ticker}-${i}`} className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    t.action.includes('BUY') ? 'bg-emerald-500/20' : 'bg-red-500/20'
                  }`}>
                    {t.action.includes('BUY')
                      ? <TrendingUp size={14} className="text-emerald-400" />
                      : <TrendingDown size={14} className="text-red-400" />
                    }
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-white text-sm font-semibold">{t.ticker.replace('.NS', '')}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        t.action.includes('BUY') ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      }`}>{t.action}</span>
                      <span className={`text-[10px] font-medium ${outcomeColor[t.outcome] || 'text-zinc-500'}`}>
                        {t.outcome === 'TARGET_HIT' && <Target size={10} className="inline mr-0.5" />}
                        {t.outcome === 'STOPLOSS_HIT' && <AlertTriangle size={10} className="inline mr-0.5" />}
                        {outcomeLabel[t.outcome] || t.outcome}
                      </span>
                    </div>
                    <p className="text-zinc-600 text-[10px]">{t.name} · {t.sector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${t.pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct?.toFixed(2)}%
                  </p>
                  <p className="text-zinc-600 text-[10px]">
                    ₹{t.price?.toFixed(2)} → ₹{t.current_price?.toFixed(2)}
                  </p>
                </div>
              </div>
              <div className="flex gap-4 mt-2 text-[10px] text-zinc-600">
                <span>Target: ₹{t.target_price?.toFixed(2)}</span>
                <span>SL: ₹{t.stop_loss?.toFixed(2)}</span>
                <span>Confidence: {t.confidence}%</span>
                <span>{new Date(t.timestamp).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      ) : !loading ? (
        <div className="text-center py-12 border border-dashed border-white/10 rounded-xl">
          <DollarSign size={28} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No mock investments yet</p>
          <p className="text-zinc-600 text-xs mt-1">Analyze stocks in the Scanner tab — every BUY/SELL decision is tracked as a paper trade</p>
        </div>
      ) : null}

      {loading && trades.length === 0 && (
        <div className="text-center py-12">
          <Loader2 size={28} className="text-cyan-400 animate-spin mx-auto mb-3" />
          <p className="text-zinc-400 text-sm">Loading mock investments...</p>
        </div>
      )}
    </div>
  );
}
