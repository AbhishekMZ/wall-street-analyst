import { useState } from 'react';
import { Radar, Loader2, Search, Zap } from 'lucide-react';
import { api } from '../api';
import type { StockDecision } from '../types';
import DecisionCard from './DecisionCard';

export default function ScannerPanel() {
  const [ticker, setTicker] = useState('');
  const [scanning, setScanning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<StockDecision[]>([]);
  const [singleResult, setSingleResult] = useState<StockDecision | null>(null);
  const [error, setError] = useState('');

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

  const scanNifty50 = async () => {
    setScanning(true);
    setError('');
    setResults([]);
    try {
      const data = await api.scanMarket(undefined, 10);
      setResults([...data.top_buys, ...data.top_sells]);
    } catch (e: any) {
      setError(e.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Single Stock Analysis */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Search size={16} className="text-emerald-400" />
          <h3 className="text-white font-semibold text-sm">Analyze Stock</h3>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && analyzeSingle()}
            placeholder="Enter NSE ticker (e.g., RELIANCE, TCS, INFY)"
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

      {/* Full Market Scan */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Radar size={16} className="text-cyan-400" />
            <h3 className="text-white font-semibold text-sm">Nifty 50 Scanner</h3>
          </div>
          <button
            onClick={scanNifty50}
            disabled={scanning}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 
                       text-white text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
          >
            {scanning ? <Loader2 size={14} className="animate-spin" /> : <Radar size={14} />}
            {scanning ? 'Scanning All 50 Stocks...' : 'Scan Nifty 50'}
          </button>
        </div>

        {scanning && (
          <div className="text-center py-12">
            <Loader2 size={32} className="text-cyan-400 animate-spin mx-auto mb-3" />
            <p className="text-zinc-400 text-sm">Analyzing all Nifty 50 stocks...</p>
            <p className="text-zinc-600 text-xs mt-1">This may take 2-5 minutes</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-3">
            <p className="text-zinc-400 text-xs">{results.length} actionable recommendations</p>
            {results.map((r, i) => (
              <DecisionCard key={`${r.ticker}-${i}`} decision={r} />
            ))}
          </div>
        )}

        {!scanning && results.length === 0 && (
          <div className="text-center py-12 border border-dashed border-white/10 rounded-xl">
            <Radar size={32} className="text-zinc-700 mx-auto mb-3" />
            <p className="text-zinc-500 text-sm">Scan the entire Nifty 50 for buy/sell signals</p>
            <p className="text-zinc-600 text-xs mt-1">Multi-factor analysis across technical, fundamental, momentum & macro</p>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
          <p className="text-red-400 text-sm">{error}</p>
          <p className="text-zinc-500 text-xs mt-1">Make sure the backend server is running: <code className="text-zinc-400">python -m uvicorn app.main:app --reload</code></p>
        </div>
      )}
    </div>
  );
}
