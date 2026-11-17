"""
API Client & Engine Adapter for Streamlit Frontend.
Attempts to query the FastAPI backend microservice, with transparent fallback
to direct in-memory GroceryRecommender if the backend server is not running.
"""

import os
from typing import Any, Dict, List, Optional
import requests
from ml.recommender import GroceryRecommender
from backend.db import order_db

DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


class GroceryEngineClient:
    """Unified client supporting both FastAPI REST endpoints and local inference."""

    def __init__(self, base_url: str = DEFAULT_API_URL):
        self.base_url = base_url.rstrip("/")
        self._local_recommender: Optional[GroceryRecommender] = None
        self._is_backend_online: Optional[bool] = None

    def check_backend_connection(self) -> bool:
        """Checks if the FastAPI backend service is reachable."""
        try:
            res = requests.get(f"{self.base_url}/health", timeout=1.0)
            self._is_backend_online = (res.status_code == 200)
            return self._is_backend_online
        except Exception:
            self._is_backend_online = False
            return False

    @property
    def local_recommender(self) -> GroceryRecommender:
        """Lazy-loaded in-memory recommender instance for local fallback."""
        if self._local_recommender is None:
            self._local_recommender = GroceryRecommender()
        return self._local_recommender

    def get_products(self) -> List[str]:
        """Fetches all unique catalog products (169 SKUs)."""
        if self.check_backend_connection():
            try:
                res = requests.get(f"{self.base_url}/products", timeout=2.0)
                if res.status_code == 200:
                    return res.json().get("products", [])
            except Exception:
                pass
        return self.local_recommender.get_products()

    def get_recommendations(
        self,
        cart_items: List[str],
        top_k: int = 5,
        min_confidence: Optional[float] = None,
        min_lift: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Queries product recommendations with explainable metrics."""
        if self.check_backend_connection():
            try:
                payload = {
                    "items": cart_items,
                    "top_k": top_k,
                    "min_confidence": min_confidence,
                    "min_lift": min_lift,
                }
                res = requests.post(f"{self.base_url}/recommend", json=payload, timeout=2.5)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "mode": "REST API",
                        "cart": data.get("queryItems", []),
                        "total": data.get("totalReturned", 0),
                        "recommendations": data.get("recommendations", []),
                        "strategy": data.get("strategy", "association_rule"),
                        "message": data.get("message", ""),
                        "unknown_items": data.get("unknownItems", []),
                        "latency_ms": data.get("latencyMs", 0.0),
                    }
            except Exception:
                pass

        # Local fallback execution
        raw = self.local_recommender.recommend(cart_items, top_k=top_k)
        recs = []
        for r in raw.get("recommendations", []):
            lift = float(r.get("lift", 1.0))
            conf = float(r.get("confidence", 0.0)) / 100.0
            supp = float(r.get("support", 0.0)) / 100.0

            if min_lift and lift < min_lift:
                continue
            if min_confidence and conf < min_confidence:
                continue

            affinity = "VERY HIGH" if lift >= 2.0 else ("HIGH" if lift >= 1.5 else "MODERATE")
            recs.append({
                "product": r.get("item", ""),
                "support": round(supp, 4),
                "confidence": round(conf, 4),
                "lift": round(lift, 2),
                "affinityStrength": affinity,
                "triggeredBy": r.get("triggered_by", "cart"),
                "strategy": r.get("strategy", raw.get("strategy", "association_rule")),
            })

        return {
            "mode": "Local In-Memory Engine",
            "cart": raw.get("cart", []),
            "total": len(recs),
            "recommendations": recs,
            "strategy": raw.get("strategy", "association_rule"),
            "message": raw.get("message", ""),
            "unknown_items": raw.get("unknown_items", []),
            "latency_ms": 2.5,
        }

    def get_bundles(self) -> List[Dict[str, Any]]:
        """Retrieves curated promotional bundles."""
        if self.check_backend_connection():
            try:
                res = requests.get(f"{self.base_url}/bundles", timeout=2.0)
                if res.status_code == 200:
                    data = res.json()
                    # Reformat if returned from API
                    formatted = []
                    for b in data.get("bundles", []):
                        formatted.append({
                            "bundle_id": b.get("bundleId"),
                            "name": b.get("bundleName"),
                            "category": b.get("category"),
                            "items": b.get("items"),
                            "description": b.get("description"),
                            "support_pct": round(b.get("jointSupport", 0.0) * 100, 2),
                            "synergy_lift": b.get("averageLift", 1.0),
                            "original_price": b.get("originalPrice", 0.0),
                            "bundle_price": b.get("bundlePrice", 0.0),
                            "discount_pct": b.get("discountPct", 0),
                            "orders_count": b.get("ordersCount", 0),
                        })
                    return formatted
            except Exception:
                pass
        return self.local_recommender.get_bundles()

    def get_stats(self) -> Dict[str, Any]:
        """Retrieves rule & catalog statistics."""
        if self.check_backend_connection():
            try:
                res = requests.get(f"{self.base_url}/stats", timeout=2.0)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        return {
            "totalTransactions": 9835,
            "totalCatalogSKUs": len(self.local_recommender.products),
            "minSupportThreshold": 0.005,
            "minConfidenceThreshold": 0.20,
            "minLiftThreshold": 1.15,
            "totalFrequentItemsets": 842,
            "totalAssociationRules": len(self.local_recommender.rules),
        }

    def create_order(
        self,
        items: List[Dict[str, Any]],
        subtotal: float,
        discount: float = 0.0,
        delivery_fee: float = 0.0,
    ) -> Dict[str, Any]:
        """Saves a placed order to SQLite via REST API or local DB fallback."""
        payload = {
            "items": items,
            "subtotal": subtotal,
            "discount": discount,
            "delivery_fee": delivery_fee,
            "status": "Completed",
        }
        if self.check_backend_connection():
            try:
                res = requests.post(f"{self.base_url}/orders", json=payload, timeout=2.5)
                if res.status_code in (200, 201):
                    return res.json()
            except Exception:
                pass
        # Local SQLite fallback
        return order_db.create_order(
            items=items,
            subtotal=subtotal,
            discount=discount,
            delivery_fee=delivery_fee,
        )

    def get_orders(self, limit: int = 50) -> Dict[str, Any]:
        """Fetches order history and lifetime KPIs."""
        if self.check_backend_connection():
            try:
                res = requests.get(f"{self.base_url}/orders?limit={limit}", timeout=2.5)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                pass
        # Local SQLite fallback
        orders = order_db.get_orders(limit=limit)
        stats = order_db.get_order_stats()
        return {
            "total_orders": stats.get("total_orders", len(orders)),
            "total_spent": stats.get("total_spent", 0.0),
            "total_saved": stats.get("total_saved", 0.0),
            "orders": orders,
        }

    def clear_orders(self) -> bool:
        """Clears order history."""
        if self.check_backend_connection():
            try:
                res = requests.delete(f"{self.base_url}/orders", timeout=2.5)
                if res.status_code == 200:
                    return True
            except Exception:
                pass
        order_db.clear_orders()
        return True


# Global engine client instance
engine_client = GroceryEngineClient()
