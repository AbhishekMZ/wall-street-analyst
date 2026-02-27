import { useState, useEffect, useCallback } from 'react';
import { Bot, Loader2, RefreshCw, Play, Zap, Brain, Clock, Activity, AlertTriangle, TrendingUp } from 'lucide-react';
import { api } from '../api';

interface AgentActivity {
  timestamp: string;
  action: string;
  detail: string;
  category: string;
}

interface ScheduledJob {
  id: string;
  name: string;
  next_run: string | null;
}

const CATEGORY_ICONS: Record<string, { icon: typeof Bot; color: string }> = {
  scan: { icon: Activity, color: 'text-cyan-400' },
  signal: { icon: TrendingUp, color: 'text-emerald-400' },
  analysis: { icon: Zap, color: 'text-amber-400' },
  learning: { icon: Brain, color: 'text-purple-400' },
  error: { icon: AlertTriangle, color: 'text-red-400' },
  system: { icon: Bot, color: 'text-zinc-400' },
};

const ACTION_COLORS: Record<string, string> = {
  SIGNAL_STRONG_BUY: 'bg-emerald-500/20 text-emerald-400',
  SIGNAL_BUY: 'bg-emerald-500/10 text-emerald-400',
  SIGNAL_SELL: 'bg-red-500/10 text-red-400',
  SIGNAL_STRONG_SELL: 'bg-red-500/20 text-red-400',
  SCAN_STARTED: 'bg-cyan-500/10 text-cyan-400',
  SCAN_COMPLETE: 'bg-cyan-500/20 text-cyan-400',
  LEARNING_COMPLETE: 'bg-purple-500/10 text-purple-400',
  AGENT_STARTED: 'bg-emerald-500/10 text-emerald-400',
  ANALYSIS_COMPLETE: 'bg-amber-500/10 text-amber-400',
};

export default function AgentPanel() {
  const [status, setStatus] = useState<any>(null);
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggering, setTriggering] = useState('');
  const [error, setError] = useState('');

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getAgentStatus() as any;
      setStatus(data.state || {});
      setJobs(data.scheduled_jobs || []);
      setActivities(data.recent_activity || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 15000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  const triggerScan = async (universe: string) => {
    setTriggering(universe);
    try {
      await api.triggerScan(universe);
      setTimeout(loadStatus, 2000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setTriggering('');
    }
  };

  const triggerLearn = async () => {
    setTriggering('learn');
    try {
      await api.triggerLearning();
      setTimeout(loadStatus, 2000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setTriggering('');
    }
  };

  const timeAgo = (ts: string) => {
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="space-y-6">
      {/* Agent Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h3 className="text-white font-bold text-base">Autonomous Agent</h3>
            <p className="text-zinc-600 text-[10px]">
              {status?.scan_in_progress
                ? `Scanning ${status.current_scan_universe}...`
                : status?.agent_started_at
                  ? `Running since ${timeAgo(status.agent_started_at)}`
                  : 'Waiting for deployment...'
              }
            </p>
          </div>
          <div className={`w-2.5 h-2.5 rounded-full ${status?.agent_started_at ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
        </div>
        <button
          onClick={loadStatus}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-zinc-300 text-xs hover:bg-white/10 transition-colors cursor-pointer"
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

      {/* Stats */}
      {status && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Scans Done</p>
            <p className="text-white text-xl font-bold mt-1">{status.total_scans_completed || 0}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Stocks Analyzed</p>
            <p className="text-white text-xl font-bold mt-1">{status.total_stocks_analyzed || 0}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Decisions Saved</p>
            <p className="text-white text-xl font-bold mt-1">{status.total_decisions_saved || 0}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <p className="text-zinc-500 text-[10px] uppercase tracking-wider">Learning Cycles</p>
            <p className="text-white text-xl font-bold mt-1">{status.learning_cycles || 0}</p>
          </div>
        </div>
      )}

      {/* Scheduled Jobs */}
      {jobs.length > 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={14} className="text-cyan-400" />
            <h4 className="text-white font-semibold text-sm">Scheduled Jobs</h4>
          </div>
          <div className="space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div>
                  <p className="text-zinc-300 text-xs font-medium">{job.name}</p>
                  <p className="text-zinc-600 text-[10px]">ID: {job.id}</p>
                </div>
                <div className="text-right">
                  <p className="text-zinc-400 text-[10px]">Next run</p>
                  <p className="text-white text-xs font-mono">
                    {job.next_run ? new Date(job.next_run).toLocaleTimeString() : 'N/A'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Manual Triggers */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
        <div className="flex items-center gap-2 mb-3">
          <Play size={14} className="text-emerald-400" />
          <h4 className="text-white font-semibold text-sm">Manual Triggers</h4>
          <span className="text-zinc-600 text-[10px]">— Force a scan or learning cycle now</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {['nifty50', 'nifty_next50', 'midcap_gems', 'smallcap_hidden', 'all'].map((u) => (
            <button
              key={u}
              onClick={() => triggerScan(u)}
              disabled={!!triggering}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[11px] font-medium hover:bg-cyan-500/20 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {triggering === u ? <Loader2 size={12} className="animate-spin" /> : <Activity size={12} />}
              {u === 'all' ? 'Full Scan' : u.replace('_', ' ')}
            </button>
          ))}
          <button
            onClick={triggerLearn}
            disabled={!!triggering}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 text-[11px] font-medium hover:bg-purple-500/20 transition-colors disabled:opacity-50 cursor-pointer"
          >
            {triggering === 'learn' ? <Loader2 size={12} className="animate-spin" /> : <Brain size={12} />}
            Learn Now
          </button>
        </div>
      </div>

      {/* Activity Log */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={14} className="text-amber-400" />
          <h4 className="text-white font-semibold text-sm">Activity Log</h4>
          <span className="text-zinc-600 text-[10px]">— Real-time agent actions</span>
        </div>

        {activities.length > 0 ? (
          <div className="space-y-1.5 max-h-[500px] overflow-y-auto">
            {[...activities].reverse().map((a, i) => {
              const cat = CATEGORY_ICONS[a.category] || CATEGORY_ICONS.system;
              const Icon = cat.icon;
              const actionColor = ACTION_COLORS[a.action] || 'bg-white/5 text-zinc-400';
              return (
                <div key={i} className="flex items-start gap-2.5 py-1.5">
                  <Icon size={13} className={`${cat.color} mt-0.5 shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${actionColor}`}>
                        {a.action}
                      </span>
                      <span className="text-zinc-600 text-[10px]">{timeAgo(a.timestamp)}</span>
                    </div>
                    <p className="text-zinc-400 text-xs mt-0.5 truncate">{a.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 border border-dashed border-white/10 rounded-xl">
            <Bot size={24} className="text-zinc-700 mx-auto mb-2" />
            <p className="text-zinc-500 text-xs">No activity yet</p>
            <p className="text-zinc-600 text-[10px] mt-1">The agent will start scanning automatically, or trigger a scan above</p>
          </div>
        )}
      </div>
    </div>
  );
}
