import unittest

from scorer import flag_early_window, rank_products, score_product


class ScorerTests(unittest.TestCase):
    def test_flag_early_window_true_for_high_sales_low_reviews(self):
        product = {"sold_count": 1400, "review_count": 12}

        self.assertTrue(flag_early_window(product))

    def test_flag_early_window_false_when_review_count_too_high(self):
        product = {"sold_count": 1400, "review_count": 45}

        self.assertFalse(flag_early_window(product))

    def test_score_product_adds_numeric_score(self):
        product = {
            "product_id": "p1",
            "title": "Travel organizer",
            "sold_count": 2400,
            "review_count": 22,
            "rating": 4.8,
            "creator_video_count": 18,
            "seller_catalog_count": 9,
        }

        scored = score_product(product)

        self.assertIn("score", scored)
        self.assertGreater(scored["score"], 0)
        self.assertTrue(scored["early_window"])

    def test_rank_products_orders_by_signal_score_desc(self):
        products = [
            {
                "product_id": "a",
                "title": "A",
                "sold_count": 3000,
                "review_count": 1400,
                "rating": 4.2,
                "creator_video_count": 3,
                "seller_catalog_count": 320,
            },
            {
                "product_id": "b",
                "title": "B",
                "sold_count": 2100,
                "review_count": 18,
                "rating": 4.9,
                "creator_video_count": 21,
                "seller_catalog_count": 12,
            },
        ]

        ranked = rank_products(products)

        self.assertEqual(ranked[0]["product_id"], "b")
        self.assertEqual(ranked[1]["product_id"], "a")

    def test_score_product_preserves_supplementary_signals_without_changing_core_scoring(self):
        product = {
            "product_id": "p3",
            "title": "Travel organizer deluxe",
            "sold_count": 2400,
            "review_count": 22,
            "rating": 4.8,
            "creator_video_count": 18,
            "seller_catalog_count": 9,
            "related_video_count": 6,
            "shop_review_count": 340,
            "shop_follower_count": 1200,
            "shop_on_sell_product_count": 48,
            "shop_performance_count": 3,
        }

        scored = score_product(product)

        self.assertIn("supplementary_signals", scored)
        self.assertEqual(scored["supplementary_signals"]["related_video_count"], 6)
        self.assertEqual(scored["supplementary_signals"]["shop_performance_count"], 3)


if __name__ == "__main__":
    unittest.main()
