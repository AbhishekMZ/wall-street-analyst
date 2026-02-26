import { useEffect, useState } from 'react';
import {
  Globe, TrendingUp, Minus, AlertTriangle,
  DollarSign, Fuel, BarChart3, Activity,
} from 'lucide-react';
import { api } from '../api';
import type { MacroData } from '../types';

const INDICATOR_META: Record<string, { label: string; icon: React.ComponentType<any>; unit?: string }> = {
  nifty: { label: 'Nifty 50', icon: BarChart3 },
  sensex: { label: 'Sensex', icon: BarChart3 },
  sp500: { label: 'S&P 500', icon: TrendingUp },
  crude_oil: { label: 'Crude Oil', icon: Fuel, unit: '$' },
  gold: { label: 'Gold', icon: DollarSign, unit: '$' },
  usdinr: { label: 'USD/INR', icon: DollarSign, unit: '₹' },
  us10y: { label: 'US 10Y Yield', icon: Activity, unit: '%' },
  vix_india: { label: 'India VIX', icon: AlertTriangle },
  dxy: { label: 'DXY Index', icon: Globe },
};

export default function MacroPanel() {
  const [data, setData] = useState<MacroData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getMacro()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-white/5 rounded w-32" />
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-20 bg-white/5 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <AlertTriangle size={20} className="text-red-400 mx-auto mb-2" />
        <p className="text-red-400 text-sm">Failed to load macro data: {error}</p>
        <p className="text-zinc-500 text-xs mt-1">Make sure the backend server is running on port 8000</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Globe size={16} className="text-cyan-400" />
        <h3 className="text-white font-semibold text-sm">Macro Dashboard</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {Object.entries(data.indicators).map(([key, val]) => {
          const meta = INDICATOR_META[key] || { label: key, icon: Minus };
          const Icon = meta.icon;
          const isPositive = val.week_change_pct > 0;
          return (
            <div key={key} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
              <div className="flex items-center gap-2 mb-2">
                <Icon size={13} className="text-zinc-500" />
                <span className="text-zinc-400 text-[10px] uppercase tracking-wider">{meta.label}</span>
              </div>
              <p className="text-white font-bold text-lg">
                {meta.unit === '$' ? '$' : meta.unit === '₹' ? '₹' : ''}{val.current.toLocaleString()}
                {meta.unit === '%' ? '%' : ''}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-xs font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPositive ? '+' : ''}{val.week_change_pct}% W
                </span>
                <span className={`text-xs ${val.month_change_pct > 0 ? 'text-emerald-400/60' : 'text-red-400/60'}`}>
                  {val.month_change_pct > 0 ? '+' : ''}{val.month_change_pct}% M
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {data.analysis.signals.length > 0 && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
          <p className="text-amber-400 text-xs font-semibold uppercase tracking-wider mb-2">Market Signals</p>
          <div className="space-y-2">
            {data.analysis.signals.map((s, i) => (
              <div key={i} className="flex items-start gap-2">
                <AlertTriangle size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="text-white text-xs font-medium">{s.factor}: </span>
                  <span className="text-zinc-400 text-xs">{s.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
