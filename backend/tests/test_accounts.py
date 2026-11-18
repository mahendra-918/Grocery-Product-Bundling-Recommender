from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.db import order_db
from backend.main import app


def test_accounts_isolate_orders_and_logout_revokes_session():
    with TemporaryDirectory() as directory, patch.object(order_db, "DB_PATH", Path(directory) / "test.db"):
        client = TestClient(app)
        password = "test-only-password"
        first = {"username": "first-shopper", "password": password}
        second = {"username": "second-shopper", "password": password}

        def register(credentials):
            response = client.post("/api/v1/auth/register", json=credentials)
            assert response.status_code == 201
            return {"Authorization": f"Bearer {response.json()['token']}"}

        assert client.get("/api/v1/orders").status_code == 401
        first_headers = register(first)
        second_headers = register(second)
        assert client.post("/api/v1/auth/register", json=first).status_code == 409
        assert client.post("/api/v1/auth/login", json={**first, "password": "wrong-password"}).status_code == 401

        order = {
            "items": [{"product_name": "whole milk", "unit_price": 2.99, "quantity": 2}],
            "subtotal": 5.98,
        }
        response = client.post("/api/v1/orders", json=order, headers=first_headers)
        assert response.status_code == 201
        order_id = response.json()["order_id"]
        assert client.get(f"/orders/{order_id}", headers=second_headers).status_code == 404
        assert client.get("/orders", headers=second_headers).json()["total_orders"] == 0
        assert client.delete("/orders", headers=second_headers).status_code == 200
        assert client.get("/orders", headers=first_headers).json()["total_orders"] == 1

        assert client.post("/api/v1/auth/logout", headers=first_headers).status_code == 204
        assert client.get("/orders", headers=first_headers).status_code == 401
        response = client.post("/api/v1/auth/login", json=first)
        assert response.status_code == 200
        signed_in = {"Authorization": f"Bearer {response.json()['token']}"}
        assert client.get(f"/orders/{order_id}", headers=signed_in).json()["items"][0]["quantity"] == 2
