import type { CandidateProduct, CandidateRow } from "@/types/avori";

type CandidatesTableProps = {
  products: CandidateProduct[];
  selectedProductId?: string;
  onSelect: (productId: string) => void;
  onExportCsv: () => void;
};

function scoreBadge(score: number) {
  if (score >= 90) {
    return { label: "High", className: "bg-emerald-100 text-emerald-700" };
  }
  if (score >= 60) {
    return { label: "Medium", className: "bg-amber-100 text-amber-700" };
  }
  return { label: "Low", className: "bg-slate-200 text-slate-700" };
}

function candidateRow(product: CandidateProduct, index: number): CandidateRow {
  return {
    rank: index + 1,
    title: product.title,
    price: product.price,
    sold_count: product.sold_count,
    review_count: product.review_count,
    score: product.score,
    early_window: Boolean(product.early_window),
    keyword: product.discovered_keywords?.[0] ?? "",
    seller: product.seller_name ?? "unknown",
  };
}

export function CandidatesTable({
  products,
  selectedProductId,
  onSelect,
  onExportCsv,
}: CandidatesTableProps) {
  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-slate-500">
            Candidates
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-900">
            Ranked candidates
          </h2>
        </div>
        <button
          className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 transition hover:border-slate-500"
          onClick={onExportCsv}
          type="button"
        >
          Export CSV
        </button>
      </div>

      <div className="mt-5 overflow-hidden rounded-[1.5rem] border border-slate-200">
        <div className="max-h-[26rem] overflow-auto">
          <table className="min-w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 bg-[#f8f5ef] text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Price</th>
                <th className="px-4 py-3 font-medium">Sold</th>
                <th className="px-4 py-3 font-medium">Reviews</th>
                <th className="px-4 py-3 font-medium">Score</th>
                <th className="px-4 py-3 font-medium">Seller</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product, index) => {
                const row = candidateRow(product, index);
                const selected = selectedProductId === product.product_id;
                const badge = scoreBadge(row.score);
                return (
                  <tr
                    className={selected ? "bg-[#eef6f2]" : "border-t border-slate-100 bg-white"}
                    key={product.product_id}
                  >
                    <td className="px-4 py-3">{row.rank}</td>
                    <td className="px-4 py-3">
                      <button
                        className="text-left font-medium text-slate-900"
                        onClick={() => onSelect(product.product_id)}
                        type="button"
                      >
                        {row.title}
                      </button>
                      {row.early_window ? (
                        <span className="mt-2 inline-flex rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">
                          Early Window
                        </span>
                      ) : null}
                    </td>
                    <td className="px-4 py-3">${row.price.toFixed(2)}</td>
                    <td className="px-4 py-3">{row.sold_count}</td>
                    <td className="px-4 py-3">{row.review_count}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-2">
                        <span>{row.score.toFixed(2)}</span>
                        <span className={`inline-flex w-fit rounded-full px-2 py-1 text-xs font-semibold ${badge.className}`}>
                          {badge.label}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">{row.seller}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
