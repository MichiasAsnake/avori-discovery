from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from config import ensure_output_dir, results_filename


def write_results_json(results_payload, output_dir: Path, run_date: date):
    resolved_dir = ensure_output_dir(output_dir)
    results_path = resolved_dir / results_filename(run_date)
    results_path.write_text(json.dumps(results_payload, indent=2))
    return results_path


def build_daily_brief(results_payload, run_date: date):
    products = results_payload.get("products", [])
    audit = results_payload.get("endpoint_audit", [])
    search_bridge_endpoint = results_payload.get("search_bridge_endpoint")
    seed_terms = results_payload.get("seed_terms", [])
    discovered_keywords = results_payload.get("discovered_keywords", [])
    keyword_product_counts = results_payload.get("keyword_product_counts", {})
    fallback_seller_product_counts = results_payload.get("fallback_seller_product_counts", {})
    usable_endpoints = [entry["name"] for entry in audit if entry.get("usable")]
    skipped_endpoints = [
        f"{entry['name']} ({entry.get('inner_code')})" for entry in audit if not entry.get("usable")
    ]

    lines = [
        f"Avori Daily Discovery Brief - {run_date.isoformat()}",
        "",
        f"Usable endpoints: {', '.join(usable_endpoints) if usable_endpoints else 'none'}",
    ]
    if skipped_endpoints:
        lines.append(f"Skipped endpoints: {', '.join(skipped_endpoints)}")
    if search_bridge_endpoint:
        lines.append(f"Primary bridge: {search_bridge_endpoint}")
    if seed_terms:
        lines.append(f"Seed terms: {', '.join(seed_terms)}")
    if discovered_keywords:
        lines.append(f"Discovered keywords: {', '.join(discovered_keywords)}")

    if keyword_product_counts:
        lines.extend(["", "Products pulled per keyword"])
        for keyword, product_count in keyword_product_counts.items():
            lines.append(f"- {keyword}: {product_count}")

    if fallback_seller_product_counts:
        lines.extend(["", "Fallback seller pull"])
        for seller_id, info in fallback_seller_product_counts.items():
            lines.append(f"- {info.get('seller_name', seller_id)} ({seller_id}): {info.get('product_count', 0)}")

    lines.extend(["", f"Top candidates: {len(products)}", ""])
    for index, product in enumerate(products[:5], start=1):
        early_window_marker = " EARLY WINDOW" if product.get("early_window") else ""
        price = product.get("price")
        price_text = f"${price:.2f}" if isinstance(price, (int, float)) else "n/a"
        supplementary_signals = product.get("supplementary_signals") or {}
        supplementary_text = ""
        if supplementary_signals:
            signal_parts = [f"{key}={value}" for key, value in supplementary_signals.items()]
            supplementary_text = f" | bonus {', '.join(signal_parts)}"
        lines.append(
            f"{index}. {product.get('title', 'Untitled')} | {price_text} | sold {product.get('sold_count', 0)}"
            f" | reviews {product.get('review_count', 0)} | seller {product.get('seller_name', 'unknown')}"
            f" | via {product.get('source_endpoint', 'unknown')} | score {product.get('score', 0)}"
            f"{supplementary_text}{early_window_marker}"
        )

    return "\n".join(lines)


def write_daily_brief(brief_text, output_dir: Path):
    resolved_dir = ensure_output_dir(output_dir)
    brief_path = resolved_dir / "avori_daily_brief.txt"
    brief_path.write_text(brief_text)
    return brief_path
