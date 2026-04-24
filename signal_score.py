from __future__ import annotations

from utils import safe_float, safe_int

AVORI_NICHE_KEYWORDS = (
    "bag",
    "purse",
    "handbag",
    "tote",
    "travel",
    "organizer",
    "organiser",
    "makeup",
    "cosmetic",
    "beauty",
    "jewelry",
    "jewellery",
    "desk",
    "home",
    "packing",
    "toiletry",
)

DEMO_KEYWORDS = (
    "organizer",
    "organiser",
    "storage",
    "before",
    "after",
    "travel",
    "makeup",
    "bag",
    "purse",
    "packing",
    "toiletry",
    "case",
    "holder",
)


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _rounded(value: float) -> float:
    return round(value, 2)


def _combined_text(product: dict) -> str:
    category_names = product.get("category_names") or []
    if not isinstance(category_names, list):
        category_names = [str(category_names)]
    return " ".join(
        [
            str(product.get("title") or ""),
            str(product.get("seller_name") or ""),
            " ".join(str(category) for category in category_names),
        ]
    ).lower()


def score_demand(product: dict) -> float:
    sold_count = safe_int(product.get("sold_count"))
    if sold_count <= 0:
        return 0.0
    if sold_count < 250:
        return _rounded(sold_count / 250 * 6)
    if sold_count < 1000:
        return _rounded(6 + (sold_count - 250) / 750 * 7)
    if sold_count < 5000:
        return _rounded(13 + (sold_count - 1000) / 4000 * 8)
    return _rounded(_clamp(21 + min((sold_count - 5000) / 20000 * 4, 4), 0, 25))


def score_velocity(product: dict) -> float:
    velocity = safe_float(
        product.get("velocity")
        or product.get("weekly_sold_velocity")
        or product.get("sold_velocity_7d")
        or 0
    )
    if velocity <= 0:
        return 0.0
    if velocity < 100:
        return _rounded(velocity / 100 * 3)
    if velocity < 500:
        return _rounded(3 + (velocity - 100) / 400 * 4)
    return _rounded(_clamp(7 + min((velocity - 500) / 1000 * 3, 3), 0, 10))


def score_low_saturation(product: dict) -> float:
    sold_count = safe_int(product.get("sold_count"))
    review_count = safe_int(product.get("review_count"))
    if sold_count <= 0 and review_count <= 0:
        return 8.0
    if review_count >= 3000:
        return 0.0

    review_ratio = review_count / max(sold_count, 1)
    ratio_score = _clamp((0.08 - review_ratio) / 0.08 * 14, 0, 14)

    if review_count <= 30 and sold_count >= 1000:
        count_score = 6
    elif review_count <= 100:
        count_score = 4
    elif review_count <= 500:
        count_score = 2
    else:
        count_score = 0

    return _rounded(_clamp(ratio_score + count_score, 0, 20))


def score_content_potential(product: dict) -> float:
    creator_video_count = safe_int(product.get("creator_video_count"))
    related_video_count = safe_int(product.get("related_video_count"))
    video_score = min((creator_video_count + related_video_count) * 0.55, 9)

    text = _combined_text(product)
    demo_hits = sum(1 for keyword in DEMO_KEYWORDS if keyword in text)
    demo_score = min(demo_hits * 1.5, 6)
    return _rounded(_clamp(video_score + demo_score, 0, 15))


def score_price_viability(product: dict) -> float:
    price = safe_float(product.get("price"))
    if price <= 0:
        return 4.0
    if 14 <= price <= 35:
        return 15.0
    if 10 <= price < 14:
        return 12.0
    if 35 < price <= 50:
        return 11.0
    if 7 <= price < 10:
        return 8.0
    if 50 < price <= 80:
        return 6.0
    return 2.0


def score_seller_signal(product: dict) -> float:
    follower_count = safe_int(product.get("shop_follower_count"))
    review_count = safe_int(product.get("shop_review_count"))
    performance_count = safe_int(product.get("shop_performance_count"))
    catalog_count = safe_int(product.get("seller_catalog_count") or product.get("shop_on_sell_product_count"))

    score = 0.0
    if follower_count >= 1000:
        score += 3
    elif follower_count >= 100:
        score += 1.5
    if review_count >= 100:
        score += 2
    elif review_count >= 20:
        score += 1
    if performance_count > 0:
        score += min(performance_count, 3)
    if 3 <= catalog_count <= 80:
        score += 2
    elif catalog_count > 250:
        score -= 2
    return _rounded(_clamp(score, 0, 10))


