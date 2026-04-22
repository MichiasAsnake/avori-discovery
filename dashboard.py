from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from agents import Runner

from agent import _create_chat_session
from agent import add_to_watchlist as agent_add_to_watchlist
from agent import agent as avori_agent
from agent import get_product_detail as agent_get_product_detail
from agent import get_watchlist as agent_get_watchlist
from agent import remove_from_watchlist as agent_remove_from_watchlist
from agent import run_discovery as agent_run_discovery
from agent import search_products as agent_search_products
from config import OUTPUT_DIR


RESULTS_STATE_KEY = "dashboard_results_payload"
SELECTED_PRODUCT_KEY = "dashboard_selected_product_id"
DETAIL_CACHE_KEY = "dashboard_detail_cache"
CHAT_MESSAGES_KEY = "dashboard_chat_messages"
CHAT_SESSION_KEY = "dashboard_chat_session"
WATCHLIST_STATE_KEY = "dashboard_watchlist"


def load_latest_results_file(output_dir: Path = OUTPUT_DIR):
    result_files = sorted(output_dir.glob("avori_results_*.json"), key=lambda path: path.stat().st_mtime)
    if not result_files:
        return None
    return json.loads(result_files[-1].read_text())


def apply_product_filters(products, price_range=(0.0, 50.0), min_sold_count=0, early_window_only=False):
    filtered = []
    min_price, max_price = price_range
    for product in products:
        price = float(product.get("price") or 0.0)
        sold_count = int(product.get("sold_count") or 0)
        early_window = bool(product.get("early_window"))
        if price < min_price or price > max_price:
            continue
        if sold_count < min_sold_count:
            continue
        if early_window_only and not early_window:
            continue
        filtered.append(product)
    return filtered


def build_stats_summary(products, discovered_keywords, keyword_product_counts):
    top_keyword = None
    if keyword_product_counts:
        top_keyword = max(keyword_product_counts.items(), key=lambda item: item[1])[0]
    return {
        "total_candidates": len(products),
        "early_window_count": sum(1 for product in products if product.get("early_window")),
        "keywords_discovered": len(discovered_keywords or []),
        "top_keyword": top_keyword or "n/a",
    }


def truncate_title(title: str, limit: int = 40) -> str:
    title = title or "Untitled"
    if len(title) <= limit:
        return title
    return f"{title[: limit - 3]}..."


def prepare_table_rows(products):
    rows = []
    for index, product in enumerate(products, start=1):
        discovered_keywords = product.get("discovered_keywords") or []
        rows.append(
            {
                "rank": index,
                "product_id": product.get("product_id"),
                "title": truncate_title(product.get("title", "Untitled")),
                "price": product.get("price"),
                "sold_count": product.get("sold_count", 0),
                "review_count": product.get("review_count", 0),
                "score": product.get("score", 0),
                "early_window": bool(product.get("early_window")),
                "keyword": ", ".join(discovered_keywords[:1]) if discovered_keywords else "",
                "seller": product.get("seller_name", "unknown"),
            }
        )
    return rows


def _tool_results_to_payload(tool_payload):
    results_path = tool_payload.get("results_path")
    if results_path:
        results_file = Path(results_path)
        if results_file.exists():
            return json.loads(results_file.read_text())
    return {
        "products": tool_payload.get("products", []),
        "discovered_keywords": [],
        "keyword_product_counts": {},
        "fallback_seller_product_counts": {},
        "search_bridge_endpoint": "search_products_list",
        "seed_terms": [],
    }


def _search_results_to_payload(tool_payload):
    keyword = tool_payload.get("keyword", "")
    result_count = tool_payload.get("result_count", 0)
    return {
        "products": tool_payload.get("products", []),
        "discovered_keywords": [keyword] if keyword else [],
        "keyword_product_counts": {keyword: result_count} if keyword else {},
        "fallback_seller_product_counts": {},
        "search_bridge_endpoint": "search_products_list",
        "seed_terms": [],
    }


def _seo_url_value(product):
    seo_url = product.get("seo_url")
    if isinstance(seo_url, dict):
        return seo_url.get("canonical_url") or seo_url.get("slug") or ""
    if isinstance(seo_url, str):
        return seo_url
    return ""


