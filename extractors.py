from __future__ import annotations

from utils import dig, safe_int, unique_strings


def v3_product_component(detail_payload):
    components = dig(detail_payload, "data", "product_data", "page_config", "components_map", default=[]) or []
    return next((component for component in components if component.get("component_name") == "product_info"), {})


def v3_related_videos_component(detail_payload):
    components = dig(detail_payload, "data", "product_data", "page_config", "components_map", default=[]) or []
    return next((component for component in components if component.get("component_name") == "related_videos"), {})


def extract_category_names(detail_payload, detail_endpoint):
    if detail_endpoint == "product_detail_v3":
        categories = dig(
            v3_product_component(detail_payload),
            "component_data",
            "category_info",
            "recommended_categories",
            default=[],
        ) or []
        names = []
        for entry in categories:
            category_name = entry.get("category_name_en") or entry.get("category_name")
            if category_name:
                names.append(category_name)
        return names

    categories = dig(detail_payload, "data", "data", "global_data", "product_info", "categories", default=[]) or []
    return [entry.get("category_name") for entry in categories if entry.get("category_name")]


def extract_related_video_count(component_data):
    if isinstance(component_data, list):
        return len(component_data)
    if not isinstance(component_data, dict):
        return 0
    for key in ("related_videos", "videos", "video_list", "items"):
        value = component_data.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def extract_related_creator_ids(detail_payload, detail_endpoint):
    if detail_endpoint != "product_detail_v3":
        return []
    component_data = (v3_related_videos_component(detail_payload).get("component_data") or {})
    entries = []
    if isinstance(component_data, list):
        entries = component_data
    elif isinstance(component_data, dict):
        for key in ("related_videos", "videos", "video_list", "items"):
            value = component_data.get(key)
            if isinstance(value, list):
                entries = value
                break

    creator_ids = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("creator_id", "author_id", "kol_id", "uid"):
            if entry.get(key):
                creator_ids.append(str(entry[key]))
    return unique_strings(creator_ids)


def count_matching_showcase_entries(showcase_payload, product_id: str) -> int:
    data = dig(showcase_payload, "data", "data", default={}) or {}
    for key in ("products", "product_list", "items"):
        entries = data.get(key)
        if isinstance(entries, list):
            return sum(1 for entry in entries if str(entry.get("product_id") or "") == product_id)
    return 0


def extract_detail_bonus_signals(detail_payload, detail_endpoint):
    if detail_endpoint != "product_detail_v3":
        return {}

    component_data = (v3_product_component(detail_payload).get("component_data") or {})
    shop_info = component_data.get("shop_info") or {}
    shop_performance = component_data.get("shop_performance") or []
    related_component_data = (v3_related_videos_component(detail_payload).get("component_data") or {})

    signals = {
        "related_video_count": extract_related_video_count(related_component_data),
        "shop_performance_count": len(shop_performance) if isinstance(shop_performance, list) else 0,
        "shop_review_count": safe_int(shop_info.get("review_count")),
        "shop_follower_count": safe_int(shop_info.get("followers_count")),
        "shop_on_sell_product_count": safe_int(shop_info.get("on_sell_product_count")),
    }
    return {key: value for key, value in signals.items() if value}


def extract_review_summary(detail_payload, detail_endpoint):
    if detail_endpoint == "product_detail_v3":
        product_info = dig(v3_product_component(detail_payload), "component_data", "product_info", default={}) or {}
        review_model = product_info.get("review_model")
        if review_model:
            return review_model
        return dig(v3_product_component(detail_payload), "component_data", "reviews_info", default={}) or {}

    return dig(detail_payload, "data", "data", "global_data", "product_info", "review_model", default={}) or {}
