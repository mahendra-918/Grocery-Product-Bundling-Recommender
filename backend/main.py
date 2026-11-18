"""
FastAPI REST Microservice for Grocery Product Bundling & Recommendations.
Serves real-time association rule lookups, catalog metadata, and curated promotional packs.
"""

import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.config import settings
from backend.schemas import (
    BundlesResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    OrderCreateRequest,
    OrderHistoryResponse,
    OrderResponse,
    ProductsResponse,
    RecommendRequest,
    RecommendResponse,
    StatsResponse,
)
from backend.services.recommender_service import recommender_service
from backend.db import accounts, order_db

START_TIME = time.time()
MODEL_ERROR = {503: {"model": ErrorResponse, "description": "Association rules are unavailable"}}
RECOMMEND_ERRORS = {
    400: {"model": ErrorResponse, "description": "The cart has no products"},
    404: {"model": ErrorResponse, "description": "A product is missing from the catalog"},
    422: {"model": ErrorResponse, "description": "Request validation failed"},
    **MODEL_ERROR,
}

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade Market Basket Analysis & Product Bundling recommendation engine. "
        "Powered by FP-Growth association rule learning with explainable Lift, Confidence, and Support metrics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Custom Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        409: "CONFLICT",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    detail = exc.detail
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    if isinstance(detail, dict):
        code = detail.get("code", code)
        detail = detail.get("message", detail)
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=ErrorResponse(
            error=ErrorDetail(
                code=code,
                message=str(detail),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join([f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']}" for err in exc.errors()])
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=f"Request validation failed: {error_msg}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ).model_dump(),
    )


# --- Route Handlers ---

@app.get("/", tags=["Root"])
def root():
    """Root metadata & service links."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "products": "/api/v1/products",
            "recommend": "/api/v1/recommend",
            "bundles": "/api/v1/bundles",
            "stats": "/api/v1/stats",
        },
    }


def require_model_rules() -> None:
    if recommender_service.recommender.rules.empty:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "RULES_NOT_LOADED",
                "message": "Association rules are unavailable. Check the model artifact and restart the API.",
            },
        )


@app.get("/health", response_model=HealthResponse, responses=MODEL_ERROR, tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", response_model=HealthResponse, responses=MODEL_ERROR, tags=["Health"])
def get_health() -> HealthResponse:
    """Verifies service uptime, loaded association rules count, and SKU catalog size."""
    require_model_rules()
    uptime = time.time() - START_TIME
    return recommender_service.get_health(uptime_seconds=uptime)


@app.get("/products", response_model=ProductsResponse, tags=["Catalog"])
@app.get(f"{settings.API_V1_STR}/products", response_model=ProductsResponse, tags=["Catalog"])
def get_products() -> ProductsResponse:
    """Retrieves all 169 available unique grocery SKUs for autocomplete and selection."""
    return recommender_service.get_products()


@app.post("/recommend", response_model=RecommendResponse, responses=RECOMMEND_ERRORS, tags=["Recommendations"])
@app.post(f"{settings.API_V1_STR}/recommend", response_model=RecommendResponse, responses=RECOMMEND_ERRORS, tags=["Recommendations"])
def get_recommendations(request: RecommendRequest) -> RecommendResponse:
    """
    Sub-10ms basket recommendation query based on FP-Growth association rules.
    Accepts customer basket items and returns high-synergy products with explainable Lift & Confidence.
    """
    products = sorted({item.strip().lower() for item in request.items if item.strip()})
    if not products:
        raise HTTPException(status_code=400, detail="At least one product must be specified.")

    require_model_rules()
    unknown_products = set(products) - recommender_service.recommender.products_set
    if unknown_products:
        names = ", ".join(sorted(unknown_products))
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PRODUCT_NOT_FOUND",
                "message": f"Products not found in the grocery catalog: {names}. Use /products to find valid names.",
            },
        )

    return recommender_service.get_recommendations(request)


@app.get("/bundles", response_model=BundlesResponse, tags=["Bundles"])
@app.get(f"{settings.API_V1_STR}/bundles", response_model=BundlesResponse, tags=["Bundles"])
def get_bundles(
    min_size: int = Query(default=2, ge=2, le=10, description="Minimum item count in bundle"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum bundles to return"),
) -> BundlesResponse:
    """Retrieves pre-packaged, high-affinity grocery bundles with calculated discount pricing."""
    return recommender_service.get_bundles(min_size=min_size, limit=limit)


@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
@app.get(f"{settings.API_V1_STR}/stats", response_model=StatsResponse, tags=["Statistics"])
def get_stats() -> StatsResponse:
    """Returns dataset summary, frequent itemset count, and rule distribution parameters."""
    return recommender_service.get_stats()


class AccountCredentials(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128, repr=False)


class AccountSession(BaseModel):
    username: str
    token: str


bearer = HTTPBearer(auto_error=False)


def require_account(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> int:
    user_id = accounts.session_user(credentials.credentials) if credentials else None
    if user_id is None:
        raise HTTPException(401, "Sign in to access your orders.", headers={"WWW-Authenticate": "Bearer"})
    return user_id


@app.post(f"{settings.API_V1_STR}/auth/register", response_model=AccountSession, status_code=201, tags=["Accounts"])
def register_account(payload: AccountCredentials) -> AccountSession:
    username = payload.username.lower()
    if not accounts.register(username, payload.password):
        raise HTTPException(409, "That username is already taken.")
    return AccountSession(username=username, token=accounts.sign_in(username, payload.password))


@app.post(f"{settings.API_V1_STR}/auth/login", response_model=AccountSession, tags=["Accounts"])
def sign_in_account(payload: AccountCredentials) -> AccountSession:
    username = payload.username.lower()
    token = accounts.sign_in(username, payload.password)
    if token is None:
        raise HTTPException(401, "Incorrect username or password.")
    return AccountSession(username=username, token=token)


@app.post(f"{settings.API_V1_STR}/auth/logout", status_code=204, tags=["Accounts"])
def sign_out_account(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)):
    if credentials:
        accounts.sign_out(credentials.credentials)


# --- Order History Endpoints (SQLite-backed) ---
@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
@app.post(f"{settings.API_V1_STR}/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_customer_order(payload: OrderCreateRequest, user_id: int = Depends(require_account)) -> OrderResponse:
    """Persists a placed order and line items into SQLite database."""
    items_data = [item.model_dump() for item in payload.items]
    order = order_db.create_order(
        items=items_data,
        subtotal=payload.subtotal,
        discount=payload.discount,
        delivery_fee=payload.delivery_fee,
        status=payload.status or "Completed",
        user_id=user_id,
    )
    if not order:
        raise HTTPException(status_code=500, detail="Failed to persist order to database.")
    return OrderResponse(**order)


@app.get("/orders", response_model=OrderHistoryResponse, tags=["Orders"])
@app.get(f"{settings.API_V1_STR}/orders", response_model=OrderHistoryResponse, tags=["Orders"])
def get_order_history(limit: int = Query(default=50, ge=1, le=100), user_id: int = Depends(require_account)) -> OrderHistoryResponse:
    """Retrieves all past orders and lifetime summary metrics from SQLite."""
    orders = order_db.get_orders(limit=limit, user_id=user_id)
    stats = order_db.get_order_stats(user_id=user_id)
    return OrderHistoryResponse(
        total_orders=stats.get("total_orders", len(orders)),
        total_spent=stats.get("total_spent", 0.0),
        total_saved=stats.get("total_saved", 0.0),
        orders=[OrderResponse(**o) for o in orders],
    )


@app.get("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
@app.get(f"{settings.API_V1_STR}/orders/{{order_id}}", response_model=OrderResponse, tags=["Orders"])
def get_order_by_id(order_id: str, user_id: int = Depends(require_account)) -> OrderResponse:
    """Retrieves single order details by its order ID."""
    order = order_db.get_order_by_id(order_id, user_id=user_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found.")
    return OrderResponse(**order)


@app.delete("/orders", tags=["Orders"])
@app.delete(f"{settings.API_V1_STR}/orders", tags=["Orders"])
def clear_all_orders(user_id: int = Depends(require_account)):
    """Clears all orders from the SQLite database."""
    order_db.clear_orders(user_id=user_id)
    return {"status": "success", "message": "Order history cleared."}

