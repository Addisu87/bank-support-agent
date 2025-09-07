import asyncio
from bank_agent.integrations.obp_client import OBPClient
from bank_agent.db.postgres import get_session
from bank_agent.db.models import Bank

async def sync_obp():
    client = OBPClient()
    async with get_session() as session: 
        banks = await client.get_banks()
        for b in banks: 
            bank = Bank(name=b["full_name"], 
                        bic=b["id"],
                        country=b.get("country")
                        )
            session.add(bank)
        await session.commit()
        
if __name__ == "__main___":
    asyncio.run(sync_obp())
