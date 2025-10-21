import asyncio

from app.db.models.bank import Bank
from app.db.session import get_db
from app.integrations.obp_client import OBPClient


async def sync_obp():
    client = OBPClient()
    async with get_db() as session:
        banks = await client.get_banks()
        for b in banks:
            bank = Bank(name=b["full_name"], bic=b["id"], country=b.get("country"))
            session.add(bank)
        await session.commit()


if __name__ == "__main___":
    asyncio.run(sync_obp())
