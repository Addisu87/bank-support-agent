import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bank_agent.db.crud import init_db
from bank_agent.core.config import settings

# REST routers
from bank_agent.routers.auth_router import router as auth_router
from bank_agent.routers.users_router import router as users_router
from bank_agent.routers.agent_router import router as agent_router

# Import MCP app from mcp_router.py
from bank_agent.routers.mcp_router import router as mcp_app

# Configure logfire
if settings.LOGFIRE_TOKEN:
    logfire.configure(token=settings.LOGFIRE_TOKEN)
    logfire.instrument_pydantic_ai()

# Main FastAPI app
app = FastAPI(title="Bank Agent Unified App")

# REST routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])

# Mount MCP app
app.mount("/mcp", mcp_app)

# CORS
origins = [
    "http://127.0.0.1",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup
@app.on_event("startup")
async def startup():
    logfire.info("Database initialized successfully.")
    await init_db()

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}


# Run locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
