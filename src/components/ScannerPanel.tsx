import { useState } from 'react';
import { Radar, Loader2, Search, Zap, TrendingUp, BarChart3, Gem } from 'lucide-react';
import { api } from '../api';
import type { StockDecision } from '../types';
import DecisionCard from './DecisionCard';

const UNIVERSES = [
  { key: 'nifty50', label: 'Nifty 50', desc: 'Large-cap blue chips', icon: BarChart3, color: 'cyan' },
  { key: 'nifty_next50', label: 'Next 50', desc: 'Emerging large-caps', icon: TrendingUp, color: 'blue' },
  { key: 'midcap_gems', label: 'Midcap Gems', desc: 'High-growth midcaps', icon: Gem, color: 'purple' },
  { key: 'smallcap_hidden', label: 'Smallcap Hidden', desc: 'Niche small-caps', icon: Zap, color: 'amber' },
];

export default function ScannerPanel() {
  const [ticker, setTicker] = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanningUniverse, setScanningUniverse] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<StockDecision[]>([]);
  const [singleResult, setSingleResult] = useState<StockDecision | null>(null);
  const [error, setError] = useState('');
  const [scanStats, setScanStats] = useState<{ total: number; buys: number; sells: number } | null>(null);

  const analyzeSingle = async () => {
    if (!ticker.trim()) return;
    setAnalyzing(true);
    setError('');
    setSingleResult(null);
    try {
      const result = await api.analyzeStock(ticker.trim());
      setSingleResult(result);
    } catch (e: any) {
      setError(e.message || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const scanUniverse = async (category: string) => {
    setScanning(true);
    setScanningUniverse(category);
    setError('');
    setResults([]);
    setScanStats(null);
    try {
      const data = await api.scanUniverse(category, 15);
      const allResults = [...data.top_buys, ...data.top_sells];
      setResults(allResults);
      setScanStats({
        total: data.total_scanned,
        buys: data.top_buys.length,
        sells: data.top_sells.length,
      });
    } catch (e: any) {
      setError(e.message || 'Scan failed');
    } finally {
      setScanning(false);
      setScanningUniverse('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Single Stock Analysis */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Search size={16} className="text-emerald-400" />
          <h3 className="text-white font-semibold text-sm">Analyze Any Stock</h3>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && analyzeSingle()}
            placeholder="Enter any NSE ticker (e.g., MARINE, KAYNES, DIXON, TCS)"
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm
                       placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500/30 transition-all"
          />
          <button
            onClick={analyzeSingle}
            disabled={analyzing || !ticker.trim()}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 
                       text-white text-sm font-semibold transition-colors disabled:opacity-50 cursor-pointer"
          >
            {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
            {analyzing ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {singleResult && (
          <div className="mt-4">
            <DecisionCard decision={singleResult} />
          </div>
        )}
      </div>

      {/* Universe Scanners */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Radar size={16} className="text-cyan-400" />
          <h3 className="text-white font-semibold text-sm">Market Scanner</h3>
          <span className="text-zinc-600 text-xs">— Find opportunities across 200+ stocks</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {UNIVERSES.map((u) => {
            const Icon = u.icon;
            const isScanning = scanning && scanningUniverse === u.key;
            return (
              <button
                key={u.key}
                onClick={() => scanUniverse(u.key)}
                disabled={scanning}
                className={`flex flex-col items-center gap-2 p-4 rounded-xl border transition-all cursor-pointer
                  ${isScanning
                    ? 'border-white/20 bg-white/10'
                    : 'border-white/10 bg-white/[0.02] hover:bg-white/5 hover:border-white/20'
                  } disabled:opacity-50`}
              >
                {isScanning
                  ? <Loader2 size={20} className="text-white animate-spin" />
                  : <Icon size={20} className={`text-${u.color}-400`} />
                }
                <span className="text-white text-xs font-semibold">{u.label}</span>
                <span className="text-zinc-600 text-[10px]">{u.desc}</span>
              </button>
            );
          })}
        </div>

        {scanning && (
          <div className="text-center py-8">
            <Loader2 size={28} className="text-cyan-400 animate-spin mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">Scanning {UNIVERSES.find(u => u.key === scanningUniverse)?.label || 'stocks'}...</p>
            <p className="text-zinc-600 text-xs mt-1">Multi-factor analysis on each stock — this may take a few minutes</p>
          </div>
        )}

        {scanStats && (
          <div className="flex gap-4 mb-4">
            <div className="rounded-lg bg-white/5 px-3 py-2">
              <p className="text-zinc-500 text-[10px]">Scanned</p>
              <p className="text-white text-sm font-bold">{scanStats.total}</p>
            </div>
            <div className="rounded-lg bg-emerald-500/10 px-3 py-2">
              <p className="text-emerald-500 text-[10px]">Buy Signals</p>
              <p className="text-emerald-400 text-sm font-bold">{scanStats.buys}</p>
            </div>
            <div className="rounded-lg bg-red-500/10 px-3 py-2">
              <p className="text-red-500 text-[10px]">Sell Signals</p>
              <p className="text-red-400 text-sm font-bold">{scanStats.sells}</p>
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-3">
            {results.map((r, i) => (
              <DecisionCard key={`${r.ticker}-${i}`} decision={r} />
            ))}
          </div>
        )}

        {!scanning && results.length === 0 && !scanStats && (
          <div className="text-center py-10 border border-dashed border-white/10 rounded-xl">
            <Radar size={28} className="text-zinc-700 mx-auto mb-3" />
            <p className="text-zinc-500 text-sm">Select a universe above to scan for opportunities</p>
            <p className="text-zinc-600 text-xs mt-1">Nifty 50 for blue-chips, Smallcap Hidden for niche high-growth picks</p>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
