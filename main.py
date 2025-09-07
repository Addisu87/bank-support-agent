# FastAPI entrypoint, include routers, startup/shutdown events

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bank_agent.db.crud import init_db
from bank_agent.core.config import settings
from bank_agent.routers.auth_router import router as auth_router
from bank_agent.routers.users_router import router as users_router


# configure logfire
if settings.LOGFIRE_TOKEN:
    logfire.configure(token=settings.LOGFIRE_TOKEN)
    logfire.instrument_pydantic_ai()

app = FastAPI(title="Bank Agent - Production LLM Agents")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])

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

@app.on_event("startup")
async def startup():
    logfire.info("Database initialize successfully.")
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}