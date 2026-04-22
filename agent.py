from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from agents import Agent, Runner, SQLiteSession, function_tool

from avori_discovery import (
    _extract_category_names,
    _extract_detail_bonus_signals,
    _extract_search_products,
    _extract_suggested_keywords,
    _normalize_shop_product,
)
from config import LANG, REGION, SEED_TERMS
from endpoints.detail import fetch_product_detail
from endpoints.search import fetch_search_products_list, fetch_search_word_suggestion
from scorer import rank_products


RESULT_LIMIT = 20
AGENT_SEED_TERM_LIMIT = 5
AGENT_KEYWORD_LIMIT = 10
WATCHLIST_PATH = Path(__file__).resolve().parent / "output" / "watchlist.json"
CHAT_SESSION_DB_PATH = Path(__file__).resolve().parent / "output" / "agent_sessions.sqlite3"


def _serialize_products(products, limit=RESULT_LIMIT):
    serialized = []
    for product in products[:limit]:
        serialized.append(
            {
                "product_id": product.get("product_id"),
                "title": product.get("title"),
                "price": product.get("price"),
                "currency": product.get("currency"),
                "sold_count": product.get("sold_count"),
                "review_count": product.get("review_count"),
                "score": product.get("score"),
                "seller_id": product.get("seller_id"),
                "seller_name": product.get("seller_name"),
                "source_endpoint": product.get("source_endpoint"),
                "early_window": product.get("early_window"),
                "seo_url": product.get("seo_url"),
                "discovered_keywords": product.get("discovered_keywords", []),
                "category_names": product.get("category_names", []),
                "supplementary_signals": product.get("supplementary_signals", {}),
            }
        )
    return serialized


def _load_watchlist():
    if not WATCHLIST_PATH.exists():
        return []
    try:
        payload = json.loads(WATCHLIST_PATH.read_text())
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _write_watchlist(entries):
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_PATH.write_text(json.dumps(entries, indent=2))


def _create_chat_session(session_id: str):
    CHAT_SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(session_id, db_path=CHAT_SESSION_DB_PATH)


def _cap_seller_dominance(products, limit=RESULT_LIMIT, max_per_seller=5):
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


def _extract_review_summary(detail_payload, detail_endpoint):
    if detail_endpoint == "product_detail_v3":
        components = (((detail_payload.get("data") or {}).get("product_data") or {}).get("page_config") or {}).get("components_map") or []
        product_component = next((component for component in components if component.get("component_name") == "product_info"), {})
        component_data = product_component.get("component_data") or {}
        product_info = component_data.get("product_info") or {}
        return product_info.get("review_model") or component_data.get("reviews_info") or {}

    data = ((detail_payload.get("data") or {}).get("data")) or {}
    return (((data.get("global_data") or {}).get("product_info") or {}).get("review_model")) or {}


def _discover_agent_keywords():
    discovered_keywords = []
    seen_keywords = set()

    for seed_term in SEED_TERMS[:AGENT_SEED_TERM_LIMIT]:
        payload = fetch_search_word_suggestion(seed_term, lang=f"{LANG}-{REGION}", region=REGION)
        for keyword in _extract_suggested_keywords(payload):
            if keyword in seen_keywords:
                continue
            seen_keywords.add(keyword)
            discovered_keywords.append(keyword)
            if len(discovered_keywords) >= AGENT_KEYWORD_LIMIT:
                return discovered_keywords

    return discovered_keywords


def _fetch_agent_products(keywords):
    products_by_id = {}

    for keyword in keywords:
        payload = fetch_search_products_list(keyword, offset=0, page_token="", region=REGION)
        raw_products = _extract_search_products(payload, "search_products_list")
        for product in raw_products:
            normalized = _normalize_shop_product(product, "search_products_list")
            product_id = normalized.get("product_id")
            if not product_id:
                continue
            if product_id not in products_by_id:
                normalized["discovered_keywords"] = [keyword]
                products_by_id[product_id] = normalized
            else:
                discovered_keywords = products_by_id[product_id].setdefault("discovered_keywords", [])
                if keyword not in discovered_keywords:
                    discovered_keywords.append(keyword)

    return list(products_by_id.values())