def _get_selected_product(products, selected_product_id):
    return next((product for product in products if product.get("product_id") == selected_product_id), None)


def _load_product_detail(product_id):
    return json.loads(agent_get_product_detail(product_id))


def load_watchlist():
    return json.loads(agent_get_watchlist()).get("watchlist", [])


def run_chat_turn(session, user_input: str):
    return Runner.run_sync(avori_agent, user_input, session=session).final_output


def create_dashboard_session():
    return _create_chat_session("streamlit-dashboard")


def _ensure_session_state():
    if RESULTS_STATE_KEY not in st.session_state:
        st.session_state[RESULTS_STATE_KEY] = load_latest_results_file() or {"products": []}
    if SELECTED_PRODUCT_KEY not in st.session_state:
        st.session_state[SELECTED_PRODUCT_KEY] = None
    if DETAIL_CACHE_KEY not in st.session_state:
        st.session_state[DETAIL_CACHE_KEY] = {}
    if CHAT_MESSAGES_KEY not in st.session_state:
        st.session_state[CHAT_MESSAGES_KEY] = []
    if CHAT_SESSION_KEY not in st.session_state:
        st.session_state[CHAT_SESSION_KEY] = create_dashboard_session()
    if WATCHLIST_STATE_KEY not in st.session_state:
        st.session_state[WATCHLIST_STATE_KEY] = load_watchlist()


def _refresh_watchlist():
    st.session_state[WATCHLIST_STATE_KEY] = load_watchlist()


def _run_discovery_action():
    tool_payload = json.loads(agent_run_discovery())
    st.session_state[RESULTS_STATE_KEY] = _tool_results_to_payload(tool_payload)
    st.session_state[SELECTED_PRODUCT_KEY] = None


def _run_keyword_search_action(keyword):
    tool_payload = json.loads(agent_search_products(keyword))
    st.session_state[RESULTS_STATE_KEY] = _search_results_to_payload(tool_payload)
    st.session_state[SELECTED_PRODUCT_KEY] = None


def _add_selected_product_to_watchlist(product, reason):
    if not product:
        return
    agent_add_to_watchlist(
        product.get("product_id", ""),
        product.get("title", "Untitled"),
        reason.strip() or "Interesting candidate for Avori.",
    )
    _refresh_watchlist()


def _remove_watchlist_item(product_id):
    agent_remove_from_watchlist(product_id)
    _refresh_watchlist()


def _send_chat_message(user_input: str):
    st.session_state[CHAT_MESSAGES_KEY].append({"role": "user", "content": user_input})
    reply = run_chat_turn(st.session_state[CHAT_SESSION_KEY], user_input)
    st.session_state[CHAT_MESSAGES_KEY].append({"role": "assistant", "content": reply})


