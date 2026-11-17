"""
Production Grocery Recommender Engine.
Loads precomputed association rules, serves low-latency cart recommendations,
and exposes curated theme bundles with explainability and fallback strategies.
"""

import json
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd

# Support standalone and package imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_FALLBACK_STAPLES = [
    "whole milk",
    "other vegetables",
    "rolls/buns",
    "soda",
    "yogurt"
]


class GroceryRecommender:
    """
    High-performance, in-memory association rule recommender.
    Provides sub-5ms query times with explainable metrics (Lift, Confidence, Support).
    """

    def __init__(
        self,
        rules_path: Optional[str] = None,
        products_path: Optional[str] = None,
        bundles_path: Optional[str] = None,
        fallback_staples: Optional[List[str]] = None
    ):
        models_dir = project_root / "models"

        self.rules_path = Path(rules_path) if rules_path else (models_dir / "association_rules.pkl")
        self.products_path = Path(products_path) if products_path else (models_dir / "products.json")
        self.bundles_path = Path(bundles_path) if bundles_path else (models_dir / "top_bundles.json")
        self.fallback_staples = fallback_staples or DEFAULT_FALLBACK_STAPLES

        self.rules: pd.DataFrame = pd.DataFrame()
        self.products: List[str] = []
        self.products_set: Set[str] = set()
        self.bundles: List[Dict[str, Any]] = []

        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Loads serialized rules, products, and bundles into memory."""
        # 1. Load Association Rules
        if self.rules_path.exists():
            with open(self.rules_path, "rb") as f:
                self.rules = pickle.load(f)
            # Ensure antecedents and consequents are sets for fast subset checks
            if not self.rules.empty:
                if not isinstance(self.rules["antecedents"].iloc[0], (set, frozenset)):
                    self.rules["antecedents"] = self.rules["antecedents"].apply(set)
                if not isinstance(self.rules["consequents"].iloc[0], (set, frozenset)):
                    self.rules["consequents"] = self.rules["consequents"].apply(set)
        else:
            print(f"Warning: Association rules artifact not found at {self.rules_path}. Recommender in fallback mode.")

        # 2. Load Products Catalog
        if self.products_path.exists():
            with open(self.products_path, "r", encoding="utf-8") as f:
                self.products = json.load(f)
            self.products_set = set(self.products)
        else:
            print(f"Warning: Products catalog not found at {self.products_path}.")

        # 3. Load Theme Bundles
        if self.bundles_path.exists():
            with open(self.bundles_path, "r", encoding="utf-8") as f:
                self.bundles = json.load(f)
        else:
            print(f"Warning: Theme bundles artifact not found at {self.bundles_path}.")

    def get_products(self) -> List[str]:
        """Returns the sorted list of all catalog products (169 SKUs)."""
        return list(self.products)

    def get_bundles(self) -> List[Dict[str, Any]]:
        """Returns the pre-mined theme bundles."""
        return list(self.bundles)

    def get_bundle_by_id(self, bundle_id: str) -> Optional[Dict[str, Any]]:
        """Finds and returns a single bundle by ID, or None if not found."""
        for bundle in self.bundles:
            if bundle.get("bundle_id") == bundle_id:
                return bundle
        return None

    def recommend(self, cart_items: List[str], top_k: int = 5) -> Dict[str, Any]:
        """
        Generates personalized, explainable product recommendations for a customer's cart.

        Args:
            cart_items: List of product names in the customer's cart.
            top_k: Maximum number of recommendations to return (default: 5).

        Returns:
            Dict containing recommendations, strategy, status message, and cart metadata.
        """
        # 1. Sanitize cart items
        normalized_cart = sorted(list(set(
            str(item).strip().lower() for item in cart_items if str(item).strip()
        )))
        cart_set = set(normalized_cart)

        # Detect unknown items if product catalog is populated
        unknown_items = [item for item in normalized_cart if self.products_set and item not in self.products_set]

        # 2. Handle empty cart or missing rules -> Fallback
        if not cart_set or self.rules.empty:
            fallback_items = [item for item in self.fallback_staples if item not in cart_set][:top_k]
            return {
                "cart": normalized_cart,
                "recommendations": [
                    {
                        "item": item,
                        "triggered_by": "store_bestseller",
                        "lift": 1.00,
                        "confidence": 0.0,
                        "support": 0.0,
                        "strategy": "fallback_staples"
                    }
                    for item in fallback_items
                ],
                "strategy": "fallback_staples",
                "message": "Cart is empty or no rules available; displaying top store staples.",
                "unknown_items": unknown_items
            }

        # 3. Match association rules: antecedent must be a subset of cart
        matching_rules = self.rules[
            self.rules["antecedents"].apply(lambda ant: ant.issubset(cart_set))
        ]

        if matching_rules.empty:
            # Cold start / no matching rules
            fallback_items = [item for item in self.fallback_staples if item not in cart_set][:top_k]
            return {
                "cart": normalized_cart,
                "recommendations": [
                    {
                        "item": item,
                        "triggered_by": "store_bestseller",
                        "lift": 1.00,
                        "confidence": 0.0,
                        "support": 0.0,
                        "strategy": "fallback_staples"
                    }
                    for item in fallback_items
                ],
                "strategy": "fallback_staples",
                "message": "No strong association rules found for this combination; falling back to store staples.",
                "unknown_items": unknown_items
            }

        # 4. Extract candidate recommendations and exclude items already in cart
        candidate_map: Dict[str, Dict[str, Any]] = {}

        for _, rule in matching_rules.iterrows():
            consequents = rule["consequents"]
            recommended_items = consequents - cart_set
            if not recommended_items:
                continue

            lift = float(rule["lift"])
            confidence = float(rule["confidence"]) * 100.0
            support = float(rule["support"]) * 100.0
            trigger = str(rule["antecedents_str"])

            for item in recommended_items:
                # Deduplicate: if an item is suggested by multiple rules, keep the highest Lift
                if item not in candidate_map or lift > candidate_map[item]["lift"]:
                    candidate_map[item] = {
                        "item": item,
                        "triggered_by": trigger,
                        "lift": round(lift, 2),
                        "confidence": round(confidence, 1),
                        "support": round(support, 2),
                        "strategy": "association_rule"
                    }

        # If all consequents were already in cart, fallback
        if not candidate_map:
            fallback_items = [item for item in self.fallback_staples if item not in cart_set][:top_k]
            return {
                "cart": normalized_cart,
                "recommendations": [
                    {
                        "item": item,
                        "triggered_by": "store_bestseller",
                        "lift": 1.00,
                        "confidence": 0.0,
                        "support": 0.0,
                        "strategy": "fallback_staples"
                    }
                    for item in fallback_items
                ],
                "strategy": "fallback_staples",
                "message": "All rule-associated items are already in your cart; showing store staples.",
                "unknown_items": unknown_items
            }

        # 5. Sort by Lift descending, tiebreak by confidence descending
        sorted_recommendations = sorted(
            candidate_map.values(),
            key=lambda x: (x["lift"], x["confidence"]),
            reverse=True
        )[:top_k]

        return {
            "cart": normalized_cart,
            "recommendations": sorted_recommendations,
            "strategy": "association_rule",
            "message": f"Found {len(sorted_recommendations)} personalized bundle recommendations.",
            "unknown_items": unknown_items
        }
