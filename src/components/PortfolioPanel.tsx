import { useState, useEffect } from 'react';
import {
  Briefcase, Plus, Upload, Loader2, AlertTriangle, TrendingUp, TrendingDown,
  Trash2, PieChart, ShieldAlert,
} from 'lucide-react';
import { api } from '../api';

interface Holding {
  ticker: string;
  qty: number;
  avg_price: number;
  current_price: number;
  invested: number;
  current_value: number;
  pnl: number;
  pnl_pct: number;
  day_change_pct: number;
  week_change_pct: number;
  weight_pct: number;
  sector: string;
}

interface PortfolioPerf {
  summary: {
    total_invested: number;
    current_value: number;
    total_pnl: number;
    total_pnl_pct: number;
    num_holdings: number;
  };
  sector_diversification: Record<string, number>;
  holdings: Holding[];
}

interface Recommendation {
  type: string;
  severity: string;
  message: string;
}

export default function PortfolioPanel() {
  const [perf, setPerf] = useState<PortfolioPerf | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Add holding form
  const [showAdd, setShowAdd] = useState(false);
  const [ticker, setTicker] = useState('');
  const [qty, setQty] = useState('');
  const [price, setPrice] = useState('');
  const [adding, setAdding] = useState(false);

  // CSV import
  const [showImport, setShowImport] = useState(false);
  const [csvText, setCsvText] = useState('');
  const [importing, setImporting] = useState(false);

  // File upload
  const [uploading, setUploading] = useState(false);

  const loadPerf = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getPortfolioPerformance() as unknown as PortfolioPerf;
      setPerf(data);
      const recData = await api.getPortfolioRecommendations() as any;
      setRecs(recData.recommendations || []);
    } catch (e: any) {
      if (e.message?.includes('No holdings')) {
        setPerf(null);
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadPerf(); }, []);

  const handleAdd = async () => {
    if (!ticker || !qty || !price) return;
    setAdding(true);
    try {
      await api.addHolding(ticker.toUpperCase(), parseFloat(qty), parseFloat(price));
      setTicker(''); setQty(''); setPrice('');
      setShowAdd(false);
      loadPerf();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (t: string) => {
    if (!confirm(`Remove ${t.replace('.NS', '')} from portfolio?`)) return;
    try {
      await api.removeHolding(t);
      loadPerf();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleImport = async () => {
    if (!csvText.trim()) return;
    setImporting(true);
    try {
      const result = await api.importPortfolio(csvText) as any;
      alert(`Imported ${result.imported} holdings` + (result.errors?.length ? `\nErrors: ${result.errors.join(', ')}` : ''));
      setCsvText('');
      setShowImport(false);
      loadPerf();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setImporting(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    setError('');
    try {
      const result = await api.uploadPortfolio(file) as any;
      alert(`Imported ${result.imported} holdings` + (result.errors?.length ? `\nErrors: ${result.errors.join(', ')}` : ''));
      setShowImport(false);
      loadPerf();
      if (e.target) e.target.value = '';
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const sevColor: Record<string, string> = {
    high: 'border-red-500/20 bg-red-500/5 text-red-400',
    medium: 'border-amber-500/20 bg-amber-500/5 text-amber-400',
    low: 'border-blue-500/20 bg-blue-500/5 text-blue-400',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Briefcase size={18} className="text-emerald-400" />
          <h3 className="text-white font-bold text-base">My Portfolio</h3>
        </div>
        <div className="flex gap-2">
          <label className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-colors cursor-pointer">
            <Upload size={13} />
            {uploading ? 'Uploading...' : 'Upload Excel/CSV'}
            <input type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} className="hidden" disabled={uploading} />
          </label>
          <button onClick={() => { setShowImport(!showImport); setShowAdd(false); }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-zinc-300 text-xs font-medium hover:bg-white/10 transition-colors cursor-pointer">
            <Upload size={13} /> Paste CSV
          </button>
          <button onClick={() => { setShowAdd(!showAdd); setShowImport(false); }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors cursor-pointer">
            <Plus size={13} /> Add Holding
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
          <p className="text-red-400 text-xs">{error}</p>
        </div>
      )}

      {/* Add Holding Form */}
      {showAdd && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 space-y-3">
          <p className="text-emerald-400 text-xs font-semibold">Add Holding</p>
          <div className="grid grid-cols-3 gap-3">
            <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Ticker (e.g. RELIANCE)" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-xs placeholder:text-zinc-600 focus:outline-none" />
            <input value={qty} onChange={(e) => setQty(e.target.value)} type="number"
              placeholder="Quantity" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-xs placeholder:text-zinc-600 focus:outline-none" />
            <input value={price} onChange={(e) => setPrice(e.target.value)} type="number"
              placeholder="Avg Price (₹)" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-xs placeholder:text-zinc-600 focus:outline-none" />
          </div>
          <button onClick={handleAdd} disabled={adding || !ticker || !qty || !price}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold disabled:opacity-50 cursor-pointer">
            {adding ? 'Adding...' : 'Add'}
          </button>
        </div>
      )}

      {/* CSV Import */}
      {showImport && (
        <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 space-y-3">
          <p className="text-cyan-400 text-xs font-semibold">Import from CSV</p>
          <p className="text-zinc-500 text-[10px]">Paste CSV with columns: ticker/symbol, qty/quantity, avg_price/price, date (optional)</p>
          <textarea value={csvText} onChange={(e) => setCsvText(e.target.value)} rows={6}
            placeholder={"ticker,qty,avg_price\nRELIANCE,10,2450\nTCS,5,3800"}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-xs font-mono placeholder:text-zinc-600 focus:outline-none resize-none" />
          <button onClick={handleImport} disabled={importing || !csvText.trim()}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold disabled:opacity-50 cursor-pointer">
            {importing ? 'Importing...' : 'Import'}
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={24} className="animate-spin text-emerald-400" />
        </div>
      )}

      {/* Portfolio Summary */}
      {perf && perf.summary && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Invested</p>
              <p className="text-white font-bold text-lg">₹{perf.summary.total_invested.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Current Value</p>
              <p className="text-white font-bold text-lg">₹{perf.summary.current_value.toLocaleString()}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider">P&L</p>
              <p className={`font-bold text-lg ${perf.summary.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {perf.summary.total_pnl >= 0 ? '+' : ''}₹{perf.summary.total_pnl.toLocaleString()}
              </p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Return</p>
              <p className={`font-bold text-lg ${perf.summary.total_pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {perf.summary.total_pnl_pct >= 0 ? '+' : ''}{perf.summary.total_pnl_pct}%
              </p>
            </div>
          </div>

          {/* Sector Diversification */}
          {Object.keys(perf.sector_diversification).length > 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <div className="flex items-center gap-2 mb-3">
                <PieChart size={14} className="text-cyan-400" />
                <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider">Sector Allocation</p>
              </div>
              <div className="space-y-2">
                {Object.entries(perf.sector_diversification).map(([sector, weight]) => (
                  <div key={sector} className="flex items-center gap-3">
                    <span className="text-zinc-400 text-xs w-28 truncate">{sector}</span>
                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500"
                        style={{ width: `${weight}%` }} />
                    </div>
                    <span className="text-zinc-400 text-xs w-10 text-right font-mono">{weight}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Holdings Table */}
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider mb-3">Holdings</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-zinc-500 border-b border-white/5">
                    <th className="text-left pb-2 font-medium">Stock</th>
                    <th className="text-right pb-2 font-medium">Qty</th>
                    <th className="text-right pb-2 font-medium">Avg</th>
                    <th className="text-right pb-2 font-medium">CMP</th>
                    <th className="text-right pb-2 font-medium">P&L</th>
                    <th className="text-right pb-2 font-medium">%</th>
                    <th className="text-right pb-2 font-medium">Day</th>
                    <th className="text-right pb-2 font-medium">Wt</th>
                    <th className="text-right pb-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {perf.holdings.map((h) => (
                    <tr key={h.ticker} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-2.5">
                        <span className="text-white font-medium">{h.ticker.replace('.NS', '')}</span>
                        {h.sector && <span className="text-zinc-600 text-[10px] ml-1.5">{h.sector}</span>}
                      </td>
                      <td className="py-2.5 text-right text-zinc-400">{h.qty}</td>
                      <td className="py-2.5 text-right text-zinc-400">₹{h.avg_price.toLocaleString()}</td>
                      <td className="py-2.5 text-right text-white font-medium">₹{h.current_price.toLocaleString()}</td>
                      <td className={`py-2.5 text-right font-medium ${h.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {h.pnl >= 0 ? '+' : ''}₹{h.pnl.toLocaleString()}
                      </td>
                      <td className={`py-2.5 text-right ${h.pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {h.pnl_pct >= 0 ? '+' : ''}{h.pnl_pct}%
                      </td>
                      <td className="py-2.5 text-right">
                        <span className={`inline-flex items-center gap-0.5 ${h.day_change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {h.day_change_pct >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                          {Math.abs(h.day_change_pct)}%
                        </span>
                      </td>
                      <td className="py-2.5 text-right text-zinc-500">{h.weight_pct}%</td>
                      <td className="py-2.5 text-right">
                        <button onClick={() => handleRemove(h.ticker)}
                          className="text-zinc-600 hover:text-red-400 transition-colors cursor-pointer p-1">
                          <Trash2 size={12} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Recommendations */}
      {recs.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ShieldAlert size={14} className="text-amber-400" />
            <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider">Recommendations</p>
          </div>
          {recs.map((r, i) => (
            <div key={i} className={`rounded-lg border p-3 ${sevColor[r.severity] || sevColor.low}`}>
              <div className="flex items-start gap-2">
                <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
                <p className="text-xs">{r.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {!perf && !loading && !error && (
        <div className="text-center py-16 rounded-xl border border-dashed border-white/10">
          <Briefcase size={32} className="text-zinc-700 mx-auto mb-3" />
          <p className="text-zinc-500 text-sm">No portfolio yet</p>
          <p className="text-zinc-600 text-xs mt-1">Add holdings manually or import your equity sheet as CSV</p>
        </div>
      )}
    </div>
  );
}
