"""Insert clearly fictional development records for local MCP testing.

Run this only for a fresh development database. It does not create real customers.
"""
from database.db import get_connection, init_database


def seed_database() -> None:
    init_database()

    customers = [
        ("CUS-1001", "Aarav Demo", "aarav.demo@example.test", "+91-90000-10001"),
        ("CUS-1002", "Mira Sample", "mira.sample@example.test", "+91-90000-10002"),
    ]

    orders = [
        ("ORD-2026-10452", "CUS-1001", "Wireless Headphones", 2499.00, "INR",
         "delivered", "paid", "2026-10-25T10:30:00", "2026-10-28T15:20:00"),
        ("ORD-2026-10453", "CUS-1001", "USB-C Charging Cable", 499.00, "INR",
         "shipped", "paid", "2026-11-01T09:15:00", None),
        ("ORD-2026-20881", "CUS-1002", "Laptop Stand", 1299.00, "INR",
         "delivered", "paid", "2026-10-20T12:00:00", "2026-10-23T16:45:00"),
    ]

    tickets = [
        ("TKT-5001", "CUS-1001", "ORD-2026-10452",
         "Product arrived damaged",
         "The left earcup is not working and the package was damaged.",
         "damaged_or_defective", "open", "2026-11-04T09:00:00")
    ]

    refunds = [
        ("RFD-7001", "ORD-2026-20881", 1299.00, "INR",
         "completed", "2026-10-24T11:00:00", "2026-10-25T14:30:00")
    ]

    with get_connection() as connection:
        connection.executemany(
            """INSERT OR IGNORE INTO customers
               (customer_id, full_name, email, phone)
               VALUES (?, ?, ?, ?)""",
            customers,
        )
        connection.executemany(
            """INSERT OR IGNORE INTO orders
               (order_id, customer_id, product_name, order_amount, currency,
                order_status, payment_status, ordered_at, delivered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            orders,
        )
        connection.executemany(
            """INSERT OR IGNORE INTO tickets
               (ticket_id, customer_id, order_id, subject, message,
                reported_category, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            tickets,
        )
        connection.executemany(
            """INSERT OR IGNORE INTO refunds
               (refund_id, order_id, amount, currency, refund_status,
                requested_at, processed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            refunds,
        )
        connection.commit()

    print("Development database initialized and synthetic records inserted.")
    print("Sample customer: aarav.demo@example.test")
    print("Sample order: ORD-2026-10452")


if __name__ == "__main__":
    seed_database()
