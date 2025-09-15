from mcp.server.fastmcp import FastMCP
from bank_agent.services.account_service import get_customer_accounts_data, get_account_transactions_data

# Create the MCP server
mcp_server = FastMCP(name="Bank Support Agent")

@mcp_server.tool()
async def get_customer_balance_by_email(user_email: str) -> list[dict]:
    """Returns the customer's current account balance."""
    return await get_customer_accounts_data(user_email)

@mcp_server.tool()
async def recent_transactions(user_email: str, account_number: str, limit: int = 5) -> list[dict]:
    """Returns the customer's recent transactions for a given account."""
    return await get_account_transactions_data(user_email, account_number, limit)

# Expose its FastAPI app as router so `main.py` can include it
router = mcp_server.streamable_http_app()