def run_discovery() -> str:
    """Run a fast keyword-driven discovery pass and return ranked candidates."""
    print("[1/3] Discovering keywords from seed terms...")
    discovered_keywords = _discover_agent_keywords()

    print(f"[2/3] Fetching products for {len(discovered_keywords)} keywords...")
    normalized_products = _fetch_agent_products(discovered_keywords)

    print(f"[3/3] Scoring {len(normalized_products)} candidates...")
    ranked_products = rank_products(normalized_products)
    ranked_products = _cap_seller_dominance(ranked_products, limit=RESULT_LIMIT, max_per_seller=5)

    print("Done. Top 20 results ready.")
    payload = {
        "candidate_count": len(ranked_products),
        "products": _serialize_products(ranked_products),
    }
    return json.dumps(payload, indent=2)


def get_product_detail(product_id: str) -> str:
    """Get full detail for a specific product including category, reviews, shop performance."""
    detail_endpoint, detail_payload = fetch_product_detail(product_id, region=REGION)
    payload = {
        "product_id": product_id,
        "detail_endpoint": detail_endpoint,
        "category_names": _extract_category_names(detail_payload, detail_endpoint),
        "review_summary": _extract_review_summary(detail_payload, detail_endpoint),
        "supplementary_signals": _extract_detail_bonus_signals(detail_payload, detail_endpoint),
    }
    return json.dumps(payload, indent=2)


def add_to_watchlist(product_id: str, title: str, reason: str) -> str:
    """Save a product to the Avori watchlist with a note on why it's interesting."""
    watchlist = [entry for entry in _load_watchlist() if entry.get("product_id") != product_id]
    entry = {
        "product_id": product_id,
        "title": title,
        "reason": reason,
        "added_at": date.today().isoformat(),
        "score": None,
    }
    watchlist.append(entry)
    _write_watchlist(watchlist)
    return json.dumps({"status": "saved", "entry": entry}, indent=2)


def get_watchlist() -> str:
    """Return all products currently on the watchlist with their notes and when they were added."""
    return json.dumps({"watchlist": _load_watchlist()}, indent=2)


def remove_from_watchlist(product_id: str) -> str:
    """Remove a product from the watchlist."""
    watchlist = _load_watchlist()
    filtered_watchlist = [entry for entry in watchlist if entry.get("product_id") != product_id]
    status = "removed" if len(filtered_watchlist) != len(watchlist) else "not_found"
    _write_watchlist(filtered_watchlist)
    return json.dumps({"status": status, "product_id": product_id}, indent=2)


def search_products(keyword: str) -> str:
    """Search TikTok Shop for products by keyword and return scored results."""
    payload = fetch_search_products_list(keyword, offset=0, page_token="", region=REGION)
    raw_products = _extract_search_products(payload, "search_products_list")
    normalized_products = [
        _normalize_shop_product(product, "search_products_list")
        for product in raw_products
        if product.get("product_id")
    ]
    ranked_products = rank_products(normalized_products)
    response = {
        "keyword": keyword,
        "result_count": len(ranked_products),
        "products": _serialize_products(ranked_products),
    }
    return json.dumps(response, indent=2)


agent = Agent(
    name="Avori Discovery Agent",
    model="gpt-4o",
    instructions="""
You are Avori's product discovery and strategy agent. You help find early-window
TikTok Shop products and think through product decisions for Avori, a travel
accessories and organized-living brand ($14-$30, TikTok Shop-first, dropship).

You have tools to run discovery, search products, get product detail, and manage
a watchlist. But you're also a thinking partner — you can discuss strategy,
analyze trends, help with pricing, and reason through product decisions even
without calling a tool.

Early window flag: sold_count > 1000 AND review_count < 30 = high priority.
Avori categories: travel bags, organizers, jewelry cases, desk organizers, tech accessories.
""".strip(),
    tools=[
        function_tool(run_discovery),
        function_tool(get_product_detail),
        function_tool(search_products),
        function_tool(add_to_watchlist),
        function_tool(get_watchlist),
        function_tool(remove_from_watchlist),
    ],
)


def chat_loop():
    print("Avori Agent ready. Type 'exit' to quit.\n")
    session = _create_chat_session("cli-chat")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        result = Runner.run_sync(agent, user_input, session=session)
        print(f"\nAgent: {result.final_output}\n")


if __name__ == "__main__":
    chat_loop()
