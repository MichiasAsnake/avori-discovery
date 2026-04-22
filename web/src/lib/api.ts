import type {
  CandidatesPayload,
  ChatResponse,
  DiscoveryJob,
  WatchlistEntry,
} from "@/types/avori";

const API_BASE_URL = (process.env.NEXT_PUBLIC_AVORI_API_BASE_URL ?? "/api").replace(/\/$/, "");

function apiPath(path: string) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function startDiscovery() {
  const response = await fetch(apiPath("/discovery/run"), {
    method: "POST",
  });
  return parseJson<DiscoveryJob>(response);
}

export async function getDiscoveryJob(jobId: string) {
  const response = await fetch(apiPath(`/discovery/jobs/${jobId}`));
  return parseJson<DiscoveryJob>(response);
}

export async function searchProducts(keyword: string) {
  const response = await fetch(apiPath(`/products/search?keyword=${encodeURIComponent(keyword)}`));
  return parseJson<CandidatesPayload>(response);
}

export async function getProductDetail(productId: string) {
  const response = await fetch(apiPath(`/products/${productId}`));
  return parseJson<Record<string, unknown>>(response);
}

export async function listWatchlist() {
  const response = await fetch(apiPath("/watchlist"));
  const payload = await parseJson<{ watchlist: WatchlistEntry[] }>(response);
  return payload.watchlist;
}

export async function addWatchlistEntry(payload: Record<string, unknown>) {
  const response = await fetch(apiPath("/watchlist"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson<{ status: string; entry?: WatchlistEntry }>(response);
}

export async function removeWatchlistEntry(productId: string) {
  const response = await fetch(apiPath(`/watchlist/${productId}`), {
    method: "DELETE",
  });
  return parseJson<{ status: string }>(response);
}

export async function refreshWatchlist() {
  const response = await fetch(apiPath("/watchlist/refresh"), {
    method: "POST",
  });
  return parseJson<Record<string, unknown>>(response);
}

export async function chat(message: string, sessionId?: string) {
  const response = await fetch(apiPath("/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  return parseJson<ChatResponse>(response);
}
