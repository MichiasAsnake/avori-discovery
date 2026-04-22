import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class StorageTests(unittest.TestCase):
    def test_watchlist_velocity_and_graduation_are_computed_from_snapshots(self):
        import storage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "avori_state.sqlite3"
            with patch.object(storage, "STATE_DB_PATH", db_path):
                storage.upsert_watchlist_entry("p1", "Travel Case", "Track this", tracked=True, score=80.0)
                storage.record_watchlist_snapshot(
                    "p1",
                    sold_count=1000,
                    review_count=10,
                    price=20.0,
                    score=80.0,
                    observed_at="2026-04-01T00:00:00Z",
                )
                storage.record_watchlist_snapshot(
                    "p1",
                    sold_count=6000,
                    review_count=40,
                    price=20.0,
                    score=95.0,
                    observed_at="2026-04-08T00:00:00Z",
                )
                entries = storage.list_watchlist_entries()

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["graduated"])
        self.assertEqual(entries[0]["velocity"], 5000.0)

    def test_discovery_jobs_round_trip(self):
        import storage

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "avori_state.sqlite3"
            with patch.object(storage, "STATE_DB_PATH", db_path):
                storage.create_discovery_job("job-123")
                storage.update_discovery_job("job-123", status="completed", payload={"candidate_count": 5}, results_path="/tmp/results.json")
                job = storage.get_discovery_job("job-123")

        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["payload"]["candidate_count"], 5)
