"""Customer Service: drafts messages to requesters. Drafts only, never sent."""

from models import SpecialistReport
from team import make_agent

customer_service_agent = make_agent(
    name="customer_service",
    prompt_file="customer_service.md",
    mcp_tools=["get_shop_date", "get_ticket", "draft_customer_message", "list_message_drafts"],
    delegates_to=["inventory", "accounting", "facilities"],
    output_type=SpecialistReport,
)