def score_niche_bonus(product: dict) -> float:
    text = _combined_text(product)
    hits = sum(1 for keyword in AVORI_NICHE_KEYWORDS if keyword in text)
    if hits >= 3:
        return 5.0
    if hits == 2:
        return 3.5
    if hits == 1:
        return 2.0
    return 0.0


def score_risk_penalty(product: dict) -> tuple[float, list[str]]:
    risks: list[str] = []
    penalty = 0.0
    sold_count = safe_int(product.get("sold_count"))
    review_count = safe_int(product.get("review_count"))
    rating = safe_float(product.get("rating"))
    price = safe_float(product.get("price"))
    catalog_count = safe_int(product.get("seller_catalog_count") or product.get("shop_on_sell_product_count"))

    if review_count >= 1000:
        penalty += 10
        risks.append("Saturated review profile")
    elif review_count >= 500:
        penalty += 6
        risks.append("Moderate review saturation")

    if sold_count >= 25000 and review_count >= 1000:
        penalty += 5
        if "Saturated review profile" not in risks:
            risks.append("Saturated review profile")

    if rating and rating < 4.0:
        penalty += 7
        risks.append("Weak rating")
    elif rating and rating < 4.3:
        penalty += 3
        risks.append("Rating needs review")

    if price and price < 7:
        penalty += 4
        risks.append("Low price may limit margin")
    elif price > 80:
        penalty += 4
        risks.append("High price may reduce impulse conversion")

    if catalog_count > 250:
        penalty += 4
        risks.append("Large seller catalog may signal broad seller dominance")

    return _rounded(_clamp(penalty, 0, 30)), risks


def _decision(final_score: float, risk_penalty: float, low_saturation_signal: float) -> tuple[str, str]:
    if risk_penalty >= 22 or (low_saturation_signal <= 3 and final_score < 65):
        return "skip", "Reject unless a manual review finds a unique angle."
    if final_score >= 90 and risk_penalty <= 8:
        return "test_now", "Run sourcing, margin, and listing-package checks."
    if final_score >= 65:
        return "deep_dive", "Build a sourcing and content-angle deep dive."
    if final_score >= 45:
        return "watch", "Track velocity and saturation before deciding."
    return "skip", "Reject unless a manual review finds a unique angle."


def _reasons(components: dict[str, float]) -> list[str]:
    reasons = []
    if components["demand_signal"] >= 13:
        reasons.append("Strong demand")
    if components["velocity_signal"] >= 5:
        reasons.append("Positive tracked velocity")
    if components["low_saturation_signal"] >= 12:
        reasons.append("Low review saturation")
    if components["content_signal"] >= 7:
        reasons.append("TikTok content signal")
    if components["price_signal"] >= 12:
        reasons.append("Price supports impulse testing")
    if components["seller_signal"] >= 5:
        reasons.append("Seller/shop signal present")
    if components["niche_bonus"] > 0:
        reasons.append("Relevant to Avori lanes")
    return reasons


def score_product_signal(product: dict) -> dict:
    risk_penalty, risks = score_risk_penalty(product)
    components = {
        "demand_signal": score_demand(product),
        "velocity_signal": score_velocity(product),
        "low_saturation_signal": score_low_saturation(product),
        "content_signal": score_content_potential(product),
        "price_signal": score_price_viability(product),
        "seller_signal": score_seller_signal(product),
        "niche_bonus": score_niche_bonus(product),
        "risk_penalty": risk_penalty,
    }
    positive_total = sum(value for key, value in components.items() if key != "risk_penalty")
    final_score = _rounded(_clamp(positive_total - risk_penalty, 0, 100))
    decision, next_step = _decision(
        final_score,
        risk_penalty,
        components["low_saturation_signal"],
    )
    return {
        "final_score": final_score,
        "decision": decision,
        "next_step": next_step,
        "components": components,
        "reasons": _reasons(components),
        "risks": risks,
    }
