"""Accounting: cash, invoices, payment requests (human approval) and discount quotes."""

from models import SpecialistReport
from team import make_agent

accounting_agent = make_agent(
    name="accounting",
    prompt_file="accounting.md",
    mcp_tools=["get_shop_date", "pay_bill", "quote_bulk_price", "get_cash_balance",
               "list_invoices", "list_vendors", "list_payments", "list_payment_approvals",
               "request_restock_purchase", "list_purchase_orders"],
    delegates_to=["inventory", "facilities", "customer_service"],
    output_type=SpecialistReport,
)
