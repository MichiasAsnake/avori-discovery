from __future__ import annotations

from copy import deepcopy

from config import SCORING_WEIGHTS
from signal_score import score_product_signal


def flag_early_window(product):
    return int(product.get("sold_count") or 0) > 1000 and int(product.get("review_count") or 0) < 30


def _supplementary_signals(product):
    signals = {}
    for key in (
        "related_video_count",
        "shop_performance_count",
        "shop_review_count",
        "shop_follower_count",
        "shop_on_sell_product_count",
    ):
        value = product.get(key)
        if value:
            signals[key] = value
    return signals


def score_product(product):
    scored = deepcopy(product)
    sold_count = float(scored.get("sold_count") or 0)
    review_count = float(scored.get("review_count") or 0)
    rating = float(scored.get("rating") or 0)
    creator_video_count = float(scored.get("creator_video_count") or 0)
    seller_catalog_count = float(scored.get("seller_catalog_count") or 0)
    early_window = flag_early_window(scored)

    score = (
        sold_count * SCORING_WEIGHTS["sold_count"]
        + review_count * SCORING_WEIGHTS["review_count"]
        + rating * SCORING_WEIGHTS["rating"]
        + creator_video_count * SCORING_WEIGHTS["creator_video_count"]
        + seller_catalog_count * SCORING_WEIGHTS["seller_catalog_count"]
    )
    if early_window:
        score += SCORING_WEIGHTS["early_window_bonus"]

    scored["early_window"] = early_window
    scored["score"] = round(score, 2)
    product_signal = score_product_signal(scored)
    scored["product_signal"] = product_signal
    scored["signal_score"] = product_signal["final_score"]
    scored["recommended_action"] = product_signal["decision"]
    supplementary_signals = _supplementary_signals(scored)
    if supplementary_signals:
        scored["supplementary_signals"] = supplementary_signals
    return scored


def rank_products(products):
    scored = [score_product(product) for product in products]
    return sorted(scored, key=lambda product: product["signal_score"], reverse=True)
