import type { CandidateProduct } from "@/types/avori";

export function buildTikTokShopUrl(
  seoUrl: CandidateProduct["seo_url"],
  baseUrl = "https://shop.tiktok.com",
) {
  const resolved =
    typeof seoUrl === "string"
      ? seoUrl
      : seoUrl?.canonical_url ?? seoUrl?.slug ?? "";

  if (!resolved) {
    return null;
  }
  if (resolved.startsWith("http://") || resolved.startsWith("https://")) {
    return resolved;
  }
  return new URL(resolved.replace(/^\//, ""), `${baseUrl.replace(/\/$/, "")}/`).toString();
}
