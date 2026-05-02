from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import date
from pathlib import Path

import httpx

from config import (
    DETAIL_CONCURRENCY,
    KEYWORD_CONCURRENCY,
    LANG,
    MAX_KEYWORDS,
    OUTPUT_DIR,
    REGION,
    SEARCH_COUNT,
    SEARCH_PAGE_COUNT,
    SEED_TERMS,
    SELLER_IDS,
    ensure_output_dir,
)
from endpoints.detail import (
    fetch_product_detail,
    fetch_product_detail_async,
    fetch_seller_products_list,
    fetch_showcase_product_list_async,
)
from endpoints.search import (
    extract_search_pagination,
    fetch_search_products_list,
    fetch_search_products_list_async,
    fetch_search_products_list_v2_async,
    fetch_search_word_suggestion,
    fetch_search_word_suggestion_async,
)
from extractors import (
    count_matching_showcase_entries,
    extract_category_names,
    extract_detail_bonus_signals,
    extract_related_creator_ids,
    extract_review_summary,
)
from output import build_daily_brief, write_daily_brief, write_results_json
from scorer import rank_products
from storage import list_watchlist_entries, record_watchlist_snapshot
from tikhub_client import (
    SAMPLE_ENDPOINT_AUDIT,
    SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD,
    SAMPLE_PRODUCTS,
    SAMPLE_SEARCH_PRODUCTS_PAYLOAD,
    SAMPLE_SEARCH_PRODUCTS_PAYLOAD_V2,
    SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD,
    audit_tikhub_endpoints,
)
from utils import dig, safe_float, safe_int, unique_strings


def _normalize_shop_product(product, source_endpoint):
    image = product.get("image") or {}
    price_info = product.get("product_price_info") or {}
    rate_info = product.get("rate_info") or {}
    sold_info = product.get("sold_info") or {}
    seller_info = product.get("seller_info") or {}

    price_text = price_info.get("sale_price_format") or price_info.get("sale_price_decimal") or "0"

    return {
        "product_id": str(product.get("product_id") or ""),
        "title": product.get("title") or "Untitled",
        "price": safe_float(price_text),
        "currency": price_info.get("currency_name") or "USD",
        "sold_count": safe_int(sold_info.get("sold_count")),
        "review_count": safe_int(rate_info.get("review_count")),
        "rating": safe_float(rate_info.get("score")),
        "seller_id": str(seller_info.get("seller_id") or ""),
        "seller_name": seller_info.get("shop_name") or "unknown",
        "image_url": (image.get("url_list") or [None])[0],
        "seo_url": product.get("seo_url"),
        "source_endpoint": source_endpoint,
        "category_names": [],
    }


def _extract_search_products(payload, _search_endpoint):
    return (
        dig(payload, "data", "data", "products", default=[])
        or dig(payload, "data", "data", "component_data", "products", default=[])
        or []
    )


def _extract_suggested_keywords(payload):
    data = dig(payload, "data", "data", default=[]) or []
    if not isinstance(data, list):
        return []
    return [keyword.strip() for keyword in data if isinstance(keyword, str) and keyword.strip()]


async def _discover_keywords_async(seed_terms, use_sample_data=False):
    if use_sample_data:
        payloads = [deepcopy(SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD) for _ in seed_terms]
    else:
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(KEYWORD_CONCURRENCY)

            async def fetch_seed(term: str):
                async with semaphore:
                    return await fetch_search_word_suggestion_async(term, lang=f"{LANG}-{REGION}", region=REGION, client=client)

            payloads = await asyncio.gather(*(fetch_seed(seed_term) for seed_term in seed_terms))

    discovered_keywords = []
    seen_keywords = set()
    for payload in payloads:
        for keyword in _extract_suggested_keywords(payload):
            if keyword in seen_keywords:
                continue
            seen_keywords.add(keyword)
            discovered_keywords.append(keyword)
            if len(discovered_keywords) >= MAX_KEYWORDS:
                return discovered_keywords
    return discovered_keywords


