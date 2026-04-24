import unittest

from signal_score import score_product_signal
from scorer import score_product


class ProductSignalScoreTests(unittest.TestCase):
    def test_score_product_signal_breaks_out_actionable_components(self):
        product = {
            "product_id": "winner-1",
            "title": "Travel Makeup Bag Organizer for Purse and Toiletries",
            "price": 18.99,
            "sold_count": 2800,
            "review_count": 24,
            "rating": 4.8,
            "creator_video_count": 14,
            "related_video_count": 9,
            "seller_catalog_count": 18,
            "shop_follower_count": 1800,
            "shop_review_count": 420,
            "shop_performance_count": 3,
            "velocity": 640,
            "category_names": ["Beauty & Personal Care", "Travel Accessories"],
        }

        signal = score_product_signal(product)

        self.assertGreaterEqual(signal["final_score"], 65)
        self.assertEqual(signal["decision"], "deep_dive")
        self.assertEqual(signal["components"]["niche_bonus"], 5)
        self.assertGreater(signal["components"]["demand_signal"], 0)
        self.assertGreater(signal["components"]["content_signal"], 0)
        self.assertGreater(signal["components"]["velocity_signal"], 0)
        self.assertLess(signal["components"]["risk_penalty"], 10)
        self.assertIn("Strong demand", signal["reasons"])
        self.assertIn("TikTok content signal", signal["reasons"])
        self.assertEqual(signal["next_step"], "Build a sourcing and content-angle deep dive.")

    def test_score_product_signal_penalizes_saturated_or_low_quality_products(self):
        product = {
            "product_id": "late-1",
            "title": "Generic Phone Cable",
            "price": 4.99,
            "sold_count": 50000,
            "review_count": 12000,
            "rating": 3.7,
            "creator_video_count": 0,
            "related_video_count": 0,
            "seller_catalog_count": 500,
            "shop_follower_count": 20,
            "shop_review_count": 5,
            "category_names": ["Electronics"],
        }

        signal = score_product_signal(product)

        self.assertLess(signal["final_score"], 45)
        self.assertEqual(signal["decision"], "skip")
        self.assertGreaterEqual(signal["components"]["risk_penalty"], 20)
        self.assertIn("Saturated review profile", signal["risks"])
        self.assertIn("Weak rating", signal["risks"])

    def test_score_product_preserves_legacy_score_and_adds_product_signal(self):
        product = {
            "product_id": "p1",
            "title": "Purse organizer insert",
            "price": 16.99,
            "sold_count": 1500,
            "review_count": 20,
            "rating": 4.7,
            "creator_video_count": 6,
            "related_video_count": 4,
            "seller_catalog_count": 10,
        }

        scored = score_product(product)

        self.assertIn("score", scored)
        self.assertIn("product_signal", scored)
        self.assertIn("signal_score", scored)
        self.assertIn(scored["product_signal"]["decision"], {"watch", "deep_dive", "test_now"})
        self.assertEqual(scored["signal_score"], scored["product_signal"]["final_score"])


if __name__ == "__main__":
    unittest.main()
