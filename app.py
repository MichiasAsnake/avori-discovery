from __future__ import annotations

import json
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from agent import add_to_watchlist, get_product_detail, get_watchlist, remove_from_watchlist, run_discovery, search_products
from config import OUTPUT_DIR


app = FastAPI(
    title="Avori Discovery API",
    version="1.0.0",
    summary="Vercel-ready API wrapper for the Avori discovery workflow.",
)


class WatchlistEntryRequest(BaseModel):
    product_id: str
    title: str
    reason: str = "Interesting candidate for Avori."


def _parse_json_payload(raw_payload: str) -> dict[str, Any]:
    return json.loads(raw_payload)


@app.get("/")
def index():
    return {
        "name": "Avori Discovery API",
        "status": "ok",
        "vercel_ready": True,
        "streamlit_dashboard": "local-only",
        "docs_path": "/docs",
        "health_path": "/health",
        "data_dir": str(OUTPUT_DIR),
        "vercel": bool(os.getenv("VERCEL")),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "data_dir": str(OUTPUT_DIR),
        "vercel": bool(os.getenv("VERCEL")),
    }


@app.post("/discovery/run")
def discovery_run():
    return _parse_json_payload(run_discovery())


@app.get("/products/search")
def products_search(keyword: str):
    return _parse_json_payload(search_products(keyword))


@app.get("/products/{product_id}")
def products_detail(product_id: str):
    return _parse_json_payload(get_product_detail(product_id))


@app.get("/watchlist")
def watchlist_list():
    return _parse_json_payload(get_watchlist())


@app.post("/watchlist")
def watchlist_add(entry: WatchlistEntryRequest):
    return _parse_json_payload(add_to_watchlist(entry.product_id, entry.title, entry.reason))


@app.delete("/watchlist/{product_id}")
def watchlist_delete(product_id: str):
    return _parse_json_payload(remove_from_watchlist(product_id))
