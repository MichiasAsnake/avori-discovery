import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from output import build_daily_brief, write_daily_brief, write_results_json


class OutputTests(unittest.TestCase):
    def test_build_daily_brief_includes_audit_products_and_discovered_keywords(self):
        results_payload = {
            "endpoint_audit": [
                {"name": "search_word_suggestion", "usable": True, "status_code": 200},
                {"name": "search_products_list", "usable": True, "status_code": 200},
                {"name": "seller_products_list", "usable": True, "status_code": 200},
                {"name": "product_detail", "usable": True, "status_code": 200},
            ],
            "search_bridge_endpoint": "search_products_list",
            "seed_terms": ["travel", "organizer"],
            "discovered_keywords": ["travel organizer", "travel toiletry bag"],
            "products": [
                {
                    "product_id": "p1",
                    "title": "Travel Hanging Toiletry Organizer",
                    "price": 29.99,
                    "seller_name": "Avori Demo Shop",
                    "score": 91.4,
                    "sold_count": 2200,
                    "review_count": 18,
                    "early_window": True,
                    "source_endpoint": "seller_products_list",
                    "supplementary_signals": {"related_video_count": 6, "shop_performance_count": 3},
                },
                {
                    "product_id": "p2",
                    "title": "Purse Organizer Insert",
                    "price": 16.99,
                    "seller_name": "Avori Demo Shop",
                    "score": 74.2,
                    "sold_count": 900,
                    "review_count": 66,
                    "early_window": False,
                    "source_endpoint": "seller_products_list",
                },
            ],
            "keyword_product_counts": {
                "travel organizer": 25,
                "travel toiletry bag": 12,
            },
            "fallback_seller_product_counts": {
                "seller-1": {"seller_name": "Avori Demo Shop", "product_count": 12},
                "seller-2": {"seller_name": "Travel Store", "product_count": 4},
            },
        }

        brief = build_daily_brief(results_payload, date(2026, 4, 19))

        self.assertIn("Avori Daily Discovery Brief", brief)
        self.assertIn("Usable endpoints: search_word_suggestion, search_products_list, seller_products_list, product_detail", brief)
        self.assertIn("Primary bridge: search_products_list", brief)
        self.assertIn("Seed terms: travel, organizer", brief)
        self.assertIn("Discovered keywords: travel organizer, travel toiletry bag", brief)
        self.assertIn("Travel Hanging Toiletry Organizer", brief)
        self.assertIn("$29.99", brief)
        self.assertIn("Products pulled per keyword", brief)
        self.assertIn("travel organizer: 25", brief)
        self.assertIn("Avori Demo Shop", brief)
        self.assertIn("EARLY WINDOW", brief)
        self.assertIn("bonus related_video_count=6, shop_performance_count=3", brief)

    def test_write_results_json_and_brief(self):
        results_payload = {
            "products": [{"product_id": "p1", "title": "Travel bag", "score": 90.0}],
            "endpoint_audit": [],
            "keyword_product_counts": {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            results_path = write_results_json(results_payload, output_dir, date(2026, 4, 19))
            brief_path = write_daily_brief("brief body", output_dir)

            self.assertTrue(results_path.exists())
            self.assertTrue(brief_path.exists())
            self.assertEqual(brief_path.read_text(), "brief body")
            self.assertEqual(json.loads(results_path.read_text())["products"][0]["product_id"], "p1")


if __name__ == "__main__":
    unittest.main()
