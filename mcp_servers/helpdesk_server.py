"""Read-only Helpdesk MCP server for TicketPilot.

This server exposes customer/order/ticket/refund lookup tools.
It deliberately does not expose refund execution or customer-message sending.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server import MCPServer

from database.db import get_connection, init_database

mcp = MCPServer(
    "TicketPilot Helpdesk",
    instructions=(
        "Read-only support data tools. Use these tools to retrieve customer, order, "
        "ticket, and refund-history records. Never infer missing data."
    ),
)


@mcp.tool()
def get_customer(customer_id: str = "", email: str = "") -> dict:
    """Look up one customer by exact customer ID or exact email address.

    Provide either customer_id or email. Returns a customer record or a not-found result.
    """
    if not customer_id.strip() and not email.strip():
        return {"found": False, "error": "Provide customer_id or email."}

    query = "SELECT customer_id, full_name, email, phone, created_at FROM customers WHERE "
    value = customer_id.strip() if customer_id.strip() else email.strip()
    query += "customer_id = ?" if customer_id.strip() else "email = ?"

    with get_connection() as connection:
        row = connection.execute(query, (value,)).fetchone()

    if row is None:
        return {"found": False, "customer": None}
    return {"found": True, "customer": dict(row)}


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Retrieve one order by its exact order ID, including customer ID and payment/order status."""
    if not order_id.strip():
        return {"found": False, "error": "order_id is required."}

    with get_connection() as connection:
        row = connection.execute(
            """SELECT order_id, customer_id, product_name, order_amount, currency,
                      order_status, payment_status, ordered_at, delivered_at
               FROM orders WHERE order_id = ?""",
            (order_id.strip(),),
        ).fetchone()

    if row is None:
        return {"found": False, "order": None}
    return {"found": True, "order": dict(row)}


@mcp.tool()
def get_customer_orders(customer_id: str, limit: int = 10) -> dict:
    """List a customer's orders, newest first. Limit is clamped between 1 and 50."""
    if not customer_id.strip():
        return {"found": False, "error": "customer_id is required.", "orders": []}

    safe_limit = max(1, min(int(limit), 50))
    with get_connection() as connection:
        customer = connection.execute(
            "SELECT customer_id FROM customers WHERE customer_id = ?",
            (customer_id.strip(),),
        ).fetchone()
        if customer is None:
            return {"found": False, "customer_id": customer_id, "orders": []}

        rows = connection.execute(
            """SELECT order_id, customer_id, product_name, order_amount, currency,
                      order_status, payment_status, ordered_at, delivered_at
               FROM orders
               WHERE customer_id = ?
               ORDER BY ordered_at DESC
               LIMIT ?""",
            (customer_id.strip(), safe_limit),
        ).fetchall()

    return {"found": True, "customer_id": customer_id, "orders": [dict(row) for row in rows]}


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Retrieve a support ticket by its exact ticket ID."""
    if not ticket_id.strip():
        return {"found": False, "error": "ticket_id is required."}

    with get_connection() as connection:
        row = connection.execute(
            """SELECT ticket_id, customer_id, order_id, subject, message,
                      reported_category, status, created_at
               FROM tickets WHERE ticket_id = ?""",
            (ticket_id.strip(),),
        ).fetchone()

    if row is None:
        return {"found": False, "ticket": None}
    return {"found": True, "ticket": dict(row)}


@mcp.tool()
def get_refund_history(order_id: str) -> dict:
    """List refund records for an exact order ID. This tool does not issue refunds."""
    if not order_id.strip():
        return {"found": False, "error": "order_id is required.", "refunds": []}

    with get_connection() as connection:
        order = connection.execute(
            "SELECT order_id FROM orders WHERE order_id = ?",
            (order_id.strip(),),
        ).fetchone()
        if order is None:
            return {"found": False, "order_id": order_id, "refunds": []}

        rows = connection.execute(
            """SELECT refund_id, order_id, amount, currency, refund_status,
                      requested_at, processed_at
               FROM refunds WHERE order_id = ?
               ORDER BY requested_at DESC""",
            (order_id.strip(),),
        ).fetchall()

    return {"found": True, "order_id": order_id, "refunds": [dict(row) for row in rows]}


if __name__ == "__main__":
    init_database()
    mcp.run()
