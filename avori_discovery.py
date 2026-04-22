from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path

from config import LANG, MAX_KEYWORDS, OUTPUT_DIR, REGION, SEARCH_COUNT, SEED_TERMS, SELLER_IDS, ensure_output_dir
from endpoints.detail import fetch_product_detail, fetch_seller_products_list
from endpoints.search import fetch_search_products_list, fetch_search_word_suggestion
from output import build_daily_brief, write_daily_brief, write_results_json
from scorer import rank_products
from tikhub_client import (
    SAMPLE_ENDPOINT_AUDIT,
    SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD,
    SAMPLE_PRODUCTS,
    SAMPLE_SEARCH_PRODUCTS_PAYLOAD,
    SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD,
    audit_tikhub_endpoints,
)


def _normalize_shop_product(product, source_endpoint):
    image = product.get("image") or {}
    price_info = product.get("product_price_info") or {}
    rate_info = product.get("rate_info") or {}
    sold_info = product.get("sold_info") or {}
    seller_info = product.get("seller_info") or {}

    price_text = price_info.get("sale_price_format") or price_info.get("sale_price_decimal") or "0"
    try:
        price = float(price_text)
    except (TypeError, ValueError):
        price = 0.0

    return {
        "product_id": str(product.get("product_id") or ""),
        "title": product.get("title") or "Untitled",
        "price": price,
        "currency": price_info.get("currency_name") or "USD",
        "sold_count": int(sold_info.get("sold_count") or 0),
        "review_count": int(rate_info.get("review_count") or 0),
        "rating": float(rate_info.get("score") or 0),
        "seller_id": str(seller_info.get("seller_id") or ""),
        "seller_name": seller_info.get("shop_name") or "unknown",
        "image_url": (image.get("url_list") or [None])[0],
        "seo_url": product.get("seo_url"),
        "source_endpoint": source_endpoint,
        "category_names": [],
    }


def _v3_product_component(detail_payload):
    components = (((detail_payload.get("data") or {}).get("product_data") or {}).get("page_config") or {}).get("components_map") or []
    return next((component for component in components if component.get("component_name") == "product_info"), {})


def _v3_related_videos_component(detail_payload):
    components = (((detail_payload.get("data") or {}).get("product_data") or {}).get("page_config") or {}).get("components_map") or []
    return next((component for component in components if component.get("component_name") == "related_videos"), {})


def _extract_category_names(detail_payload, detail_endpoint):
    if detail_endpoint == "product_detail_v3":
        category_info = ((_v3_product_component(detail_payload).get("component_data") or {}).get("category_info")) or {}
        categories = category_info.get("recommended_categories") or []
        names = []
        for entry in categories:
            category_name = entry.get("category_name_en") or entry.get("category_name")
            if category_name:
                names.append(category_name)
        return names

    categories = (
        ((detail_payload.get("data") or {}).get("data") or {}).get("global_data", {}).get("product_info", {}).get("categories")
        or []
    )
    return [entry.get("category_name") for entry in categories if entry.get("category_name")]


def _extract_related_video_count(component_data):
    if isinstance(component_data, list):
        return len(component_data)
    if not isinstance(component_data, dict):
        return 0
    for key in ("related_videos", "videos", "video_list", "items"):
        value = component_data.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def _extract_detail_bonus_signals(detail_payload, detail_endpoint):
    if detail_endpoint != "product_detail_v3":
        return {}

    component_data = (_v3_product_component(detail_payload).get("component_data") or {})
    shop_info = component_data.get("shop_info") or {}
    shop_performance = component_data.get("shop_performance") or []
    related_component_data = (_v3_related_videos_component(detail_payload).get("component_data") or {})

    signals = {
        "related_video_count": _extract_related_video_count(related_component_data),
        "shop_performance_count": len(shop_performance) if isinstance(shop_performance, list) else 0,
        "shop_review_count": int(shop_info.get("review_count") or 0),
        "shop_follower_count": int(shop_info.get("followers_count") or 0),
        "shop_on_sell_product_count": int(shop_info.get("on_sell_product_count") or 0),
    }
    return {key: value for key, value in signals.items() if value}


def _extract_search_products(payload, search_endpoint):
    data = ((payload.get("data") or {}).get("data")) or {}
    return data.get("products") or []


def _extract_suggested_keywords(payload):
    data = ((payload.get("data") or {}).get("data")) or []
    if not isinstance(data, list):
        return []
    return [keyword.strip() for keyword in data if isinstance(keyword, str) and keyword.strip()]


