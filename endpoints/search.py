from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from tikhub_client import (
    SAMPLE_LIVE_SEARCH_PAYLOAD,
    SAMPLE_SEARCH_PRODUCTS_PAYLOAD,
    SAMPLE_SEARCH_PRODUCTS_PAYLOAD_V2,
    SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD,
    request_tikhub_json,
    request_tikhub_json_async,
)


def _shop_suggestion_payload_usable(payload):
    data = payload.get("data") or {}
    return isinstance(data, dict) and data.get("code") == 0 and isinstance(data.get("data"), list)


def _normalize_web_keyword_suggest_payload(payload):
    data = payload.get("data") or {}
    suggestions = data.get("data") or []
    words = [entry.get("word", "").strip() for entry in suggestions if isinstance(entry, dict) and entry.get("word")]
    return {
        "code": payload.get("code", 200),
        "router": payload.get("router", "/api/v1/tiktok/web/fetch_search_keyword_suggest"),
        "data": {
            "code": 0 if data.get("status_code") == 0 else data.get("status_code"),
            "message": data.get("status_msg", ""),
            "data": words,
        },
    }


def fetch_live_search_result(keyword, offset=0, count=20, region="US"):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/app/v3/fetch_live_search_result",
            {"keyword": keyword, "offset": offset, "count": count, "region": region},
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_LIVE_SEARCH_PAYLOAD)


def fetch_search_word_suggestion(search_word, lang="en-US", region="US"):
    try:
        status_code, payload = request_tikhub_json(
            "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
            {"search_word": search_word, "lang": lang, "region": region},
        )
        if status_code == 200 and _shop_suggestion_payload_usable(payload):
            return payload

        fallback_status, fallback_payload = request_tikhub_json(
            "/api/v1/tiktok/web/fetch_search_keyword_suggest",
            {"keyword": search_word, "region": region},
        )
        if fallback_status == 200:
            normalized_payload = _normalize_web_keyword_suggest_payload(fallback_payload)
            if _shop_suggestion_payload_usable(normalized_payload):
                return normalized_payload
    except Exception:
        pass
    return deepcopy(SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD)


def fetch_search_products_list(search_word, offset=0, page_token="", region="US"):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/shop/web/fetch_search_products_list",
            {"search_word": search_word, "offset": offset, "page_token": page_token, "region": region},
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_SEARCH_PRODUCTS_PAYLOAD)


async def fetch_search_products_list_async(search_word, offset=0, page_token="", region="US", client=None):
    try:
        _, payload = await request_tikhub_json_async(
            "/api/v1/tiktok/shop/web/fetch_search_products_list",
            {"search_word": search_word, "offset": offset, "page_token": page_token, "region": region},
            client=client,
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_SEARCH_PRODUCTS_PAYLOAD)


def fetch_search_products_list_v2(search_word, offset=0, page_token="", region="US"):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
            {"search_word": search_word, "offset": offset, "page_token": page_token, "region": region},
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_SEARCH_PRODUCTS_PAYLOAD_V2)


async def fetch_search_word_suggestion_async(search_word, lang="en-US", region="US", client=None):
    try:
        status_code, payload = await request_tikhub_json_async(
            "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
            {"search_word": search_word, "lang": lang, "region": region},
            client=client,
        )
        if status_code == 200 and _shop_suggestion_payload_usable(payload):
            return payload

        fallback_status, fallback_payload = await request_tikhub_json_async(
            "/api/v1/tiktok/web/fetch_search_keyword_suggest",
            {"keyword": search_word, "region": region},
            client=client,
        )
        if fallback_status == 200:
            normalized_payload = _normalize_web_keyword_suggest_payload(fallback_payload)
            if _shop_suggestion_payload_usable(normalized_payload):
                return normalized_payload
    except Exception:
        pass
    return deepcopy(SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD)


def extract_search_pagination(payload: dict[str, Any]) -> tuple[bool, str]:
    data = ((payload.get("data") or {}).get("data")) or {}
    component_data = data.get("component_data") or {}
    source = component_data if isinstance(component_data, dict) else data
    return bool(source.get("has_more")), str(source.get("page_token") or "")


def extract_seller_ids_from_live_search(live_results):
    seller_ids = []
    seen = set()

    for item in live_results:
        live = item.get("lives") or {}
        has_goods = bool(live.get("is_live_has_products") or (live.get("room") or {}).get("has_commerce_goods"))
        if not has_goods:
            continue

        seller_id = None
        rawdata = live.get("rawdata")
        if rawdata:
            try:
                parsed = json.loads(rawdata)
                owner = parsed.get("owner") or {}
                seller_id = owner.get("id") or owner.get("display_id")
            except (TypeError, ValueError, json.JSONDecodeError):
                seller_id = None

        if not seller_id:
            seller_id = ((live.get("author") or {}).get("uid")) or None

        if seller_id:
            seller_id = str(seller_id)
            if seller_id not in seen:
                seen.add(seller_id)
                seller_ids.append(seller_id)

    return seller_ids
