import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index_reports_api_status(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["vercel_ready"])

    @patch("api.index.run_discovery")
    def test_discovery_run_returns_agent_payload(self, mock_run_discovery):
        mock_run_discovery.return_value = '{"candidate_count": 1, "products": [{"product_id": "p1"}]}'

        response = self.client.post("/discovery/run")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidate_count"], 1)

    @patch("api.index.search_products")
    def test_products_search_returns_payload(self, mock_search_products):
        mock_search_products.return_value = '{"keyword": "travel bag", "result_count": 1, "products": [{"product_id": "p1"}]}'

        response = self.client.get("/products/search", params={"keyword": "travel bag"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["keyword"], "travel bag")

    @patch("api.index.add_to_watchlist")
    def test_watchlist_add_posts_entry(self, mock_add_to_watchlist):
        mock_add_to_watchlist.return_value = '{"status": "saved", "entry": {"product_id": "p1"}}'

        response = self.client.post(
            "/watchlist",
            json={"product_id": "p1", "title": "Travel Case", "reason": "Strong candidate"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "saved")


if __name__ == "__main__":
    unittest.main()
