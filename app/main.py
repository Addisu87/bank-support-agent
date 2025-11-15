from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import create_tables, engine
from app.core.logging import LogfireMiddleware

# Configure logfire
if settings.LOGFIRE_TOKEN:
    logfire.configure(token=settings.LOGFIRE_TOKEN)
    logfire.instrument_pydantic_ai()
    logfire.instrument_sqlalchemy()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize PostgreSQL database
    await create_tables()
    logfire.info("PostgreSQL database initialized successfully")
    yield
    # Shutdown
    await engine.dispose()
    logfire.info("Application shutdown complete")


# Main FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A modern banking system with AI support agent",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logfire middleware
if settings.LOGFIRE_TOKEN:
    app.add_middleware(LogfireMiddleware)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "database": "postgresql",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
    }


# Run locally
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
