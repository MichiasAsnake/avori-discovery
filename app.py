from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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
from tikhub_client import has_live_api_access, request_tikhub_json


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


def _status_payload() -> dict[str, Any]:
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


def _landing_page_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Avori Discovery</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #080b12;
      --panel: rgba(255, 255, 255, 0.08);
      --panel-strong: rgba(255, 255, 255, 0.14);
      --text: #f7f4ee;
      --muted: #b8b0a2;
      --accent: #d8b35f;
      --accent-2: #75d0b8;
      --danger: #ff8d8d;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(216, 179, 95, 0.25), transparent 32rem),
        radial-gradient(circle at bottom right, rgba(117, 208, 184, 0.18), transparent 34rem),
        var(--bg);
      color: var(--text);
    }
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 56px 0 44px;
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
      gap: 24px;
      align-items: stretch;
    }
    .card {
      border: 1px solid rgba(255, 255, 255, 0.14);
      background: linear-gradient(145deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0.045));
      border-radius: 28px;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.32);
      backdrop-filter: blur(18px);
    }
    .intro { padding: 42px; }
    .eyebrow {
      color: var(--accent-2);
      font-weight: 800;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      font-size: 0.78rem;
      margin: 0 0 18px;
    }
    h1 {
      margin: 0;
      max-width: 760px;
      font-size: clamp(2.6rem, 7vw, 5.8rem);
      line-height: 0.88;
      letter-spacing: -0.07em;
    }
    .lead {
      max-width: 680px;
      color: var(--muted);
      font-size: clamp(1rem, 2vw, 1.22rem);
      line-height: 1.65;
      margin: 28px 0 0;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 30px;
    }
    a.button, button {
      border: 0;
      border-radius: 999px;
      padding: 13px 18px;
      color: #15110a;
      background: var(--accent);
      font-weight: 800;
      text-decoration: none;
      cursor: pointer;
    }
    a.button.secondary {
      color: var(--text);
      background: var(--panel-strong);
      border: 1px solid rgba(255,255,255,0.16);
    }
    .console { padding: 28px; display: flex; flex-direction: column; gap: 16px; }
    .status-pill {
      align-self: flex-start;
      border: 1px solid rgba(117, 208, 184, 0.45);
      color: var(--accent-2);
      background: rgba(117, 208, 184, 0.10);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.9rem;
      font-weight: 800;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .metric {
      border-radius: 18px;
      background: rgba(0,0,0,0.24);
      border: 1px solid rgba(255,255,255,0.10);
      padding: 16px;
    }
    .metric span { display: block; color: var(--muted); font-size: 0.78rem; margin-bottom: 8px; }
    .metric strong { font-size: 1.1rem; }
    .search {
      margin-top: 24px;
      padding: 24px;
    }
    .search-row {
      display: flex;
      gap: 10px;
      margin-top: 18px;
    }
    input {
      width: 100%;
      color: var(--text);
      background: rgba(0,0,0,0.24);
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 999px;
      padding: 13px 16px;
      font: inherit;
      outline: none;
    }
    input:focus { border-color: var(--accent); }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 180px;
      max-height: 420px;
      overflow: auto;
      margin: 18px 0 0;
      padding: 18px;
      border-radius: 18px;
      background: rgba(0,0,0,0.36);
      border: 1px solid rgba(255,255,255,0.10);
      color: #e9dfcf;
    }
    h2 { margin: 0; font-size: 1.25rem; }
    .muted { color: var(--muted); }
    .endpoints {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 24px;
    }
    .endpoint {
      display: block;
      color: var(--text);
      text-decoration: none;
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.10);
    }
    .endpoint small { display: block; color: var(--muted); margin-top: 6px; }
    @media (max-width: 860px) {
      .hero, .endpoints { grid-template-columns: 1fr; }
      .intro { padding: 30px; }
      .search-row { flex-direction: column; }
    }
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <div class=\"card intro\">
        <p class=\"eyebrow\">TikTok Shop signal engine</p>
        <h1>Find products with real selling momentum.</h1>
        <p class=\"lead\">Avori Discovery scans TikTok Shop product signals, scores opportunities, and helps decide what to skip, watch, deep-dive, or test now.</p>
        <div class=\"actions\">
          <a class=\"button\" href=\"/docs\">Open API docs</a>
          <a class=\"button secondary\" href=\"/health\">Health check</a>
          <a class=\"button secondary\" href=\"/api\">JSON status</a>
        </div>
      </div>
      <aside class=\"card console\">
        <div class=\"status-pill\">API online</div>
        <div class=\"metric-grid\">
          <div class=\"metric\"><span>Runtime</span><strong>Vercel API</strong></div>
          <div class=\"metric\"><span>Dashboard</span><strong>Local Streamlit</strong></div>
          <div class=\"metric\"><span>Docs</span><strong>/docs</strong></div>
          <div class=\"metric\"><span>Data</span><strong>/tmp</strong></div>
        </div>
        <p class=\"muted\">Use this hosted surface for quick API checks. The richer Streamlit dashboard still runs locally.</p>
      </aside>
    </section>

    <section class=\"card search\">
      <h2>Quick product search</h2>
      <p class=\"muted\">Try a TikTok Shop query without opening Swagger.</p>
      <div class=\"search-row\">
        <input id=\"keyword\" value=\"travel bag\" aria-label=\"Product keyword\" />
        <button id=\"search\" type=\"button\">Search</button>
      </div>
      <pre id=\"results\">Click Search to call /products/search.</pre>
    </section>

    <nav class=\"endpoints\" aria-label=\"API endpoints\">
      <a class=\"endpoint\" href=\"/products/search?keyword=travel+bag\">Products search<small>GET /products/search</small></a>
      <a class=\"endpoint\" href=\"/watchlist\">Watchlist<small>GET /watchlist</small></a>
      <a class=\"endpoint\" href=\"/docs\">Swagger docs<small>GET /docs</small></a>
      <a class=\"endpoint\" href=\"/api\">API status<small>GET /api</small></a>
    </nav>
  </main>
  <script>
    const button = document.getElementById('search');
    const input = document.getElementById('keyword');
    const output = document.getElementById('results');

    async function runSearch() {
      const keyword = input.value.trim() || 'travel bag';
      output.textContent = `Searching for "${keyword}"...`;
      try {
        const response = await fetch(`/products/search?keyword=${encodeURIComponent(keyword)}`);
        const payload = await response.json();
        output.textContent = JSON.stringify(payload, null, 2);
      } catch (error) {
        output.textContent = `Search failed: ${error.message}`;
      }
    }

    button.addEventListener('click', runSearch);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') runSearch();
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return _landing_page_html()


@app.get("/api")
def api_status():
    return _status_payload()


@app.get("/health")
def health():
    tikhub_status: dict[str, Any] = {
        "has_api_key": has_live_api_access(),
        "reachable": False,
        "status_code": None,
    }
    if tikhub_status["has_api_key"]:
        try:
            status_code, _ = request_tikhub_json(
                "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
                {"search_word": "travel", "lang": "en-US", "region": "US"},
                timeout=8.0,
            )
            tikhub_status["status_code"] = status_code
            tikhub_status["reachable"] = status_code == 200
        except Exception as exc:
            tikhub_status["error"] = str(exc)

    return {
        "status": "ok",
        "data_dir": str(OUTPUT_DIR),
        "vercel": bool(os.getenv("VERCEL")),
        "tikhub": tikhub_status,
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
