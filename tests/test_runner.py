import io
import json
import tempfile
import unittest
from unittest.mock import AsyncMock
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from tikhub_client import SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD, SAMPLE_SELLER_PRODUCTS_PAYLOAD
from avori_discovery import run_discovery


class RunnerTests(unittest.TestCase):
    def test_run_discovery_writes_payload_and_prints_brief(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = run_discovery(
                    output_dir=Path(tmpdir),
                    run_date=date(2026, 4, 19),
                    use_sample_data=True,
                )

            brief_text = stdout.getvalue()
            self.assertIn("Avori Daily Discovery Brief", brief_text)
            self.assertTrue(result["results_path"].exists())
            self.assertTrue(result["brief_path"].exists())
            self.assertGreater(len(result["ranked_products"]), 0)
            self.assertGreater(len(result["results_payload"]["endpoint_audit"]), 0)
            self.assertEqual(result["results_payload"]["search_bridge_endpoint"], "search_products_list")
            self.assertGreater(len(result["results_payload"]["seed_terms"]), 0)
            self.assertGreater(len(result["results_payload"]["discovered_keywords"]), 0)
            self.assertGreater(len(result["results_payload"]["keyword_product_counts"]), 0)
            self.assertEqual(result["results_payload"]["fallback_seller_product_counts"], {})

            saved = json.loads(result["results_path"].read_text())
            self.assertEqual(saved["products"][0]["product_id"], result["ranked_products"][0]["product_id"])
            self.assertEqual(saved["keyword_product_counts"], result["results_payload"]["keyword_product_counts"])

    @patch("avori_discovery.fetch_product_detail_async", new_callable=AsyncMock)
    @patch("avori_discovery.fetch_seller_products_list", return_value=SAMPLE_SELLER_PRODUCTS_PAYLOAD)
    @patch("avori_discovery.fetch_search_products_list_async", new_callable=AsyncMock)
    @patch("avori_discovery.fetch_search_word_suggestion_async", new_callable=AsyncMock)
    @patch("avori_discovery.audit_tikhub_endpoints")
    def test_run_discovery_falls_back_to_seed_sellers_when_search_returns_zero_products(
        self,
        mock_audit,
        mock_search_word_suggestion,
        mock_search,
        _mock_seller_products,
        mock_product_detail,
    ):
        mock_audit.return_value = [
            {"name": "search_word_suggestion", "usable": True},
            {"name": "search_products_list", "usable": True},
            {"name": "seller_products_list", "usable": True},
            {"name": "product_detail", "usable": True},
        ]
        mock_search_word_suggestion.return_value = {"data": {"code": 0, "data": ["travel organizer"]}}
        mock_search.return_value = {"data": {"code": 0, "data": {"products": []}}}
        mock_product_detail.return_value = ("product_detail_v3", SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_discovery(
                output_dir=Path(tmpdir),
                run_date=date(2026, 4, 19),
                use_sample_data=False,
            )

        self.assertEqual(result["results_payload"]["search_bridge_endpoint"], "search_products_list")
        self.assertEqual(result["results_payload"]["discovered_keywords"], ["travel organizer"])
        self.assertEqual(result["results_payload"]["keyword_product_counts"]["travel organizer"], 0)
        self.assertGreater(len(result["ranked_products"]), 0)
        self.assertGreater(len(result["results_payload"]["fallback_seller_product_counts"]), 0)

    @patch("avori_discovery.fetch_product_detail_async", new_callable=AsyncMock)
    @patch("avori_discovery.fetch_seller_products_list", return_value=SAMPLE_SELLER_PRODUCTS_PAYLOAD)
    @patch("avori_discovery.fetch_search_products_list_async", new_callable=AsyncMock)
    @patch("avori_discovery.fetch_search_word_suggestion_async", new_callable=AsyncMock)
    @patch("avori_discovery.audit_tikhub_endpoints")
    def test_run_discovery_can_disable_seed_seller_fallback(
        self,
        mock_audit,
        mock_search_word_suggestion,
        mock_search,
        mock_seller_products,
        mock_product_detail,
    ):
        mock_audit.return_value = [
            {"name": "search_word_suggestion", "usable": True},
            {"name": "search_products_list", "usable": True},
            {"name": "seller_products_list", "usable": True},
            {"name": "product_detail", "usable": True},
        ]
        mock_search_word_suggestion.return_value = {"data": {"code": 0, "data": ["travel organizer"]}}
        mock_search.return_value = {"data": {"code": 0, "data": {"products": []}}}
        mock_product_detail.return_value = ("product_detail_v3", SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_discovery(
                output_dir=Path(tmpdir),
                run_date=date(2026, 4, 19),
                use_sample_data=False,
                seller_fallback=False,
            )

        self.assertEqual(result["results_payload"]["search_bridge_endpoint"], "search_products_list")
        self.assertEqual(result["results_payload"]["discovered_keywords"], ["travel organizer"])
        self.assertEqual(result["results_payload"]["keyword_product_counts"]["travel organizer"], 0)
        self.assertEqual(result["ranked_products"], [])
        self.assertEqual(result["results_payload"]["fallback_seller_product_counts"], {})
        mock_seller_products.assert_not_called()


if __name__ == "__main__":
    unittest.main()
