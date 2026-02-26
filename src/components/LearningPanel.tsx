import { useState, useEffect } from 'react';
import { Brain, Loader2, RefreshCw, TrendingUp, AlertTriangle, Zap, BarChart3 } from 'lucide-react';
import { api } from '../api';

interface FactorRank {
  factor: string;
  accuracy: number;
  sample_size: number;
}

interface LearningSummary {
  total_evaluated: number;
  overall_accuracy_pct: number;
  market_regime: string;
  current_weights: Record<string, number>;
  factor_rankings: FactorRank[];
  action_accuracy: Record<string, { accuracy: number; sample_size: number }>;
  confidence_calibration: Record<string, { predicted_count: number; actual_accuracy: number }>;
  sector_rankings: { sector: string; accuracy: number; avg_pnl: number; decisions: number }[];
  recent_lessons: { timestamp: string; lesson: string }[];
  adaptations_count: number;
  created_at: string;
  last_updated: string;
}

function AccuracyRing({ value, size = 80, label }: { value: number; size?: number; label: string }) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const color = value >= 60 ? '#10b981' : value >= 45 ? '#f59e0b' : '#ef4444';

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          className="transition-all duration-1000" />
      </svg>
      <span className="text-white font-bold text-sm -mt-12">{value}%</span>
      <span className="text-zinc-500 text-[10px] mt-5 uppercase tracking-wider">{label}</span>
    </div>
  );
}

export default function LearningPanel() {
  const [data, setData] = useState<LearningSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');

  const fetchData = () => {
    setLoading(true);
    setError('');
    api.getLearning()
      .then((d) => setData(d as unknown as LearningSummary))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const triggerTraining = async () => {
    setTraining(true);
    try {
      await api.triggerLearning();
      fetchData();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 size={28} className="animate-spin text-violet-400" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <AlertTriangle size={20} className="text-red-400 mx-auto mb-2" />
        <p className="text-red-400 text-sm">{error}</p>
        <p className="text-zinc-500 text-xs mt-1">Make sure the backend is running</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={18} className="text-violet-400" />
          <h3 className="text-white font-bold text-base">Self-Learning Engine</h3>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-400 font-medium">
            {data?.market_regime?.replace('_', ' ').toUpperCase() || 'INITIALIZING'}
          </span>
        </div>
        <button
          onClick={triggerTraining}
          disabled={training}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
        >
          {training ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          {training ? 'Training...' : 'Run Learning Cycle'}
        </button>
      </div>

      {/* Stats row */}
      {data && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex flex-col items-center">
              <AccuracyRing value={data.overall_accuracy_pct} label="Hit Rate" />
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Evaluated</p>
              <p className="text-white font-bold text-2xl">{data.total_evaluated}</p>
              <p className="text-zinc-600 text-xs">decisions</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Adaptations</p>
              <p className="text-cyan-400 font-bold text-2xl">{data.adaptations_count}</p>
              <p className="text-zinc-600 text-xs">weight updates</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Regime</p>
              <p className="text-amber-400 font-bold text-sm mt-2">{data.market_regime?.replace('_', ' ') || '—'}</p>
              <p className="text-zinc-600 text-xs mt-1">current market</p>
            </div>
          </div>

          {/* Current Weights */}
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 size={14} className="text-cyan-400" />
              <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider">Adapted Weights</p>
              <span className="text-zinc-600 text-[10px]">(auto-tuned based on accuracy)</span>
            </div>
            <div className="space-y-2.5">
              {Object.entries(data.current_weights)
                .sort(([, a], [, b]) => b - a)
                .map(([factor, weight]) => {
                  const acc = data.factor_rankings.find((f) => f.factor === factor);
                  const pct = Math.round(weight * 100);
                  return (
                    <div key={factor} className="flex items-center gap-3">
                      <span className="text-zinc-400 text-xs w-32 capitalize">{factor.replace('_', ' ')}</span>
                      <div className="flex-1 h-2.5 bg-white/5 rounded-full overflow-hidden">
                        <div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all duration-700"
                          style={{ width: `${pct * 3}%` }} />
                      </div>
                      <span className="text-white text-xs font-mono w-10 text-right">{pct}%</span>
                      {acc && (
                        <span className={`text-[10px] w-16 text-right ${acc.accuracy >= 55 ? 'text-emerald-400' : acc.accuracy >= 45 ? 'text-amber-400' : 'text-red-400'}`}>
                          {acc.accuracy}% acc
                        </span>
                      )}
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Factor Rankings */}
          {data.factor_rankings.length > 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp size={14} className="text-emerald-400" />
                <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider">Factor Performance</p>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {data.factor_rankings.map((f) => (
                  <div key={f.factor} className="rounded-lg bg-white/5 p-3 text-center">
                    <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1 capitalize">{f.factor}</p>
                    <p className={`font-bold text-lg ${f.accuracy >= 55 ? 'text-emerald-400' : f.accuracy >= 45 ? 'text-amber-400' : 'text-red-400'}`}>
                      {f.accuracy}%
                    </p>
                    <p className="text-zinc-600 text-[10px]">{f.sample_size} samples</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sector Rankings */}
          {data.sector_rankings.length > 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
              <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider mb-3">Sector Performance</p>
              <div className="space-y-2">
                {data.sector_rankings.map((s) => (
                  <div key={s.sector} className="flex items-center justify-between text-xs">
                    <span className="text-zinc-400">{s.sector}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-zinc-500">{s.decisions} trades</span>
                      <span className={`font-medium ${s.accuracy >= 55 ? 'text-emerald-400' : 'text-amber-400'}`}>{s.accuracy}% hit</span>
                      <span className={`font-medium ${s.avg_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {s.avg_pnl >= 0 ? '+' : ''}{s.avg_pnl}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Lessons */}
          {data.recent_lessons.length > 0 && (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Zap size={14} className="text-amber-400" />
                <p className="text-amber-400 text-xs font-semibold uppercase tracking-wider">Lessons Learned</p>
              </div>
              <div className="space-y-2">
                {data.recent_lessons.map((l, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">•</span>
                    <div>
                      <p className="text-zinc-300 text-xs">{l.lesson}</p>
                      <p className="text-zinc-600 text-[10px]">{new Date(l.timestamp).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.total_evaluated === 0 && (
            <div className="text-center py-12 rounded-xl border border-dashed border-white/10">
              <Brain size={32} className="text-zinc-700 mx-auto mb-3" />
              <p className="text-zinc-500 text-sm">No learning data yet</p>
              <p className="text-zinc-600 text-xs mt-1">Analyze stocks first, then click "Run Learning Cycle" to evaluate past decisions and adapt</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
