import unittest
from unittest.mock import patch

from endpoints.detail import fetch_product_detail, fetch_product_detail_v3, fetch_product_detail_v4, fetch_seller_products_list, fetch_showcase_product_list
from endpoints.search import (
    extract_seller_ids_from_live_search,
    fetch_live_search_result,
    fetch_search_products_list,
    fetch_search_products_list_v2,
    fetch_search_word_suggestion,
)
from endpoints.trending import fetch_top_products_list
from tikhub_client import SAMPLE_PRODUCT_DETAIL_PAYLOAD, SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD, audit_tikhub_endpoints


class EndpointFallbackTests(unittest.TestCase):
    @patch("endpoints.search.request_tikhub_json")
    def test_fetch_live_search_result_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_live_search_result("travel organizer")

        self.assertEqual(payload["data"]["status_code"], 0)
        self.assertGreater(len(payload["data"]["data"]), 0)

    @patch("endpoints.search.request_tikhub_json")
    def test_fetch_search_products_list_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_search_products_list("travel organizer")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertGreater(len(payload["data"]["data"]["products"]), 0)

    @patch("endpoints.search.request_tikhub_json")
    def test_fetch_search_products_list_v2_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_search_products_list_v2("travel organizer")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertGreater(len(payload["data"]["data"]["component_data"]["products"]), 0)

    @patch("endpoints.search.request_tikhub_json")
    def test_fetch_search_word_suggestion_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_search_word_suggestion("travel")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertGreater(len(payload["data"]["data"]), 0)

    @patch("endpoints.search.request_tikhub_json")
    def test_fetch_search_word_suggestion_uses_web_keyword_fallback_on_shop_400(self, mock_request):
        mock_request.side_effect = [
            (
                400,
                {
                    "detail": {
                        "code": 400,
                        "router": "/api/v1/tiktok/shop/web/fetch_search_word_suggestion",
                    }
                },
            ),
            (
                200,
                {
                    "code": 200,
                    "router": "/api/v1/tiktok/web/fetch_search_keyword_suggest",
                    "data": {
                        "status_code": 0,
                        "status_msg": "",
                        "data": [
                            {"word": "travel destinations", "group_id": "1"},
                            {"word": "travel trends", "group_id": "2"},
                        ],
                    },
                },
            ),
        ]

        payload = fetch_search_word_suggestion("travel")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertEqual(payload["data"]["data"], ["travel destinations", "travel trends"])
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(
            mock_request.call_args_list[1].args[0],
            "/api/v1/tiktok/web/fetch_search_keyword_suggest",
        )

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_seller_products_list_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_seller_products_list("seller-avori-1")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertGreater(len(payload["data"]["data"]["products"]), 0)

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_product_detail_v3_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_product_detail_v3("1729001")

        self.assertIn("product_data", payload["data"])

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_product_detail_v4_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_product_detail_v4("1729001")

        self.assertEqual(payload["data"]["code"], 0)
        self.assertIn("categories", payload["data"]["data"]["global_data"]["product_info"])

    @patch("endpoints.trending.request_tikhub_json")
    def test_fetch_top_products_list_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_top_products_list()

        self.assertEqual(payload["data"]["code"], 50004)

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_showcase_product_list_falls_back_on_live_error(self, mock_request):
        mock_request.side_effect = RuntimeError("upstream 400")

        payload = fetch_showcase_product_list("demo-kol-id")

        self.assertEqual(payload["data"]["code"], 100000)

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_product_detail_uses_v4_after_three_v3_400_responses(self, mock_request):
        mock_request.side_effect = [
            (400, {"detail": {"code": 400}}),
            (400, {"detail": {"code": 400}}),
            (400, {"detail": {"code": 400}}),
            (200, SAMPLE_PRODUCT_DETAIL_PAYLOAD),
        ]

        detail_endpoint, payload = fetch_product_detail("1729001")

        self.assertEqual(detail_endpoint, "product_detail_v4")
        self.assertEqual(payload["data"]["code"], 0)
        self.assertEqual(mock_request.call_count, 4)
        for call in mock_request.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 30.0)

    @patch("endpoints.detail.request_tikhub_json")
    def test_fetch_product_detail_prefers_v3_when_available(self, mock_request):
        mock_request.return_value = (200, SAMPLE_PRODUCT_DETAIL_V3_PAYLOAD)

        detail_endpoint, payload = fetch_product_detail("1729001")

        self.assertEqual(detail_endpoint, "product_detail_v3")
        self.assertIn("product_data", payload["data"])

    def test_audit_tikhub_endpoints_sample_marks_usable_endpoints(self):
        audit = audit_tikhub_endpoints(use_sample_data=True)

        usable_names = [entry["name"] for entry in audit if entry["usable"]]

        self.assertEqual(
            usable_names,
            ["search_word_suggestion", "search_products_list", "search_products_list_v2", "seller_products_list", "product_detail"],
        )

    def test_extract_seller_ids_from_live_search_uses_rawdata_then_author_uid(self):
        live_results = [
            {
                "lives": {
                    "is_live_has_products": True,
                    "author": {"uid": "author-1"},
                    "rawdata": '{"owner":{"id":"seller-1","display_id":"display-1"}}',
                }
            },
            {
                "lives": {
                    "is_live_has_products": True,
                    "author": {"uid": "author-2"},
                    "rawdata": '{"owner":{"display_id":"display-2"}}',
                }
            },
            {
                "lives": {
                    "is_live_has_products": True,
                    "author": {"uid": "author-3"},
                    "rawdata": '{"id":"room-3"}',
                }
            },
            {
                "lives": {
                    "is_live_has_products": False,
                    "author": {"uid": "author-4"},
                    "rawdata": '{"owner":{"id":"seller-4"}}',
                }
            },
            {
                "lives": {
                    "room": {"has_commerce_goods": True},
                    "author": {"uid": "author-1"},
                    "rawdata": '{"owner":{"id":"seller-1"}}',
                }
            },
        ]

        seller_ids = extract_seller_ids_from_live_search(live_results)

        self.assertEqual(seller_ids, ["seller-1", "display-2", "author-3"])


if __name__ == "__main__":
    unittest.main()
