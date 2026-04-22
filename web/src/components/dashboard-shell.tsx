"use client";

import { useState } from "react";

import { CandidatesTable } from "@/components/candidates-table";
import { ChatPanel } from "@/components/chat-panel";
import { DetailPanel } from "@/components/detail-panel";
import { DiscoverySidebar } from "@/components/discovery-sidebar";
import { EmptyState } from "@/components/empty-state";
import { WatchlistPanel } from "@/components/watchlist-panel";
import {
  addWatchlistEntry,
  chat,
  getDiscoveryJob,
  getProductDetail,
  listWatchlist,
  refreshWatchlist,
  removeWatchlistEntry,
  searchProducts,
  startDiscovery,
} from "@/lib/api";
import { candidatesToCsv } from "@/lib/csv";
import { pollDiscoveryJob } from "@/lib/polling";
import type { CandidateProduct, ProductDetailPayload, WatchlistEntry } from "@/types/avori";

type DashboardShellProps = {
  initialCandidates: CandidateProduct[];
  initialWatchlist: WatchlistEntry[];
};

type ActiveTab = "Candidates" | "Watchlist";

export function DashboardShell({
  initialCandidates,
  initialWatchlist,
}: DashboardShellProps) {
  const [activeTab, setActiveTab] = useState<ActiveTab>("Candidates");
  const [candidates, setCandidates] = useState(initialCandidates);
  const [watchlist, setWatchlist] = useState(initialWatchlist);
  const [selectedProductId, setSelectedProductId] = useState(initialCandidates[0]?.product_id);
  const [keyword, setKeyword] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [chatSessionId, setChatSessionId] = useState<string>();
  const [priceMax, setPriceMax] = useState(200);
  const [minSoldCount, setMinSoldCount] = useState(0);
  const [earlyWindowOnly, setEarlyWindowOnly] = useState(false);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isWatchlistLoading, setIsWatchlistLoading] = useState(false);
  const [isWatchlistPending, setIsWatchlistPending] = useState(false);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [watchlistLoaded, setWatchlistLoaded] = useState(initialWatchlist.length > 0);

  const visibleCandidates = candidates.filter((product) => {
    if (product.price > priceMax) {
      return false;
    }
    if (product.sold_count < minSoldCount) {
      return false;
    }
    if (earlyWindowOnly && !product.early_window) {
      return false;
    }
    return true;
  });
  const selectedProduct =
    visibleCandidates.find((product) => product.product_id === selectedProductId) ?? visibleCandidates[0];
  const watchlistProductIds = new Set(watchlist.map((entry) => entry.product_id));

  async function loadWatchlist(forceRefresh = false) {
    if (watchlistLoaded && !forceRefresh) {
      return;
    }
    setIsWatchlistLoading(true);
    try {
      const entries = await listWatchlist();
      setWatchlist(entries);
      setWatchlistLoaded(true);
    } finally {
      setIsWatchlistLoading(false);
    }
  }

  async function hydrateProductDetail(productId: string) {
    setIsDetailLoading(true);
    try {
      const detail = (await getProductDetail(productId)) as ProductDetailPayload;
      setCandidates((current) =>
        current.map((product) =>
          product.product_id === productId
            ? {
                ...product,
                category_names: detail.category_names ?? product.category_names,
                review_summary: detail.review_summary ?? product.review_summary,
                supplementary_signals: detail.supplementary_signals ?? product.supplementary_signals,
              }
            : product,
        ),
      );
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function handleRunDiscovery() {
    setIsRunningDiscovery(true);
    setStatusMessage("Running discovery — this usually takes around 30 seconds.");
    try {
      const job = await startDiscovery();
      const finishedJob = await pollDiscoveryJob(() => getDiscoveryJob(job.job_id), {
        intervalMs: 10,
        timeoutMs: 5_000,
      });

      const nextProducts = finishedJob.payload?.products ?? [];
      setCandidates(nextProducts);
      setSelectedProductId(nextProducts[0]?.product_id);
      setActiveTab("Candidates");
      setStatusMessage(
        nextProducts.length
          ? `Discovery completed with ${nextProducts.length} ranked candidates.`
          : "Discovery completed, but no candidates were returned.",
      );
    } finally {
      setIsRunningDiscovery(false);
    }
  }

  async function handleSearch() {
    if (!keyword.trim()) {
      return;
    }
    setIsSearching(true);
    setStatusMessage(`Searching TikTok Shop for "${keyword.trim()}"...`);
    try {
      const payload = await searchProducts(keyword.trim());
      setCandidates(payload.products);
      setSelectedProductId(payload.products[0]?.product_id);
      setActiveTab("Candidates");
      setStatusMessage(`Loaded ${payload.products.length} products for "${keyword.trim()}".`);
    } finally {
      setIsSearching(false);
    }
  }

  async function sendChatMessage(message: string) {
    setIsChatLoading(true);
    setMessages((current) => [...current, { role: "user", content: message }]);
    try {
      const response = await chat(message, chatSessionId);
      setChatSessionId(response.session_id);
      setMessages((current) => [...current, { role: "assistant", content: response.reply }]);
    } finally {
      setIsChatLoading(false);
    }
  }

  async function handleDiscuss(product: CandidateProduct) {
    const prompt = `Can you assess ${product.title} as an Avori candidate? It's priced at $${product.price.toFixed(2)}, has ${product.sold_count} sales and ${product.review_count} reviews, sold by ${product.seller_name ?? "unknown seller"}.`;
    await sendChatMessage(prompt);
  }

  async function handleToggleWatchlist(product: CandidateProduct) {
    setIsWatchlistPending(true);
    try {
      if (watchlistProductIds.has(product.product_id)) {
        await removeWatchlistEntry(product.product_id);
        setWatchlist((current) => current.filter((entry) => entry.product_id !== product.product_id));
        return;
      }

      const response = await addWatchlistEntry({
        product_id: product.product_id,
        title: product.title,
        reason: product.early_window ? "Early window candidate from Avori discovery." : "Saved from Avori research board.",
        track: true,
        score: product.score,
        sold_count: product.sold_count,
        review_count: product.review_count,
        price: product.price,
      });

      if (response.entry) {
        setWatchlist((current) => [response.entry as WatchlistEntry, ...current.filter((entry) => entry.product_id !== product.product_id)]);
      } else {
        await loadWatchlist(true);
      }
      setWatchlistLoaded(true);
    } finally {
      setIsWatchlistPending(false);
    }
  }

  async function handleRefreshWatchlist() {
    setIsWatchlistLoading(true);
    try {
      await refreshWatchlist();
      const entries = await listWatchlist();
      setWatchlist(entries);
      setWatchlistLoaded(true);
    } finally {
      setIsWatchlistLoading(false);
    }
  }

  async function handleRemoveWatchlist(productId: string) {
    await removeWatchlistEntry(productId);
    setWatchlist((current) => current.filter((entry) => entry.product_id !== productId));
  }

  async function handleSelectProduct(productId: string) {
    setSelectedProductId(productId);
    await hydrateProductDetail(productId);
  }

  async function handleTabChange(tab: ActiveTab) {
    setActiveTab(tab);
    if (tab === "Watchlist") {
      await loadWatchlist();
    }
  }

  function handleExportCsv() {
    const csv = candidatesToCsv(
      visibleCandidates.map((product, index) => ({
        rank: index + 1,
        title: product.title,
        price: product.price,
        sold_count: product.sold_count,
        review_count: product.review_count,
        score: product.score,
        early_window: Boolean(product.early_window),
        keyword: product.discovered_keywords?.[0] ?? "",
        seller: product.seller_name ?? "unknown",
      })),
    );

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "avori_candidates.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleManualChat(message: string) {
    await sendChatMessage(message);
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(135deg,#f7f3ec_0%,#ffffff_45%,#e5efe9_100%)] px-6 py-8 text-slate-900">
      <div className="mx-auto grid max-w-[1440px] gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <DiscoverySidebar
          earlyWindowOnly={earlyWindowOnly}
          isRunningDiscovery={isRunningDiscovery}
          isSearching={isSearching}
          keyword={keyword}
          minSoldCount={minSoldCount}
          onEarlyWindowOnlyChange={setEarlyWindowOnly}
          onKeywordChange={setKeyword}
          onMinSoldCountChange={setMinSoldCount}
          onPriceMaxChange={setPriceMax}
          onRunDiscovery={() => void handleRunDiscovery()}
          onSearch={() => void handleSearch()}
          priceMax={priceMax}
          statusMessage={statusMessage}
        />

        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            {(["Candidates", "Watchlist"] as const).map((tab) => {
              const active = activeTab === tab;
              return (
                <button
                  aria-selected={active}
                  className={active ? "rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white" : "rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700"}
                  key={tab}
                  onClick={() => void handleTabChange(tab)}
                  role="tab"
                  type="button"
                >
                  {tab}
                </button>
              );
            })}
          </div>

          {activeTab === "Candidates" ? (
            visibleCandidates.length ? (
              <div className="space-y-6">
                <CandidatesTable
                  onExportCsv={handleExportCsv}
                  onSelect={(productId) => void handleSelectProduct(productId)}
                  products={visibleCandidates}
                  selectedProductId={selectedProduct?.product_id}
                />
                <div className="grid gap-6 xl:grid-cols-[1.4fr_0.6fr]">
                  <DetailPanel
                    isLoading={isDetailLoading}
                    isSavedToWatchlist={selectedProduct ? watchlistProductIds.has(selectedProduct.product_id) : false}
                    isWatchlistPending={isWatchlistPending}
                    onDiscuss={handleDiscuss}
                    onToggleWatchlist={handleToggleWatchlist}
                    product={selectedProduct}
                  />
                  <ChatPanel isLoading={isChatLoading} messages={messages} onSend={handleManualChat} />
                </div>
              </div>
            ) : (
              <EmptyState onRunDiscovery={() => void handleRunDiscovery()} />
            )
          ) : (
            <WatchlistPanel
              isLoading={isWatchlistLoading}
              onRefresh={() => void handleRefreshWatchlist()}
              onRemove={(productId) => void handleRemoveWatchlist(productId)}
              watchlist={watchlist}
            />
          )}
        </div>
      </div>
    </main>
  );
}
