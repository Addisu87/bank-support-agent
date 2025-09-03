from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def mcp_health():
    return {"status": "mcp_router_ok"}
