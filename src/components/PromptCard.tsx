import { useState } from 'react';
import {
  Search, Calculator, Shield, BarChart3, PieChart,
  TrendingUp, DollarSign, Layers, Activity, Globe,
  Copy, Check, ChevronRight,
} from 'lucide-react';
import type { PromptTemplate } from '../data/prompts';
import { generatePrompt } from '../utils/generatePrompt';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const iconMap: Record<string, React.ComponentType<any>> = {
  Search, Calculator, Shield, BarChart3, PieChart,
  TrendingUp, DollarSign, Layers, Activity, Globe,
};

interface PromptCardProps {
  prompt: PromptTemplate;
  isSelected: boolean;
  onSelect: () => void;
}

export default function PromptCard({ prompt, isSelected, onSelect }: PromptCardProps) {
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);

  const Icon = iconMap[prompt.icon] || Search;

  const handleCopy = async () => {
    const text = generatePrompt(prompt, fieldValues);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isSelected) {
    return (
      <button
        onClick={onSelect}
        className="group relative w-full text-left rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5 
                   hover:border-white/20 hover:bg-white/8 transition-all duration-300 cursor-pointer"
      >
        <div className="flex items-start gap-4">
          <div
            className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: prompt.color + '20' }}
          >
            <Icon size={22} style={{ color: prompt.color }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: prompt.color + '20', color: prompt.color }}>
                {prompt.category}
              </span>
            </div>
            <h3 className="text-white font-semibold text-base leading-tight mb-0.5">
              {prompt.title}
            </h3>
            <p className="text-zinc-400 text-sm font-medium">{prompt.firm}</p>
            <p className="text-zinc-500 text-xs mt-1.5 line-clamp-2">{prompt.description}</p>
          </div>
          <ChevronRight size={18} className="text-zinc-600 group-hover:text-zinc-400 transition-colors mt-1 flex-shrink-0" />
        </div>
      </button>
    );
  }

  return (
    <div className="rounded-2xl border border-white/15 bg-white/5 backdrop-blur-sm overflow-hidden">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-4 mb-4">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: prompt.color + '20' }}
          >
            <Icon size={26} style={{ color: prompt.color }} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: prompt.color + '20', color: prompt.color }}>
                {prompt.category}
              </span>
            </div>
            <h2 className="text-white font-bold text-xl">{prompt.title}</h2>
            <p className="text-zinc-400 text-sm">{prompt.firm}</p>
          </div>
        </div>

        <div className="space-y-1 mb-4">
          <p className="text-zinc-300 text-sm italic">"{prompt.role}"</p>
        </div>

        <p className="text-zinc-300 text-sm mb-3">{prompt.task}</p>
        <p className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-2">{prompt.action}</p>
        <ul className="space-y-1.5 mb-4">
          {prompt.items.map((item, i) => (
            <li key={i} className="text-zinc-400 text-sm flex items-start gap-2">
              <span className="text-zinc-600 mt-0.5 flex-shrink-0">•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
        <p className="text-zinc-500 text-xs italic">{prompt.format}</p>
      </div>

      <div className="p-6 space-y-4">
        <p className="text-zinc-300 text-sm font-semibold">Fill in your details:</p>
        {prompt.fields.map((field) => (
          <div key={field.id}>
            <label className="block text-zinc-400 text-xs font-medium uppercase tracking-wider mb-1.5">
              {field.label}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                value={fieldValues[field.id] || ''}
                onChange={(e) => setFieldValues({ ...fieldValues, [field.id]: e.target.value })}
                placeholder={field.placeholder}
                rows={4}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm
                           placeholder:text-zinc-600 focus:outline-none focus:border-white/25 focus:ring-1 
                           focus:ring-white/10 resize-none transition-all"
              />
            ) : (
              <input
                type="text"
                value={fieldValues[field.id] || ''}
                onChange={(e) => setFieldValues({ ...fieldValues, [field.id]: e.target.value })}
                placeholder={field.placeholder}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm
                           placeholder:text-zinc-600 focus:outline-none focus:border-white/25 focus:ring-1 
                           focus:ring-white/10 transition-all"
              />
            )}
          </div>
        ))}

        <div className="flex gap-3 pt-2">
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center gap-2 py-3 px-5 rounded-xl font-semibold text-sm
                       transition-all duration-200 cursor-pointer"
            style={{
              backgroundColor: copied ? '#059669' : prompt.color,
              color: 'white',
            }}
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy Prompt'}
          </button>
          <button
            onClick={onSelect}
            className="px-5 py-3 rounded-xl border border-white/10 text-zinc-400 text-sm font-medium
                       hover:bg-white/5 hover:text-white transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
