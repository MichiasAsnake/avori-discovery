import type { WatchlistEntry } from "@/types/avori";

type WatchlistPanelProps = {
  watchlist: WatchlistEntry[];
  isLoading?: boolean;
  onRefresh: () => void;
  onRemove: (productId: string) => void;
};

function velocityText(velocity?: number | null) {
  if (velocity == null) {
    return "Tracking started";
  }
  if (velocity > 0) {
    return `↑ ${velocity} sold/wk`;
  }
  if (velocity < 0) {
    return `↓ ${Math.abs(velocity)} sold/wk`;
  }
  return "→ 0 sold/wk";
}

export function WatchlistPanel({
  watchlist,
  isLoading = false,
  onRefresh,
  onRemove,
}: WatchlistPanelProps) {
  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-2xl font-semibold tracking-[-0.03em] text-slate-900">Watchlist</h2>
        <button
          className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
          onClick={onRefresh}
          type="button"
        >
          Refresh Tracking
        </button>
      </div>
      {isLoading ? <p className="mt-4 text-sm text-slate-500">Refreshing watchlist...</p> : null}
      {watchlist.length ? (
        <div className="mt-5 space-y-4">
          {watchlist.map((entry) => (
            <article
              className="rounded-[1.5rem] border border-slate-200 bg-[#fbfaf7] p-5"
              key={entry.product_id}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{entry.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">{entry.reason}</p>
                </div>
                {entry.graduated ? (
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                    Graduated
                  </span>
                ) : null}
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Velocity</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{velocityText(entry.velocity)}</p>
                </div>
                <div className="rounded-2xl bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Latest Sales</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{entry.latest_sold_count ?? "n/a"}</p>
                </div>
                <div className="rounded-2xl bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Latest Reviews</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{entry.latest_review_count ?? "n/a"}</p>
                </div>
                <div className="rounded-2xl bg-white p-4">
                  <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Snapshots</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{entry.snapshots_count ?? 0}</p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
                  onClick={() => onRemove(entry.product_id)}
                  type="button"
                >
                  Remove
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-slate-600">Your tracked products will appear here once you save candidates.</p>
      )}
    </section>
  );
}