async def _collect_keyword_products_async(keywords, search_endpoint, use_sample_data=False):
    products_by_id = {}
    keyword_product_counts = {}

    async def collect_keyword(keyword: str, client: httpx.AsyncClient | None = None):
        pages = []
        page_token = ""
        offset = 0
        use_v2 = search_endpoint == "search_products_list_v2"
        for _ in range(SEARCH_PAGE_COUNT):
            if use_sample_data:
                payload = deepcopy(SAMPLE_SEARCH_PRODUCTS_PAYLOAD_V2 if use_v2 else SAMPLE_SEARCH_PRODUCTS_PAYLOAD)
            else:
                fetcher = fetch_search_products_list_v2_async if use_v2 else fetch_search_products_list_async
                payload = await fetcher(keyword, offset=offset, page_token=page_token, region=REGION, client=client)
            pages.append(payload)
            has_more, next_page_token = extract_search_pagination(payload)
            if not has_more and not next_page_token:
                break
            page_token = next_page_token
            offset += SEARCH_COUNT
        return keyword, pages

    if use_sample_data:
        results = [await collect_keyword(keyword) for keyword in keywords]
    else:
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(KEYWORD_CONCURRENCY)

            async def limited_collect(keyword: str):
                async with semaphore:
                    return await collect_keyword(keyword, client=client)

            results = await asyncio.gather(*(limited_collect(keyword) for keyword in keywords))

    for keyword, pages in results:
        keyword_products = []
        for payload in pages:
            keyword_products.extend(_extract_search_products(payload, search_endpoint))
        keyword_product_counts[keyword] = len(keyword_products)
        for product in keyword_products:
            normalized = _normalize_shop_product(product, search_endpoint)
            if not normalized["product_id"]:
                continue
            if normalized["product_id"] not in products_by_id:
                normalized["discovered_keywords"] = [keyword]
                products_by_id[normalized["product_id"]] = normalized
            else:
                discovered_keywords = products_by_id[normalized["product_id"]].setdefault("discovered_keywords", [])
                if keyword not in discovered_keywords:
                    discovered_keywords.append(keyword)

    return list(products_by_id.values()), keyword_product_counts


def _collect_fallback_seller_products(seller_ids, use_sample_data=False):
    if use_sample_data:
        products = []
        seller_product_counts = {seller_id: {"seller_name": seller_id, "product_count": 0} for seller_id in seller_ids}
        for product in SAMPLE_PRODUCTS:
            product_copy = deepcopy(product)
            product_copy["discovered_keywords"] = []
            products.append(product_copy)
            seller_product_counts[product_copy["seller_id"]] = {
                "seller_name": product_copy["seller_name"],
                "product_count": seller_product_counts.get(product_copy["seller_id"], {}).get("product_count", 0) + 1,
            }
        return products, seller_product_counts

    products = []
    seller_product_counts = {seller_id: {"seller_name": seller_id, "product_count": 0} for seller_id in seller_ids}
    for seller_id in seller_ids:
        payload = fetch_seller_products_list(seller_id)
        seller_products = dig(payload, "data", "data", "products", default=[]) or []
        for product in seller_products:
            normalized = _normalize_shop_product(product, "seller_products_list")
            if normalized["product_id"]:
                normalized["discovered_keywords"] = []
                products.append(normalized)
                seller_product_counts[seller_id] = {
                    "seller_name": normalized["seller_name"],
                    "product_count": seller_product_counts.get(seller_id, {}).get("product_count", 0) + 1,
                }
    deduped = {}
    for product in products:
        deduped[product["product_id"]] = product
    return list(deduped.values()), seller_product_counts


