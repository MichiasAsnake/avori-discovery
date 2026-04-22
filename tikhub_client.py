from __future__ import annotations

from copy import deepcopy

import httpx

from config import TIKHUB_API_KEY


BASE_URL = "https://api.tikhub.io"

SAMPLE_PRODUCTS = [
    {
        "product_id": "1729001",
        "title": "Travel Hanging Toiletry Organizer",
        "price": 29.99,
        "currency": "USD",
        "sold_count": 2400,
        "review_count": 18,
        "rating": 4.8,
        "seller_id": "7495150558072178725",
        "seller_name": "Avori Demo Shop",
        "image_url": "https://example.com/travel-organizer.jpg",
        "source_endpoint": "seller_products_list",
        "category_names": ["Travel Accessories", "Organizer Bags"],
    },
    {
        "product_id": "1729002",
        "title": "Everyday Purse Organizer Insert",
        "price": 16.99,
        "currency": "USD",
        "sold_count": 1300,
        "review_count": 27,
        "rating": 4.7,
        "seller_id": "7495150558072178725",
        "seller_name": "Avori Demo Shop",
        "image_url": "https://example.com/purse-organizer.jpg",
        "source_endpoint": "seller_products_list",
        "category_names": ["Bag Organizers"],
    },
    {
        "product_id": "1729003",
        "title": "Compact Cosmetic Packing Cube",
        "price": 18.5,
        "currency": "USD",
        "sold_count": 860,
        "review_count": 14,
        "rating": 4.6,
        "seller_id": "7495150558072178725",
        "seller_name": "Avori Demo Shop",
        "image_url": "https://example.com/packing-cube.jpg",
        "source_endpoint": "seller_products_list",
        "category_names": ["Packing Organizers"],
    },
]

SAMPLE_LIVE_SEARCH_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/app/v3/fetch_live_search_result",
    "data": {
        "status_code": 0,
        "data": [
            {
                "type": 1,
                "lives": {
                    "author": {"nickname": "Host One", "uid": "7495150558072178725"},
                    "is_live_has_products": True,
                    "rawdata": '{"owner":{"id":"7495150558072178725","display_id":"avori-demo-shop"}}',
                },
            },
            {
                "type": 1,
                "lives": {
                    "author": {"nickname": "Host Two", "uid": "seller-live-two"},
                    "is_live_has_products": True,
                    "rawdata": '{"owner":{"display_id":"seller-live-two"}}',
                },
            },
            {
                "type": 1,
                "lives": {
                    "author": {"nickname": "Host Three", "uid": "author-only-three"},
                    "is_live_has_products": True,
                    "rawdata": '{"id":"room-3"}',
                },
            },
            {"type": 1, "lives": {"author": {"nickname": "Host Four", "uid": "no-commerce"}, "is_live_has_products": False}},
        ],
        "has_more": False,
        "cursor": 0,
    },
}

SAMPLE_SEARCH_WORD_SUGGESTION_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
    "data": {
        "code": 0,
        "message": "success",
        "data": [
            "travel organizer",
            "travel toiletry bag",
            "travel makeup bag",
            "travel bag organizer",
        ],
    },
}

SAMPLE_SEARCH_PRODUCTS_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/shop/web/fetch_search_products_list",
    "data": {
        "code": 0,
        "message": "Request successful. This request will incur a charge.",
        "data": {
            "products": [
                {
                    "product_id": "1729001",
                    "title": "Travel Hanging Toiletry Organizer",
                    "image": {"url_list": ["https://example.com/travel-organizer.jpg"]},
                    "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                    "rate_info": {"score": 4.8, "review_count": "18"},
                    "sold_info": {"sold_count": 2400},
                    "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                    "seo_url": "/travel-hanging-toiletry-organizer",
                    "product_marketing_info": {},
                    "sku_info": {},
                },
                {
                    "product_id": "1729002",
                    "title": "Everyday Purse Organizer Insert",
                    "image": {"url_list": ["https://example.com/purse-organizer.jpg"]},
                    "product_price_info": {"currency_name": "USD", "sale_price_format": "16.99"},
                    "rate_info": {"score": 4.7, "review_count": "27"},
                    "sold_info": {"sold_count": 1300},
                    "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                    "seo_url": "/everyday-purse-organizer-insert",
                    "product_marketing_info": {},
                    "sku_info": {},
                },
            ],
            "page_token": "",
            "has_more": False,
        },
    },
}

