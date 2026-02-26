import { useState } from 'react';
import {
  TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp,
  Target, ShieldAlert, Clock, Zap,
} from 'lucide-react';
import type { StockDecision } from '../types';

const ACTION_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  STRONG_BUY: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  BUY: { bg: 'bg-green-500/15', text: 'text-green-400', border: 'border-green-500/30' },
  HOLD: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' },
  SELL: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30' },
  STRONG_SELL: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30' },
};

function ActionIcon({ action }: { action: string }) {
  if (action.includes('BUY')) return <TrendingUp size={16} />;
  if (action.includes('SELL')) return <TrendingDown size={16} />;
  return <Minus size={16} />;
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-zinc-500 text-xs w-24 flex-shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-zinc-400 text-xs w-10 text-right font-mono">{score}</span>
    </div>
  );
}

export default function DecisionCard({ decision }: { decision: StockDecision }) {
  const [expanded, setExpanded] = useState(false);
  const style = ACTION_STYLES[decision.action] || ACTION_STYLES.HOLD;

  const pnlAvailable = decision.pnl_pct !== undefined;
  const pnlPositive = (decision.pnl_pct || 0) > 0;

  return (
    <div className={`rounded-2xl border ${style.border} bg-white/[0.03] backdrop-blur-sm overflow-hidden`}>
      <div
        className="p-5 cursor-pointer hover:bg-white/[0.02] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl ${style.bg} flex items-center justify-center ${style.text}`}>
              <ActionIcon action={decision.action} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-white font-bold text-base">{decision.name}</h3>
                <span className="text-zinc-600 text-xs font-mono">{decision.ticker.replace('.NS', '')}</span>
              </div>
              <p className="text-zinc-500 text-xs">{decision.sector}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full text-xs font-bold ${style.bg} ${style.text}`}>
              {decision.action.replace('_', ' ')}
            </div>
            {expanded ? <ChevronUp size={16} className="text-zinc-600" /> : <ChevronDown size={16} className="text-zinc-600" />}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Price</p>
            <p className="text-white font-semibold text-sm">₹{decision.price.toLocaleString()}</p>
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Target</p>
            <p className="text-emerald-400 font-semibold text-sm">₹{decision.target_price.toLocaleString()}</p>
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Stop Loss</p>
            <p className="text-red-400 font-semibold text-sm">₹{decision.stop_loss.toLocaleString()}</p>
          </div>
          <div className="bg-white/5 rounded-lg px-3 py-2">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Confidence</p>
            <p className="text-cyan-400 font-semibold text-sm">{decision.confidence}%</p>
          </div>
        </div>

        {pnlAvailable && (
          <div className={`mt-3 px-3 py-2 rounded-lg ${pnlPositive ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 text-xs">P&L</span>
              <span className={`font-bold text-sm ${pnlPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                {pnlPositive ? '+' : ''}{decision.pnl_pct?.toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {expanded && (
        <div className="border-t border-white/5 p-5 space-y-5">
          <div className="grid grid-cols-3 gap-3">
            <div className="flex items-center gap-2 text-zinc-400 text-xs">
              <Target size={13} className="text-cyan-400" />
              <span>R:R {decision.risk_reward_ratio}</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400 text-xs">
              <Clock size={13} className="text-amber-400" />
              <span>{decision.time_horizon}</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400 text-xs">
              <ShieldAlert size={13} className="text-red-400" />
              <span>Risk: {decision.risk_rating}/10</span>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider">Score Breakdown</p>
            <ScoreBar label="Technical" score={decision.scores.technical} color="#10b981" />
            <ScoreBar label="Fundamental" score={decision.scores.fundamental} color="#3b82f6" />
            <ScoreBar label="Momentum" score={decision.scores.momentum} color="#f59e0b" />
            <ScoreBar label="Macro" score={decision.scores.macro} color="#8b5cf6" />
          </div>

          <div className="space-y-2">
            <p className="text-zinc-300 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <Zap size={12} className="text-amber-400" />
              Reasoning
            </p>
            <ul className="space-y-1.5">
              {decision.reasoning.map((r, i) => (
                <li key={i} className="text-zinc-400 text-xs flex items-start gap-2">
                  <span className="text-zinc-600 mt-0.5">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-zinc-600 text-[10px]">
            Generated: {new Date(decision.timestamp).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
}