async def _enrich_products_with_detail_async(products, use_sample_data=False):
    async def enrich_product(product, client: httpx.AsyncClient | None = None):
        product_copy = deepcopy(product)
        if use_sample_data:
            detail_endpoint, detail_payload = "product_detail_v3", deepcopy(SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)
            showcase_payloads = []
        else:
            try:
                detail_endpoint, detail_payload = await fetch_product_detail_async(product_copy["product_id"], region=REGION, client=client)
                creator_ids = extract_related_creator_ids(detail_payload, detail_endpoint)[:3]
                showcase_payloads = []
                for creator_id in creator_ids:
                    showcase_payloads.append(await fetch_showcase_product_list_async(creator_id, client=client))
            except RuntimeError:
                # Detail API may be rate-limited; return product without enrichment
                return product_copy

        bonus_signals = extract_detail_bonus_signals(detail_payload, detail_endpoint)
        creator_showcase_hits = max(
            [count_matching_showcase_entries(payload, product_copy["product_id"]) for payload in showcase_payloads] or [0]
        )
        product_copy["category_names"] = extract_category_names(detail_payload, detail_endpoint)
        product_copy["detail_endpoint"] = detail_endpoint
        product_copy["creator_video_count"] = max(
            bonus_signals.get("related_video_count", 0),
            creator_showcase_hits,
        )
        product_copy["seller_catalog_count"] = bonus_signals.get("shop_on_sell_product_count", 0)
        product_copy["review_summary"] = extract_review_summary(detail_payload, detail_endpoint)
        product_copy.update(bonus_signals)
        return product_copy

    if use_sample_data:
        return [await enrich_product(product) for product in products]

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

        async def limited_enrich(product):
            async with semaphore:
                return await enrich_product(product, client=client)

        return await asyncio.gather(*(limited_enrich(product) for product in products))


def _cap_seller_dominance(products, limit=20, max_per_seller=5):
    capped_products = []
    seller_counts = {}

    for product in products:
        if len(capped_products) >= limit:
            break

        seller_key = product.get("seller_id") or product.get("seller_name") or product.get("product_id")
        current_count = seller_counts.get(seller_key, 0)
        if current_count >= max_per_seller:
            continue

        capped_products.append(product)
        seller_counts[seller_key] = current_count + 1

    return capped_products


async def _build_discovery_payload_async(
    *,
    use_sample_data: bool,
    seller_fallback: bool,
    endpoint_audit: list[dict],
) -> dict:
    usable_endpoints = {entry["name"] for entry in endpoint_audit if entry.get("usable")}
    if "search_products_list" in usable_endpoints:
        search_bridge_endpoint = "search_products_list"
    elif "search_products_list_v2" in usable_endpoints:
        search_bridge_endpoint = "search_products_list_v2"
    else:
        search_bridge_endpoint = None

    discovered_keywords = []
    keyword_product_counts = {}
    products = []
    fallback_seller_product_counts = {}
    errors = []

    if search_bridge_endpoint and "search_word_suggestion" in usable_endpoints:
        discovered_keywords = await _discover_keywords_async(SEED_TERMS, use_sample_data=use_sample_data)
    elif not use_sample_data:
        errors.append("Keyword suggestion endpoint is unavailable.")

    if search_bridge_endpoint and discovered_keywords:
        products, keyword_product_counts = await _collect_keyword_products_async(
            discovered_keywords,
            search_bridge_endpoint,
            use_sample_data=use_sample_data,
        )
    elif not use_sample_data:
        errors.append("Search products endpoint is unavailable or produced no keywords.")

    if seller_fallback and not products:
        if use_sample_data:
            products, fallback_seller_product_counts = _collect_fallback_seller_products(SELLER_IDS, use_sample_data=True)
        elif "seller_products_list" in usable_endpoints:
            products, fallback_seller_product_counts = _collect_fallback_seller_products(SELLER_IDS, use_sample_data=False)
        else:
            errors.append("Seller fallback endpoint is unavailable.")

    if products:
        if use_sample_data:
            enriched_products = await _enrich_products_with_detail_async(products, use_sample_data=True)
        elif "product_detail" in usable_endpoints:
            enriched_products = await _enrich_products_with_detail_async(products, use_sample_data=False)
        else:
            errors.append("Product detail endpoint is unavailable; returning products without detail enrichment.")
            enriched_products = products
    else:
        enriched_products = []

    ranked_products = rank_products(enriched_products)
    ranked_products = _cap_seller_dominance(ranked_products, limit=20, max_per_seller=5)
    data_mode = "sample" if use_sample_data else "live"

    return {
        "endpoint_audit": endpoint_audit,
        "search_bridge_endpoint": search_bridge_endpoint,
        "seed_terms": SEED_TERMS,
        "discovered_keywords": discovered_keywords,
        "keyword_product_counts": keyword_product_counts,
        "fallback_seller_product_counts": fallback_seller_product_counts,
        "seller_ids": SELLER_IDS,
        "products": ranked_products,
        "data_mode": data_mode,
        "errors": errors,
    }


