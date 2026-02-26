export interface StockDecision {
  ticker: string;
  name: string;
  sector: string;
  action: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  confidence: number;
  composite_score: number;
  price: number;
  target_price: number;
  stop_loss: number;
  risk_reward_ratio: number;
  time_horizon: string;
  risk_rating: number;
  reasoning: string[];
  scores: {
    technical: number;
    fundamental: number;
    momentum: number;
    macro: number;
  };
  analysis: {
    technical: AnalysisResult;
    fundamental: AnalysisResult;
    momentum: AnalysisResult;
    macro: AnalysisResult;
  };
  timestamp: string;
  // Report evaluation fields
  current_price?: number;
  pnl_pct?: number;
  outcome?: string;
}

export interface AnalysisResult {
  score: number;
  signal: string;
  details?: Record<string, unknown>;
  breakdown?: Record<string, unknown>;
}

export interface ScanResult {
  total_scanned: number;
  top_buys: StockDecision[];
  top_sells: StockDecision[];
  holds: StockDecision[];
  all_results: StockDecision[];
}

export interface WeeklyReport {
  report_date: string;
  period: string;
  summary: {
    total_decisions: number;
    winners: number;
    losers: number;
    hit_rate_pct: number;
    targets_hit: number;
    stoplosses_hit: number;
    avg_pnl_pct: number;
    total_pnl_pct: number;
    best_trade_pnl_pct: number;
    worst_trade_pnl_pct: number;
  };
  sector_breakdown: Record<string, { count: number; avg_pnl: number; total_pnl: number }>;
  decisions: StockDecision[];
}

export interface MacroData {
  indicators: Record<string, { current: number; week_change_pct: number; month_change_pct: number }>;
  analysis: {
    signals: { factor: string; signal: string; detail: string }[];
    count: number;
  };
}
