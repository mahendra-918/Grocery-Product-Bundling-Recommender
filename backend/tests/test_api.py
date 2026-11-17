"""
Integration & End-to-End API Test Suite for Grocery Recommender Service.
Validates HTTP endpoints, response schemas, error handling, and latency bounds.
"""

import unittest
from fastapi.testclient import TestClient
from backend.main import app


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

    def test_recommend_cold_start_fallback(self):
        payload = {
            "items": ["non_existent_exotic_dragonfruit_xyz"],
            "top_k": 3
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["strategy"], "fallback_staples")
        self.assertIn("non_existent_exotic_dragonfruit_xyz", data["unknownItems"])
        self.assertGreater(len(data["recommendations"]), 0)

    def test_recommend_empty_cart(self):
        payload = {
            "items": [],
            "top_k": 3
        }
        response = self.client.post("/api/v1/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["strategy"], "fallback_staples")
        self.assertGreater(len(data["recommendations"]), 0)

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
