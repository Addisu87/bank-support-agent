import logfire
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.db.postgres import engine, init_db
from app.core.config import settings

# REST routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.accounts import router as account_router
from app.api.v1.agent import router as agent_router
from app.api.v1.banks import router as banks_router

# Configure logfire
if settings.LOGFIRE_TOKEN:
    logfire.configure(token=settings.LOGFIRE_TOKEN)
    logfire.instrument_pydantic_ai()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logfire.info("Database initialized successfully.")
    yield
    
    # Shutdown
    await engine.dispose()
    logfire.info("Application shutdown complete.")

# Main FastAPI app
app = FastAPI(title="Bank Agent Unified App", lifespan=lifespan)

# REST routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(account_router, prefix="/api/v1/accounts", tags=["accounts"])
app.include_router(banks_router, prefix="/api/v1/banks", tags=["banks"])
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


# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}


# Run locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
