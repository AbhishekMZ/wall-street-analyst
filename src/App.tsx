import { useState, useMemo, useEffect } from 'react';
import {
  TrendingUp, Radar, Globe, FileText, BookOpen, Sparkles, Brain, Briefcase, DollarSign, Bot,
} from 'lucide-react';
import { prompts } from './data/prompts';
import CategoryFilter from './components/CategoryFilter';
import PromptCard from './components/PromptCard';
import ScannerPanel from './components/ScannerPanel';
import MacroPanel from './components/MacroPanel';
import ReportPanel from './components/ReportPanel';
import LearningPanel from './components/LearningPanel';
import PortfolioPanel from './components/PortfolioPanel';
import MockInvestmentsPanel from './components/MockInvestmentsPanel';
import AgentPanel from './components/AgentPanel';
import { startKeepAlive } from './api';

type Tab = 'scanner' | 'agent' | 'macro' | 'learning' | 'portfolio' | 'mock' | 'reports' | 'templates';

const TABS: { id: Tab; label: string; icon: React.ComponentType<any> }[] = [
  { id: 'scanner', label: 'Analyzer', icon: Radar },
  { id: 'agent', label: 'Agent', icon: Bot },
  { id: 'macro', label: 'Macro', icon: Globe },
  { id: 'learning', label: 'Brain', icon: Brain },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase },
  { id: 'mock', label: 'Trades', icon: DollarSign },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'templates', label: 'Prompts', icon: BookOpen },
];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('scanner');

  // Keep Render backend alive while any browser tab is open
  useEffect(() => { startKeepAlive(); }, []);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = useMemo(
    () => [...new Set(prompts.map((p) => p.category))],
    []
  );

  const filtered = useMemo(
    () =>
      selectedCategory === 'All'
        ? prompts
        : prompts.filter((p) => p.category === selectedCategory),
    [selectedCategory]
  );

  return (
    <div className="min-h-screen bg-[#09090b] text-white font-[Inter,system-ui,sans-serif]">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#09090b]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
                <TrendingUp size={18} className="text-white" />
              </div>
              <div>
                <h1 className="text-white font-bold text-base tracking-tight">Wall Street Analyst</h1>
                <p className="text-zinc-600 text-[10px] uppercase tracking-wider">Indian Market • NSE/BSE</p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
              <Sparkles size={12} className="text-amber-400" />
              <span className="text-zinc-400 text-[10px] font-medium">Multi-Factor Analysis Engine</span>
            </div>
          </div>
          {/* Tab Navigation */}
          <nav className="flex gap-1 -mb-px">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-medium border-b-2 transition-all cursor-pointer
                  ${activeTab === id
                    ? 'border-emerald-400 text-white'
                    : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:border-white/10'
                  }`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Hero — only on scanner tab */}
      {activeTab === 'scanner' && (
        <section className="relative py-12 text-center">
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent pointer-events-none" />
          <div className="relative max-w-2xl mx-auto px-6">
            <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight leading-tight mb-3">
              Institutional-Grade
              <br />
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Decision Engine
              </span>
            </h2>
            <p className="text-zinc-500 text-sm max-w-lg mx-auto leading-relaxed">
              15-factor analysis combining technical, fundamental, momentum, and macro signals.
              Scan 200+ stocks across Nifty 50, Next 50, Midcaps & Hidden Smallcaps.
            </p>
          </div>
        </section>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8 pb-24">
        {activeTab === 'scanner' && <ScannerPanel />}
        {activeTab === 'agent' && <AgentPanel />}
        {activeTab === 'macro' && <MacroPanel />}
        {activeTab === 'learning' && <LearningPanel />}
        {activeTab === 'portfolio' && <PortfolioPanel />}
        {activeTab === 'mock' && <MockInvestmentsPanel />}
        {activeTab === 'reports' && <ReportPanel />}
        {activeTab === 'templates' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-white font-bold text-lg mb-1">AI Prompt Templates</h2>
              <p className="text-zinc-500 text-sm">Copy-paste into ChatGPT or Claude for deeper manual analysis</p>
            </div>
            <CategoryFilter
              categories={categories}
              selected={selectedCategory}
              onSelect={setSelectedCategory}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filtered.map((prompt) => (
                <div
                  key={prompt.id}
                  className={selectedId === prompt.id ? 'md:col-span-2' : ''}
                >
                  <PromptCard
                    prompt={prompt}
                    isSelected={selectedId === prompt.id}
                    onSelect={() =>
                      setSelectedId(selectedId === prompt.id ? null : prompt.id)
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-white/10 py-6 text-center">
        <p className="text-zinc-700 text-[10px]">
          Wall Street Analyst — Not financial advice. For educational and research purposes only.
        </p>
      </footer>
    </div>
  );
}

export default App;
