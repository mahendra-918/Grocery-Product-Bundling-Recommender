"""
In-memory Recommender Service layer.
Coordinates GroceryRecommender engine, formats API responses, and calculates metrics.
"""

import time
from typing import Dict, List, Optional
from ml.recommender import GroceryRecommender
from backend.config import settings
from backend.schemas import (
    BundleResponseItem,
    BundlesResponse,
    HealthResponse,
    ProductsResponse,
    RecommendationItem,
    RecommendRequest,
    RecommendResponse,
    StatsResponse,
)


def calculate_affinity_strength(lift: float) -> str:
    """Categorizes rule synergy into marketing affinity tiers."""
    if lift >= 2.0:
        return "VERY HIGH"
    elif lift >= 1.5:
        return "HIGH"
    elif lift >= 1.15:
        return "MODERATE"
    return "LOW"


class RecommenderService:
    """Singleton service wrapping the core GroceryRecommender for the API."""

    def __init__(self):
        self.recommender = GroceryRecommender(
            rules_path=str(settings.RULES_PATH),
            products_path=str(settings.PRODUCTS_PATH),
            bundles_path=str(settings.BUNDLES_PATH),
        )

    def get_health(self, uptime_seconds: float) -> HealthResponse:
        """Returns API health status, loaded rules count, and catalog size."""
        return HealthResponse(
            status="healthy",
            version=settings.VERSION,
            artifactVersion=settings.ARTIFACT_VERSION,
            rulesLoaded=len(self.recommender.rules),
            catalogSize=len(self.recommender.products),
            uptimeSeconds=round(uptime_seconds, 1),
        )

    def get_products(self) -> ProductsResponse:
        """Returns the complete list of unique catalog grocery SKUs."""
        products = self.recommender.get_products()
        return ProductsResponse(
            total=len(products),
            products=products,
        )

    def get_recommendations(self, req: RecommendRequest) -> RecommendResponse:
        """
        Executes sub-10ms in-memory association lookup for customer cart.
        Applies optional dynamic confidence and lift filters.
        """
        start_time = time.perf_counter()

        # Call core recommender engine
        raw_res = self.recommender.recommend(cart_items=req.items, top_k=req.top_k)
        raw_recs = raw_res.get("recommendations", [])

        # Apply user threshold filters if provided
        filtered_recs: List[RecommendationItem] = []
        for r in raw_recs:
            lift = float(r.get("lift", 1.0))
            # recommender stores confidence as percentage (0-100), convert to ratio (0-1) for API
            conf_pct = float(r.get("confidence", 0.0))
            conf_ratio = conf_pct / 100.0 if conf_pct > 1.0 else conf_pct
            supp_pct = float(r.get("support", 0.0))
            supp_ratio = supp_pct / 100.0 if supp_pct > 1.0 else supp_pct

            if req.min_lift is not None and lift < req.min_lift:
                continue
            if req.min_confidence is not None and conf_ratio < req.min_confidence:
                continue

            filtered_recs.append(
                RecommendationItem(
                    product=r.get("item", ""),
                    support=round(supp_ratio, 4),
                    confidence=round(conf_ratio, 4),
                    lift=round(lift, 2),
                    affinityStrength=calculate_affinity_strength(lift),
                    triggeredBy=r.get("triggered_by"),
                    strategy=r.get("strategy", raw_res.get("strategy", "association_rule")),
                )
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return RecommendResponse(
            queryItems=raw_res.get("cart", []),
            totalReturned=len(filtered_recs),
            recommendations=filtered_recs,
            strategy=raw_res.get("strategy", "association_rule"),
            message=raw_res.get("message", "Success"),
            unknownItems=raw_res.get("unknown_items", []),
            latencyMs=latency_ms,
        )

    def get_bundles(self, min_size: int = 2, limit: int = 10) -> BundlesResponse:
        """Retrieves curated promotional bundles filtered by size and count."""
        raw_bundles = self.recommender.get_bundles()

        filtered_bundles: List[BundleResponseItem] = []
        for b in raw_bundles:
            items = b.get("items", [])
            if len(items) >= min_size:
                support_pct = float(b.get("support_pct", 0.0))
                joint_support = support_pct / 100.0 if support_pct > 1.0 else support_pct

                filtered_bundles.append(
                    BundleResponseItem(
                        bundleId=b.get("bundle_id", ""),
                        bundleName=b.get("name", ""),
                        category=b.get("category", "General"),
                        items=items,
                        description=b.get("description"),
                        jointSupport=round(joint_support, 4),
                        averageLift=round(float(b.get("synergy_lift", 1.0)), 2),
                        originalPrice=round(float(b.get("original_price", 0.0)), 2),
                        bundlePrice=round(float(b.get("bundle_price", 0.0)), 2),
                        discountPct=int(b.get("discount_pct", 0)),
                        ordersCount=b.get("orders_count"),
                    )
                )

        # Slice to requested limit
        sliced = filtered_bundles[:limit]
        return BundlesResponse(
            totalBundles=len(sliced),
            bundles=sliced,
        )

    def get_stats(self) -> StatsResponse:
        """Returns rule mining and catalog distribution statistics."""
        return StatsResponse(
            totalTransactions=9835,
            totalCatalogSKUs=len(self.recommender.products),
            minSupportThreshold=0.005,
            minConfidenceThreshold=settings.DEFAULT_MIN_CONFIDENCE,
            minLiftThreshold=settings.DEFAULT_MIN_LIFT,
            totalFrequentItemsets=842,
            totalAssociationRules=len(self.recommender.rules),
        )


# Global service instance
recommender_service = RecommenderService()
