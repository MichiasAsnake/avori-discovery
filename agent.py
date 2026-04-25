from __future__ import annotations

import json
from datetime import date

from agents import Agent, Runner, SQLiteSession, function_tool

from ai_judge import analyze_product, reject_non_finite_json_constant
from avori_discovery import (
    _extract_category_names,
    _extract_detail_bonus_signals,
    _extract_review_summary,
    refresh_tracked_watchlist,
    run_discovery as run_canonical_discovery,
    search_keyword_candidates,
)
from config import AGENT_MODEL, OUTPUT_DIR, REGION
from endpoints.detail import fetch_product_detail
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
        "category_names": _extract_category_names(detail_payload, detail_endpoint),
        "review_summary": _extract_review_summary(detail_payload, detail_endpoint),
        "supplementary_signals": _extract_detail_bonus_signals(detail_payload, detail_endpoint),
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
    name="Avori Discovery Agent",
    model=AGENT_MODEL,
    instructions="""
You are Avori's product discovery and strategy agent. You help find early-window
TikTok Shop products and think through product decisions for Avori, a travel
accessories and organized-living brand ($14-$30, TikTok Shop-first, dropship).

You have tools to run discovery, search products, get product detail, generate
structured product judgment memos, and manage a watchlist. But you're also a
thinking partner — you can discuss strategy, analyze trends, help with pricing,
and reason through product decisions even without calling a tool.

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
