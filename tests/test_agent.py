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
        self.assertEqual(agent.agent.model, "gpt-4o-mini")
        self.assertEqual(agent.agent.__class__.__name__, "Agent")
        self.assertTrue(callable(agent.run_discovery))
        self.assertTrue(callable(agent.get_product_detail))
        self.assertTrue(callable(agent.search_products))
        self.assertTrue(callable(agent.add_to_watchlist))
        self.assertTrue(callable(agent.get_watchlist))
        self.assertTrue(callable(agent.remove_from_watchlist))
        self.assertTrue(callable(agent.refresh_watchlist_tracking))
        self.assertTrue(callable(agent.analyze_product_candidate))
        self.assertIn("thinking partner", agent.agent.instructions)
        self.assertIn("watchlist", agent.agent.instructions)

    def test_run_discovery_tool_returns_canonical_payload(self):
        import agent

        with tempfile.TemporaryDirectory() as tmpdir:
            results_path = Path(tmpdir) / "avori_results_2026-04-22.json"
            results_path.write_text(json.dumps({"products": [{"product_id": "p1"}]}))
            with patch.object(
                agent,
                "run_canonical_discovery",
                return_value={
                    "results_payload": {
                        "run_date": "2026-04-22",
                        "products": [{"product_id": "p1", "category_names": ["travel-accessories"]}],
                        "discovered_keywords": ["travel organizer"],
                    },
                    "results_path": results_path,
                    "brief_path": Path(tmpdir) / "avori_daily_brief.txt",
                },
            ):
                payload = json.loads(agent.run_discovery())

        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["products"][0]["category_names"], ["travel-accessories"])
        self.assertEqual(payload["results_path"], str(results_path))

    def test_watchlist_tools_round_trip_entries(self):
        import agent
        import storage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "avori_state.sqlite3"
            with patch.object(storage, "STATE_DB_PATH", db_path):
                added = json.loads(
                    agent.add_to_watchlist(
                        "p1",
                        "Travel Case",
                        "Strong early-window signals",
                        True,
                        91.2,
                        1400,
                        22,
                        29.99,
                    )
                )
                listed = json.loads(agent.get_watchlist())
                removed = json.loads(agent.remove_from_watchlist("p1"))
                empty = json.loads(agent.get_watchlist())

        self.assertEqual(added["status"], "saved")
        self.assertTrue(added["entry"]["track"])
        self.assertEqual(len(listed["watchlist"]), 1)
        self.assertEqual(listed["watchlist"][0]["latest_sold_count"], 1400)
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
    @patch("agent._extract_review_summary")
    def test_get_product_detail_tool_formats_detail_payload(
        self,
        mock_extract_review_summary,
        mock_extract_category_names,
        mock_extract_detail_bonus_signals,
        mock_fetch_product_detail,
    ):
        import agent

        mock_fetch_product_detail.return_value = ("product_detail_v3", {"data": {"product_data": {}}})
        mock_extract_category_names.return_value = ["travel-accessories"]
        mock_extract_detail_bonus_signals.return_value = {"shop_on_sell_product_count": 9}
        mock_extract_review_summary.return_value = {"review_count": 18}

        payload = json.loads(agent.get_product_detail("1729001"))

        self.assertEqual(payload["product_id"], "1729001")
        self.assertEqual(payload["detail_endpoint"], "product_detail_v3")
        self.assertEqual(payload["category_names"], ["travel-accessories"])
        self.assertEqual(payload["review_summary"]["review_count"], 18)
        self.assertEqual(payload["supplementary_signals"]["shop_on_sell_product_count"], 9)

    def test_search_products_tool_returns_scored_results(self):
        import agent

        with patch.object(
            agent,
            "search_keyword_candidates",
            return_value={
                "keyword": "travel organizer",
                "result_count": 1,
                "products": [{"product_id": "p1", "score": 91.4}],
            },
        ):
            payload = json.loads(agent.search_products("travel organizer"))

        self.assertEqual(payload["keyword"], "travel organizer")
        self.assertEqual(payload["result_count"], 1)
        self.assertEqual(payload["products"][0]["product_id"], "p1")
        self.assertGreater(payload["products"][0]["score"], 0)

    def test_analyze_product_candidate_tool_returns_memo(self):
        import agent

        product_json = json.dumps(
            {
                "product_id": "p-analysis",
                "title": "Purse Organizer Insert",
                "price": 16.99,
                "sold_count": 1400,
                "review_count": 20,
                "rating": 4.7,
            }
        )

        payload = json.loads(agent.analyze_product_candidate(product_json))

        self.assertEqual(payload["product_id"], "p-analysis")
        self.assertIn("decision", payload)
        self.assertIn("content_angles", payload)
        self.assertIn("signal_snapshot", payload)

    def test_analyze_product_candidate_rejects_non_finite_json_constants(self):
        import agent

        payload = json.loads(agent.analyze_product_candidate('{"product_id":"bad","price": NaN}'))

        self.assertEqual(payload["error"], "invalid_product_json")


if __name__ == "__main__":
    unittest.main()