def build_discovery_payload(
    *,
    use_sample_data: bool = False,
    seller_fallback: bool = True,
) -> dict:
    endpoint_audit = audit_tikhub_endpoints(use_sample_data=use_sample_data)
    if not endpoint_audit:
        endpoint_audit = deepcopy(SAMPLE_ENDPOINT_AUDIT)
    return asyncio.run(
        _build_discovery_payload_async(
            use_sample_data=use_sample_data,
            seller_fallback=seller_fallback,
            endpoint_audit=endpoint_audit,
        )
    )


def run_discovery(
    output_dir: Path | None = None,
    run_date: date | None = None,
    use_sample_data: bool = False,
    seller_fallback: bool = True,
):
    active_date = run_date or date.today()
    resolved_output_dir = ensure_output_dir(output_dir or OUTPUT_DIR)

    results_payload = {
        "run_date": active_date.isoformat(),
        **build_discovery_payload(use_sample_data=use_sample_data, seller_fallback=seller_fallback),
    }

    brief_text = build_daily_brief(results_payload, active_date)
    results_path = write_results_json(results_payload, resolved_output_dir, active_date)
    brief_path = write_daily_brief(brief_text, resolved_output_dir)
    print(brief_text)
    return {
        "results_payload": results_payload,
        "ranked_products": results_payload["products"],
        "results_path": results_path,
        "brief_path": brief_path,
    }


def search_keyword_candidates(keyword: str, *, use_sample_data: bool = False) -> dict:
    products, keyword_product_counts = asyncio.run(
        _collect_keyword_products_async([keyword], "search_products_list_v2", use_sample_data=use_sample_data)
    )
    enriched_products = asyncio.run(_enrich_products_with_detail_async(products, use_sample_data=use_sample_data))
    ranked_products = rank_products(enriched_products)
    return {
        "keyword": keyword,
        "result_count": len(ranked_products),
        "keyword_product_counts": keyword_product_counts,
        "products": ranked_products,
    }


def refresh_tracked_watchlist(*, use_sample_data: bool = False) -> dict:
    refreshed = 0
    tracked_entries = [entry for entry in list_watchlist_entries() if entry.get("track")]
    for entry in tracked_entries:
        search_payload = search_keyword_candidates(entry["title"], use_sample_data=use_sample_data)
        match = next(
            (product for product in search_payload["products"] if product.get("product_id") == entry["product_id"]),
            None,
        )
        if match is None and search_payload["products"]:
            match = search_payload["products"][0]
        if match is None:
            continue
        record_watchlist_snapshot(
            entry["product_id"],
            sold_count=safe_int(match.get("sold_count")),
            review_count=safe_int(match.get("review_count")),
            price=safe_float(match.get("price")),
            score=safe_float(match.get("score")),
        )
        refreshed += 1

    return {"tracked_entries": len(tracked_entries), "refreshed_entries": refreshed}


if __name__ == "__main__":
    run_discovery()
