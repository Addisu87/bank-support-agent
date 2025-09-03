# FastAPI entrypoint, include routers, startup/shutdown events

from bank_agent.db.storage import init_db
from fastapi import FastAPI
import logfire
from bank_agent.routers.auth_router import router as auth_router
from bank_agent.routers.mcp_router import router as mcp_router

app = FastAPI(title="Bank Agent - Production LLM Agents")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(mcp_router, prefix="/mcp", tags=["mcp"])

@app.on_event("startup")
async def startup():
    await init_db()
    logfire("✅ Database initialized successfully")

@app.get("/health")
async def health():
    return {"status": "ok"}