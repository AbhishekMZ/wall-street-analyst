interface CategoryFilterProps {
  categories: string[];
  selected: string;
  onSelect: (cat: string) => void;
}

export default function CategoryFilter({ categories, selected, onSelect }: CategoryFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect('All')}
        className={`px-4 py-2 rounded-full text-xs font-semibold transition-all cursor-pointer
          ${selected === 'All'
            ? 'bg-white text-black'
            : 'bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-white border border-white/10'
          }`}
      >
        All
      </button>
      {categories.map((cat) => (
        <button
          key={cat}
          onClick={() => onSelect(cat)}
          className={`px-4 py-2 rounded-full text-xs font-semibold transition-all cursor-pointer
            ${selected === cat
              ? 'bg-white text-black'
              : 'bg-white/5 text-zinc-400 hover:bg-white/10 hover:text-white border border-white/10'
            }`}
        >
          {cat}
        </button>
      ))}
    </div>
  );
}
