const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API Error');
  }
  return res.json();
}

// Keep Render backend alive by pinging every 10 minutes (free tier sleeps after 15min)
let _keepAliveTimer: ReturnType<typeof setInterval> | null = null;
export function startKeepAlive() {
  if (_keepAliveTimer) return;
  _keepAliveTimer = setInterval(() => {
    fetch(`${API_BASE}/`, { method: 'GET' }).catch(() => {});
  }, 10 * 60 * 1000); // 10 minutes
  // Also ping immediately
  fetch(`${API_BASE}/`, { method: 'GET' }).catch(() => {});
}

export const api = {
  analyzeStock: (ticker: string) =>
    fetchJson<import('./types').StockDecision>(`/api/analyze/${ticker}`),

  scanMarket: (tickers?: string[], topN = 10) =>
    fetchJson<import('./types').ScanResult>('/api/scan', {
      method: 'POST',
      body: JSON.stringify({ tickers, top_n: topN }),
    }),

  quickScan: (tickers: string[]) =>
    fetchJson<{ results: import('./types').StockDecision[] }>('/api/scan/quick', {
      method: 'POST',
      body: JSON.stringify({ tickers }),
    }),

  getDecisions: (limit = 50) =>
    fetchJson<{ total: number; decisions: import('./types').StockDecision[] }>(
      `/api/decisions?limit=${limit}`
    ),

  weeklyReport: () =>
    fetchJson<import('./types').WeeklyReport>('/api/reports/weekly'),

  cumulativeReport: () =>
    fetchJson<Record<string, unknown>>('/api/reports/cumulative'),

  getMacro: () =>
    fetchJson<import('./types').MacroData>('/api/macro'),

  getUniverse: (category = 'all') =>
    fetchJson<Record<string, unknown>>(`/api/universe?category=${category}`),

  scanUniverse: (category: string, topN = 10) =>
    fetchJson<import('./types').ScanResult>(`/api/scan/universe?category=${category}&top_n=${topN}`, {
      method: 'POST',
    }),

  getMockInvestments: (limit = 50) =>
    fetchJson<Record<string, unknown>>(`/api/decisions/mock?limit=${limit}`),

  getStockInfo: (ticker: string) =>
    fetchJson<Record<string, unknown>>(`/api/info/${ticker}`),

  // Agent
  getAgentStatus: () =>
    fetchJson<Record<string, unknown>>('/api/agent/status'),

  getAgentActivity: (limit = 50) =>
    fetchJson<{ activities: Array<Record<string, unknown>> }>(`/api/agent/activity?limit=${limit}`),

  triggerScan: (universe: string) =>
    fetchJson<Record<string, unknown>>(`/api/agent/trigger/${universe}`, { method: 'POST' }),

  triggerLearning: () =>
    fetchJson<Record<string, unknown>>('/api/agent/learn', { method: 'POST' }),

  analyzeBackground: (ticker: string) =>
    fetchJson<Record<string, unknown>>(`/api/analyze/background/${ticker}`),

  getBackgroundResults: () =>
    fetchJson<Record<string, unknown>>('/api/analyze/results'),

  // Learning Engine
  getLearning: () =>
    fetchJson<Record<string, unknown>>('/api/learning'),

  triggerLegacyLearning: () =>
    fetchJson<Record<string, unknown>>('/api/learning/evaluate', { method: 'POST' }),

  // Portfolio
  getPortfolio: () =>
    fetchJson<Record<string, unknown>>('/api/portfolio'),

  getPortfolioPerformance: () =>
    fetchJson<Record<string, unknown>>('/api/portfolio/performance'),

  getPortfolioRecommendations: () =>
    fetchJson<Record<string, unknown>>('/api/portfolio/recommendations'),

  addHolding: (ticker: string, qty: number, avg_price: number, buy_date?: string) =>
    fetchJson<Record<string, unknown>>('/api/portfolio/add', {
      method: 'POST',
      body: JSON.stringify({ ticker, qty, avg_price, buy_date }),
    }),

  removeHolding: (ticker: string, qty?: number) =>
    fetchJson<Record<string, unknown>>('/api/portfolio/remove', {
      method: 'POST',
      body: JSON.stringify({ ticker, qty }),
    }),

  importPortfolio: (csvContent: string) =>
    fetchJson<Record<string, unknown>>('/api/portfolio/import', {
      method: 'POST',
      body: JSON.stringify({ csv_content: csvContent }),
    }),

  uploadPortfolio: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/portfolio/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
};
