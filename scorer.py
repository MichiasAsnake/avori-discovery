from __future__ import annotations

from copy import deepcopy

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
    scored["early_window"] = flag_early_window(scored)
    product_signal = score_product_signal(scored)
    scored["product_signal"] = product_signal
    scored["score"] = product_signal["final_score"]
    scored["recommended_action"] = product_signal["decision"]
    supplementary_signals = _supplementary_signals(scored)
    if supplementary_signals:
        scored["supplementary_signals"] = supplementary_signals
    return scored


def rank_products(products):
    scored = [score_product(product) for product in products]
    return sorted(scored, key=lambda p: p["score"], reverse=True)
