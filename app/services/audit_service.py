from app.db.schema import Audit
from app.db.session import AsyncSessionLocal

async def save_audit(actor, tool, args, result, request_id=None):
    async with AsyncSessionLocal() as session: 
        aud = Audit(actor=actor, tool=tool, args=str(args), result=str(result), request_id=request_id)
        session.add(aud)
        await session.commit()
        return aud