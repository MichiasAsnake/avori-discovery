from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = Path("/tmp/avori-discovery") if os.getenv("VERCEL") else BASE_DIR / "output"
DATA_DIR = Path(os.getenv("AVORI_DATA_DIR", str(DEFAULT_DATA_DIR)))
OUTPUT_DIR = DATA_DIR
REGION = os.getenv("AVORI_REGION", "US")
LANG = os.getenv("AVORI_LANG", "en")
SEARCH_COUNT = int(os.getenv("AVORI_SEARCH_COUNT", "20"))
SEARCH_PAGE_COUNT = int(os.getenv("AVORI_SEARCH_PAGE_COUNT", "3"))
HOT_COUNT = int(os.getenv("AVORI_HOT_COUNT", "20"))
TIKHUB_API_KEY = os.getenv("TIKHUB_API_KEY", "").strip()
DISCOVERED_SELLER_LIMIT = int(os.getenv("AVORI_DISCOVERED_SELLER_LIMIT", "20"))
MAX_KEYWORDS = int(os.getenv("AVORI_MAX_KEYWORDS", "20"))
DETAIL_CONCURRENCY = int(os.getenv("AVORI_DETAIL_CONCURRENCY", "8"))
KEYWORD_CONCURRENCY = int(os.getenv("AVORI_KEYWORD_CONCURRENCY", "6"))
AGENT_MODEL = os.getenv("AVORI_AGENT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
DASHBOARD_PRICE_MAX = float(os.getenv("AVORI_DASHBOARD_PRICE_MAX", "200"))
TRACKING_GRADUATION_SOLD_COUNT = int(os.getenv("AVORI_TRACKING_GRADUATION_SOLD_COUNT", "5000"))
TIKTOK_SHOP_BASE_URL = os.getenv("AVORI_TIKTOK_SHOP_BASE_URL", "https://shop.tiktok.com")
SELLER_IDS = [
    seller_id.strip()
    for seller_id in os.getenv("AVORI_SELLER_IDS", "7495150558072178725").split(",")
    if seller_id.strip()
]
SEED_TERMS = [
    term.strip()
    for keyword in os.getenv(
        "AVORI_SEED_TERMS",
        "travel,organizer,bag,makeup,jewelry,desk,packing",
    ).split(",")
    if (term := keyword.strip())
]

SCORING_WEIGHTS = {
    "sold_count": float(os.getenv("AVORI_WEIGHT_SOLD_COUNT", "0.02")),
    "review_count": float(os.getenv("AVORI_WEIGHT_REVIEW_COUNT", "-0.7")),
    "rating": float(os.getenv("AVORI_WEIGHT_RATING", "8.0")),
    "creator_video_count": float(os.getenv("AVORI_WEIGHT_CREATOR_VIDEO_COUNT", "1.5")),
    "seller_catalog_count": float(os.getenv("AVORI_WEIGHT_SELLER_CATALOG_COUNT", "-0.08")),
    "early_window_bonus": float(os.getenv("AVORI_WEIGHT_EARLY_WINDOW_BONUS", "12.0")),
}


def ensure_output_dir(output_dir: Path | None = None) -> Path:
    resolved = output_dir or OUTPUT_DIR
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def results_filename(run_date: date) -> str:
    return f"avori_results_{run_date.isoformat()}.json"