SAMPLE_SEARCH_PRODUCTS_PAYLOAD_V2 = {
    "code": 200,
    "router": "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
    "data": {
        "code": 0,
        "message": "Request successful. This request will incur a charge.",
        "data": {
            "component_data": {
                "products": [
                    {
                        "product_id": "1729001",
                        "title": "Travel Hanging Toiletry Organizer",
                        "image": {"url_list": ["https://example.com/travel-organizer.jpg"]},
                        "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                        "rate_info": {"score": 4.8, "review_count": "18"},
                        "sold_info": {"sold_count": 2400},
                        "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                        "seo_url": "/travel-hanging-toiletry-organizer",
                        "product_marketing_info": {},
                        "sku_info": {},
                    },
                    {
                        "product_id": "1729002",
                        "title": "Everyday Purse Organizer Insert",
                        "image": {"url_list": ["https://example.com/purse-organizer.jpg"]},
                        "product_price_info": {"currency_name": "USD", "sale_price_format": "16.99"},
                        "rate_info": {"score": 4.7, "review_count": "27"},
                        "sold_info": {"sold_count": 1300},
                        "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                        "seo_url": "/everyday-purse-organizer-insert",
                        "product_marketing_info": {},
                        "sku_info": {},
                    },
                    {
                        "product_id": "1729003",
                        "title": "Compact Cosmetic Packing Cube",
                        "image": {"url_list": ["https://example.com/packing-cube.jpg"]},
                        "product_price_info": {"currency_name": "USD", "sale_price_format": "18.50"},
                        "rate_info": {"score": 4.6, "review_count": "14"},
                        "sold_info": {"sold_count": 860},
                        "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                        "seo_url": "/compact-cosmetic-packing-cube",
                        "product_marketing_info": {},
                        "sku_info": {},
                    },
                ],
                "page_token": "",
                "has_more": False,
            }
        },
    },
}

SAMPLE_TOP_PRODUCTS_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/ads/get_top_products",
    "data": {"code": 50004, "msg": "no available es index"},
}

SAMPLE_SELLER_PRODUCTS_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/shop/web/fetch_seller_products_list",
    "data": {
        "code": 0,
        "message": "success",
        "data": {
            "products": [
                {
                    "product_id": "1729001",
                    "title": "Travel Hanging Toiletry Organizer",
                    "image": {"url_list": ["https://example.com/travel-organizer.jpg"]},
                    "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                    "rate_info": {"score": 4.8, "review_count": "18"},
                    "sold_info": {"sold_count": 2400},
                    "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                    "seo_url": "/travel-hanging-toiletry-organizer",
                },
                {
                    "product_id": "1729002",
                    "title": "Everyday Purse Organizer Insert",
                    "image": {"url_list": ["https://example.com/purse-organizer.jpg"]},
                    "product_price_info": {"currency_name": "USD", "sale_price_format": "16.99"},
                    "rate_info": {"score": 4.7, "review_count": "27"},
                    "sold_info": {"sold_count": 1300},
                    "seller_info": {"seller_id": "7495150558072178725", "shop_name": "Avori Demo Shop"},
                    "seo_url": "/everyday-purse-organizer-insert",
                },
            ],
            "has_more": False,
            "load_more_params": {},
        },
    },
}

SAMPLE_PRODUCT_DETAIL_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/app/v3/fetch_product_detail_v4",
    "data": {
        "code": 0,
        "message": "success",
        "data": {
            "global_fe_config": {"page_name": "product_detail"},
            "components_map": [],
            "global_data": {
                "product_info": {
                    "error_code": 0,
                    "categories": [
                        {"category_id": "603014", "category_name": "Travel Accessories"},
                        {"category_id": "834568", "category_name": "Organizer Bags"},
                    ],
                    "product_info": {"product_model": {"product_id": "1729001", "seller_id": "7495150558072178725"}},
                }
            },
            "global_api_data": {"nova_config": {}},
        },
    },
}

SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
    "data": {
        "product_data": {
            "page_config": {
                "components_map": [
                    {
                        "component_name": "product_info",
                        "component_data": {
                            "product_info": {
                                "product_model": {"product_id": "1729001", "seller_id": "7495150558072178725"}
                            },
                            "category_info": {
                                "recommended_categories": [
                                    {"category_id": "603014", "category_name": "Travel Accessories", "category_name_en": "travel-accessories"},
                                    {"category_id": "834568", "category_name": "Organizer Bags", "category_name_en": "organizer-bags"},
                                ]
                            },
                            "shop_info": {
                                "seller_id": "7495150558072178725",
                                "shop_name": "Avori Demo Shop",
                                "review_count": 18,
                                "followers_count": "1200",
                                "video_count": "18",
                                "on_sell_product_count": 9,
                                "store_sub_score": [{"title": "Shipping", "score": "4.8"}],
                            },
                            "shop_performance": [{"metric": "shipping"}],
                        },
                    },
                    {
                        "component_name": "related_videos",
                        "component_data": {
                            "videos": [{"video_id": "v1"}, {"video_id": "v2"}]
                        },
                    },
                ]
            }
        }
    },
}

SAMPLE_SHOWCASE_PAYLOAD = {
    "code": 200,
    "router": "/api/v1/tiktok/app/v3/fetch_creator_showcase_product_list",
    "data": {"code": 100000},
}

SAMPLE_ENDPOINT_AUDIT = [
    {
        "name": "search_word_suggestion",
        "requested_path": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
        "tested_path": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
        "status_code": 200,
        "outer_code": 200,
        "inner_code": 0,
        "available_fields": ["data"],
        "usable": True,
    },
    {
        "name": "search_products_list",
        "requested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list",
        "tested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list",
        "status_code": 200,
        "outer_code": 200,
        "inner_code": 0,
        "available_fields": [
            "products.product_id",
            "products.title",
            "products.image",
            "products.product_price_info",
            "products.rate_info",
            "products.sold_info",
            "products.seller_info",
            "products.seo_url",
        ],
        "usable": True,
    },
    {
        "name": "search_products_list_v2",
        "requested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
        "tested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
        "status_code": 200,
        "outer_code": 200,
        "inner_code": 0,
        "available_fields": [
            "products.product_id",
            "products.title",
            "products.image",
            "products.product_price_info",
            "products.rate_info",
            "products.sold_info",
            "products.seller_info",
            "products.seo_url",
        ],
        "usable": True,
    },
    {
        "name": "seller_products_list",
        "requested_path": "/api/v1/tiktok/shop/web/fetch_seller_products_list",
        "tested_path": "/api/v1/tiktok/shop/web/fetch_seller_products_list",
        "status_code": 200,
        "outer_code": 200,
        "inner_code": 0,
        "available_fields": [
            "products.product_id",
            "products.title",
            "products.image",
            "products.product_price_info",
            "products.rate_info",
            "products.sold_info",
            "products.seller_info",
            "products.seo_url",
        ],
        "usable": True,
    },
    {
        "name": "product_detail",
        "requested_path": "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
        "tested_path": "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
        "status_code": 200,
        "outer_code": 200,
        "inner_code": 0,
        "available_fields": ["product_data.page_config.components_map.product_info.category_info", "product_data.page_config.components_map.product_info.shop_info", "product_data.page_config.components_map.related_videos"],
        "usable": True,
    },
]

SAMPLE_LIVE_SIGNALS = [
    {
        "keyword": "travel organizer",
        "result_count": 4,
        "rooms_with_products": 3,
        "top_hosts": ["Host One", "Host Two"],
    }
]


def has_live_api_access() -> bool:
    return bool(TIKHUB_API_KEY)


def request_tikhub_json(path: str, params: dict | None = None, timeout: float = 35.0) -> tuple[int, dict]:
    response = httpx.get(
        f"{BASE_URL}{path}",
        params=params or {},
        headers={"Authorization": f"Bearer {TIKHUB_API_KEY}"},
        timeout=timeout,
    )
    return response.status_code, response.json()


def _available_fields(name: str, payload: dict) -> list[str]:
    data = payload.get("data")
    if name == "search_word_suggestion" and isinstance(data, dict):
        return ["data"]
    if name in {"search_products_list", "search_products_list_v2"} and isinstance(data, dict):
        return [
            "products.product_id",
            "products.title",
            "products.image",
            "products.product_price_info",
            "products.rate_info",
            "products.sold_info",
            "products.seller_info",
            "products.seo_url",
        ]
    if name == "seller_products_list" and isinstance(data, dict):
        return [
            "products.product_id",
            "products.title",
            "products.image",
            "products.product_price_info",
            "products.rate_info",
            "products.sold_info",
            "products.seller_info",
            "products.seo_url",
        ]
    if name == "product_detail" and isinstance(data, dict):
        return [
            "product_data.page_config.components_map.product_info.category_info",
            "product_data.page_config.components_map.product_info.shop_info",
            "product_data.page_config.components_map.related_videos",
        ]
    if isinstance(data, dict):
        return list(data.keys())[:10]
    return []


