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

    def get_discovered_bundles(self) -> List[Dict[str, Any]]:
        """Read the mined combinations from the same artifact directory as the curated kits."""
        path = self.bundles_path.with_name("discovered_bundles.json")
        try:
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    def get_bundle_by_id(self, bundle_id: str) -> Optional[Dict[str, Any]]:
        """Finds and returns a single bundle by ID, or None if not found."""
        for bundle in self.bundles:
            if bundle.get("bundle_id") == bundle_id:
                return bundle
        return None

    def recommend(
        self,
        cart_items: List[str],
        top_k: int = 5,
        min_confidence: Optional[float] = None,
        min_lift: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Rank qualifying recommendations for a cart. Minimum confidence is a ratio."""
        cart_set = {str(item).strip().lower() for item in cart_items if str(item).strip()}
        normalized_cart = sorted(cart_set)
        unknown_items = [item for item in normalized_cart if self.products_set and item not in self.products_set]
        confidence_floor = min_confidence if min_confidence is not None else 0.0
        lift_floor = min_lift if min_lift is not None else 0.0

        candidate_map: Dict[str, Dict[str, Any]] = {}
        if cart_set and not self.rules.empty:
            matching_rules = self.rules[
                self.rules["antecedents"].apply(lambda ant: ant.issubset(cart_set))
            ]
            for _, rule in matching_rules.iterrows():
                lift = float(rule["lift"])
                confidence = float(rule["confidence"])
                if confidence < confidence_floor or lift < lift_floor:
                    continue

                for item in rule["consequents"] - cart_set:
                    current = candidate_map.get(item)
                    if current is None or (lift, confidence * 100) > (current["lift"], current["confidence"]):
                        candidate_map[item] = {
                            "item": item,
                            "triggered_by": str(rule["antecedents_str"]),
                            "lift": lift,
                            "confidence": confidence * 100,
                            "support": float(rule["support"]) * 100,
                            "strategy": "association_rule",
                        }

        if candidate_map:
            recommendations = sorted(
                candidate_map.values(),
                key=lambda rec: (-rec["lift"], -rec["confidence"], rec["item"]),
            )[:top_k]
            strategy = "association_rule"
            message = f"Found {len(recommendations)} personalized bundle recommendations."
        else:
            fallback_items = []
            if confidence_floor <= 0 and lift_floor <= 1:
                fallback_items = [item for item in self.fallback_staples if item not in cart_set][:top_k]
            recommendations = [
                {
                    "item": item,
                    "triggered_by": "store_bestseller",
                    "lift": 1.0,
                    "confidence": 0.0,
                    "support": 0.0,
                    "strategy": "fallback_staples",
                }
                for item in fallback_items
            ]
            strategy = "fallback_staples"
            message = (
                "No matching rules; showing store staples." if recommendations
                else "No recommendations match this cart and thresholds."
            )

        return {
            "cart": normalized_cart,
            "recommendations": recommendations,
            "strategy": strategy,
            "message": message,
            "unknown_items": unknown_items,
        }
