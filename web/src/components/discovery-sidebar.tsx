import { scoreLegend } from "@/lib/score";

type DiscoverySidebarProps = {
  keyword: string;
  onKeywordChange: (value: string) => void;
  onSearch: () => void;
  onRunDiscovery: () => void;
  priceMax: number;
  minSoldCount: number;
  earlyWindowOnly: boolean;
  onPriceMaxChange: (value: number) => void;
  onMinSoldCountChange: (value: number) => void;
  onEarlyWindowOnlyChange: (value: boolean) => void;
  isRunningDiscovery?: boolean;
  isSearching?: boolean;
  statusMessage?: string | null;
};

export function DiscoverySidebar({
  keyword,
  onKeywordChange,
  onSearch,
  onRunDiscovery,
  priceMax,
  minSoldCount,
  earlyWindowOnly,
  onPriceMaxChange,
  onMinSoldCountChange,
  onEarlyWindowOnlyChange,
  isRunningDiscovery = false,
  isSearching = false,
  statusMessage,
}: DiscoverySidebarProps) {
  return (
    <aside className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-slate-500">
        Controls
      </p>
      <button
        className="mt-5 w-full rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
        disabled={isRunningDiscovery}
        onClick={onRunDiscovery}
        type="button"
      >
        {isRunningDiscovery ? "Running Discovery..." : "Run Discovery"}
      </button>
      {statusMessage ? (
        <p className="mt-3 text-sm leading-6 text-slate-600">{statusMessage}</p>
      ) : null}

      <div className="mt-6">
        <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="keyword-search">
          Keyword Search
        </label>
        <input
          id="keyword-search"
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-400"
          onChange={(event) => onKeywordChange(event.target.value)}
          placeholder="travel organizer"
          value={keyword}
        />
        <button
          className="mt-3 w-full rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
          disabled={isSearching}
          onClick={onSearch}
          type="button"
        >
          {isSearching ? "Searching..." : "Search Keyword"}
        </button>
      </div>

      <div className="mt-6 rounded-[1.5rem] border border-slate-200 bg-[#fbfaf7] p-4">
        <p className="text-sm font-semibold text-slate-900">Filters</p>
        <label className="mt-4 block text-sm text-slate-700" htmlFor="price-max">
          Max price
        </label>
        <input
          id="price-max"
          className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-400"
          min={0}
          onChange={(event) => onPriceMaxChange(Number(event.target.value) || 0)}
          type="number"
          value={priceMax}
        />

        <label className="mt-4 block text-sm text-slate-700" htmlFor="min-sold">
          Minimum sold
        </label>
        <input
          id="min-sold"
          className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-slate-400"
          min={0}
          onChange={(event) => onMinSoldCountChange(Number(event.target.value) || 0)}
          type="number"
          value={minSoldCount}
        />

        <label className="mt-4 flex items-center gap-3 text-sm font-medium text-slate-700">
          <input
            checked={earlyWindowOnly}
            onChange={(event) => onEarlyWindowOnlyChange(event.target.checked)}
            type="checkbox"
          />
          Early window only
        </label>
      </div>

      <div className="mt-8 rounded-[1.5rem] bg-[#f4efe6] p-4">
        <p className="text-sm font-semibold text-slate-900">Score guide</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">{scoreLegend()}</p>
      </div>
    </aside>
  );
}
