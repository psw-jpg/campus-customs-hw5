"""Facilities: the Chapel Street lease, rent timing, overhead and shop layout."""

from models import SpecialistReport
from team import make_agent

facilities_agent = make_agent(
    name="facilities",
    prompt_file="facilities.md",
    mcp_tools=["get_shop_date", "list_leases", "get_inventory", "list_payment_approvals"],
    delegates_to=["inventory", "accounting", "customer_service"],
    output_type=SpecialistReport,
)