def _inner_code(name: str, payload: dict):
    data = payload.get("data")
    if name == "product_detail" and isinstance(data, dict):
        if isinstance(data.get("product_data"), dict):
            return 0
        return data.get("code")
    if isinstance(data, dict):
        return data.get("code")
    return None


def _normalize_keyword_suggest_payload(payload: dict) -> dict:
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


def _endpoint_definitions() -> list[dict]:
    return [
        {
            "name": "search_word_suggestion",
            "requested_path": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
            "tested_path": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
            "params": {"search_word": "travel", "lang": "en-US", "region": "US"},
        },
        {
            "name": "search_products_list",
            "requested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list",
            "tested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list",
            "params": {"search_word": "travel organizer", "offset": 0, "page_token": "", "region": "US"},
        },
        {
            "name": "search_products_list_v2",
            "requested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
            "tested_path": "/api/v1/tiktok/shop/web/fetch_search_products_list_v2",
            "params": {"search_word": "travel organizer", "offset": 0, "page_token": "", "region": "US"},
        },
        {
            "name": "seller_products_list",
            "requested_path": "/api/v1/tiktok/shop/web/fetch_seller_products_list",
            "tested_path": "/api/v1/tiktok/shop/web/fetch_seller_products_list",
            "params": {"seller_id": "7495150558072178725", "search_params": "", "region": "US"},
        },
        {
            "name": "product_detail",
            "requested_path": "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
            "tested_path": "/api/v1/tiktok/shop/web/fetch_product_detail_v3",
            "params": {"product_id": "1729385239712731370", "region": "US"},
        },
    ]


def audit_tikhub_endpoints(use_sample_data: bool = False) -> list[dict]:
    if use_sample_data or not has_live_api_access():
        return deepcopy(SAMPLE_ENDPOINT_AUDIT)

    audit = []
    for endpoint in _endpoint_definitions():
        status_code, payload = request_tikhub_json(endpoint["tested_path"], endpoint["params"])
        inner_code = _inner_code(endpoint["name"], payload)
        tested_path = endpoint["tested_path"]
        if endpoint["name"] == "search_word_suggestion" and not (status_code == 200 and inner_code == 0):
            fallback_path = "/api/v1/tiktok/web/fetch_search_keyword_suggest"
            fallback_params = {"keyword": endpoint["params"]["search_word"], "region": endpoint["params"]["region"]}
            fallback_status, fallback_payload = request_tikhub_json(fallback_path, fallback_params)
            normalized_payload = _normalize_keyword_suggest_payload(fallback_payload)
            fallback_inner = _inner_code(endpoint["name"], normalized_payload)
            if fallback_status == 200 and fallback_inner == 0:
                status_code, payload, inner_code, tested_path = fallback_status, normalized_payload, fallback_inner, fallback_path
        if endpoint["name"] == "product_detail" and not (status_code == 200 and inner_code == 0):
            fallback_path = "/api/v1/tiktok/app/v3/fetch_product_detail_v4"
            fallback_status, fallback_payload = request_tikhub_json(fallback_path, endpoint["params"], timeout=30.0)
            fallback_inner = _inner_code(endpoint["name"], fallback_payload)
            if fallback_status == 200 and fallback_inner == 0:
                status_code, payload, inner_code, tested_path = fallback_status, fallback_payload, fallback_inner, fallback_path
        usable = False
        if endpoint["name"] in {"search_word_suggestion", "search_products_list", "search_products_list_v2"}:
            usable = status_code == 200 and inner_code == 0
        elif endpoint["name"] in {"seller_products_list", "product_detail"}:
            usable = status_code == 200 and inner_code == 0
        audit.append(
            {
                "name": endpoint["name"],
                "requested_path": endpoint["requested_path"],
                "tested_path": tested_path,
                "status_code": status_code,
                "outer_code": payload.get("code"),
                "inner_code": inner_code,
                "available_fields": _available_fields(endpoint["name"], payload),
                "usable": usable,
            }
        )
    return audit
