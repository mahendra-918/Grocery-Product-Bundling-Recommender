"""
Unit & Integration Tests for Association Rules, Model Artifacts, and Recommender Engine.
"""

import json
import pickle
import unittest
from pathlib import Path
from ml.recommender import GroceryRecommender

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


class TestModelArtifacts(unittest.TestCase):
    """Verifies that all required production artifacts exist and conform to schemas."""

    def test_artifacts_exist_and_non_empty(self):
        rules_file = MODELS_DIR / "association_rules.pkl"
        products_file = MODELS_DIR / "products.json"
        bundles_file = MODELS_DIR / "top_bundles.json"

        self.assertTrue(rules_file.exists(), f"Missing {rules_file}")
        self.assertTrue(products_file.exists(), f"Missing {products_file}")
        self.assertTrue(bundles_file.exists(), f"Missing {bundles_file}")

        self.assertGreater(rules_file.stat().st_size, 1000)
        self.assertGreater(products_file.stat().st_size, 500)
        self.assertGreater(bundles_file.stat().st_size, 500)

    def test_products_catalog(self):
        with open(MODELS_DIR / "products.json", "r", encoding="utf-8") as f:
            products = json.load(f)

        self.assertEqual(len(products), 169, f"Expected 169 SKUs, got {len(products)}")
        self.assertIn("whole milk", products)
        self.assertIn("other vegetables", products)
        self.assertIn("rolls/buns", products)
        self.assertIn("yogurt", products)

    def test_top_bundles_schema(self):
        with open(MODELS_DIR / "top_bundles.json", "r", encoding="utf-8") as f:
            bundles = json.load(f)

        self.assertEqual(len(bundles), 6, f"Expected 6 curated bundles, got {len(bundles)}")
        required_keys = {
            "bundle_id", "name", "category", "items", "description",
            "support_pct", "orders_count", "synergy_lift",
            "original_price", "bundle_price", "discount_pct"
        }

        for b in bundles:
            self.assertTrue(required_keys.issubset(b.keys()), f"Bundle missing keys: {b}")
            self.assertGreaterEqual(len(b["items"]), 3, f"Bundle has fewer than 3 items: {b['bundle_id']}")
            self.assertGreater(b["original_price"], b["bundle_price"])
            self.assertGreater(b["discount_pct"], 0)
            self.assertGreater(b["synergy_lift"], 1.0)


class TestGroceryRecommender(unittest.TestCase):
    """Verifies in-memory recommendation query logic, ranking, explainability, and fallbacks."""

    @classmethod
    def setUpClass(cls):
        cls.recommender = GroceryRecommender()

    def test_recommender_initialization(self):
        self.assertGreater(len(self.recommender.rules), 0)
        self.assertEqual(len(self.recommender.get_products()), 169)
        self.assertEqual(len(self.recommender.get_bundles()), 6)

    def test_recommend_single_item(self):
        res = self.recommender.recommend(["yogurt"], top_k=5)
        self.assertEqual(res["strategy"], "association_rule")
        self.assertGreater(len(res["recommendations"]), 0)
        self.assertLessEqual(len(res["recommendations"]), 5)

        recommended_items = [r["item"] for r in res["recommendations"]]
        self.assertNotIn("yogurt", recommended_items, "Cart item should not be recommended")

        for r in res["recommendations"]:
            self.assertIn("item", r)
            self.assertIn("triggered_by", r)
            self.assertGreaterEqual(r["lift"], 1.15)
            self.assertGreaterEqual(r["confidence"], 20.0)

    def test_recommend_multi_item_basket(self):
        cart = ["tropical fruit", "whole milk"]
        res = self.recommender.recommend(cart, top_k=5)
        self.assertEqual(res["strategy"], "association_rule")
        self.assertGreater(len(res["recommendations"]), 0)

        recommended_items = [r["item"] for r in res["recommendations"]]
        for item in cart:
            self.assertNotIn(item, recommended_items, f"{item} should not be in recommendations")

    def test_recommend_excludes_cart_items(self):
        cart = ["root vegetables", "other vegetables", "whole milk"]
        res = self.recommender.recommend(cart, top_k=5)
        recommended_items = [r["item"] for r in res["recommendations"]]
        for item in cart:
            self.assertNotIn(item, recommended_items)

    def test_recommend_cold_start_fallback(self):
        res = self.recommender.recommend(["rare_nonexistent_product_xyz"], top_k=5)
        self.assertEqual(res["strategy"], "fallback_staples")
        self.assertIn("rare_nonexistent_product_xyz", res["unknown_items"])
        self.assertGreater(len(res["recommendations"]), 0)

    def test_recommend_empty_cart(self):
        res = self.recommender.recommend([], top_k=5)
        self.assertEqual(res["strategy"], "fallback_staples")
        self.assertGreater(len(res["recommendations"]), 0)

    def test_get_bundle_by_id(self):
        bundle = self.recommender.get_bundle_by_id("bundle_produce_stew")
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle["bundle_id"], "bundle_produce_stew")
        self.assertEqual(bundle["name"], "Fresh Stew & Veggie Pack")

        invalid = self.recommender.get_bundle_by_id("non_existent_id")
        self.assertIsNone(invalid)


if __name__ == "__main__":
    unittest.main()
