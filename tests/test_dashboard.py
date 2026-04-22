import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class DashboardHelperTests(unittest.TestCase):
    def test_load_latest_results_file_prefers_most_recent(self):
        import dashboard

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            older = output_dir / "avori_results_2026-04-18.json"
            newer = output_dir / "avori_results_2026-04-19.json"
            older.write_text(json.dumps({"run_date": "2026-04-18"}))
            newer.write_text(json.dumps({"run_date": "2026-04-19"}))

            payload = dashboard.load_latest_results_file(output_dir)

            self.assertEqual(payload["run_date"], "2026-04-19")

    def test_apply_product_filters_honors_price_sold_and_early_window(self):
        import dashboard

        products = [
            {"product_id": "a", "price": 12.0, "sold_count": 1200, "early_window": True},
            {"product_id": "b", "price": 32.0, "sold_count": 800, "early_window": False},
            {"product_id": "c", "price": 22.0, "sold_count": 50, "early_window": True},
        ]

        filtered = dashboard.apply_product_filters(
            products,
            price_range=(10.0, 25.0),
            min_sold_count=100,
            early_window_only=True,
        )

        self.assertEqual([product["product_id"] for product in filtered], ["a"])

    def test_build_stats_summary_reports_keyword_counts(self):
        import dashboard

        stats = dashboard.build_stats_summary(
            products=[
                {"product_id": "a", "early_window": True},
                {"product_id": "b", "early_window": False},
                {"product_id": "c", "early_window": True},
            ],
            discovered_keywords=["travel organizer", "makeup organizer"],
            keyword_product_counts={"travel organizer": 25, "makeup organizer": 12},
        )

        self.assertEqual(stats["total_candidates"], 3)
        self.assertEqual(stats["early_window_count"], 2)
        self.assertEqual(stats["keywords_discovered"], 2)
        self.assertEqual(stats["top_keyword"], "travel organizer")

    def test_prepare_table_rows_adds_rank_and_truncates_title(self):
        import dashboard

        rows = dashboard.prepare_table_rows(
            [
                {
                    "product_id": "p1",
                    "title": "Travel Hanging Toiletry Organizer With Very Long Descriptive Title",
                    "price": 29.99,
                    "sold_count": 2400,
                    "review_count": 18,
                    "score": 91.4,
                    "early_window": True,
                    "seller_name": "Avori Demo Shop",
                    "discovered_keywords": ["travel organizer"],
                }
            ]
        )

        self.assertEqual(rows[0]["rank"], 1)
        self.assertTrue(rows[0]["title"].endswith("..."))
        self.assertEqual(rows[0]["keyword"], "travel organizer")

    def test_tool_results_payload_prefers_results_file(self):
        import dashboard

        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "avori_results_2026-04-22.json"
            results_path.write_text(json.dumps({"products": [{"product_id": "p1"}]}))

            payload = dashboard._tool_results_to_payload({"results_path": str(results_path), "products": []})

        self.assertEqual(payload["products"][0]["product_id"], "p1")

    def test_seo_url_value_builds_absolute_url(self):
        import dashboard

        url = dashboard._seo_url_value({"seo_url": "/travel-hanging-toiletry-organizer"})

        self.assertTrue(url.startswith("https://shop.tiktok.com/"))

    def test_format_review_summary_rows_flattens_values(self):
        import dashboard

        rows = dashboard.format_review_summary_rows({"review_count": 18, "average_rating": 4.8})

        self.assertEqual(rows[0][0], "Review Count")
        self.assertEqual(rows[0][1], 18)

    @patch("dashboard.agent_get_watchlist")
    def test_load_watchlist_uses_agent_tool_payload(self, mock_get_watchlist):
        import dashboard

        mock_get_watchlist.return_value = json.dumps(
            {
                "watchlist": [
                    {
                        "product_id": "p1",
                        "title": "Travel Case",
                        "reason": "Early window",
                        "added_at": "2026-04-19",
                        "score": None,
                    }
                ]
            }
        )

        watchlist = dashboard.load_watchlist()

        self.assertEqual(len(watchlist), 1)
        self.assertEqual(watchlist[0]["product_id"], "p1")
        self.assertEqual(watchlist[0]["reason"], "Early window")

    @patch("dashboard.Runner.run_sync")
    def test_run_chat_turn_uses_session(self, mock_run_sync):
        import dashboard

        session = object()
        mock_run_sync.return_value = SimpleNamespace(final_output="This looks promising.")

        reply = dashboard.run_chat_turn(session, "Compare this to a packing cube")

        self.assertEqual(reply, "This looks promising.")
        mock_run_sync.assert_called_once()
        self.assertIs(mock_run_sync.call_args.kwargs["session"], session)
        self.assertEqual(mock_run_sync.call_args.args[1], "Compare this to a packing cube")

    def test_create_dashboard_session_uses_local_chat_session(self):
        import dashboard

        with patch.object(dashboard, "_create_chat_session", return_value="session") as mock_create_chat_session:
            session = dashboard.create_dashboard_session()

        self.assertEqual(session, "session")
        mock_create_chat_session.assert_called_once_with("streamlit-dashboard")


if __name__ == "__main__":
    unittest.main()
