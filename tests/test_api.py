import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index_reports_api_status(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["vercel_ready"])

    @patch("app._run_discovery_job")
    @patch("app.create_discovery_job")
    @patch("app.uuid4")
    def test_discovery_run_returns_job_payload(self, mock_uuid4, mock_create_discovery_job, _mock_run_discovery_job):
        mock_uuid4.return_value = type("UUID", (), {"hex": "job-123"})()
        mock_create_discovery_job.return_value = {"job_id": "job-123", "status": "queued"}

        response = self.client.post("/discovery/run")

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["job_id"], "job-123")
        self.assertEqual(response.json()["status"], "queued")

    @patch("app.get_discovery_job")
    def test_discovery_status_returns_job_payload(self, mock_get_discovery_job):
        mock_get_discovery_job.return_value = {"job_id": "job-123", "status": "completed", "payload": {"candidate_count": 1}}

        response = self.client.get("/discovery/jobs/job-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")

    @patch("app.search_products")
    def test_products_search_returns_payload(self, mock_search_products):
        mock_search_products.return_value = '{"keyword": "travel bag", "result_count": 1, "products": [{"product_id": "p1"}]}'

        response = self.client.get("/products/search", params={"keyword": "travel bag"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["keyword"], "travel bag")

    @patch("app.chat_with_agent")
    def test_chat_endpoint_returns_reply(self, mock_chat_with_agent):
        mock_chat_with_agent.return_value = '{"reply": "Strong candidate", "session_id": "session-1"}'

        response = self.client.post("/chat", json={"message": "Assess this candidate", "session_id": "session-1"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "Strong candidate")
        self.assertEqual(response.json()["session_id"], "session-1")

    @patch("app.add_to_watchlist")
    def test_watchlist_add_posts_entry(self, mock_add_to_watchlist):
        mock_add_to_watchlist.return_value = '{"status": "saved", "entry": {"product_id": "p1"}}'

        response = self.client.post(
            "/watchlist",
            json={"product_id": "p1", "title": "Travel Case", "reason": "Strong candidate", "track": True, "score": 91.2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "saved")


if __name__ == "__main__":
    unittest.main()