def main():
    st.set_page_config(page_title="Avori Discovery Dashboard", layout="wide")
    _ensure_session_state()

    with st.sidebar:
        st.header("Controls")
        if st.button("Run Discovery", use_container_width=True):
            _run_discovery_action()

        keyword = st.text_input("Keyword Search", value="")
        if st.button("Search Keyword", use_container_width=True, disabled=not keyword.strip()):
            _run_keyword_search_action(keyword.strip())

        st.divider()
        price_range = st.slider("Price range", min_value=0.0, max_value=50.0, value=(0.0, 50.0), step=1.0)
        min_sold_count = st.number_input("Min sold count", min_value=0, value=0, step=10)
        early_window_only = st.toggle("Early window only", value=False)

        st.divider()
        st.header("Watchlist")
        watchlist = st.session_state[WATCHLIST_STATE_KEY]
        if not watchlist:
            st.caption("No products saved yet.")
        else:
            for entry in watchlist:
                with st.container(border=True):
                    st.markdown(f"**{entry.get('title', 'Untitled')}**")
                    st.caption(f"{entry.get('product_id')} • added {entry.get('added_at', 'n/a')}")
                    st.write(entry.get("reason", ""))
                    if st.button(
                        "Remove",
                        key=f"watchlist-remove-{entry.get('product_id')}",
                        use_container_width=True,
                    ):
                        _remove_watchlist_item(entry.get("product_id"))
                        st.rerun()

    results_payload = st.session_state[RESULTS_STATE_KEY]
    products = results_payload.get("products", [])
    discovered_keywords = results_payload.get("discovered_keywords", [])
    keyword_product_counts = results_payload.get("keyword_product_counts", {})

    filtered_products = apply_product_filters(
        products,
        price_range=price_range,
        min_sold_count=int(min_sold_count),
        early_window_only=early_window_only,
    )

    stats = build_stats_summary(filtered_products, discovered_keywords, keyword_product_counts)
    stat_columns = st.columns(4)
    stat_columns[0].metric("Total candidates", stats["total_candidates"])
    stat_columns[1].metric("Early window count", stats["early_window_count"])
    stat_columns[2].metric("Keywords discovered", stats["keywords_discovered"])
    stat_columns[3].metric("Top keyword", stats["top_keyword"])

    st.subheader("Ranked candidates")
    table_rows = prepare_table_rows(filtered_products)
    if table_rows:
        dataframe = pd.DataFrame(table_rows)

        def highlight_early_window(row):
            color = "background-color: #d9f2d9" if row["early_window"] else ""
            return [color for _ in row]

        event = st.dataframe(
            dataframe.style.apply(highlight_early_window, axis=1),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_order=["rank", "title", "price", "sold_count", "review_count", "score", "early_window", "keyword", "seller"],
        )
        selected_rows = getattr(getattr(event, "selection", None), "rows", []) or []
        if selected_rows:
            selected_row = table_rows[selected_rows[0]]
            st.session_state[SELECTED_PRODUCT_KEY] = selected_row["product_id"]
    else:
        st.info("No products match the current filters.")

    detail_column, chat_column = st.columns([1.05, 0.95], gap="large")

    with detail_column:
        st.subheader("Product detail")
        selected_product = _get_selected_product(filtered_products or products, st.session_state[SELECTED_PRODUCT_KEY])
        if selected_product is None:
            st.info("Select a product row to load detail.")
        else:
            detail_cache = st.session_state[DETAIL_CACHE_KEY]
            product_id = selected_product["product_id"]
            if product_id not in detail_cache:
                detail_cache[product_id] = _load_product_detail(product_id)
            detail_payload = detail_cache[product_id]

            st.markdown(f"### {selected_product.get('title', 'Untitled')}")
            detail_cols = st.columns(4)
            detail_cols[0].metric("Price", f"${float(selected_product.get('price') or 0):.2f}")
            detail_cols[1].metric("Sold", int(selected_product.get("sold_count") or 0))
            detail_cols[2].metric("Reviews", int(selected_product.get("review_count") or 0))
            detail_cols[3].metric("Shop", selected_product.get("seller_name") or "unknown")

            st.write("Categories:", ", ".join(detail_payload.get("category_names", [])) or "n/a")
            st.write("Supplementary signals:", detail_payload.get("supplementary_signals", {}))

            seo_url = _seo_url_value(selected_product)
            if seo_url:
                st.markdown(f"[TikTok Shop URL]({seo_url})")
            else:
                st.write("TikTok Shop URL: n/a")

            watch_reason = st.text_area(
                "Why save this?",
                value=f"Interesting {selected_product.get('seller_name', 'seller')} candidate for Avori.",
                key=f"watch-reason-{product_id}",
            )
            action_cols = st.columns(2)
            if action_cols[0].button("Add To Watchlist", use_container_width=True):
                _add_selected_product_to_watchlist(selected_product, watch_reason)
                st.success("Saved to watchlist.")
            if action_cols[1].button("Discuss In Chat", use_container_width=True):
                prompt = (
                    f"Assess this Avori candidate: {selected_product.get('title', 'Untitled')} | "
                    f"price={selected_product.get('price')} | sold={selected_product.get('sold_count')} | "
                    f"reviews={selected_product.get('review_count')} | seller={selected_product.get('seller_name')}."
                )
                _send_chat_message(prompt)
                st.rerun()

    with chat_column:
        st.subheader("Strategy chat")
        st.caption("Ask about trends, pricing, comparisons, or the selected product.")
        for message in st.session_state[CHAT_MESSAGES_KEY]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        chat_prompt = st.chat_input("Ask Avori's agent about products, pricing, or strategy")
        if chat_prompt:
            _send_chat_message(chat_prompt)
            st.rerun()


if __name__ == "__main__":
    main()
