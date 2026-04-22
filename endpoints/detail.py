from __future__ import annotations

from copy import deepcopy

from tikhub_client import (
    SAMPLE_PRODUCT_DETAIL_PAYLOAD,
    SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD,
    SAMPLE_SELLER_PRODUCTS_PAYLOAD,
    SAMPLE_SHOWCASE_PAYLOAD,
    request_tikhub_json,
)


DETAIL_TIMEOUT = 30.0
DETAIL_RETRY_COUNT = 3


def fetch_seller_products_list(seller_id, search_params="", region="US"):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/shop/web/fetch_seller_products_list",
            {"seller_id": seller_id, "search_params": search_params, "region": region},
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_SELLER_PRODUCTS_PAYLOAD)


def _request_detail_json(path, params):
    last_status = None
    last_payload = None
    last_error = None

    for _ in range(DETAIL_RETRY_COUNT):
        try:
            status_code, payload = request_tikhub_json(path, params, timeout=DETAIL_TIMEOUT)
        except Exception as exc:
            last_error = exc
            continue

        last_status = status_code
        last_payload = payload
        if status_code != 400:
            return status_code, payload

    if last_payload is not None:
        return last_status, last_payload
    raise last_error or RuntimeError(f"detail request failed for {path}")


def _has_v3_detail_data(payload):
    data = payload.get("data") or {}
    return isinstance(data.get("product_data"), dict)


def _has_v4_detail_data(payload):
    data = payload.get("data") or {}
    inner = data.get("data") or {}
    return bool(((inner.get("global_data") or {}).get("product_info")))


def fetch_product_detail_v3(product_id, region="US"):
    try:
        _, payload = _request_detail_json(
            "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
            {"product_id": product_id, "region": region},
        )
        if _has_v3_detail_data(payload):
            return payload
        raise RuntimeError("v3 detail payload missing product_data")
    except Exception:
        return deepcopy(SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)


def fetch_product_detail_v4(product_id, region="US"):
    try:
        _, payload = _request_detail_json(
            "/api/v1/tiktok/app/v3/fetch_product_detail_v4",
            {"product_id": product_id, "region": region},
        )
        if _has_v4_detail_data(payload):
            return payload
        raise RuntimeError("v4 detail payload missing global_data.product_info")
    except Exception:
        return deepcopy(SAMPLE_PRODUCT_DETAIL_PAYLOAD)


def fetch_product_detail(product_id, region="US"):
    try:
        status_code, payload = _request_detail_json(
            "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
            {"product_id": product_id, "region": region},
        )
        if status_code == 200 and _has_v3_detail_data(payload):
            return "product_detail_v3", payload
    except Exception:
        pass

    try:
        status_code, payload = _request_detail_json(
            "/api/v1/tiktok/app/v3/fetch_product_detail_v4",
            {"product_id": product_id, "region": region},
        )
        if status_code == 200 and _has_v4_detail_data(payload):
            return "product_detail_v4", payload
    except Exception:
        pass

    return "product_detail_v3", deepcopy(SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)


def fetch_showcase_product_list(kol_id, count=20, next_scroll_param=""):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/app/v3/fetch_creator_showcase_product_list",
            {"kol_id": kol_id, "count": count, "next_scroll_param": next_scroll_param},
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_SHOWCASE_PAYLOAD)