def _discover_keywords(seed_terms, use_sample_data=False):
    discovered_keywords = []
    seen_keywords = set()

    for seed_term in seed_terms:
        if len(discovered_keywords) >= MAX_KEYWORDS:
            break
        if use_sample_data:
            payload = deepcopy(SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD)
        else:
            payload = fetch_search_word_suggestion(seed_term, lang=f"{LANG}-{REGION}", region=REGION)

        for keyword in _extract_suggested_keywords(payload):
            if keyword in seen_keywords:
                continue
            seen_keywords.add(keyword)
            discovered_keywords.append(keyword)
            if len(discovered_keywords) >= MAX_KEYWORDS:
                break

    return discovered_keywords


def _collect_keyword_products(keywords, search_endpoint, use_sample_data=False):
    products_by_id = {}
    keyword_product_counts = {}

    for keyword in keywords:
        if use_sample_data:
            payload = deepcopy(SAMPLE_SEARCH_PRODUCTS_PAYLOAD)
        else:
            payload = fetch_search_products_list(keyword, offset=0, page_token="", region=REGION)

        search_products = _extract_search_products(payload, search_endpoint)
        keyword_product_counts[keyword] = len(search_products)
        for product in search_products:
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
        seller_products = (((payload.get("data") or {}).get("data") or {}).get("products")) or []
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


def _enrich_products_with_detail(products, use_sample_data=False):
    enriched = []
    for product in products:
        product_copy = deepcopy(product)
        if use_sample_data:
            detail_endpoint, detail_payload = "product_detail_v3", SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD
        else:
            detail_endpoint, detail_payload = fetch_product_detail(product_copy["product_id"])
        product_copy["category_names"] = _extract_category_names(detail_payload, detail_endpoint)
        product_copy.update(_extract_detail_bonus_signals(detail_payload, detail_endpoint))
        product_copy["detail_endpoint"] = detail_endpoint
        enriched.append(product_copy)
    return enriched


def run_discovery(
    output_dir: Path | None = None,
    run_date: date | None = None,
    use_sample_data: bool = False,
    seller_fallback: bool = True,
):
    active_date = run_date or date.today()
    resolved_output_dir = ensure_output_dir(output_dir or OUTPUT_DIR)

    endpoint_audit = audit_tikhub_endpoints(use_sample_data=use_sample_data)
    usable_endpoints = {entry["name"] for entry in endpoint_audit if entry.get("usable")}
    search_bridge_endpoint = "search_products_list" if "search_products_list" in usable_endpoints else None

    discovered_keywords = []
    keyword_product_counts = {}
    products = []
    fallback_seller_product_counts = {}
    if search_bridge_endpoint and "search_word_suggestion" in usable_endpoints:
        discovered_keywords = _discover_keywords(SEED_TERMS, use_sample_data=use_sample_data)
    if search_bridge_endpoint and discovered_keywords:
        products, keyword_product_counts = _collect_keyword_products(
            discovered_keywords,
            search_bridge_endpoint,
            use_sample_data=use_sample_data,
        )

    if seller_fallback and not products:
        products, fallback_seller_product_counts = _collect_fallback_seller_products(
            SELLER_IDS,
            use_sample_data=use_sample_data or "seller_products_list" not in usable_endpoints,
        )

    enriched_products = _enrich_products_with_detail(
        products,
        use_sample_data=use_sample_data or "product_detail" not in usable_endpoints,
    )
    ranked_products = rank_products(enriched_products)

    results_payload = {
        "run_date": active_date.isoformat(),
        "endpoint_audit": endpoint_audit if endpoint_audit else deepcopy(SAMPLE_ENDPOINT_AUDIT),
        "search_bridge_endpoint": search_bridge_endpoint,
        "seed_terms": SEED_TERMS,
        "discovered_keywords": discovered_keywords,
        "keyword_product_counts": keyword_product_counts,
        "fallback_seller_product_counts": fallback_seller_product_counts,
        "seller_ids": SELLER_IDS,
        "products": ranked_products,
    }

    brief_text = build_daily_brief(results_payload, active_date)
    results_path = write_results_json(results_payload, resolved_output_dir, active_date)
    brief_path = write_daily_brief(brief_text, resolved_output_dir)
    print(brief_text)
    return {
        "results_payload": results_payload,
        "ranked_products": ranked_products,
        "results_path": results_path,
        "brief_path": brief_path,
    }


if __name__ == "__main__":
    run_discovery()
