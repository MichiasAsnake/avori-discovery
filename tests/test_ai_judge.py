import json
import unittest

from ai_judge import analyze_product, build_product_judgment_prompt, validate_product_judgment


class AiJudgeTests(unittest.TestCase):
    def test_analyze_product_returns_strict_fallback_memo_without_llm_client(self):
        product = {
            "product_id": "purse-1",
            "title": "Everyday Purse Organizer Insert",
            "price": 16.99,
            "sold_count": 1800,
            "review_count": 22,
            "rating": 4.7,
            "creator_video_count": 7,
            "related_video_count": 5,
            "seller_catalog_count": 12,
            "category_names": ["Bag Organizers", "Travel Accessories"],
        }

        memo = analyze_product(product)

        self.assertEqual(memo["product_id"], "purse-1")
        self.assertEqual(memo["judge_source"], "heuristic")
        self.assertIn(memo["decision"], {"watch", "deep_dive", "test_now"})
        self.assertGreaterEqual(memo["confidence"], 0.5)
        self.assertTrue(memo["content_angles"])
        self.assertTrue(memo["why_it_might_sell"])
        self.assertIn("signal_snapshot", memo)
        self.assertIn("final_score", memo["signal_snapshot"])
        self.assertIn("prompt_version", memo)

    def test_analyze_product_uses_injected_llm_client_and_validates_json(self):
        product = {
            "product_id": "makeup-1",
            "title": "Wide Open Makeup Bag",
            "price": 21.99,
            "sold_count": 2600,
            "review_count": 30,
            "rating": 4.8,
            "related_video_count": 8,
            "category_names": ["Beauty", "Travel"],
        }
        calls = []

        def fake_client(prompt):
            calls.append(prompt)
            return json.dumps(
                {
                    "decision": "deep_dive",
                    "confidence": 0.82,
                    "ideal_customer": "Women who want a visible travel makeup routine.",
                    "why_it_might_sell": ["Clear packing pain point", "Strong TikTok demo potential"],
                    "content_angles": ["Everything fits and stays visible", "Pack with me for a weekend trip"],
                    "risks": ["Need to confirm shipping speed"],
                    "recommended_next_step": "Check sourcing margin and build a UGC test brief.",
                }
            )

        memo = analyze_product(product, llm_client=fake_client)

        self.assertEqual(len(calls), 1)
        self.assertIn("Return ONLY valid JSON", calls[0])
        self.assertEqual(memo["judge_source"], "llm")
        self.assertEqual(memo["decision"], "deep_dive")
        self.assertEqual(memo["confidence"], 0.82)
        self.assertEqual(memo["recommended_next_step"], "Check sourcing margin and build a UGC test brief.")
        self.assertIn("signal_snapshot", memo)

    def test_invalid_llm_payload_falls_back_to_heuristic_memo(self):
        product = {
            "product_id": "bad-json-1",
            "title": "Generic Cable Organizer",
            "price": 4.99,
            "sold_count": 50000,
            "review_count": 9000,
            "rating": 3.8,
        }

        memo = analyze_product(product, llm_client=lambda _prompt: "not json")

        self.assertEqual(memo["judge_source"], "heuristic")
        self.assertEqual(memo["llm_error"], "invalid_json")
        self.assertIn(memo["decision"], {"skip", "watch", "deep_dive", "test_now"})

    def test_validate_product_judgment_normalizes_missing_and_invalid_fields(self):
        product = {"product_id": "p2", "title": "Travel Organizer", "price": 19.99}
        raw = {
            "decision": "buy_immediately",
            "confidence": 9,
            "content_angles": "before and after bag cleanup",
            "why_it_might_sell": [],
        }

        memo = validate_product_judgment(raw, product, judge_source="llm")

        self.assertEqual(memo["decision"], "watch")
        self.assertEqual(memo["confidence"], 1.0)
        self.assertEqual(memo["content_angles"], ["before and after bag cleanup"])
        self.assertTrue(memo["ideal_customer"])
        self.assertTrue(memo["recommended_next_step"])

    def test_invalid_llm_payload_with_non_finite_json_falls_back(self):
        product = {"product_id": "nan-llm", "title": "Purse Organizer", "price": 16.99}

        memo = analyze_product(
            product,
            llm_client=lambda _prompt: '{"decision":"watch","confidence": NaN}',
        )

        self.assertEqual(memo["judge_source"], "heuristic")
        self.assertEqual(memo["llm_error"], "invalid_json")

    def test_malformed_product_signal_from_user_input_is_recomputed(self):
        product = {
            "product_id": "malformed-signal",
            "title": "Purse Organizer Insert",
            "price": 16.99,
            "sold_count": 1400,
            "review_count": 20,
            "rating": 4.7,
            "product_signal": {"final_score": "not-a-number", "decision": "deep_dive"},
        }

        memo = analyze_product(product)

        self.assertEqual(memo["product_id"], "malformed-signal")
        self.assertIsInstance(memo["signal_snapshot"]["final_score"], float)
        self.assertIn(memo["decision"], {"watch", "deep_dive", "test_now", "skip"})

    def test_validate_product_judgment_falls_back_for_blank_required_strings(self):
        product = {"product_id": "blank-fields", "title": "Purse Organizer", "price": 16.99}
        raw = {
            "decision": "watch",
            "confidence": 0.7,
            "ideal_customer": "   ",
            "recommended_next_step": "   ",
            "why_it_might_sell": ["Useful organization demo"],
            "content_angles": ["before and after"],
            "risks": [],
        }

        memo = validate_product_judgment(raw, product, judge_source="llm")

        self.assertTrue(memo["ideal_customer"].strip())
        self.assertTrue(memo["recommended_next_step"].strip())

    def test_prompt_builder_sanitizes_non_finite_product_values(self):
        product = {
            "product_id": "nan-prompt",
            "title": "Purse Organizer",
            "price": float("nan"),
            "sold_count": 1400,
            "review_count": 20,
        }

        prompt = build_product_judgment_prompt(product)

        self.assertNotIn("NaN", prompt)
        self.assertIn('"price": null', prompt)

    def test_prompt_includes_product_signal_and_schema(self):
        product = {
            "product_id": "p3",
            "title": "Mini Travel Jewelry Case",
            "price": 18.99,
            "sold_count": 1200,
            "review_count": 18,
            "rating": 4.9,
        }

        prompt = build_product_judgment_prompt(product)

        self.assertIn("Mini Travel Jewelry Case", prompt)
        self.assertIn("product_signal", prompt)
        self.assertIn("content_angles", prompt)
        self.assertIn("recommended_next_step", prompt)


if __name__ == "__main__":
    unittest.main()
