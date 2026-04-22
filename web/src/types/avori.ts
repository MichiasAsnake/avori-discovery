export type CandidateProduct = {
  product_id: string;
  title: string;
  price: number;
  sold_count: number;
  review_count: number;
  score: number;
  early_window?: boolean;
  keyword?: string;
  seller?: string;
  seller_name?: string;
  seo_url?: string | { canonical_url?: string; slug?: string };
  image_url?: string | null;
  discovered_keywords?: string[];
  category_names?: string[];
  supplementary_signals?: Record<string, unknown>;
  review_summary?: Record<string, unknown>;
};

export type ProductDetailPayload = {
  product_id: string;
  detail_endpoint?: string;
  category_names?: string[];
  review_summary?: Record<string, unknown>;
  supplementary_signals?: Record<string, unknown>;
};

export type CandidatesPayload = {
  products: CandidateProduct[];
  discovered_keywords?: string[];
  keyword_product_counts?: Record<string, number>;
  fallback_seller_product_counts?: Record<string, unknown>;
  search_bridge_endpoint?: string | null;
  seed_terms?: string[];
};

export type DiscoveryJob = {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  error?: string | null;
  payload?: CandidatesPayload & {
    candidate_count?: number;
    results_path?: string;
    brief_path?: string;
  };
};

export type WatchlistEntry = {
  product_id: string;
  title: string;
  reason: string;
  added_at: string;
  track?: boolean;
  graduated?: boolean;
  velocity?: number | null;
  latest_sold_count?: number | null;
  latest_review_count?: number | null;
  snapshots_count?: number;
  latest_price?: number | null;
  score?: number | null;
};

export type ChatResponse = {
  reply: string;
  session_id: string;
};

export type CandidateRow = {
  rank: number;
  title: string;
  price: number;
  sold_count: number;
  review_count: number;
  score: number;
  early_window: boolean;
  keyword: string;
  seller: string;
};
