import { useState } from 'react';
import {
  FileText, Trophy, Target, ShieldAlert,
  Loader2, BarChart3,
} from 'lucide-react';
import { api } from '../api';
import type { WeeklyReport } from '../types';

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <p className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">{label}</p>
      <p className="font-bold text-lg" style={{ color }}>{value}</p>
      {sub && <p className="text-zinc-600 text-xs mt-0.5">{sub}</p>}
    </div>
  );
}

export default function ReportPanel() {
  const [report, setReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadReport = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.weeklyReport();
      setReport(data);
    } catch (e: any) {
      setError(e.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-violet-400" />
          <h3 className="text-white font-semibold text-sm">Performance Report</h3>
        </div>
        <button
          onClick={loadReport}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 
                     text-white text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <BarChart3 size={14} />}
          {loading ? 'Generating...' : 'Generate Weekly Report'}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {report && report.summary && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <StatCard
              label="Total Decisions"
              value={String(report.summary.total_decisions)}
              color="#a78bfa"
            />
            <StatCard
              label="Hit Rate"
              value={`${report.summary.hit_rate_pct}%`}
              sub={`${report.summary.winners}W / ${report.summary.losers}L`}
              color={report.summary.hit_rate_pct >= 50 ? '#10b981' : '#ef4444'}
            />
            <StatCard
              label="Avg P&L"
              value={`${report.summary.avg_pnl_pct > 0 ? '+' : ''}${report.summary.avg_pnl_pct}%`}
              color={report.summary.avg_pnl_pct > 0 ? '#10b981' : '#ef4444'}
            />
            <StatCard
              label="Best Trade"
              value={`+${report.summary.best_trade_pnl_pct}%`}
              sub="Highest single P&L"
              color="#10b981"
            />
            <StatCard
              label="Worst Trade"
              value={`${report.summary.worst_trade_pnl_pct}%`}
              sub="Lowest single P&L"
              color="#ef4444"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 mb-3">
                <Target size={14} className="text-emerald-400" />
                <p className="text-zinc-300 text-xs font-semibold">Targets Hit</p>
              </div>
              <p className="text-emerald-400 font-bold text-2xl">{report.summary.targets_hit}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 mb-3">
                <ShieldAlert size={14} className="text-red-400" />
                <p className="text-zinc-300 text-xs font-semibold">Stop Losses Hit</p>
              </div>
              <p className="text-red-400 font-bold text-2xl">{report.summary.stoplosses_hit}</p>
            </div>
          </div>

          {Object.keys(report.sector_breakdown).length > 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider mb-3">Sector Breakdown</p>
              <div className="space-y-2">
                {Object.entries(report.sector_breakdown).map(([sector, data]) => (
                  <div key={sector} className="flex items-center justify-between">
                    <span className="text-zinc-400 text-xs">{sector}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-zinc-500 text-xs">{data.count} trades</span>
                      <span className={`text-xs font-semibold ${data.avg_pnl > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {data.avg_pnl > 0 ? '+' : ''}{data.avg_pnl}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider mb-3">Decision Details</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-zinc-500 border-b border-white/5">
                    <th className="text-left pb-2 font-medium">Stock</th>
                    <th className="text-left pb-2 font-medium">Action</th>
                    <th className="text-right pb-2 font-medium">Entry</th>
                    <th className="text-right pb-2 font-medium">Current</th>
                    <th className="text-right pb-2 font-medium">P&L</th>
                    <th className="text-right pb-2 font-medium">Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {report.decisions.map((d, i) => (
                    <tr key={i} className="border-b border-white/5">
                      <td className="py-2 text-white font-medium">{d.name}</td>
                      <td className={`py-2 ${d.action.includes('BUY') ? 'text-emerald-400' : d.action.includes('SELL') ? 'text-red-400' : 'text-amber-400'}`}>
                        {d.action.replace('_', ' ')}
                      </td>
                      <td className="py-2 text-right text-zinc-400">₹{d.price?.toLocaleString()}</td>
                      <td className="py-2 text-right text-zinc-400">₹{d.current_price?.toLocaleString() || '-'}</td>
                      <td className={`py-2 text-right font-medium ${(d.pnl_pct || 0) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {d.pnl_pct !== undefined ? `${d.pnl_pct > 0 ? '+' : ''}${d.pnl_pct}%` : '-'}
                      </td>
                      <td className="py-2 text-right">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium
                          ${d.outcome === 'TARGET_HIT' ? 'bg-emerald-500/15 text-emerald-400' :
                            d.outcome === 'STOPLOSS_HIT' ? 'bg-red-500/15 text-red-400' :
                            'bg-zinc-500/15 text-zinc-400'}`}>
                          {d.outcome || 'OPEN'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!report && !loading && !error && (
        <div className="text-center py-16 rounded-xl border border-dashed border-white/10">
          <Trophy size={32} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No report generated yet</p>
          <p className="text-zinc-600 text-xs mt-1">Click "Generate Weekly Report" to evaluate past decisions</p>
        </div>
      )}
    </div>
  );
}
