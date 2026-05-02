from __future__ import annotations

import json
from datetime import date

from agents import Agent, Runner, SQLiteSession, function_tool

from ai_judge import analyze_product, reject_non_finite_json_constant
from avori_discovery import (
    refresh_tracked_watchlist,
    run_discovery as run_canonical_discovery,
    search_keyword_candidates,
)
from config import AGENT_MODEL, OUTPUT_DIR, REGION
from endpoints.detail import fetch_product_detail
from extractors import extract_category_names, extract_detail_bonus_signals, extract_review_summary
from storage import list_watchlist_entries, record_watchlist_snapshot, remove_watchlist_entry, upsert_watchlist_entry


CHAT_SESSION_DB_PATH = OUTPUT_DIR / "agent_sessions.sqlite3"


def _create_chat_session(session_id: str):
    CHAT_SESSION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(session_id, db_path=CHAT_SESSION_DB_PATH)


def run_discovery() -> str:
    """Run the canonical discovery workflow and return ranked candidates plus artifact paths."""
    result = run_canonical_discovery(output_dir=OUTPUT_DIR, run_date=date.today())
    payload = {
        "candidate_count": len(result["results_payload"]["products"]),
        "results_path": str(result["results_path"]),
        "brief_path": str(result["brief_path"]),
        **result["results_payload"],
    }
    return json.dumps(payload, indent=2)


def get_product_detail(product_id: str) -> str:
    """Get full detail for a specific product including category, reviews, and shop performance."""
    detail_endpoint, detail_payload = fetch_product_detail(product_id, region=REGION)
    payload = {
        "product_id": product_id,
        "detail_endpoint": detail_endpoint,
        "category_names": extract_category_names(detail_payload, detail_endpoint),
        "review_summary": extract_review_summary(detail_payload, detail_endpoint),
        "supplementary_signals": extract_detail_bonus_signals(detail_payload, detail_endpoint),
    }
    return json.dumps(payload, indent=2)


def add_to_watchlist(
    product_id: str,
    title: str,
    reason: str,
    track: bool = False,
    score: float | None = None,
    sold_count: int | None = None,
    review_count: int | None = None,
    price: float | None = None,
) -> str:
    """Save a product to the Avori watchlist with a note and optional tracking."""
    entry = upsert_watchlist_entry(product_id, title, reason, tracked=track, score=score)
    if any(value is not None for value in (score, sold_count, review_count, price)):
        record_watchlist_snapshot(
            product_id,
            sold_count=sold_count,
            review_count=review_count,
            price=price,
            score=score,
        )
    return json.dumps({"status": "saved", "entry": entry}, indent=2)


def get_watchlist() -> str:
    """Return all products currently on the watchlist with tracking metadata."""
    return json.dumps({"watchlist": list_watchlist_entries()}, indent=2)


def remove_from_watchlist(product_id: str) -> str:
    """Remove a product from the watchlist."""
    status = "removed" if remove_watchlist_entry(product_id) else "not_found"
    return json.dumps({"status": status, "product_id": product_id}, indent=2)


def search_products(keyword: str) -> str:
    """Search TikTok Shop for products by keyword and return enriched scored results."""
    response = search_keyword_candidates(keyword)
    return json.dumps(response, indent=2)


def refresh_watchlist_tracking() -> str:
    """Refresh tracked watchlist products and compute their weekly velocity."""
    return json.dumps(refresh_tracked_watchlist(), indent=2)


def analyze_product_candidate(product_json: str) -> str:
    """Return a structured product judgment memo for one product JSON payload."""
    try:
        product = json.loads(product_json, parse_constant=reject_non_finite_json_constant)
    except (json.JSONDecodeError, ValueError):
        return json.dumps({"error": "invalid_product_json"}, indent=2, allow_nan=False)
    if not isinstance(product, dict):
        return json.dumps({"error": "product_json_must_be_an_object"}, indent=2, allow_nan=False)
    return json.dumps(analyze_product(product), indent=2, allow_nan=False)


agent = Agent(
    name="TikTok Shop Product Intelligence Agent",
    model=AGENT_MODEL,
    instructions="""
You are a TikTok Shop product discovery and market intelligence agent. Your job
is to identify products with genuine sell-through momentum and help reason
through market opportunities.

You evaluate products on market signals first:
- Early window candidates: high sold_count with low review_count (sold > 1000,
  reviews < 30) means demand is building before the market catches on.
- Velocity products: fast-rising sales in a short window, especially with
  minimal ad spend.
- Content-driven opportunities: products where short-form video naturally
  demonstrates value (before/after, packing, organization, transformations).
- Saturation risk: high review counts, many established sellers, declining
  momentum despite high totals.

You have tools to run discovery, search products, get product detail, generate
structured product judgment memos, and manage a watchlist. You can also discuss
strategy, analyze trends, help with pricing decisions, and reason through market
opportunities without calling a tool.

Be direct and data-driven. When a product shows strong signal, highlight it.
When it shows risk, explain why. Your analysis should help someone decide
whether to act on a product, watch it, or move on.
""".strip(),
    tools=[
        function_tool(run_discovery),
        function_tool(get_product_detail),
        function_tool(search_products),
        function_tool(add_to_watchlist),
        function_tool(get_watchlist),
        function_tool(remove_from_watchlist),
        function_tool(refresh_watchlist_tracking),
        function_tool(analyze_product_candidate),
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
