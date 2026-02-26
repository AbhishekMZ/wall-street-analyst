import { ArrowDown } from 'lucide-react';

export default function HeroSection() {
  return (
    <section className="relative py-16 sm:py-24 text-center">
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent pointer-events-none" />
      <div className="relative max-w-3xl mx-auto px-6">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-zinc-400 text-xs font-medium">AI-Powered Analysis Framework</span>
        </div>
        <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight mb-4">
          Institutional Research.
          <br />
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            Now in Your Hands.
          </span>
        </h2>
        <p className="text-zinc-400 text-base sm:text-lg max-w-xl mx-auto leading-relaxed mb-8">
          10 battle-tested prompt templates modeled after Goldman Sachs, Morgan Stanley, 
          Bridgewater, and more. Generate institutional-grade analysis in minutes.
        </p>
        <a
          href="#prompts"
          className="inline-flex items-center gap-2 text-zinc-500 text-sm hover:text-white transition-colors"
        >
          <span>Explore Templates</span>
          <ArrowDown size={14} className="animate-bounce" />
        </a>
      </div>
    </section>
  );
}
