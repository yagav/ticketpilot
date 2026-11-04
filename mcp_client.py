"""Streamlit-to-MCP client for TicketPilot's local Helpdesk server."""
import os
import sys
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters

PROJECT_ROOT = Path(__file__).resolve().parent
SERVER_FILE = PROJECT_ROOT / "mcp_servers" / "helpdesk_server.py"


def _tool_payload(result: Any) -> Any:
    """Return structured tool data when available, otherwise readable text blocks."""
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured

    text_parts = []
    for item in getattr(result, "content", []) or []:
        item_text = getattr(item, "text", None)
        if item_text:
            text_parts.append(item_text)
    return {"content": text_parts}


async def run_helpdesk_lookups(customer_email: str = "", order_id: str = "") -> dict:
    """Launch the real stdio MCP server and run lookups relevant to the ticket."""
    if not SERVER_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find Helpdesk MCP server at {SERVER_FILE}. "
            "Make sure mcp_servers/helpdesk_server.py is inside the TicketPilot project."
        )

    # The MCP SDK v2 client launches this script as a subprocess over stdio.
    # PYTHONPATH ensures imports such as `database.db` resolve from the project root.
    child_env = {
        "PYTHONPATH": str(PROJECT_ROOT),
        "TICKETPILOT_DB_PATH": os.getenv(
            "TICKETPILOT_DB_PATH",
            str(PROJECT_ROOT / "database" / "ticketpilot.db"),
        ),
    }
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
        env=child_env,
    )

    results = {}
    async with Client(server) as client:
        available = await client.list_tools()
        available_names = {tool.name for tool in available.tools}

        async def call(name: str, arguments: dict):
            if name not in available_names:
                raise RuntimeError(f"MCP server does not expose expected tool: {name}")
            response = await client.call_tool(name, arguments)
            if getattr(response, "is_error", False):
                raise RuntimeError(f"{name} returned an MCP tool error: {_tool_payload(response)}")
            data = _tool_payload(response)
            results[name] = data
            return data

        customer_data = None
        if customer_email and customer_email.strip():
            customer_data = await call("get_customer", {"email": customer_email.strip()})
        else:
            results["get_customer"] = {
                "skipped": True,
                "reason": "No customer email was supplied in the ticket form.",
            }

        if order_id and order_id.strip():
            order_data = await call("get_order", {"order_id": order_id.strip()})
            await call("get_refund_history", {"order_id": order_id.strip()})
        else:
            order_data = None
            results["get_order"] = {
                "skipped": True,
                "reason": "No order ID was supplied in the ticket form.",
            }
            results["get_refund_history"] = {
                "skipped": True,
                "reason": "No order ID was supplied in the ticket form.",
            }

        # Only fetch a customer's order list when the exact email lookup succeeded.
        customer_record = None
        if isinstance(customer_data, dict):
            customer_record = customer_data.get("customer")
        if customer_record and customer_record.get("customer_id"):
            await call(
                "get_customer_orders",
                {"customer_id": customer_record["customer_id"], "limit": 10},
            )
        else:
            results["get_customer_orders"] = {
                "skipped": True,
                "reason": "Customer lookup did not return a matching customer record.",
            }

        # get_ticket is intentionally not called: the current Streamlit form does not
        # create/persist a ticket_id in SQLite, so there is no reliable ID to query.
        results["get_ticket"] = {
            "skipped": True,
            "reason": "The manually entered ticket is session-only and has no database ticket ID yet.",
        }

    return results
