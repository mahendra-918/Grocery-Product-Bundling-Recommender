"""
Pydantic schemas and data transfer objects for the Grocery Recommender REST API.
Compatible with Pydantic v2.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# --- Health & Metadata ---
class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    version: str = Field(..., examples=["1.0.0"])
    artifactVersion: str = Field(..., examples=["fpgrowth-v1.0.0"])
    rulesLoaded: int = Field(..., examples=[861])
    catalogSize: int = Field(..., examples=[169])
    uptimeSeconds: float = Field(..., examples=[120.5])


# --- Products Catalog ---
class ProductsResponse(BaseModel):
    total: int = Field(..., examples=[169])
    products: List[str] = Field(..., examples=[["whole milk", "yogurt", "rolls/buns"]])


# --- Recommendation Request & Response ---
class RecommendationItem(BaseModel):
    product: str = Field(..., examples=["whole milk"])
    support: float = Field(..., examples=[0.0245], description="Frequency of co-occurrence as a ratio [0, 1]")
    confidence: float = Field(..., examples=[0.4120], description="Conditional probability as a ratio [0, 1]")
    lift: float = Field(..., examples=[2.15], description="Synergy multiplier over random chance (> 1.0)")
    affinityStrength: str = Field(..., examples=["VERY HIGH"], description="Affinity tier: VERY HIGH, HIGH, MODERATE, LOW")
    triggeredBy: Optional[str] = Field(None, examples=["yogurt"], description="Basket item(s) that triggered this rule")
    strategy: Optional[str] = Field("association_rule", examples=["association_rule"])


class RecommendRequest(BaseModel):
    items: List[str] = Field(
        default_factory=list,
        examples=[["yogurt", "tropical fruit"]],
        description="List of grocery item names currently in the customer's cart"
    )
    top_k: int = Field(default=5, ge=1, le=50, examples=[5], description="Maximum recommendations to return")
    min_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        examples=[0.20],
        description="Optional confidence threshold filter (0.0 to 1.0)"
    )
    min_lift: Optional[float] = Field(
        default=None,
        ge=0.0,
        examples=[1.15],
        description="Optional lift threshold filter"
    )


class RecommendResponse(BaseModel):
    queryItems: List[str] = Field(..., examples=[["yogurt"]])
    totalReturned: int = Field(..., examples=[3])
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    strategy: str = Field(..., examples=["association_rule"], description="'association_rule' or 'fallback_staples'")
    message: str = Field(..., examples=["Found 3 personalized bundle recommendations."])
    unknownItems: List[str] = Field(default_factory=list, examples=[[]])
    latencyMs: float = Field(..., examples=[3.2], description="In-memory lookup execution latency in milliseconds")


# --- Promotional Bundles ---
class BundleResponseItem(BaseModel):
    bundleId: str = Field(..., examples=["bundle_produce_stew"])
    bundleName: str = Field(..., examples=["Fresh Stew & Veggie Pack"])
    category: str = Field(..., examples=["Fresh Produce & Cooking"])
    items: List[str] = Field(..., examples=[["other vegetables", "root vegetables", "whole milk"]])
    description: Optional[str] = Field(None, examples=["Essential fresh vegetables paired with whole milk."])
    jointSupport: float = Field(..., examples=[0.0232])
    averageLift: float = Field(..., examples=[2.84])
    originalPrice: float = Field(..., examples=[8.50])
    bundlePrice: float = Field(..., examples=[7.65])
    discountPct: int = Field(..., examples=[10])
    ordersCount: Optional[int] = Field(None, examples=[228])


class BundlesResponse(BaseModel):
    totalBundles: int = Field(..., examples=[6])
    bundles: List[BundleResponseItem] = Field(default_factory=list)


# --- Dataset & Model Statistics ---
class StatsResponse(BaseModel):
    totalTransactions: int = Field(..., examples=[9835])
    totalCatalogSKUs: int = Field(..., examples=[169])
    minSupportThreshold: float = Field(..., examples=[0.005])
    minConfidenceThreshold: float = Field(..., examples=[0.20])
    minLiftThreshold: float = Field(..., examples=[1.15])
    totalFrequentItemsets: int = Field(..., examples=[842])
    totalAssociationRules: int = Field(..., examples=[861])


# --- Error Handling ---
class ErrorDetail(BaseModel):
    code: str = Field(..., examples=["PRODUCT_NOT_FOUND"])
    message: str = Field(..., examples=["Product not found."])
    requestId: Optional[str] = Field(None, examples=["req_8f3a921d"])
    timestamp: Optional[str] = Field(None, examples=["2026-10-14T15:30:00Z"])


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --- Order History & Database Schemas ---
class OrderItemPayload(BaseModel):
    product_name: str = Field(..., examples=["whole milk"])
    unit_price: float = Field(..., ge=0.0, examples=[2.99])
    quantity: int = Field(default=1, ge=1, examples=[1])


class OrderCreateRequest(BaseModel):
    items: List[OrderItemPayload] = Field(..., min_length=1)
    subtotal: float = Field(..., ge=0.0, examples=[12.50])
    discount: float = Field(default=0.0, ge=0.0, examples=[1.50])
    delivery_fee: float = Field(default=0.0, ge=0.0, examples=[0.0])
    status: Optional[str] = Field("Completed", examples=["Completed"])


class OrderItemResponse(BaseModel):
    product_name: str
    unit_price: float
    quantity: int


class OrderResponse(BaseModel):
    order_id: str
    created_at: str
    subtotal: float
    discount: float
    delivery_fee: float
    total_amount: float
    items_count: int
    status: str
    items: List[OrderItemResponse] = Field(default_factory=list)


class OrderHistoryResponse(BaseModel):
    total_orders: int
    total_spent: float
    total_saved: float
    orders: List[OrderResponse] = Field(default_factory=list)

