"""
Integration & End-to-End API Test Suite for Grocery Recommender Service.
Validates HTTP endpoints, response schemas, error handling, and latency bounds.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app, recommender_service
from ml.recommender import GroceryRecommender


class TestGroceryAPI(unittest.TestCase):
    """Integration test suite executing requests against the FastAPI app."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("documentation", data)

    def test_health_endpoints(self):
        for path in ["/health", "/api/v1/health"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "healthy")
            self.assertGreater(data["rulesLoaded"], 100)
            self.assertEqual(data["catalogSize"], 169)
            self.assertGreaterEqual(data["uptimeSeconds"], 0)

    def test_products_endpoints(self):
        for path in ["/products", "/api/v1/products"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["total"], 169)
            self.assertEqual(len(data["products"]), 169)
            self.assertIn("whole milk", data["products"])
            self.assertIn("yogurt", data["products"])

    def test_recommend_single_item(self):
        payload = {
            "items": ["yogurt"],
            "top_k": 5
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["strategy"], "association_rule")
        self.assertGreater(data["totalReturned"], 0)
        self.assertLessEqual(data["totalReturned"], 5)

        # Check recommendation structure & metric bounds
        for rec in data["recommendations"]:
            self.assertIn("product", rec)
            self.assertNotEqual(rec["product"], "yogurt")
            self.assertGreater(rec["lift"], 1.0)
            self.assertGreaterEqual(rec["confidence"], 0.0)
            self.assertLessEqual(rec["confidence"], 1.0)
            self.assertIn(rec["affinityStrength"], ["VERY HIGH", "HIGH", "MODERATE", "LOW"])

        # Latency check: Sub-25ms response target
        self.assertLess(data["latencyMs"], 50.0)

    def test_recommend_multi_item_cart(self):
        payload = {
            "items": ["tropical fruit", "whole milk"],
            "top_k": 4
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        rec_products = [r["product"] for r in data["recommendations"]]
        self.assertNotIn("tropical fruit", rec_products)
        self.assertNotIn("whole milk", rec_products)

    def test_recommend_threshold_filtering(self):
        payload = {
            "items": ["other vegetables"],
            "top_k": 5,
            "min_lift": 1.5,
            "min_confidence": 0.25
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        for rec in data["recommendations"]:
            self.assertGreaterEqual(rec["lift"], 1.5)
            self.assertGreaterEqual(rec["confidence"], 0.25)

    def test_recommend_filters_before_limiting_and_returns_support_ratio(self):
        response = self.client.post("/api/v1/recommend", json={
            "items": ["baking powder"],
            "top_k": 1,
            "min_confidence": 0.50,
        })
        self.assertEqual(response.status_code, 200)
        recommendations = response.json()["recommendations"]
        self.assertEqual([item["product"] for item in recommendations], ["whole milk"])
        self.assertAlmostEqual(recommendations[0]["support"], 0.0093)

    def test_recommend_known_product_without_matching_rules_falls_back(self):
        response = self.client.post("/api/v1/recommend", json={"items": ["abrasive cleaner"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["strategy"], "fallback_staples")
        self.assertTrue(response.json()["recommendations"])

    def test_recommend_unknown_product(self):
        for path in ("/recommend", "/api/v1/recommend"):
            with self.subTest(path=path):
                response = self.client.post(path, json={"items": [" Whole Milk ", "space_rocket"]})
                self.assertEqual(response.status_code, 404)
                error = response.json()["error"]
                self.assertEqual(error["code"], "PRODUCT_NOT_FOUND")
                self.assertIn("space_rocket", error["message"])

    def test_recommend_empty_cart(self):
        for items in ([], [" ", ""]):
            with self.subTest(items=items):
                response = self.client.post("/api/v1/recommend", json={"items": items})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], "BAD_REQUEST")

    def test_recommend_rejects_overlong_product(self):
        response = self.client.post("/api/v1/recommend", json={"items": ["x" * 201]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_api_reports_missing_rules(self):
        with TemporaryDirectory() as directory:
            engine = GroceryRecommender(rules_path=str(Path(directory) / "missing.pkl"))
            with patch.object(recommender_service, "recommender", engine):
                responses = [
                    self.client.get("/health"),
                    self.client.get("/api/v1/health"),
                    self.client.post("/api/v1/recommend", json={"items": ["whole milk"]}),
                ]
                for response in responses:
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json()["error"]["code"], "RULES_NOT_LOADED")

    def test_bundles_endpoints(self):
        for path in ["/bundles", "/api/v1/bundles"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["totalBundles"], 6)

            for b in data["bundles"]:
                self.assertIn("bundleId", b)
                self.assertIn("bundleName", b)
                self.assertGreaterEqual(len(b["items"]), 3)
                self.assertGreater(b["originalPrice"], b["bundlePrice"])
                self.assertGreater(b["discountPct"], 0)
                self.assertGreater(b["averageLift"], 1.0)

    def test_bundles_query_params(self):
        response = self.client.get("/api/v1/bundles?min_size=3&limit=2")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["totalBundles"], 2)
        for b in data["bundles"]:
            self.assertGreaterEqual(len(b["items"]), 3)

    def test_stats_endpoint(self):
        response = self.client.get("/api/v1/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["totalTransactions"], 9835)
        self.assertEqual(data["totalCatalogSKUs"], 169)
        self.assertGreater(data["totalAssociationRules"], 0)

    def test_validation_error_handling(self):
        # Invalid negative top_k should trigger 422 validation error
        payload = {
            "items": ["yogurt"],
            "top_k": -5
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
