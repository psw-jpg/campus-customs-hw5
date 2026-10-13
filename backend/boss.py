"""Boss: reads the ticket, delegates to specialists, makes the final call."""

from models import TicketDecision
from team import make_agent

boss_agent = make_agent(
    name="boss",
    prompt_file="boss.md",
    mcp_tools=["get_shop_date", "get_ticket", "list_tickets", "update_ticket",
               "list_payment_approvals", "list_message_drafts", "list_purchase_orders"],
    delegates_to=["inventory", "accounting", "facilities", "customer_service"],
    output_type=TicketDecision,
)
