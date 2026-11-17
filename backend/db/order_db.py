"""
SQLite Database Layer for FreshCart Order Management.
Zero external dependencies (uses standard library sqlite3).
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Database path in data directory
DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "freshcart.db"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dict-like row access."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initializes tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subtotal REAL NOT NULL,
                discount REAL NOT NULL DEFAULT 0.0,
                delivery_fee REAL NOT NULL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                items_count INTEGER NOT NULL,
                status TEXT DEFAULT 'Completed'
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                unit_price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
            """
        )


def create_order(
    items: List[Dict[str, Any]],
    subtotal: float,
    discount: float = 0.0,
    delivery_fee: float = 0.0,
    status: str = "Completed",
) -> Dict[str, Any]:
    """
    Creates a new customer order and associated items in SQLite.
    Returns the persisted order dict.
    """
    init_db()
    # Generate human-readable Order ID e.g. ORD-20261117-A4B2
    short_uuid = uuid.uuid4().hex[:4].upper()
    date_str = datetime.now().strftime("%Y%m%d")
    order_id = f"ORD-{date_str}-{short_uuid}"
    total_amount = round(subtotal - discount + delivery_fee, 2)
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (order_id, created_at, subtotal, discount, delivery_fee, total_amount, items_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, now_iso, subtotal, discount, delivery_fee, total_amount, len(items), status),
        )

        for item in items:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_name, unit_price, quantity)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    item.get("product_name", item.get("name", "Unknown SKU")),
                    item.get("unit_price", item.get("price", 2.49)),
                    item.get("quantity", 1),
                ),
            )
        conn.commit()

    return get_order_by_id(order_id)


def get_orders(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches all orders ordered by newest first with their items."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))
        order_rows = cursor.fetchall()

        orders = []
        for o in order_rows:
            order_dict = dict(o)
            cursor.execute(
                "SELECT product_name, unit_price, quantity FROM order_items WHERE order_id = ?",
                (order_dict["order_id"],),
            )
            order_dict["items"] = [dict(it) for it in cursor.fetchall()]
            orders.append(order_dict)

        return orders


def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single order by order_id."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            return None

        order_dict = dict(row)
        cursor.execute(
            "SELECT product_name, unit_price, quantity FROM order_items WHERE order_id = ?",
            (order_id,),
        )
        order_dict["items"] = [dict(it) for it in cursor.fetchall()]
        return order_dict


def get_order_stats() -> Dict[str, Any]:
    """Aggregates lifetime order KPIs."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0.0) as total_spent,
                COALESCE(SUM(discount), 0.0) as total_saved,
                COALESCE(SUM(items_count), 0) as total_items
            FROM orders
            """
        )
        row = cursor.fetchone()
        return dict(row) if row else {
            "total_orders": 0,
            "total_spent": 0.0,
            "total_saved": 0.0,
            "total_items": 0,
        }


def clear_orders() -> None:
    """Empties all orders and items."""
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM order_items;")
        conn.execute("DELETE FROM orders;")
        conn.commit()

