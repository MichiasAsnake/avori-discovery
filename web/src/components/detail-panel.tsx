/* eslint-disable @next/next/no-img-element */
import { buildTikTokShopUrl } from "@/lib/url";
import type { CandidateProduct } from "@/types/avori";

type DetailPanelProps = {
  product?: CandidateProduct;
  onDiscuss: (product: CandidateProduct) => void;
  onToggleWatchlist: (product: CandidateProduct) => void;
  isSavedToWatchlist: boolean;
  isWatchlistPending?: boolean;
  isLoading?: boolean;
};

function detailRows(values?: Record<string, unknown>) {
  if (!values) {
    return [];
  }
  return Object.entries(values).map(([key, value]) => ({
    label: key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase()),
    value: String(value),
  }));
}

export function DetailPanel({
  product,
  onDiscuss,
  onToggleWatchlist,
  isSavedToWatchlist,
  isWatchlistPending = false,
  isLoading = false,
}: DetailPanelProps) {
  if (!product) {
    return (
      <section className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
        <h2 className="text-2xl font-semibold tracking-[-0.03em] text-slate-900">Product detail</h2>
        <p className="mt-4 text-sm leading-6 text-slate-600">Select a candidate to inspect the detail view.</p>
      </section>
    );
  }

  const reviewRows = detailRows(product.review_summary);
  const signalRows = detailRows(product.supplementary_signals);
  const categories = product.category_names ?? [];
  const tiktokShopUrl = buildTikTokShopUrl(product.seo_url);

  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
      {product.image_url ? (
        <img
          alt={product.title}
          className="h-52 w-full rounded-[1.5rem] object-cover"
          src={product.image_url}
        />
      ) : null}
      <h2 className="mt-5 text-3xl font-semibold tracking-[-0.04em] text-slate-900">{product.title}</h2>
      {isLoading ? (
        <p className="mt-3 text-sm text-slate-500">Loading latest product detail...</p>
      ) : null}
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-2xl bg-[#f8f5ef] p-4">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Price</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">${product.price.toFixed(2)}</p>
        </div>
        <div className="rounded-2xl bg-[#f8f5ef] p-4">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Sales</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{product.sold_count}</p>
        </div>
        <div className="rounded-2xl bg-[#f8f5ef] p-4">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Reviews</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{product.review_count}</p>
        </div>
        <div className="rounded-2xl bg-[#f8f5ef] p-4">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-500">Score</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{product.score.toFixed(2)}</p>
        </div>
      </div>

      <div className="mt-6 rounded-[1.5rem] border border-slate-200 p-4">
        <h3 className="text-lg font-semibold text-slate-900">Review summary</h3>
        {reviewRows.length ? (
          <dl className="mt-3 space-y-2 text-sm text-slate-600">
            {reviewRows.map((row) => (
              <div className="flex items-center justify-between gap-4" key={row.label}>
                <dt>{row.label}</dt>
                <dd className="font-medium text-slate-900">{row.value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No review summary available.</p>
        )}
      </div>

      <div className="mt-6 rounded-[1.5rem] border border-slate-200 p-4">
        <h3 className="text-lg font-semibold text-slate-900">Categories</h3>
        {categories.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {categories.map((category) => (
              <span
                className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700"
                key={category}
              >
                {category}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No category data available yet.</p>
        )}
      </div>

      <div className="mt-6 rounded-[1.5rem] border border-slate-200 p-4">
        <h3 className="text-lg font-semibold text-slate-900">Signals</h3>
        {signalRows.length ? (
          <dl className="mt-3 space-y-2 text-sm text-slate-600">
            {signalRows.map((row) => (
              <div className="flex items-center justify-between gap-4" key={row.label}>
                <dt>{row.label}</dt>
                <dd className="font-medium text-slate-900">{row.value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No supplementary signals available.</p>
        )}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
          onClick={() => onDiscuss(product)}
          type="button"
        >
          Discuss in Chat
        </button>
        <button
          className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
          disabled={isWatchlistPending}
          onClick={() => onToggleWatchlist(product)}
          type="button"
        >
          {isSavedToWatchlist ? "Remove From Watchlist" : "Save To Watchlist"}
        </button>
        {tiktokShopUrl ? (
          <a
            className="rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
            href={tiktokShopUrl}
            rel="noreferrer"
            target="_blank"
          >
            TikTok Shop URL
          </a>
        ) : null}
      </div>
    </section>
  );
}
