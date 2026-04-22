from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urljoin

from config import TIKTOK_SHOP_BASE_URL


def dig(payload, *keys, default=None):
    current = payload
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
        if current is None:
            return default
    return current


def build_tiktok_shop_url(seo_url: str | dict | None) -> str:
    if isinstance(seo_url, dict):
        seo_url = seo_url.get("canonical_url") or seo_url.get("slug") or ""
    if not isinstance(seo_url, str) or not seo_url.strip():
        return ""
    if seo_url.startswith(("http://", "https://")):
        return seo_url
    return urljoin(f"{TIKTOK_SHOP_BASE_URL.rstrip('/')}/", seo_url.lstrip("/"))


def flatten_keys(payload, prefix: str = "", max_depth: int = 4) -> list[str]:
    if max_depth < 0:
        return []

    fields: set[str] = set()

    if isinstance(payload, dict):
        for key, value in payload.items():
            field_name = f"{prefix}.{key}" if prefix else str(key)
            fields.add(field_name)
            if isinstance(value, (dict, list)):
                fields.update(flatten_keys(value, field_name, max_depth - 1))
    elif isinstance(payload, list):
        for item in payload[:3]:
            fields.update(flatten_keys(item, prefix, max_depth - 1))

    return sorted(fields)


def compact_dict_rows(values: dict[str, object]) -> list[tuple[str, object]]:
    rows = []
    for key, value in values.items():
        if value in (None, "", [], {}):
            continue
        label = key.replace("_", " ").title()
        rows.append((label, value))
    return rows


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def unique_strings(values: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique
