from fastapi import APIRouter

from app.api.v1.accounts import router as account_router
from app.api.v1.agent import router as agent_router

# REST routers
from app.api.v1.auth import router as auth_router
from app.api.v1.banks import router as banks_router
from app.api.v1.cards import router as cards_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.users import router as users_router
from app.api.v1.email import router as email_router

api_router = APIRouter()

# REST routes
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(users_router, prefix="/users")
api_router.include_router(banks_router, prefix="/banks")
api_router.include_router(account_router, prefix="/accounts")
api_router.include_router(transactions_router, prefix="/transactions")
api_router.include_router(cards_router, prefix="/cards")
api_router.include_router(agent_router, prefix="/agent")
api_router.include_router(email_router, prefix="/email")
