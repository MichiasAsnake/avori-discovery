from __future__ import annotations

import json
import math
from collections.abc import Callable
from typing import Any

from signal_score import score_product_signal
from utils import safe_float

PROMPT_VERSION = "tiktok-judgment-v2"
VALID_DECISIONS = {"skip", "watch", "deep_dive", "test_now"}
DEFAULT_DECISION = "watch"


def reject_non_finite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value is not allowed: {value}")


def _sanitize_json_value(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    return value


JsonClient = Callable[[str], str | dict[str, Any]]


def _as_list(value: Any, fallback: list[str] | None = None, *, limit: int = 6) -> list[str]:
    if value is None:
        return list(fallback or [])[:limit]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else list(fallback or [])[:limit]
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned[:limit] or list(fallback or [])[:limit]
    return list(fallback or [])[:limit]


def _clamp_confidence(value: Any) -> float:
    confidence = safe_float(value, 0.65)
    if not math.isfinite(confidence):
        confidence = 0.65
    if confidence > 1:
        confidence = 1
    return round(max(0.0, min(1.0, confidence)), 2)


def _product_identity(product: dict[str, Any]) -> tuple[str, str]:
    return str(product.get("product_id") or ""), str(product.get("title") or "Untitled")


def _signal(product: dict[str, Any]) -> dict[str, Any]:
    existing = product.get("product_signal")
    if isinstance(existing, dict) and isinstance(existing.get("final_score"), (int, float)):
        decision = existing.get("decision")
        if decision is None or str(decision) in VALID_DECISIONS:
            return existing
    return score_product_signal(product)


def _build_product_angles(product: dict[str, Any]) -> list[str]:
    """Generate TikTok content angles from product data, not hardcoded niches."""
    title = str(product.get("title") or "").lower()
    category_names = product.get("category_names") or []

    # Detect the product type dynamically
    if any(w in title for w in ("packing cube", "luggage organiz")):
        return [
            "How I fit everything in one carry-on with packing cubes",
            "Before/after: messy suitcase vs cubed packing system",
            "Packing cubes that actually compress",
        ]
    if any(w in title for w in ("purse", "bag insert", "tote organ")):
        return [
            "What's actually in my bag, but organized",
            "Before/after: messy tote to clean setup",
            "One organizer, every bag switch",
        ]
    if any(w in title for w in ("toiletry", "makeup bag", "cosmetic")):
        return [
            "Everything fits and stays visible in one bag",
            "Pack my full travel routine with me",
            "Hotel counter setup in 30 seconds",
        ]
    if any(w in title for w in ("jewelry", "jewellery")):
        return [
            "No more tangled travel jewelry",
            "Weekend trip jewelry organized in 10 seconds",
        ]
    if any(w in title for w in ("storage", "container", "box")):
        return [
            "Before/after: chaos to organized with one product",
            "Small product that actually solves a daily problem",
        ]

    # Generic but useful TikTok hooks for any product
    return [
        f"Watch how {title[:40]} solves a real problem",
        "Before/after demo with this product",
        "Why this simple product keeps selling out",
    ]


def _fallback_why(product_signal: dict[str, Any]) -> list[str]:
    reasons = _as_list(product_signal.get("reasons"), limit=5)
    if reasons:
        return reasons
    return ["Product has enough measurable signal to justify a structured review."]


def _fallback_risks(product_signal: dict[str, Any]) -> list[str]:
    risks = _as_list(product_signal.get("risks"), limit=5)
    if risks:
        return risks
    return ["Needs sourcing, margin, shipping, and competitor checks before testing."]


def build_product_judgment_prompt(product: dict[str, Any]) -> str:
    product = _sanitize_json_value(product)
    product_with_signal = dict(product)
    product_with_signal["product_signal"] = _signal(product)
    compact_product = json.dumps(product_with_signal, indent=2, sort_keys=True, allow_nan=False)
    return f"""
You are a TikTok Shop product analyst. Judge whether a product should be skipped, watched, deep-dived, or tested now.

Rules:
- Optimize for products likely to sell on TikTok Shop, regardless of category.
- Use the deterministic product_signal as evidence, but don't blindly copy it if qualitative risks are obvious.
- Be concise and practical. Focus on market signals, not brand fit.
- Return ONLY valid JSON. No markdown. No prose outside JSON.

Allowed decision values: skip, watch, deep_dive, test_now.

Required JSON schema:
{{
  "decision": "skip|watch|deep_dive|test_now",
  "confidence": 0.0,
  "ideal_customer": "specific buyer segment this product appeals to",
  "why_it_might_sell": ["reason 1", "reason 2"],
  "content_angles": ["TikTok hook or demo angle 1", "TikTok hook or demo angle 2"],
  "risks": ["risk 1"],
  "recommended_next_step": "single concrete next action"
}}

Product input:
{compact_product}
""".strip()


def validate_product_judgment(
    payload: dict[str, Any],
    product: dict[str, Any],
    *,
    judge_source: str,
    llm_error: str | None = None,
) -> dict[str, Any]:
    product_id, title = _product_identity(product)
    product_signal = _signal(product)
    decision = str(payload.get("decision") or product_signal.get("decision") or DEFAULT_DECISION)
    if decision not in VALID_DECISIONS:
        decision = DEFAULT_DECISION

    # Build ideal_customer dynamically from product context instead of hardcoded
    raw_ideal_customer = str(payload.get("ideal_customer") or "").strip()
    if not raw_ideal_customer:
        # Fallback: derive from title/category signal patterns
        sold = product.get("sold_count", 0)
        reviews = product.get("review_count", 0)
        price = product.get("price", 0)
        product_type = "practical, easy-to-demonstrate product"
        if reviews <= 30 and sold >= 1000:
            product_type = "early-window product with demand before mainstream awareness"
        elif sold >= 5000:
            product_type = "proven winner with strong market validation"
        ideal_customer = f"TikTok Shop buyers seeking {product_type} with clear everyday utility at ~${price}"
    else:
        ideal_customer = raw_ideal_customer

    recommended_next_step = (
        str(payload.get("recommended_next_step") or "").strip()
        or str(product_signal.get("next_step") or "").strip()
        or "Review sourcing, margin, competition, and content fit."
    )

    memo = {
        "product_id": product_id,
        "title": title,
        "decision": decision,
        "confidence": _clamp_confidence(payload.get("confidence", 0.65)),
        "ideal_customer": ideal_customer,
        "why_it_might_sell": _as_list(
            payload.get("why_it_might_sell"),
            fallback=_fallback_why(product_signal),
            limit=6,
        ),
        "content_angles": _as_list(
            payload.get("content_angles"),
            fallback=_build_product_angles(product),
            limit=6,
        ),
        "risks": _as_list(
            payload.get("risks"),
            fallback=_fallback_risks(product_signal),
            limit=6,
        ),
        "recommended_next_step": recommended_next_step,
        "signal_snapshot": product_signal,
        "judge_source": judge_source,
        "prompt_version": PROMPT_VERSION,
    }
    if llm_error:
        memo["llm_error"] = llm_error
    return memo


def _fallback_judgment(product: dict[str, Any], *, llm_error: str | None = None) -> dict[str, Any]:
    product_signal = _signal(product)
    payload = {
        "decision": product_signal.get("decision", DEFAULT_DECISION),
        "confidence": 0.72 if product_signal.get("final_score", 0) >= 65 else 0.62,
        "why_it_might_sell": _fallback_why(product_signal),
        "risks": _fallback_risks(product_signal),
        "recommended_next_step": product_signal.get("next_step"),
    }
    return validate_product_judgment(payload, product, judge_source="heuristic", llm_error=llm_error)


def _parse_llm_response(response: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(response, dict):
        return _sanitize_json_value(response)
    parsed = json.loads(response, parse_constant=reject_non_finite_json_constant)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response was not a JSON object")
    return _sanitize_json_value(parsed)


def analyze_product(product: dict[str, Any], llm_client: JsonClient | None = None) -> dict[str, Any]:
    product = _sanitize_json_value(product)
    if llm_client is None:
        return _fallback_judgment(product)

    prompt = build_product_judgment_prompt(product)
    try:
        raw_response = llm_client(prompt)
        parsed = _parse_llm_response(raw_response)
    except json.JSONDecodeError:
        return _fallback_judgment(product, llm_error="invalid_json")
    except ValueError:
        return _fallback_judgment(product, llm_error="invalid_json")
    except Exception as exc:
        return _fallback_judgment(product, llm_error=exc.__class__.__name__)

    return validate_product_judgment(parsed, product, judge_source="llm")
