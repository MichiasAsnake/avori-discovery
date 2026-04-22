import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class AgentModuleTests(unittest.TestCase):
    def test_agent_module_exposes_agent_and_tools(self):
        import agent

        self.assertEqual(agent.agent.name, "Avori Discovery Agent")
        self.assertEqual(agent.agent.model, "gpt-4o")
        self.assertEqual(agent.agent.__class__.__name__, "Agent")
        self.assertTrue(callable(agent.run_discovery))
        self.assertTrue(callable(agent.get_product_detail))
        self.assertTrue(callable(agent.search_products))
        self.assertTrue(callable(agent.add_to_watchlist))
        self.assertTrue(callable(agent.get_watchlist))
        self.assertTrue(callable(agent.remove_from_watchlist))
        self.assertIn("thinking partner", agent.agent.instructions)
        self.assertIn("watchlist", agent.agent.instructions)

    @patch("agent.fetch_search_products_list")
    @patch("agent.fetch_search_word_suggestion")
    @patch("agent.SEED_TERMS", ["one", "two", "three", "four", "five", "six"])
    def test_run_discovery_tool_returns_ranked_candidates(self, mock_fetch_search_word_suggestion, mock_fetch_search_products_list):
        import agent

        mock_fetch_search_word_suggestion.side_effect = [
            {"data": {"code": 0, "data": ["travel organizer", "packing cube", "makeup organizer"]}},
            {"data": {"code": 0, "data": ["drawer organizer", "desk organizer", "toiletry pouch"]}},
            {"data": {"code": 0, "data": ["jewelry case", "travel pouch", "cosmetic bag"]}},
            {"data": {"code": 0, "data": ["bag organizer", "hanging bag", "travel case"]}},
            {"data": {"code": 0, "data": ["makeup case", "storage pouch", "travel bottle bag"]}},
        ]

        def _search_payload(search_word, offset=0, page_token="", region="US"):
            return {
                "data": {
                    "code": 0,
                    "data": {
                        "products": [
                            {
                                "product_id": f"{search_word}-1",
                                "title": f"{search_word} product 1",
                                "image": {"url_list": [f"https://example.com/{search_word}-1.jpg"]},
                                "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                                "rate_info": {"score": 4.8, "review_count": "18"},
                                "sold_info": {"sold_count": 2400},
                                "seller_info": {"seller_id": f"seller-{search_word}-1", "shop_name": f"Seller {search_word} One"},
                                "seo_url": f"/{search_word}-1",
                            },
                            {
                                "product_id": f"{search_word}-2",
                                "title": f"{search_word} product 2",
                                "image": {"url_list": [f"https://example.com/{search_word}-2.jpg"]},
                                "product_price_info": {"currency_name": "USD", "sale_price_format": "16.99"},
                                "rate_info": {"score": 4.6, "review_count": "12"},
                                "sold_info": {"sold_count": 1200},
                                "seller_info": {"seller_id": f"seller-{search_word}-2", "shop_name": f"Seller {search_word} Two"},
                                "seo_url": f"/{search_word}-2",
                            },
                        ]
                    },
                }
            }

        mock_fetch_search_products_list.side_effect = _search_payload

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            payload = json.loads(agent.run_discovery())

        self.assertLessEqual(mock_fetch_search_word_suggestion.call_count, 5)
        self.assertGreaterEqual(mock_fetch_search_word_suggestion.call_count, 1)
        self.assertEqual(mock_fetch_search_products_list.call_count, 10)
        self.assertEqual(payload["candidate_count"], 20)
        self.assertEqual(len(payload["products"]), 20)
        self.assertTrue(payload["products"][0]["seller_id"].startswith("seller-"))
        self.assertIn("[1/3] Discovering keywords from seed terms...", stdout.getvalue())
        self.assertIn("[2/3] Fetching products for 10 keywords...", stdout.getvalue())
        self.assertIn("[3/3] Scoring 20 candidates...", stdout.getvalue())
        self.assertIn("Done. Top 20 results ready.", stdout.getvalue())

    @patch("agent.fetch_search_products_list")
    @patch("agent.fetch_search_word_suggestion")
    def test_run_discovery_tool_stays_search_only(self, mock_fetch_search_word_suggestion, mock_fetch_search_products_list):
        import agent

        mock_fetch_search_word_suggestion.return_value = {"data": {"code": 0, "data": ["travel organizer"]}}
        mock_fetch_search_products_list.return_value = {
            "data": {
                "code": 0,
                "data": {
                    "products": [
                        {
                            "product_id": "p1",
                            "title": "Travel Hanging Toiletry Organizer",
                            "image": {"url_list": ["https://example.com/p1.jpg"]},
                            "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                            "rate_info": {"score": 4.8, "review_count": "18"},
                            "sold_info": {"sold_count": 2400},
                            "seller_info": {"seller_id": "seller-1", "shop_name": "Seller One"},
                            "seo_url": "/travel-hanging-toiletry-organizer",
                        }
                    ]
                },
            }
        }

        with patch("agent.fetch_product_detail") as mock_fetch_product_detail:
            payload = json.loads(agent.run_discovery())

        mock_fetch_product_detail.assert_not_called()
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["products"][0]["product_id"], "p1")

    def test_cap_seller_dominance_limits_top_twenty_to_five_per_seller(self):
        import agent

        products = []
        for index in range(8):
            products.append({"product_id": f"a-{index}", "seller_id": "seller-a", "score": 100 - index})
        for index in range(8):
            products.append({"product_id": f"b-{index}", "seller_id": "seller-b", "score": 90 - index})
        for index in range(8):
            products.append({"product_id": f"c-{index}", "seller_id": "seller-c", "score": 80 - index})

        capped = agent._cap_seller_dominance(products, limit=20, max_per_seller=5)

        self.assertEqual(len(capped), 15)
        self.assertEqual(sum(1 for product in capped if product["seller_id"] == "seller-a"), 5)
        self.assertEqual(sum(1 for product in capped if product["seller_id"] == "seller-b"), 5)
        self.assertEqual(sum(1 for product in capped if product["seller_id"] == "seller-c"), 5)
        self.assertEqual(capped[0]["product_id"], "a-0")

    def test_watchlist_tools_round_trip_entries(self):
        import agent

        with tempfile.TemporaryDirectory() as tmpdir:
            watchlist_path = Path(tmpdir) / "watchlist.json"
            with patch.object(agent, "WATCHLIST_PATH", watchlist_path):
                added = json.loads(agent.add_to_watchlist("p1", "Travel Case", "Strong early-window signals"))
                listed = json.loads(agent.get_watchlist())
                removed = json.loads(agent.remove_from_watchlist("p1"))
                empty = json.loads(agent.get_watchlist())

        self.assertEqual(added["status"], "saved")
        self.assertEqual(added["entry"]["product_id"], "p1")
        self.assertEqual(added["entry"]["score"], None)
        self.assertEqual(len(listed["watchlist"]), 1)
        self.assertEqual(listed["watchlist"][0]["reason"], "Strong early-window signals")
        self.assertEqual(removed["status"], "removed")
        self.assertEqual(empty["watchlist"], [])

    def test_chat_loop_reuses_single_session_with_runner(self):
        import agent

        session = object()
        stdout = io.StringIO()
        with (
            patch("builtins.input", side_effect=["find me a travel organizer", "exit"]),
            patch.object(agent, "_create_chat_session", return_value=session) as mock_session_factory,
            patch.object(agent.Runner, "run_sync", return_value=SimpleNamespace(final_output="Top candidates ready")) as mock_run_sync,
            redirect_stdout(stdout),
        ):
            agent.chat_loop()

        mock_session_factory.assert_called_once_with("cli-chat")
        mock_run_sync.assert_called_once()
        self.assertIs(mock_run_sync.call_args.kwargs["session"], session)
        self.assertIn("Avori Agent ready. Type 'exit' to quit.", stdout.getvalue())
        self.assertIn("Agent: Top candidates ready", stdout.getvalue())

    def test_create_chat_session_uses_sqlite_backend(self):
        import agent

        with patch.object(agent, "SQLiteSession", return_value="session") as mock_sqlite_session:
            session = agent._create_chat_session("dashboard-chat")

        self.assertEqual(session, "session")
        mock_sqlite_session.assert_called_once()
        self.assertEqual(mock_sqlite_session.call_args.args[0], "dashboard-chat")

    @patch("agent.fetch_product_detail")
    @patch("agent._extract_detail_bonus_signals")
    @patch("agent._extract_category_names")
    def test_get_product_detail_tool_formats_detail_payload(
        self,
        mock_extract_category_names,
        mock_extract_detail_bonus_signals,
        mock_fetch_product_detail,
    ):
        import agent

        mock_fetch_product_detail.return_value = ("product_detail_v3", {"data": {"product_data": {}}})
        mock_extract_category_names.return_value = ["travel-accessories"]
        mock_extract_detail_bonus_signals.return_value = {"shop_on_sell_product_count": 9}

        payload = json.loads(agent.get_product_detail("1729001"))

        self.assertEqual(payload["product_id"], "1729001")
        self.assertEqual(payload["detail_endpoint"], "product_detail_v3")
        self.assertEqual(payload["category_names"], ["travel-accessories"])
        self.assertEqual(payload["supplementary_signals"]["shop_on_sell_product_count"], 9)

    @patch("agent.fetch_search_products_list")
    def test_search_products_tool_returns_scored_results(self, mock_fetch_search_products_list):
        import agent

        mock_fetch_search_products_list.return_value = {
            "data": {
                "code": 0,
                "data": {
                    "products": [
                        {
                            "product_id": "p1",
                            "title": "Travel Hanging Toiletry Organizer",
                            "image": {"url_list": ["https://example.com/p1.jpg"]},
                            "product_price_info": {"currency_name": "USD", "sale_price_format": "29.99"},
                            "rate_info": {"score": 4.8, "review_count": "18"},
                            "sold_info": {"sold_count": 2400},
                            "seller_info": {"seller_id": "seller-1", "shop_name": "Avori Demo Shop"},
                            "seo_url": "/travel-hanging-toiletry-organizer",
                        }
                    ]
                },
            }
        }

        payload = json.loads(agent.search_products("travel organizer"))

        self.assertEqual(payload["keyword"], "travel organizer")
        self.assertEqual(payload["result_count"], 1)
        self.assertEqual(payload["products"][0]["product_id"], "p1")
        self.assertGreater(payload["products"][0]["score"], 0)


if __name__ == "__main__":
    unittest.main()
