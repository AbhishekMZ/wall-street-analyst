import { TrendingUp, Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <header className="relative border-b border-white/10 bg-black/40 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <TrendingUp size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg tracking-tight">Wall Street Analyst</h1>
              <p className="text-zinc-500 text-xs">Institutional-Grade Investment Prompts</p>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
            <Sparkles size={13} className="text-amber-400" />
            <span className="text-zinc-400 text-xs font-medium">10 Analysis Templates</span>
          </div>
        </div>
      </div>
    </header>
  );
}
