"""Inventory: stock on hand, shortfalls, restock cost, vendor lead times and blocks."""

from models import SpecialistReport
from team import make_agent

inventory_agent = make_agent(
    name="inventory",
    prompt_file="inventory.md",
    mcp_tools=["get_shop_date", "check_restock", "get_inventory", "get_low_stock", "list_vendors", "list_purchase_orders"],
    delegates_to=["accounting", "facilities", "customer_service"],
    output_type=SpecialistReport,
)
