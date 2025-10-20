from fastapi import APIRouter

# REST routers
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.banks import router as banks_router
from app.api.v1.accounts import router as account_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.cards import router as cards_router
from app.api.v1.agent import router as agent_router

api_router = APIRouter()

# REST routes
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(banks_router, prefix="/banks", tags=["banks"])
api_router.include_router(account_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])
api_router.include_router(cards_router, prefix="/card", tags=["cards"])