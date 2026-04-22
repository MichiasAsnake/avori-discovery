from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from agent import (
    add_to_watchlist,
    get_product_detail,
    get_watchlist,
    refresh_watchlist_tracking,
    remove_from_watchlist,
    search_products,
)
from avori_discovery import run_discovery as run_canonical_discovery
from config import OUTPUT_DIR
from storage import create_discovery_job, get_discovery_job, update_discovery_job


app = FastAPI(
    title="Avori Discovery API",
    version="1.1.0",
    summary="Vercel-ready API wrapper for the Avori discovery workflow.",
)


class WatchlistEntryRequest(BaseModel):
    product_id: str
    title: str
    reason: str = "Interesting candidate for Avori."
    track: bool = False
    score: float | None = None
    sold_count: int | None = None
    review_count: int | None = None
    price: float | None = None


def _parse_json_payload(raw_payload: str) -> dict[str, Any]:
    return json.loads(raw_payload)


def _run_discovery_job(job_id: str) -> None:
    update_discovery_job(job_id, status="running")
    try:
        result = run_canonical_discovery(output_dir=OUTPUT_DIR)
        payload = {
            "candidate_count": len(result["results_payload"]["products"]),
            "results_path": str(result["results_path"]),
            "brief_path": str(result["brief_path"]),
            **result["results_payload"],
        }
        update_discovery_job(job_id, status="completed", results_path=result["results_path"], payload=payload)
    except Exception as exc:
        update_discovery_job(job_id, status="failed", error=str(exc))


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


@app.post("/discovery/run", status_code=202)
def discovery_run(background_tasks: BackgroundTasks):
    job_id = uuid4().hex
    job = create_discovery_job(job_id)
    background_tasks.add_task(_run_discovery_job, job_id)
    return job


@app.get("/discovery/jobs/{job_id}")
def discovery_job_status(job_id: str):
    job = get_discovery_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="discovery job not found")
    return job


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
    return _parse_json_payload(
        add_to_watchlist(
            entry.product_id,
            entry.title,
            entry.reason,
            entry.track,
            entry.score,
            entry.sold_count,
            entry.review_count,
            entry.price,
        )
    )


@app.post("/watchlist/refresh")
def watchlist_refresh():
    return _parse_json_payload(refresh_watchlist_tracking())


@app.delete("/watchlist/{product_id}")
def watchlist_delete(product_id: str):
    return _parse_json_payload(remove_from_watchlist(product_id))
