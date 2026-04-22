from __future__ import annotations

from copy import deepcopy

from tikhub_client import SAMPLE_TOP_PRODUCTS_PAYLOAD, request_tikhub_json


def fetch_top_products_list(
    last=7,
    page=1,
    limit=20,
    country_code="US",
    first_ecom_category_id="",
    ecom_type="l3",
    period_type="last",
    order_by="post",
    order_type="desc",
):
    try:
        _, payload = request_tikhub_json(
            "/api/v1/tiktok/ads/get_top_products",
            {
                "last": last,
                "page": page,
                "limit": limit,
                "country_code": country_code,
                "first_ecom_category_id": first_ecom_category_id,
                "ecom_type": ecom_type,
                "period_type": period_type,
                "order_by": order_by,
                "order_type": order_type,
            },
        )
        return payload
    except Exception:
        return deepcopy(SAMPLE_TOP_PRODUCTS_PAYLOAD)
